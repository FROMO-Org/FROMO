import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_session
from app.middleware.auth import get_current_user, require_organisation_member
from app.models import Event, Venue
from app.schemas import CreateEventBody, EventStatus, UpdateEventBody

router = APIRouter(prefix="/events", tags=["events"])

EARTH_RADIUS_KM = 6371


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1, lng1, lat2, lng2 = map(lambda v: math.radians(float(v)), [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def event_list_item(event: Event, venue: Venue, distance_km: float | None = None) -> dict:
    return {
        "event": event,
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
        "venue": {
            "id": venue.id,
            "name": venue.name,
            "lat": float(venue.lat),
            "lng": float(venue.lng),
        },
    }


@router.get("/")
def get_events(
    status: EventStatus | None = None,
    category: str | None = None,
    discounted_only: bool = False,
    starts_after: datetime | None = None,
    starts_before: datetime | None = None,
    has_spots: bool = False,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float = Query(default=5, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    query = session.query(Event, Venue).join(Venue, Event.venue_id == Venue.id)
    
    if (lat is None) != (lng is None):
        raise HTTPException(status_code=400, detail="lat and lng must be provided together")


    if status is not None:
        query = query.filter(Event.status == status)

    if category is not None:
        query = query.filter(Event.category == category)

    if discounted_only:
        query = query.filter(
            Event.original_price_cents.isnot(None),
            Event.original_price_cents > Event.price_cents,
    )

    if starts_after is not None:
        query = query.filter(Event.starts_at >= starts_after)

    if starts_before is not None:
        query = query.filter(Event.starts_at <= starts_before)

    if has_spots:
        query = query.filter(
            (Event.spots_remaining.is_(None)) | (Event.spots_remaining > 0)
    )

    query = query.order_by(Event.starts_at)

    if lat is None or lng is None:
        rows = query.limit(limit).offset(offset).all()
        return [event_list_item(event, venue) for event, venue in rows]

    nearby = []
    for event, venue in query.all():
        distance = haversine_km(lat, lng, venue.lat, venue.lng)
        if distance <= radius_km:
            nearby.append((event, venue, distance))

    nearby.sort(key=lambda row: row[2])
    page = nearby[offset:offset + limit]

    return [event_list_item(event, venue, distance) for event, venue, distance in page]


@router.get("/{event_id}")
def get_event(event_id: UUID, session: Session = Depends(get_session)):
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/")
def create_event(
    body: CreateEventBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_organisation_member(session, user["sub"], body.host_organisation_id)

    venue = session.query(Venue).filter(Venue.id == body.venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    if venue.organisation_id != body.host_organisation_id:
        raise HTTPException(status_code=400, detail="Venue does not belong to this organisation")

    event = Event(
        title=body.title,
        venue_id=body.venue_id,
        host_organisation_id=body.host_organisation_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        original_price_cents=body.original_price_cents,
        price_cents=body.price_cents,
        capacity=body.capacity,
        spots_remaining=body.capacity,
        category=body.category,
        description=body.description
    )

    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.patch("/{event_id}")
def update_event(
    event_id: UUID,
    body: UpdateEventBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    require_organisation_member(session, user["sub"], event.host_organisation_id)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(event, field, value)

    session.commit()
    session.refresh(event)
    return event


@router.delete("/{event_id}")
def delete_event(
    event_id: UUID,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    require_organisation_member(session, user["sub"], event.host_organisation_id)

    session.delete(event)
    session.commit()
    return {"detail": "Event deleted"}
