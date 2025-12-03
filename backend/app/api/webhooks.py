import os

import stripe
from fastapi import APIRouter, HTTPException, Request

from ..utils.email import send_download_email

router = APIRouter(tags=["webhooks"])

STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
PUBLIC_SITE_URL = os.environ.get(
    "PUBLIC_SITE_URL",
    "https://example-netlify-site.netlify.app",
)
BACKEND_BASE_URL = os.environ.get(
    "BACKEND_BASE_URL",
    "https://example-backend.onrender.com",
)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe Webhook:
    - validiert die Signatur
    - reagiert auf checkout.session.completed
    - schickt dem Kunden eine E-Mail mit Download-Link.
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured.")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

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
        metadata = session.get("metadata") or {}
        pack_slug = metadata.get("pack_slug")
        customer_email = (session.get("customer_details") or {}).get("email")
        session_id = session.get("id")

        if pack_slug and customer_email and session_id:
            # Der Download ist über die UI-Seite /thank-you erreichbar
            download_url = f"{PUBLIC_SITE_URL}/thank-you/?pack={pack_slug}&session_id={session_id}"
            send_download_email(customer_email, pack_slug, download_url)
            print(
                f"[stripe_webhook] Sent download email for pack={pack_slug} "
                f"to {customer_email} (session_id={session_id})"
            )
        else:
            print(
                "[stripe_webhook] Missing pack_slug, customer_email or session_id in event payload."
            )

    # Weitere Event-Typen kannst du bei Bedarf ergänzen.
    return {"received": True}
