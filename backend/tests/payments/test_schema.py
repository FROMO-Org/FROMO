from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import CreateCheckoutSessionBody


class TestCreateCheckoutSessionBody:
    def test_valid_body(self):
        body = CreateCheckoutSessionBody(event_id=uuid4(), quantity=2)
        assert body.quantity == 2

    def test_default_quantity_is_one(self):
        body = CreateCheckoutSessionBody(event_id=uuid4())
        assert body.quantity == 1

    def test_rejects_zero_quantity(self):
        with pytest.raises(ValidationError):
            CreateCheckoutSessionBody(event_id=uuid4(), quantity=0)
