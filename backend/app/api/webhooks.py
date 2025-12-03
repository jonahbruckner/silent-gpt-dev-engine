import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..utils.email import send_download_email  # relativer Import!

router = APIRouter(tags=["webhooks"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BACKEND_BASE_URL = os.getenv(
    "BACKEND_BASE_URL",
    "https://example-backend.onrender.com",
).rstrip("/")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Empfängt Stripe-Webhooks.
    Bei checkout.session.completed:
    - pack_slug aus metadata lesen (wird in payments.py gesetzt)
    - session_id aus Event nehmen
    - Download-Link bauen
    - E-Mail mit Download-Link schicken
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        session = data
        session_id = session.get("id")
        metadata = session.get("metadata") or {}
        pack_slug = metadata.get("pack_slug")

        customer_email = (session.get("customer_details") or {}).get("email")

        if pack_slug and customer_email and session_id:
            # → Download-URL verwendet deinen bestehenden /download/{pack_slug}-Endpoint
            download_url = f"{BACKEND_BASE_URL}/download/{pack_slug}?session_id={session_id}"
            send_download_email(customer_email, pack_slug, download_url)
            print(
                f"[stripe_webhook] Sent download email for pack={pack_slug} "
                f"to {customer_email} (session_id={session_id})"
            )
        else:
            print(
                "[stripe_webhook] Missing pack_slug, customer_email or session_id; "
                "skipping email."
            )

    return JSONResponse({"received": True})
