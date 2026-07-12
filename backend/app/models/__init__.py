# app/models/models.py
from sqlalchemy import (
    Boolean, Column, ForeignKey, Index, Integer,
    Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy import DateTime

from app.database import Base

# Basically follows the structure of our database but in python.
# Basically ORM. No need to separte because it is quite small as of rn.

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True)           # no default — Supabase auth sets this
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    user_type = Column(String, server_default="student")
    created_at = Column(DateTime, server_default=text("now()"))


class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=text("now()"))


class OrganisationMember(Base):
    __tablename__ = "organisation_members"

    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, primary_key=True)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=text("now()"))

    # unique(organisation_id, user_id) is covered by the composite primary_key above


class BusynessArea(Base):
    __tablename__ = "busyness_areas"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String, nullable=False)
    lat = Column(Numeric(9, 6), nullable=False)
    lng = Column(Numeric(9, 6), nullable=False)
    radius_metres = Column(Integer, nullable=False, server_default=text("500"))
    created_at = Column(DateTime, server_default=text("now()"))


class Venue(Base):
    __tablename__ = "venues"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    busyness_area_id = Column(UUID(as_uuid=True), ForeignKey("busyness_areas.id"))
    name = Column(String, nullable=False)
    address = Column(String)
    lat = Column(Numeric(9, 6), nullable=False)
    lng = Column(Numeric(9, 6), nullable=False)
    category = Column(String)
    is_accessible = Column(Boolean, server_default=text("false"))
    created_at = Column(DateTime, server_default=text("now()"))


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False)
    host_organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String)
    category = Column(String)
    price_cents = Column(Integer, nullable=False, server_default=text("0"))
    original_price_cents = Column(Integer)
    capacity = Column(Integer)
    spots_remaining = Column(Integer)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime)
    ai_summary = Column(Text)
    status = Column(String, nullable=False, server_default=text("'draft'"))
    created_at = Column(DateTime, server_default=text("now()"))
    image_url = Column(Text)
    external_event_id = Column(String)

    __table_args__ = (
        Index(None, "status", "starts_at"),
        Index(None, "venue_id"),
        Index(
            "events_external_event_id_idx",
            "external_event_id",
            unique=True,
            postgresql_where=text("external_event_id is not null"),
        ),
    )


class BusynessScore(Base):
    __tablename__ = "busyness_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    area_id = Column(UUID(as_uuid=True), ForeignKey("busyness_areas.id"), nullable=False)
    observed_at = Column(DateTime, nullable=False)
    local_day_of_week = Column(Integer, nullable=False)
    local_hour = Column(Integer, nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    source = Column(String)
    confidence = Column(Numeric(5, 2))
    level = Column(String)
    is_prediction = Column(Boolean, server_default=text("false"))
    updated_at = Column(DateTime, server_default=text("now()"))

    __table_args__ = (
        Index(None, "area_id", "local_day_of_week", "local_hour"),
        Index(None, "observed_at"),
    )


class SavedEvent(Base):
    __tablename__ = "saved_events"

    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, primary_key=True)
    saved_at = Column(DateTime, server_default=text("now()"))


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    quantity = Column(Integer, nullable=False, server_default=text("1"))
    status = Column(String, nullable=False, server_default=text("'confirmed'"))
    total_price_cents = Column(Integer, nullable=False, server_default=text("0"))
    booked_at = Column(DateTime, server_default=text("now()"))
    cancelled_at = Column(DateTime)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    feature = Column(String)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, server_default=text("now()"))


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    quantity = Column(Integer, nullable=False, server_default=text("1"))
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, server_default=text("'eur'"))
    status = Column(String, nullable=False, server_default=text("'pending'"))
    stripe_checkout_session_id = Column(String, unique=True)
    stripe_payment_intent_id = Column(String, unique=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), unique=True)
    created_at = Column(DateTime, server_default=text("now()"))
    updated_at = Column(DateTime, server_default=text("now()"))

    __table_args__ = (
        Index("payments_user_id_idx", "user_id"),
        Index("payments_event_id_idx", "event_id"),
        Index("payments_status_idx", "status"),
    )
