"""
Pure unit tests for dashboard helper functions.
No HTTP, no DB — import and call directly.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.routers.dashboard import event_display_status, sold_count, start_of_month, start_of_week


NOW = datetime(2026, 6, 15, 14, 0)  # Sunday 14:00


class TestEventDisplayStatus:
    def _event(self, **kwargs) -> SimpleNamespace:
        defaults = {
            "status": "active",
            "spots_remaining": 10,
            "capacity": 50,
            "ends_at": NOW + timedelta(hours=2),
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_draft_event_is_draft(self):
        assert event_display_status(self._event(status="draft"), 0, NOW) == "draft"

    def test_cancelled_event_is_cancelled(self):
        assert event_display_status(self._event(status="cancelled"), 0, NOW) == "cancelled"

    def test_completed_event_is_expired(self):
        assert event_display_status(self._event(status="completed"), 0, NOW) == "expired"

    def test_past_end_time_is_expired(self):
        event = self._event(ends_at=NOW - timedelta(minutes=1))
        assert event_display_status(event, 0, NOW) == "expired"

    def test_no_spots_remaining_is_sold_out(self):
        event = self._event(spots_remaining=0)
        assert event_display_status(event, 50, NOW) == "sold_out"

    def test_sold_equals_capacity_is_sold_out(self):
        event = self._event(capacity=30, spots_remaining=None)
        assert event_display_status(event, 30, NOW) == "sold_out"

    def test_active_event_with_spots_is_active(self):
        assert event_display_status(self._event(), 5, NOW) == "active"


class TestSoldCount:
    def _event(self, **kwargs) -> SimpleNamespace:
        defaults = {"capacity": 50, "spots_remaining": 40}
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_uses_booked_quantity_when_positive(self):
        assert sold_count(self._event(), booked_quantity=12) == 12

    def test_falls_back_to_capacity_minus_remaining(self):
        event = self._event(capacity=50, spots_remaining=30)
        assert sold_count(event, booked_quantity=0) == 20

    def test_returns_zero_when_no_capacity_info(self):
        event = SimpleNamespace(capacity=None, spots_remaining=None)
        assert sold_count(event, booked_quantity=0) == 0


class TestDateHelpers:
    def test_start_of_month(self):
        result = start_of_month(datetime(2026, 6, 15, 14, 30))
        assert result == datetime(2026, 6, 1, 0, 0, 0)

    def test_start_of_week_on_sunday(self):
        # June 15 2026 is a Monday — weekday() == 0
        monday = datetime(2026, 6, 15, 14, 0)
        result = start_of_week(monday)
        assert result == datetime(2026, 6, 15, 0, 0, 0)

    def test_start_of_week_mid_week(self):
        wednesday = datetime(2026, 6, 17, 10, 0)
        result = start_of_week(wednesday)
        assert result == datetime(2026, 6, 15, 0, 0, 0)
