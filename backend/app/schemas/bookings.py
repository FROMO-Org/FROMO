from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ApiSchema, OrmSchema, VenueSummary
from app.schemas.events import PublicEventResponse


class BookingResponse(OrmSchema):
    id: UUID
    event_id: UUID
    # user_id intentionally omitted — client already knows who they are
    quantity: int
    status: str
    total_price_cents: int
    booked_at: datetime
    cancelled_at: datetime | None


class MyBookingResponse(BaseModel):
    """One row in GET /bookings/me — booking + its event + venue pin."""
    booking: BookingResponse
    event: PublicEventResponse
    venue: VenueSummary


class CreateBookingBody(ApiSchema):
    event_id: UUID
    quantity: int = Field(default=1, gt=0)
