from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApiSchema(BaseModel):
    """Base for request body schemas."""
    model_config = ConfigDict(str_strip_whitespace=True)


class OrmSchema(BaseModel):
    """Base for response schemas that read from SQLAlchemy ORM objects."""
    model_config = ConfigDict(from_attributes=True)


class VenueSummary(OrmSchema):
    """Minimal venue info embedded in event/booking list rows."""
    id: UUID
    name: str
    lat: float
    lng: float
