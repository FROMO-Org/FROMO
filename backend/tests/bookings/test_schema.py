"""
Pydantic validation tests for booking schemas.
No HTTP, no DB.
"""
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import CreateBookingBody


class TestCreateBookingBody:
    def test_valid_booking(self):
        body = CreateBookingBody(event_id=uuid4(), quantity=2)
        assert body.quantity == 2

    def test_default_quantity_is_one(self):
        body = CreateBookingBody(event_id=uuid4())
        assert body.quantity == 1

    def test_rejects_zero_quantity(self):
        with pytest.raises(ValidationError):
            CreateBookingBody(event_id=uuid4(), quantity=0)

    def test_rejects_negative_quantity(self):
        with pytest.raises(ValidationError):
            CreateBookingBody(event_id=uuid4(), quantity=-1)

    def test_rejects_missing_event_id(self):
        with pytest.raises(ValidationError):
            CreateBookingBody(quantity=1)
