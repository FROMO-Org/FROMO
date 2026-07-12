from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema, OrmSchema

FeedbackRating = Literal[-1, 1]


class CreateFeedbackBody(ApiSchema):
    event_id: UUID | None = None
    feature: str | None = Field(default="app_experience", min_length=1)
    rating: FeedbackRating
    comment: str | None = None


class FeedbackResponse(OrmSchema):
    id: UUID
    event_id: UUID | None
    feature: str | None
    rating: int | None
    comment: str | None
    created_at: datetime
