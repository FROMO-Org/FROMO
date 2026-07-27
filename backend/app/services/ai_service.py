import logging
import time

import certifi
import httpx2

from app.core.config import GEMINI_API_KEY

logger = logging.getLogger("uvicorn.error")

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)
REQUEST_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 2
RETRY_BACKOFF_SECONDS = 3


def _format_price(price_cents: int | None, original_price_cents: int | None) -> str:
    if not price_cents:
        return "Free entry"
    price = f"£{price_cents / 100:.2f}"
    if original_price_cents and original_price_cents > price_cents:
        return f"{price} (discounted from £{original_price_cents / 100:.2f})"
    return price


def build_event_prompt(event_info: dict) -> str:
    """Turn the event's fields into a prompt for the summary model."""
    lines = [
        "Write a short, engaging summary (5 sentences max) for a student event listing.",
        "Be warm and concise. No hashtags, emojis, or markdown. Do not invent details "
        "that are not provided.",
        "",
        "Event details:",
        f"- Title: {event_info['title']}",
    ]
    if event_info.get("category"):
        lines.append(f"- Category: {event_info['category']}")
    if event_info.get("venue_name"):
        venue = event_info["venue_name"]
        if event_info.get("venue_address"):
            venue = f"{venue}, {event_info['venue_address']}"
        lines.append(f"- Venue: {venue}")
    if event_info.get("starts_at"):
        lines.append(f"- Starts: {event_info['starts_at']}")
    lines.append(
        f"- Price: {_format_price(event_info.get('price_cents'), event_info.get('original_price_cents'))}"
    )
    if event_info.get("description"):
        lines.append(f"- Organiser description: {event_info['description']}")
    return "\n".join(lines)


def generate_event_summary(event_info: dict) -> str | None:
    """
    Generate an AI summary for an event using Gemini.

    Returns None on ANY failure (missing key, network error, rate limit,
    unexpected response) so that event creation is never blocked by the LLM.
    """
    if not GEMINI_API_KEY:
        logger.warning("AI summary skipped: GEMINI_API_KEY is empty in this process")
        return None

    prompt = build_event_prompt(event_info)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # Auth via the documented x-goog-api-key header (works for AQ. auth keys).
            response = httpx2.post(
                GEMINI_ENDPOINT,
                headers={"x-goog-api-key": GEMINI_API_KEY},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=REQUEST_TIMEOUT_SECONDS,
                verify=certifi.where(),
            )
            if response.status_code != 200:
                # Log Google's ACTUAL error body so a failure is diagnosable,
                # not just "400 Bad Request".
                logger.warning(
                    "AI summary attempt %s/%s: Gemini HTTP %s -- %s",
                    attempt, MAX_ATTEMPTS, response.status_code, response.text[:300],
                )
                # Only transient errors are worth a retry; a 4xx won't change.
                if response.status_code in (429, 500, 502, 503, 504) and attempt < MAX_ATTEMPTS:
                    time.sleep(RETRY_BACKOFF_SECONDS)
                    continue
                return None

            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip() or None

        except Exception as exc:
            # Timeout / network / unexpected-shape: log it and retry once.
            logger.warning(
                "AI summary attempt %s/%s failed: %s", attempt, MAX_ATTEMPTS, exc
            )
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return None

    return None
