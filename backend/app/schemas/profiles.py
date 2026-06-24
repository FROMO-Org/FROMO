from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema, OrmSchema

UserType = Literal["student", "organiser", "admin"]


class ProfileResponse(OrmSchema):
    id: UUID
    email: str
    full_name: str | None
    user_type: str
    created_at: datetime


class CreateProfileBody(ApiSchema):
    full_name: str | None = Field(default=None, min_length=1)


class UpdateProfileBody(ApiSchema):
    full_name: str | None = Field(default=None, min_length=1)
    user_type: UserType | None = None
