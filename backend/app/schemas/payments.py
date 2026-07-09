from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema, OrmSchema


PaymentStatus = Literal["pending", "paid", "failed", "cancelled", "expired"]


class CreateCheckoutSessionBody(ApiSchema):
    event_id: UUID
    quantity: int = Field(default=1, gt=0)
    customer_email: str | None = None


class CheckoutSessionResponse(ApiSchema):
    payment_id: UUID
    checkout_session_id: str
    checkout_url: str
    status: PaymentStatus


class PaymentResponse(OrmSchema):
    id: UUID
    user_id: UUID
    event_id: UUID
    quantity: int
    amount_cents: int
    currency: str
    status: PaymentStatus
    stripe_checkout_session_id: str | None
    stripe_payment_intent_id: str | None
    booking_id: UUID | None
    created_at: datetime
    updated_at: datetime


class WebhookResponse(ApiSchema):
    received: bool
    payment_id: UUID | None = None
    status: PaymentStatus | None = None
    detail: str | None = None
