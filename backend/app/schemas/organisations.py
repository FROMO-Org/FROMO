from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ApiSchema, OrmSchema

OrgRole = Literal["owner", "admin", "staff"]


class OrganisationResponse(OrmSchema):
    id: UUID
    name: str
    created_at: datetime


class MembershipResponse(OrmSchema):
    organisation_id: UUID
    user_id: UUID
    role: str
    created_at: datetime


class CreateOrganisationResponse(BaseModel):
    """Returned when a user creates a new organisation."""
    organisation: OrganisationResponse
    membership: MembershipResponse


class MyOrganisationResponse(BaseModel):
    """One row in GET /organisations/me."""
    organisation: OrganisationResponse
    role: str
    joined_at: datetime


class CreateOrganisationBody(ApiSchema):
    name: str = Field(min_length=1)


class CreateMembershipBody(ApiSchema):
    user_id: UUID
    role: OrgRole
