import os
from pathlib import Path

import stripe
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, FileResponse

router = APIRouter(tags=["payments"])

# ------------------------------------------------------
# Stripe Grundkonfiguration
# ------------------------------------------------------
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    stripe.api_key = None  # erlaubt Start ohne Stripe

PUBLIC_SITE_URL = os.environ.get(
    "PUBLIC_SITE_URL",
    "https://steady-lollipop-79396b.netlify.app",
).rstrip("/")

BACKEND_BASE_URL = os.environ.get(
    "BACKEND_BASE_URL",
    "https://silent-gpt-dev-engine.onrender.com",
).rstrip("/")

ROOT_DIR = Path(__file__).resolve().parents[3]
DOWNLOADS_DIR = ROOT_DIR / "site" / "static" / "downloads"


# ------------------------------------------------------
# 1) GET /pay/{pack_slug}?price_id=price_xxx
#    -> erzeugt Stripe Checkout-Session, redirectet direkt
# ------------------------------------------------------
@router.get("/pay/{pack_slug}")
async def create_checkout_and_redirect(
    pack_slug: str,
    price_id: str = Query(..., description="Stripe price_id for this pack"),
):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Payment service not configured (missing STRIPE_SECRET_KEY).",
        )

    # Optional: prüfen, ob es die ZIP-Datei wirklich gibt
    zip_path = DOWNLOADS_DIR / f"{pack_slug}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Pack ZIP not found on server")

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
                f"{PUBLIC_SITE_URL}/thank-you/"
                f"?pack={pack_slug}&session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{PUBLIC_SITE_URL}/products/{pack_slug}/",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")

    # Browser-Navigation zu Stripe Checkout -> kein CORS
    return RedirectResponse(session.url, status_code=303)


# ------------------------------------------------------
# 2) GET /download/{pack_slug}?session_id=cs_...
#    -> prüft Zahlung + liefert ZIP
# ------------------------------------------------------
@router.get("/download/{pack_slug}")
async def download_pack(pack_slug: str, session_id: str = Query(...)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Payment service not configured (missing STRIPE_SECRET_KEY).",
        )

    clean_session_id = session_id.strip("{}")

    try:
        session = stripe.checkout.Session.retrieve(clean_session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid session: {e}")

    if session.payment_status != "paid":
        raise HTTPException(status_code=402, detail="Payment not completed")

    session_pack = (session.metadata or {}).get("pack_slug")
    if session_pack != pack_slug:
        raise HTTPException(status_code=403, detail="Pack mismatch")

    zip_path = DOWNLOADS_DIR / f"{pack_slug}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Pack file not found")

    return FileResponse(
        path=zip_path,
        filename=f"{pack_slug}.zip",
        media_type="application/zip",
    )
