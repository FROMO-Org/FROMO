from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_session
from app.middleware.auth import get_current_user, require_organisation_member
from app.models import Venue
from app.schemas import CreateVenueBody

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("/")
def create_venue(
    body: CreateVenueBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_organisation_member(session, user["sub"], body.organisation_id)

    venue = Venue(
        organisation_id=body.organisation_id,
        busyness_area_id=body.busyness_area_id,
        name=body.name,
        address=body.address,
        lat=body.lat,
        lng=body.lng,
        category=body.category,
        is_accessible=body.is_accessible,
    )

    session.add(venue)
    session.commit()
    session.refresh(venue)
    return venue


@router.get("/")
def get_venues(
    organisation_id: UUID | None = None,
    category: str | None = None,
    is_accessible: bool | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    query = session.query(Venue)

    if organisation_id is not None:
        query = query.filter(Venue.organisation_id == organisation_id)
    if category is not None:
        query = query.filter(Venue.category == category)
    if is_accessible is not None:
        query = query.filter(Venue.is_accessible == is_accessible)

    return query.limit(limit).offset(offset).all()


@router.get("/{venue_id}")
def get_venue(venue_id: UUID, session: Session = Depends(get_session)):
    venue = session.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue
