"""
HTTP behaviour tests for /bookings/.
Business rules are tested by injecting a mock DB session.
"""
from datetime import datetime, timedelta, UTC
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4


def _make_event(**overrides) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "status": "active",
        "price_cents": 1000,
        "capacity": 50,
        "spots_remaining": 10,
        "starts_at": now + timedelta(hours=2),
        "ends_at": now + timedelta(hours=4),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _session_returning(first_call, second_call):
    """
    Build a mock session where the first .query().filter().first()
    returns first_call, and the second returns second_call.

    The booking router calls:
      session.query(Booking).filter(...).first()   ← duplicate check
      session.query(Event).filter(...).first()     ← fetch event
    Both share the same mock chain, so we use side_effect to sequence them.
    """
    session = MagicMock()
    session.query.return_value.filter.return_value.first.side_effect = [
        first_call,
        second_call,
    ]
    return session


class TestBookingAuth:
    def test_get_my_bookings_requires_auth(self, client):
        response = client.get("/bookings/me")
        assert response.status_code == 401

    def test_make_booking_requires_auth(self, client):
        response = client.post("/bookings/", json={"event_id": str(uuid4())})
        assert response.status_code == 401

    def test_cancel_booking_requires_auth(self, client):
        response = client.patch(f"/bookings/{uuid4()}")
        assert response.status_code == 401


class TestMakeBookingValidation:
    def test_missing_event_id_returns_422(self, authenticated_client):
        response = authenticated_client.post("/bookings/", json={})
        assert response.status_code == 422

    def test_zero_quantity_returns_422(self, authenticated_client):
        response = authenticated_client.post(
            "/bookings/", json={"event_id": str(uuid4()), "quantity": 0}
        )
        assert response.status_code == 422


class TestMakeBookingBusinessRules:
    def test_rejects_duplicate_booking(self, authenticated_client, override_db_session):
        existing_booking = SimpleNamespace(id=uuid4())
        session = _session_returning(existing_booking, None)
        override_db_session(session)

        response = authenticated_client.post(
            "/bookings/", json={"event_id": str(uuid4()), "quantity": 1}
        )
        assert response.status_code == 409
        assert "already booked" in response.json()["detail"]

    def test_rejects_booking_on_non_active_event(
        self, authenticated_client, override_db_session
    ):
        event = _make_event(status="draft")
        session = _session_returning(None, event)
        override_db_session(session)

        response = authenticated_client.post(
            "/bookings/", json={"event_id": str(event.id), "quantity": 1}
        )
        assert response.status_code == 409
        assert "not active" in response.json()["detail"]

    def test_rejects_booking_on_ended_event(
        self, authenticated_client, override_db_session
    ):
        past = datetime.now(UTC) - timedelta(hours=1)
        event = _make_event(
            starts_at=past - timedelta(hours=2),
            ends_at=past,
        )
        session = _session_returning(None, event)
        override_db_session(session)

        response = authenticated_client.post(
            "/bookings/", json={"event_id": str(event.id), "quantity": 1}
        )
        assert response.status_code == 409
        assert "ended" in response.json()["detail"]

    def test_rejects_booking_when_not_enough_spots(
        self, authenticated_client, override_db_session
    ):
        event = _make_event(spots_remaining=1)
        session = _session_returning(None, event)
        override_db_session(session)

        response = authenticated_client.post(
            "/bookings/", json={"event_id": str(event.id), "quantity": 5}
        )
        assert response.status_code == 409
        assert "spots" in response.json()["detail"]
