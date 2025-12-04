from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import stripe

router = APIRouter(prefix="/api/checkout", tags=["checkout"])

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
if not STRIPE_SECRET_KEY:
    stripe.api_key = None
else:
    stripe.api_key = STRIPE_SECRET_KEY

PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "").rstrip("/")
if PUBLIC_SITE_URL == "":
    PUBLIC_SITE_URL = "https://steady-lollipop-79396b.netlify.app"

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "").rstrip("/")
if BACKEND_BASE_URL == "":
    BACKEND_BASE_URL = "https://silent-gpt-dev-engine.onrender.com"


@router.post("/session")
async def create_checkout_session(item: dict):
    """
    Expects JSON:
    {
        "price_id": "price_...",
        "pack_slug": "fastapi-backend-pack-2025-w49"
    }
    """
    if stripe.api_key is None:
        raise HTTPException(500, "Stripe not configured")

    price_id = item.get("price_id")
    pack_slug = item.get("pack_slug")

    if not price_id or not pack_slug:
        raise HTTPException(400, "Missing price_id or pack_slug")

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            metadata={"pack_slug": pack_slug},
            success_url=(
                f"{PUBLIC_SITE_URL}/thank-you/?pack={pack_slug}"
                "&session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{PUBLIC_SITE_URL}/products/{pack_slug}/",
        )
    except Exception as e:
        raise HTTPException(500, f"Stripe error: {str(e)}")

    return JSONResponse({"url": session.url})
