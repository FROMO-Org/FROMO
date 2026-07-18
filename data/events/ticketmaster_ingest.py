"""
data/events/ticketmaster_ingest.py — Ticketmaster -> Supabase events ingestion
===============================================================================
Fetches next-day Ticketmaster events for Manhattan, upserts venues into
Supabase, generates a 3-sentence AI summary per event via Gemini, and upserts
events into Supabase.

Env vars required (see .env.example):
    TICKETMASTER_KEY
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
    GEMINI_API_KEY

CI usage (--dry-run):
    python data/events/ticketmaster_ingest.py --dry-run

Full run:
    python data/events/ticketmaster_ingest.py
"""

import argparse
import json
import os
import queue
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai
from shapely.geometry import Point, shape
from supabase import create_client

TICKETMASTER_EVENTS_URL = "https://app.ticketmaster.com/discovery/v2/events/"
MANHATTAN_GEO_URL = "https://data.cityofnewyork.us/resource/gthc-hcne.geojson?$where=boroname='Manhattan'"
MAX_PAGES_DEFAULT = 5
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_SLEEP_SECONDS = 6  # stay under Gemini free-tier rate limits between calls


def parse_args():
    p = argparse.ArgumentParser(description="Ticketmaster -> Supabase events ingestion")
    p.add_argument(
        "--dry-run", action="store_true",
        help="Validate config/imports/Manhattan polygon only — no Supabase/Gemini/Ticketmaster writes",
    )
    p.add_argument(
        "--max-pages", type=int, default=MAX_PAGES_DEFAULT,
        help="Max Ticketmaster result pages to fetch (default: %(default)s)",
    )
    return p.parse_args()


def load_config():
    load_dotenv(Path(__file__).resolve().parent / ".env")

    config = {
        "TICKETMASTER_KEY": os.getenv("TICKETMASTER_KEY"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required environment variable(s): {', '.join(missing)}")
    return config


# ── Manhattan geometry ────────────────────────────────────────────────────────

def get_manhattan_polygon():
    response = requests.get(MANHATTAN_GEO_URL, timeout=30)
    response.raise_for_status()
    geojson = response.json()
    return shape(geojson["features"][0]["geometry"])


def is_in_manhattan(lat, lon, polygon):
    if lat is None or lon is None:
        return False
    point = Point(float(lon), float(lat))  # lon first, then lat
    return polygon.contains(point)


# ── Fetch ──────────────────────────────────────────────────────────────────────

def get_date_window():
    """Return (start, end) UTC ISO strings covering tomorrow's NY calendar day."""
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    start_date_time = tomorrow.strftime("%Y-%m-%dT04:00:00Z")
    end_date_time = (tomorrow + timedelta(days=1)).strftime("%Y-%m-%dT03:59:59Z")
    return start_date_time, end_date_time


def fetch_events(api_key, polygon, max_pages=MAX_PAGES_DEFAULT):
    """Fetch next-day NYC events from Ticketmaster, filtered to Manhattan.
    Returns a queue.Queue of raw event dicts."""
    event_queue = queue.Queue()
    events_added_count = 0
    page = 0
    total_pages = 1

    start_date_time, end_date_time = get_date_window()

    while page < total_pages:
        params = {
            "apikey": api_key,
            "city": "New York",
            "stateCode": "NY",
            "startDateTime": start_date_time,
            "endDateTime": end_date_time,
            "size": 200,
            "page": page,
        }

        response = requests.get(TICKETMASTER_EVENTS_URL, params=params, timeout=30)
        if response.status_code != 200:
            print(f"Error: Ticketmaster API returned {response.status_code}")
            break

        data = response.json()
        if "page" not in data:
            break

        total_pages = min(data["page"]["totalPages"], max_pages)
        print(f"Processing Ticketmaster page: {data['page']['number']} of {total_pages}")

        events = data.get("_embedded", {}).get("events", [])
        for event in events:
            venues = event.get("_embedded", {}).get("venues", [])
            if not venues:
                continue
            location = venues[0].get("location", {})
            lat = location.get("latitude")
            lng = location.get("longitude")
            if is_in_manhattan(lat, lng, polygon):
                event_queue.put(event)
                events_added_count += 1

        page += 1
        time.sleep(0.2)

    print(f"{events_added_count} Manhattan events loaded onto the queue.")
    return event_queue


# ── Venues ─────────────────────────────────────────────────────────────────────

def handle_venue_validation(event, supabase, org_id, processed_venues):
    """Look up (or upsert) the event's venue in Supabase; return its internal id, or None."""
    venue_embedded = event.get("_embedded", {}).get("venues", [])
    if not venue_embedded:
        return None

    venue_data = venue_embedded[0]
    venue_id = venue_data.get("id")
    if not venue_id:
        return None

    if venue_id in processed_venues:
        return processed_venues[venue_id]

    print(f"New venue encountered: {venue_data.get('name')}. Syncing with DB...")
    try:
        location = venue_data.get("location", {})
        address = venue_data.get("address", {})

        response = supabase.table("venues").upsert(
            [{
                "organisation_id": org_id,
                "name": venue_data.get("name"),
                "address": address.get("line1"),
                "lat": float(location["latitude"]) if location.get("latitude") else None,
                "lng": float(location["longitude"]) if location.get("longitude") else None,
                "external_venue_id": venue_id,
            }],
            on_conflict="external_venue_id",
            ignore_duplicates=False,
        ).execute()

        supabase_internal_id = response.data[0].get("id")
        processed_venues[venue_id] = supabase_internal_id
        return supabase_internal_id
    except Exception as exception:
        print(f"FAILED to sync venue {venue_data.get('name', 'unknown')}: {exception}")
        return None


# ── AI summary + image ──────────────────────────────────────────────────────────

def get_gemini_summary(event_data, client, retries=3):
    """Calls Gemini to generate the 3-sentence summary."""
    for attempt in range(retries):
        try:
            event_json_string = json.dumps(event_data)
            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=[{
                    "type": "text",
                    "text": (
                        "Given the elements at your disposal from this JSON, give a 3 sentence "
                        "summary of the event below. Do not use any other information than what "
                        "is in the JSON. I want the name of the event, the address, the category, "
                        "and any other information that would be useful for a young adult "
                        f"attending this event.\n\nEvent JSON:\n{event_json_string}"
                    ),
                }],
            )
            return interaction.output_text
        except Exception as exception:
            if attempt == retries - 1:
                print(f"Gemini failed to summarize: {exception}")
                return "Summary unavailable."
            sleep_time = (2 ** attempt) + random.uniform(1, 3)
            print(f"Gemini API hit a snag. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)


def get_best_image_url(event, preferred_ratio="16_9"):
    """Pick the highest-resolution image, preferring a given aspect ratio."""
    images = event.get("images", [])
    if not images:
        return None

    candidates = [img for img in images if img.get("ratio") == preferred_ratio] or images
    best = max(candidates, key=lambda img: img.get("width", 0))
    return best.get("url")


# ── Payload building + validation ────────────────────────────────────────────────

def extract_category(event):
    classifications = event.get("classifications", [])
    if not classifications:
        return None
    return classifications[0].get("segment", {}).get("name")


def compute_event_times(starts_at_raw):
    """Convert Ticketmaster's UTC start time into the NY-local naive datetimes
    the events table expects."""
    starts_dt = datetime.fromisoformat(starts_at_raw.replace("Z", "+00:00")) - timedelta(hours=4)
    ends_at = (starts_dt + timedelta(hours=3)).isoformat()
    return starts_dt, ends_at


def build_price_and_capacity():
    """Fabricate a plausible price/capacity/spots-remaining trio. Ticketmaster's
    Discovery API doesn't reliably expose these, so — until a real pricing/
    capacity source is wired in — values are randomized within ranges that
    satisfy the DB's non-negative/ordering constraints."""
    original_price_cents = random.randint(20, 70) * 100
    reduction_percent = random.randint(10, 30)
    price_cents = int(original_price_cents * (1 - reduction_percent / 100))

    capacity = random.randint(100, 300)
    spots_remaining = int(round(capacity * random.uniform(0.05, 0.10)))

    return original_price_cents, price_cents, capacity, spots_remaining


def build_event_payload(event, venue_id, org_id, category, starts_dt, ends_at, ai_summary):
    original_price_cents, price_cents, capacity, spots_remaining = build_price_and_capacity()
    return {
        "venue_id": venue_id,
        "host_organisation_id": org_id,
        "title": event.get("name"),
        "category": category,
        "price_cents": price_cents,
        "original_price_cents": original_price_cents,
        "starts_at": starts_dt.isoformat(),
        "ends_at": ends_at,
        "ai_summary": ai_summary,
        "status": "active",
        "capacity": capacity,
        "spots_remaining": spots_remaining,
        "image_url": get_best_image_url(event),
        "external_event_id": event.get("id"),
    }


def validate_event_payload(payload):
    """Check a payload has everything required before writing to Supabase.
    Returns (is_valid, reason)."""
    if payload is None:
        return False, "payload is None"

    for field in ("title", "venue_id", "host_organisation_id", "starts_at"):
        if not payload.get(field):
            return False, f"missing required field: {field}"

    if payload.get("price_cents", -1) < 0:
        return False, "price_cents is negative"

    capacity = payload.get("capacity")
    if not capacity or capacity <= 0:
        return False, "capacity must be positive"

    spots_remaining = payload.get("spots_remaining")
    if spots_remaining is None or spots_remaining < 0 or spots_remaining > capacity:
        return False, "spots_remaining out of range"

    return True, None


# ── Ingest loop ─────────────────────────────────────────────────────────────────

def run_ingest(event_queue, supabase, genai_client, org_id):
    """Drain the event queue: validate venue, build+validate payload, get AI
    summary, upsert."""
    stats = {"fetched": event_queue.qsize(), "inserted": 0, "skipped": 0, "failed": 0}
    processed_venues = {}

    print(f"Worker started. Processing {event_queue.qsize()} events...")

    while not event_queue.empty():
        event = event_queue.get()
        event_id = event.get("id")
        event_name = event.get("name")

        try:
            existing = (
                supabase.table("events")
                .select("id")
                .eq("external_event_id", event_id)
                .execute()
            )
            if existing.data:
                print(f"Event '{event_name}' is already in the database. Skipping.")
                stats["skipped"] += 1
                event_queue.task_done()
                continue
        except Exception as exception:
            print(f"Error checking database for existing event: {exception}")

        venue_id = handle_venue_validation(event, supabase, org_id, processed_venues)
        if not venue_id:
            print(f"Skipping event {event_id}: venue processing failed.")
            stats["skipped"] += 1
            event_queue.task_done()
            continue

        category = extract_category(event)
        if not category:
            print(f"Skipping event {event_id}: missing category.")
            stats["skipped"] += 1
            event_queue.task_done()
            continue

        starts_at_raw = event.get("dates", {}).get("start", {}).get("dateTime")
        if not starts_at_raw:
            print(f"Skipping event {event_id}: missing start time.")
            stats["skipped"] += 1
            event_queue.task_done()
            continue
        starts_dt, ends_at = compute_event_times(starts_at_raw)

        print(f"Generating AI summary for: {event_name}...")
        ai_summary = get_gemini_summary(event, genai_client)

        payload = build_event_payload(event, venue_id, org_id, category, starts_dt, ends_at, ai_summary)
        is_valid, reason = validate_event_payload(payload)
        if not is_valid:
            print(f"Skipping event {event_id}: invalid payload ({reason}).")
            stats["skipped"] += 1
            event_queue.task_done()
            continue

        try:
            supabase.table("events").upsert([payload], on_conflict="external_event_id").execute()
            print(f"Saved event: {event_name}")
            stats["inserted"] += 1
        except Exception as exception:
            print(f"FAILED to save event {event_name}: {exception}")
            stats["failed"] += 1

        event_queue.task_done()

        if not event_queue.empty():
            time.sleep(GEMINI_SLEEP_SECONDS)

    print("Queue empty. All events processed.")
    return stats


# ── CLI ───────────────────────────────────────────────────────────────────────

def dry_run():
    """Fast validation for CI. Checks env vars (warns, doesn't fail, since CI
    has no secrets), imports (already executed at top of file — if we got
    here they work), and that the Manhattan polygon can be fetched."""
    print("=== dry-run ===")

    try:
        load_config()
        print("[OK]  all required environment variables are set")
    except RuntimeError as exception:
        print(f"[WARN]  {exception}")
        print("        (expected when run without secrets, e.g. in CI)")

    print("[OK]  imports: requests, shapely, dotenv, supabase, google-genai")

    try:
        polygon = get_manhattan_polygon()
        print(f"[OK]  Manhattan polygon fetched (bounds: {polygon.bounds})")
    except Exception as exception:
        print(f"FAIL  could not fetch Manhattan polygon: {exception}")
        sys.exit(1)

    print()
    print("dry-run OK")
    sys.exit(0)


def main():
    args = parse_args()

    if args.dry_run:
        dry_run()  # exits inside

    config = load_config()
    supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_SERVICE_ROLE_KEY"])
    genai_client = genai.Client(api_key=config["GEMINI_API_KEY"])

    org_response = supabase.table("organisations").select("id").eq("name", "ticketmaster").execute()
    if not org_response.data:
        print("FAIL  no 'ticketmaster' organisation found in Supabase — cannot proceed.")
        sys.exit(1)
    org_id = org_response.data[0]["id"]

    polygon = get_manhattan_polygon()
    event_queue = fetch_events(config["TICKETMASTER_KEY"], polygon, max_pages=args.max_pages)
    stats = run_ingest(event_queue, supabase, genai_client, org_id)

    print()
    print(
        f"Fetched: {stats['fetched']}  Inserted: {stats['inserted']}  "
        f"Skipped: {stats['skipped']}  Failed: {stats['failed']}"
    )


if __name__ == "__main__":
    main()
