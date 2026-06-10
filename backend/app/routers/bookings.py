from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import Booking, Event, Venue
from app.schemas import CreateBookingBody

router = APIRouter(prefix="/bookings", tags=["bookings"])


def venue_summary(venue: Venue) -> dict:
    return {
        "id": venue.id,
        "name": venue.name,
        "lat": float(venue.lat),
        "lng": float(venue.lng),
    }


@router.get("/me")
def get_my_bookings(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    rows = session.query(Booking, Event, Venue).join(
        Event,
        Booking.event_id == Event.id,
    ).join(
        Venue,
        Event.venue_id == Venue.id,
    ).filter(
        Booking.user_id == user["sub"],
    ).all()

    return [
        {
            "booking": booking,
            "event": event,
            "venue": venue_summary(venue),
        }
        for booking, event, venue in rows
    ]


@router.post("/")
def make_booking(
    body: CreateBookingBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    existing = session.query(Booking).filter(
        Booking.user_id == user["sub"],
        Booking.event_id == body.event_id,
        Booking.status == "confirmed",
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Event already booked")

    event = session.query(Event).filter(Event.id == body.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Checking for specific conditions for the event so that the client won't book a bugged event.
    now = datetime.utcnow()
    # Is event active?
    if event.status != "active":
        raise HTTPException(status_code=409, detail="Event is not active")
    
    # Has it ended
    if event.ends_at is not None and event.ends_at <= now:
        raise HTTPException(status_code=409, detail="Event has ended")

    # Has it already started: maybe makes sense not to check that sometimes.
    if event.ends_at is None and event.starts_at <= now:
        raise HTTPException(status_code=409, detail="Event has already started")


    if event.spots_remaining is not None:
        if event.spots_remaining < body.quantity:
            raise HTTPException(status_code=409, detail="Not enough spots remaining")
        event.spots_remaining -= body.quantity

    booking = Booking(
        user_id=user["sub"],
        event_id=body.event_id,
        quantity=body.quantity,
        total_price_cents=event.price_cents * body.quantity,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


@router.patch("/{booking_id}")
def cancel_booking(
    booking_id: UUID,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    booking = session.query(Booking).filter(
        Booking.user_id == user["sub"],
        Booking.id == booking_id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "cancelled":
        raise HTTPException(status_code=409, detail="Booking already cancelled")

    booking.status = "cancelled"
    booking.cancelled_at = datetime.utcnow()

    event = session.query(Event).filter(Event.id == booking.event_id).first()
    if event and event.spots_remaining is not None:
        event.spots_remaining += booking.quantity

    session.commit()
    session.refresh(booking)
    return booking
