from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema, OrmSchema


class VenueResponse(OrmSchema):
    id: UUID
    organisation_id: UUID
    name: str
    address: str | None
    lat: float
    lng: float
    category: str | None
    is_accessible: bool
    created_at: datetime


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
