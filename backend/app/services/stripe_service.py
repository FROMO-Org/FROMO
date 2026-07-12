import stripe

from app.core.config import (
    FRONTEND_URL,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)


def get_stripe_client() -> stripe.StripeClient:
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Missing STRIPE_SECRET_KEY in environment.")
    return stripe.StripeClient(STRIPE_SECRET_KEY)


def build_checkout_urls(payment_id: str) -> tuple[str, str]:
    base_url = FRONTEND_URL.rstrip("/")
    success_url = (
        f"{base_url}/checkout/success"
        f"?payment_id={payment_id}&session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = f"{base_url}/checkout/cancel?payment_id={payment_id}"
    return success_url, cancel_url


def create_checkout_session(*, payment, event, customer_email: str):
    client = get_stripe_client()
    success_url, cancel_url = build_checkout_urls(str(payment.id))

    return client.v1.checkout.sessions.create(
        {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer_email": customer_email,
            "client_reference_id": str(payment.id),
            "metadata": {
                "payment_id": str(payment.id),
                "event_id": str(payment.event_id),
            },
            "payment_intent_data": {
                "metadata": {
                    "payment_id": str(payment.id),
                    "event_id": str(payment.event_id),
                }
            },
            "line_items": [
                {
                    "quantity": payment.quantity,
                    "price_data": {
                        "currency": payment.currency,
                        "unit_amount": event.price_cents,
                        "product_data": {
                            "name": event.title,
                            "description": event.description
                            or f"FROMO ticket for {event.title}",
                        },
                    },
                }
            ],
        }
    )


def verify_webhook_event(payload: bytes, signature: str | None):
    if not STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("Missing STRIPE_WEBHOOK_SECRET in environment.")
    if not signature:
        raise ValueError("Missing Stripe-Signature header.")

    client = get_stripe_client()
    return client.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
