from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# All schemase for creation/deletion/updating. Used in routers. No need to separate as of rn.
# Because it is quite small. 

EventStatus = Literal["draft", "active", "cancelled", "completed"]
OrgRole = Literal["owner", "admin", "staff"]
UserType = Literal["student", "organiser", "admin"]


class ApiSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


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

    @model_validator(mode="after")
    def validate_event_times(self):
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError("ends_at must be after starts_at")
        return self

class CreateProfileBody(ApiSchema):
    full_name: str | None = Field(default=None, min_length=1)

class UpdateProfileBody(ApiSchema):
    full_name: str | None = Field(default=None, min_length=1)
    user_type: UserType | None = None


class CreateMembershipBody(ApiSchema):
    user_id: UUID
    role: OrgRole


class CreateOrganisationBody(ApiSchema):
    name: str = Field(min_length=1)


class CreateSavedEventBody(ApiSchema):
    event_id: UUID


class CreateBookingBody(ApiSchema):
    event_id: UUID
    quantity: int = Field(default=1, gt=0)

class CreateVenueBody(ApiSchema):
    organisation_id: UUID
    busyness_area_id: UUID | None = None
    name: str = Field(min_length=1)
    address: str | None = None
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    category: str | None = None
    is_accessible: bool = False

class UpdateVenueBody(ApiSchema):
    busyness_area_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1)
    address: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    category: str | None = None
    is_accessible: bool | None = None
