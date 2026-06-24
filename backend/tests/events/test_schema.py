"""
Pydantic validation tests for event schemas.
No HTTP, no DB — pure Python.
"""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import CreateEventBody, UpdateEventBody


FUTURE = datetime(2030, 1, 1, 18, 0)


class TestCreateEventBody:
    def test_valid_minimal_body(self):
        body = CreateEventBody(
            title="Jazz Night",
            venue_id=uuid4(),
            host_organisation_id=uuid4(),
            starts_at=FUTURE,
        )
        assert body.title == "Jazz Night"
        assert body.price_cents == 0  # default

    def test_rejects_empty_title(self):
        with pytest.raises(ValidationError):
            CreateEventBody(
                title="",
                venue_id=uuid4(),
                host_organisation_id=uuid4(),
                starts_at=FUTURE,
            )

    def test_rejects_end_before_start(self):
        with pytest.raises(ValidationError):
            CreateEventBody(
                title="Jazz Night",
                venue_id=uuid4(),
                host_organisation_id=uuid4(),
                starts_at=FUTURE,
                ends_at=FUTURE - timedelta(hours=1),
            )

    def test_rejects_end_equal_to_start(self):
        with pytest.raises(ValidationError):
            CreateEventBody(
                title="Jazz Night",
                venue_id=uuid4(),
                host_organisation_id=uuid4(),
                starts_at=FUTURE,
                ends_at=FUTURE,
            )

    def test_rejects_negative_price(self):
        with pytest.raises(ValidationError):
            CreateEventBody(
                title="Jazz Night",
                venue_id=uuid4(),
                host_organisation_id=uuid4(),
                starts_at=FUTURE,
                price_cents=-1,
            )

    def test_rejects_zero_capacity(self):
        with pytest.raises(ValidationError):
            CreateEventBody(
                title="Jazz Night",
                venue_id=uuid4(),
                host_organisation_id=uuid4(),
                starts_at=FUTURE,
                capacity=0,
            )

    def test_strips_whitespace_from_title(self):
        body = CreateEventBody(
            title="  Jazz Night  ",
            venue_id=uuid4(),
            host_organisation_id=uuid4(),
            starts_at=FUTURE,
        )
        assert body.title == "Jazz Night"


class TestUpdateEventBody:
    def test_all_fields_optional(self):
        # Should not raise — every field is optional
        body = UpdateEventBody()
        assert body.title is None

    def test_rejects_end_before_start_when_both_provided(self):
        with pytest.raises(ValidationError):
            UpdateEventBody(
                starts_at=FUTURE,
                ends_at=FUTURE - timedelta(hours=1),
            )

    def test_allows_end_without_start(self):
        # Partial update: only ends_at changed, starts_at not sent
        body = UpdateEventBody(ends_at=FUTURE + timedelta(hours=3))
        assert body.ends_at is not None
