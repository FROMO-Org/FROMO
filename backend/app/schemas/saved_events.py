from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ApiSchema, OrmSchema, VenueSummary
from app.schemas.events import PublicEventResponse


class SavedEventResponse(OrmSchema):
    event_id: UUID
    saved_at: datetime
    # user_id intentionally omitted


class MySavedEventResponse(BaseModel):
    """One row in GET /saved-events/me."""
    saved_event: SavedEventResponse
    event: PublicEventResponse
    venue: VenueSummary


class CreateSavedEventBody(ApiSchema):
    event_id: UUID
