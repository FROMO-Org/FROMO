"""
Pydantic validation tests for venue schemas.
No HTTP, no DB.
"""
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import CreateVenueBody, UpdateVenueBody


class TestCreateVenueBody:
    def test_valid_venue(self):
        body = CreateVenueBody(
            organisation_id=uuid4(),
            name="The Roundhouse",
            lat=51.5414,
            lng=-0.1533,
        )
        assert body.name == "The Roundhouse"
        assert body.is_accessible is False  # default

    def test_rejects_lat_above_90(self):
        with pytest.raises(ValidationError):
            CreateVenueBody(organisation_id=uuid4(), name="X", lat=91, lng=0)

    def test_rejects_lat_below_minus_90(self):
        with pytest.raises(ValidationError):
            CreateVenueBody(organisation_id=uuid4(), name="X", lat=-91, lng=0)

    def test_rejects_lng_above_180(self):
        with pytest.raises(ValidationError):
            CreateVenueBody(organisation_id=uuid4(), name="X", lat=0, lng=181)

    def test_rejects_empty_name(self):
        with pytest.raises(ValidationError):
            CreateVenueBody(organisation_id=uuid4(), name="", lat=0, lng=0)

    def test_strips_whitespace_from_name(self):
        body = CreateVenueBody(organisation_id=uuid4(), name="  Venue  ", lat=0, lng=0)
        assert body.name == "Venue"


class TestUpdateVenueBody:
    def test_all_fields_optional(self):
        body = UpdateVenueBody()
        assert body.name is None

    def test_rejects_invalid_lat_on_update(self):
        with pytest.raises(ValidationError):
            UpdateVenueBody(lat=200)
