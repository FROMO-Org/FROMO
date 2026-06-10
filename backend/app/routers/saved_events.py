from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import Event, SavedEvent, Venue
from app.schemas import CreateSavedEventBody

router = APIRouter(prefix="/saved-events", tags=["saved_events"])


def venue_summary(venue: Venue) -> dict:
    return {
        "id": venue.id,
        "name": venue.name,
        "lat": float(venue.lat),
        "lng": float(venue.lng),
    }


@router.get("/me")
def get_my_saved_events(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    rows = session.query(SavedEvent, Event, Venue).join(
        Event,
        SavedEvent.event_id == Event.id,
    ).join(
        Venue,
        Event.venue_id == Venue.id,
    ).filter(
        SavedEvent.user_id == user["sub"],
    ).all()

    return [
        {
            "saved_event": saved,
            "event": event,
            "venue": venue_summary(venue),
        }
        for saved, event, venue in rows
    ]


@router.post("/")
def save_event(
    body: CreateSavedEventBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    existing = session.query(SavedEvent).filter(
        SavedEvent.user_id == user["sub"],
        SavedEvent.event_id == body.event_id,
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Event already saved")
    
    event_existing = session.query(Event).filter(
        Event.id == body.event_id
    ).first()

    if not event_existing:
        raise HTTPException(status_code=404, detail="Event not found")

    saved = SavedEvent(user_id=user["sub"], event_id=body.event_id)
    session.add(saved)
    session.commit()
    session.refresh(saved)
    return saved


@router.delete("/{event_id}")
def unsave_event(
    event_id: UUID,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    saved = session.query(SavedEvent).filter(
        SavedEvent.user_id == user["sub"],
        SavedEvent.event_id == event_id,
    ).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved event not found")

    session.delete(saved)
    session.commit()
    return {"detail": "Event unsaved"}
