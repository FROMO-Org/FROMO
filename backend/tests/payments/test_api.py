from datetime import datetime, timedelta, UTC
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4


def _make_event(**overrides) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "title": "Cheap Eats Crawl",
        "description": "Budget event",
        "status": "active",
        "price_cents": 1200,
        "spots_remaining": 10,
        "starts_at": now + timedelta(hours=2),
        "ends_at": now + timedelta(hours=4),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestPaymentAuth:
    def test_checkout_requires_auth(self, client):
        response = client.post("/payments/checkout-session", json={"event_id": str(uuid4())})
        assert response.status_code == 401

    def test_get_payment_requires_auth(self, client):
        response = client.get(f"/payments/{uuid4()}")
        assert response.status_code == 401


class TestCheckoutValidation:
    def test_missing_event_id_returns_422(self, authenticated_client):
        response = authenticated_client.post("/payments/checkout-session", json={})
        assert response.status_code == 422

    def test_zero_quantity_returns_422(self, authenticated_client):
        response = authenticated_client.post(
            "/payments/checkout-session",
            json={"event_id": str(uuid4()), "quantity": 0},
        )
        assert response.status_code == 422


class TestCheckoutBusinessRules:
    def test_rejects_if_event_already_booked(self, authenticated_client, override_db_session):
        session = MagicMock()
        existing_booking = SimpleNamespace(id=uuid4())
        event = _make_event()
        session.query.return_value.filter.return_value.first.side_effect = [
            existing_booking,
            None,
            event,
        ]
        override_db_session(session)

        response = authenticated_client.post(
            "/payments/checkout-session",
            json={"event_id": str(event.id), "quantity": 1},
        )
        assert response.status_code == 409
        assert "already booked" in response.json()["detail"].lower()

    def test_rejects_if_payment_is_already_pending(self, authenticated_client, override_db_session):
        session = MagicMock()
        pending_payment = SimpleNamespace(id=uuid4())
        event = _make_event()
        session.query.return_value.filter.return_value.first.side_effect = [
            None,
            pending_payment,
            event,
        ]
        override_db_session(session)

        response = authenticated_client.post(
            "/payments/checkout-session",
            json={"event_id": str(event.id), "quantity": 1},
        )
        assert response.status_code == 409
        assert "pending" in response.json()["detail"].lower()

    def test_rejects_free_event(self, authenticated_client, override_db_session):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.side_effect = [
            None,
            None,
            _make_event(price_cents=0),
        ]
        override_db_session(session)

        response = authenticated_client.post(
            "/payments/checkout-session",
            json={"event_id": str(uuid4()), "quantity": 1},
        )
        assert response.status_code == 409
        assert "free" in response.json()["detail"].lower()

    def test_rejects_when_not_enough_spots(self, authenticated_client, override_db_session):
        session = MagicMock()
        event = _make_event(spots_remaining=1)
        session.query.return_value.filter.return_value.first.side_effect = [
            None,
            None,
            event,
        ]
        override_db_session(session)

        response = authenticated_client.post(
            "/payments/checkout-session",
            json={"event_id": str(event.id), "quantity": 3},
        )
        assert response.status_code == 409
        assert "spots" in response.json()["detail"].lower()
