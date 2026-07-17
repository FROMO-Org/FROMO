"""
Unit tests for the pure/deterministic helpers in ticketmaster_ingest.py.

Runs with no network calls and no secrets required — safe for CI on every
push/PR. The live-API paths (fetch_events, handle_venue_validation,
get_gemini_summary, run_ingest) all require real credentials and are
exercised by the scheduled workflow, not here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shapely.geometry import Polygon

import ticketmaster_ingest as tm

# A simple 1x1 degree square standing in for Manhattan, centered at (0, 0),
# so tests don't depend on the live NYC Open Data endpoint.
SQUARE = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1)])

SAMPLE_EVENT = {
    "id": "evt-123",
    "name": "Test Concert",
    "classifications": [{"segment": {"name": "Music"}}],
    "dates": {"start": {"dateTime": "2026-07-16T00:00:00Z"}},
    "images": [
        {"ratio": "16_9", "width": 640, "url": "https://example.com/small.jpg"},
        {"ratio": "16_9", "width": 1920, "url": "https://example.com/large.jpg"},
        {"ratio": "3_2", "width": 3000, "url": "https://example.com/wrong_ratio.jpg"},
    ],
}


def test_is_in_manhattan_inside_point():
    assert tm.is_in_manhattan(0.5, 0.5, SQUARE) is True


def test_is_in_manhattan_outside_point():
    assert tm.is_in_manhattan(5.0, 5.0, SQUARE) is False


def test_is_in_manhattan_missing_coordinates():
    assert tm.is_in_manhattan(None, None, SQUARE) is False


def test_get_best_image_url_prefers_widest_matching_ratio():
    assert tm.get_best_image_url(SAMPLE_EVENT) == "https://example.com/large.jpg"


def test_get_best_image_url_no_images():
    assert tm.get_best_image_url({"images": []}) is None


def test_extract_category():
    assert tm.extract_category(SAMPLE_EVENT) == "Music"


def test_extract_category_missing():
    assert tm.extract_category({"classifications": []}) is None


def test_build_event_payload_shape():
    starts_dt, ends_at = tm.compute_event_times("2026-07-16T00:00:00Z")
    payload = tm.build_event_payload(
        SAMPLE_EVENT,
        venue_id="venue-uuid",
        org_id="org-uuid",
        category="Music",
        starts_dt=starts_dt,
        ends_at=ends_at,
        ai_summary="A great show.",
    )

    assert payload["venue_id"] == "venue-uuid"
    assert payload["host_organisation_id"] == "org-uuid"
    assert payload["title"] == "Test Concert"
    assert payload["category"] == "Music"
    assert payload["external_event_id"] == "evt-123"
    assert payload["ai_summary"] == "A great show."
    assert payload["status"] == "active"
    assert payload["image_url"] == "https://example.com/large.jpg"
    assert 0 <= payload["price_cents"] <= payload["original_price_cents"]
    assert 0 <= payload["spots_remaining"] <= payload["capacity"]


def _valid_payload(**overrides):
    payload = {
        "title": "Test Concert",
        "venue_id": "venue-uuid",
        "host_organisation_id": "org-uuid",
        "starts_at": "2026-07-15T20:00:00",
        "price_cents": 1000,
        "capacity": 100,
        "spots_remaining": 10,
    }
    payload.update(overrides)
    return payload


def test_validate_event_payload_valid():
    is_valid, reason = tm.validate_event_payload(_valid_payload())
    assert is_valid is True
    assert reason is None


def test_validate_event_payload_none():
    is_valid, reason = tm.validate_event_payload(None)
    assert is_valid is False


def test_validate_event_payload_missing_title():
    is_valid, reason = tm.validate_event_payload(_valid_payload(title=None))
    assert is_valid is False
    assert "title" in reason


def test_validate_event_payload_negative_price():
    is_valid, reason = tm.validate_event_payload(_valid_payload(price_cents=-100))
    assert is_valid is False


def test_validate_event_payload_zero_capacity():
    is_valid, reason = tm.validate_event_payload(_valid_payload(capacity=0))
    assert is_valid is False


def test_validate_event_payload_spots_exceed_capacity():
    is_valid, reason = tm.validate_event_payload(_valid_payload(spots_remaining=500))
    assert is_valid is False
