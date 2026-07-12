from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.datetime import to_naive_utc, utc_now_naive
from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import Booking, Event, Payment
from app.schemas import (
    CheckoutSessionResponse,
    CreateCheckoutSessionBody,
    PaymentResponse,
    WebhookResponse,
)
from app.services import create_checkout_session, verify_webhook_event

router = APIRouter(prefix="/payments", tags=["payments"])


def metadata_value(stripe_object, key: str) -> str | None:
    metadata = getattr(stripe_object, "metadata", None)
    if metadata is None:
        return None
    try:
        return metadata[key]
    except KeyError:
        return None


@router.post(
    "/checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_checkout(
    body: CreateCheckoutSessionBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    existing_booking = session.query(Booking).filter(
        Booking.user_id == user["sub"],
        Booking.event_id == body.event_id,
        Booking.status == "confirmed",
    ).first()
    if existing_booking:
        raise HTTPException(status_code=409, detail="Event already booked")

    existing_pending_payment = session.query(Payment).filter(
        Payment.user_id == user["sub"],
        Payment.event_id == body.event_id,
        Payment.status == "pending",
    ).first()
    if existing_pending_payment:
        raise HTTPException(
            status_code=409,
            detail="A payment for this event is already pending",
        )

    event = session.query(Event).filter(Event.id == body.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    now = utc_now_naive()
    event_starts_at = to_naive_utc(event.starts_at)
    event_ends_at = to_naive_utc(event.ends_at)

    if event.status != "active":
        raise HTTPException(status_code=409, detail="Event is not active")

    if event.price_cents <= 0:
        raise HTTPException(
            status_code=409,
            detail="This event is free. Use /bookings/ instead.",
        )

    if event_ends_at is not None and event_ends_at <= now:
        raise HTTPException(status_code=409, detail="Event has ended")

    if event_ends_at is None and event_starts_at <= now:
        raise HTTPException(status_code=409, detail="Event has already started")

    if event.spots_remaining is not None and event.spots_remaining < body.quantity:
        raise HTTPException(status_code=409, detail="Not enough spots remaining")

    customer_email = body.customer_email or user.get("email")
    if not customer_email:
        raise HTTPException(status_code=400, detail="Customer email is required")

    payment = Payment(
        user_id=user["sub"],
        event_id=body.event_id,
        quantity=body.quantity,
        amount_cents=event.price_cents * body.quantity,
        currency="eur",
        status="pending",
    )
    session.add(payment)
    session.flush()

    try:
        checkout_session = create_checkout_session(
            payment=payment,
            event=event,
            customer_email=customer_email,
        )
    except RuntimeError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=502,
            detail="Stripe checkout session could not be created",
        ) from exc

    payment.stripe_checkout_session_id = checkout_session.id
    session.commit()
    session.refresh(payment)

    return CheckoutSessionResponse(
        payment_id=payment.id,
        checkout_session_id=checkout_session.id,
        checkout_url=checkout_session.url,
        status=payment.status,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: UUID,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    payment = session.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user["sub"],
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        event = verify_webhook_event(payload, signature)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Stripe webhook signature verification failed",
        ) from exc

    if event.type == "checkout.session.completed":
        checkout_session = event.data.object
        payment_id = None

        payment_id = metadata_value(checkout_session, "payment_id")
        if payment_id is None:
            payment_id = getattr(checkout_session, "client_reference_id", None)

        if payment_id is None:
            raise HTTPException(status_code=400, detail="Missing payment_id metadata")

        payment = session.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment.status == "paid":
            return WebhookResponse(
                received=True,
                payment_id=payment.id,
                status=payment.status,
                detail="Payment already processed",
            )

        booking = Booking(
            user_id=payment.user_id,
            event_id=payment.event_id,
            quantity=payment.quantity,
            total_price_cents=payment.amount_cents,
        )
        session.add(booking)
        session.flush()

        payment.status = "paid"
        payment.booking_id = booking.id

        payment_intent = getattr(checkout_session, "payment_intent", None)
        if payment_intent:
            payment.stripe_payment_intent_id = str(payment_intent)

        event_row = session.query(Event).filter(Event.id == payment.event_id).first()
        if event_row and event_row.spots_remaining is not None:
            event_row.spots_remaining = max(0, event_row.spots_remaining - payment.quantity)

        session.commit()
        session.refresh(payment)

        return WebhookResponse(
            received=True,
            payment_id=payment.id,
            status=payment.status,
            detail="Payment marked as paid and booking created",
        )

    if event.type == "checkout.session.expired":
        checkout_session = event.data.object
        payment_id = metadata_value(checkout_session, "payment_id")

        if payment_id is not None:
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            if payment and payment.status == "pending":
                payment.status = "expired"
                session.commit()
                session.refresh(payment)
                return WebhookResponse(
                    received=True,
                    payment_id=payment.id,
                    status=payment.status,
                    detail="Checkout session expired",
                )

    if event.type == "payment_intent.payment_failed":
        payment_intent = event.data.object
        payment_id = metadata_value(payment_intent, "payment_id")

        if payment_id is not None:
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            if payment:
                payment.status = "failed"
                payment.stripe_payment_intent_id = str(payment_intent.id)
                session.commit()
                session.refresh(payment)
                return WebhookResponse(
                    received=True,
                    payment_id=payment.id,
                    status=payment.status,
                    detail="Payment intent failed",
                )

    return WebhookResponse(
        received=True,
        detail=f"Ignored event type: {event.type}",
    )
