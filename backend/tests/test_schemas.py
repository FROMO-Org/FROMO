from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import CreateBookingBody, CreateEventBody, CreateVenueBody


def test_create_event_rejects_end_before_start():
    starts_at = datetime(2026, 6, 18, 18, 0)

    with pytest.raises(ValidationError):
        CreateEventBody(
            title="Jazz night",
            venue_id=uuid4(),
            host_organisation_id=uuid4(),
            starts_at=starts_at,
            ends_at=starts_at - timedelta(hours=1),
        )


def test_create_venue_rejects_invalid_coordinates():
    with pytest.raises(ValidationError):
        CreateVenueBody(
            organisation_id=uuid4(),
            name="Bad venue",
            lat=100,
            lng=-73.9855,
        )


def test_create_booking_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        CreateBookingBody(event_id=uuid4(), quantity=0)
