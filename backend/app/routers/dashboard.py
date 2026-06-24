from datetime import datetime, timedelta, UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_session
from app.middleware.auth import get_current_user, require_organisation_member
from app.models import Booking, Event, Organisation, Venue

router = APIRouter(prefix="/organisations", tags=["organisations"])


def start_of_month(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def start_of_week(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())


def venue_summary(venue: Venue) -> dict:
    return {
        "id": venue.id,
        "name": venue.name,
        "address": venue.address,
        "lat": float(venue.lat),
        "lng": float(venue.lng),
    }


def event_display_status(event: Event, sold: int, now: datetime) -> str:
    if event.status == "draft":
        return "draft"
    if event.status == "cancelled":
        return "cancelled"
    if event.status == "completed":
        return "expired"
    if event.ends_at is not None and event.ends_at <= now:
        return "expired"
    if event.spots_remaining == 0:
        return "sold_out"
    if event.capacity is not None and sold >= event.capacity:
        return "sold_out"
    return event.status


def sold_count(event: Event, booked_quantity: int) -> int:
    if booked_quantity > 0:
        return booked_quantity
    if event.capacity is not None and event.spots_remaining is not None:
        return max(event.capacity - event.spots_remaining, 0)
    return 0


@router.get("/{organisation_id}/dashboard")
def get_organisation_dashboard(
    organisation_id: UUID,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    organisation = session.query(Organisation).filter(Organisation.id == organisation_id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    require_organisation_member(session, user["sub"], organisation_id)

    now = datetime.now(UTC)
    month_start = start_of_month(now)
    week_start = start_of_week(now)

    event_rows = (
        session.query(Event, Venue)
        .join(Venue, Event.venue_id == Venue.id)
        .filter(Event.host_organisation_id == organisation_id)
        .order_by(Event.starts_at.asc())
        .all()
    )
    event_ids = [event.id for event, _venue in event_rows]

    booking_totals = {}
    if event_ids:
        rows = (
            session.query(
                Booking.event_id,
                func.coalesce(func.sum(Booking.quantity), 0).label("tickets_sold"),
                func.coalesce(func.sum(Booking.total_price_cents), 0).label("revenue_cents"),
                func.coalesce(func.count(Booking.id), 0).label("booking_count"),
            )
            .filter(
                Booking.event_id.in_(event_ids),
                Booking.status == "confirmed",
            )
            .group_by(Booking.event_id)
            .all()
        )
        booking_totals = {
            row.event_id: {
                "tickets_sold": int(row.tickets_sold or 0),
                "revenue_cents": int(row.revenue_cents or 0),
                "booking_count": int(row.booking_count or 0),
            }
            for row in rows
        }

    listings = []
    for event, venue in event_rows:
        totals = booking_totals.get(
            event.id,
            {"tickets_sold": 0, "revenue_cents": 0, "booking_count": 0},
        )
        sold = sold_count(event, totals["tickets_sold"])
        display_status = event_display_status(event, sold, now)

        listings.append(
            {
                "id": event.id,
                "title": event.title,
                "category": event.category,
                "starts_at": event.starts_at,
                "ends_at": event.ends_at,
                "price_cents": event.price_cents,
                "capacity": event.capacity,
                "spots_remaining": event.spots_remaining,
                "sold": sold,
                "status": event.status,
                "display_status": display_status,
                "bookings_count": totals["booking_count"],
                "revenue_cents": totals["revenue_cents"],
                "venue": venue_summary(venue),
            }
        )

    bookings_this_month = (
        session.query(func.coalesce(func.count(Booking.id), 0))
        .join(Event, Booking.event_id == Event.id)
        .filter(
            Event.host_organisation_id == organisation_id,
            Booking.status == "confirmed",
            Booking.booked_at >= month_start,
        )
        .scalar()
    )

    revenue_this_week_cents = (
        session.query(func.coalesce(func.sum(Booking.total_price_cents), 0))
        .join(Event, Booking.event_id == Event.id)
        .filter(
            Event.host_organisation_id == organisation_id,
            Booking.status == "confirmed",
            Booking.booked_at >= week_start,
        )
        .scalar()
    )

    return {
        "organisation": {
            "id": organisation.id,
            "name": organisation.name,
            "created_at": organisation.created_at,
        },
        "summary": {
            "bookings_this_month": int(bookings_this_month or 0),
            "active_listings": sum(1 for listing in listings if listing["display_status"] == "active"),
            "revenue_this_week_cents": int(revenue_this_week_cents or 0),
            "total_listings": len(listings),
            "draft_listings": sum(1 for listing in listings if listing["display_status"] == "draft"),
            "sold_out_listings": sum(1 for listing in listings if listing["display_status"] == "sold_out"),
            "expired_listings": sum(1 for listing in listings if listing["display_status"] == "expired"),
        },
        "listings": listings,
    }
