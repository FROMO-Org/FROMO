from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ApiSchema, OrmSchema, VenueSummary

EventStatus = Literal["draft", "active", "cancelled", "completed"]


class PublicEventResponse(OrmSchema):
    id: UUID
    title: str
    description: str | None
    ai_summary: str | None = None
    category: str | None
    price_cents: int
    original_price_cents: int | None
    capacity: int | None
    spots_remaining: int | None
    starts_at: datetime
    ends_at: datetime | None
    status: EventStatus
    venue_id: UUID
    created_at: datetime
    image_url: str | None = None


class OrganiserEventResponse(PublicEventResponse):
    """Extends public response with fields only org members need."""
    host_organisation_id: UUID


class EventListItemResponse(BaseModel):
    """One row in the discovery feed: event + optional distance + venue pin."""
    event: PublicEventResponse
    distance_km: float | None
    venue: VenueSummary


class CreateEventBody(ApiSchema):
    title: str = Field(min_length=1)
    venue_id: UUID
    host_organisation_id: UUID
    starts_at: datetime
    ends_at: datetime | None = None
    original_price_cents: int | None = Field(default=None, ge=0)
    price_cents: int = Field(default=0, ge=0)
    capacity: int | None = Field(default=None, gt=0)
    description: str | None = None
    category: str | None = None
    image_url: str | None = None

    @model_validator(mode="after")
    def validate_event_times(self):
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class UpdateEventBody(ApiSchema):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    category: str | None = None
    price_cents: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, gt=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: EventStatus | None = None
    image_url: str | None = None

    @model_validator(mode="after")
    def validate_event_times(self):
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError("ends_at must be after starts_at")
        return self
