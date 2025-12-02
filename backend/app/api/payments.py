import os
from pathlib import Path

import stripe
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, FileResponse

router = APIRouter(tags=["payments"])

# Stripe nur konfigurieren, wenn der Key gesetzt ist.
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    # Kein harter Fehler beim Import – wichtig für Services,
    # die Stripe gar nicht nutzen (z. B. silent-gpt-dev-engine).
    stripe.api_key = None

PUBLIC_SITE_URL = os.environ.get(
    "PUBLIC_SITE_URL",
    "https://example-netlify-site.netlify.app",
)
BACKEND_BASE_URL = os.environ.get(
    "BACKEND_BASE_URL",
    "https://example-backend.onrender.com",
)
PACK_PRICE_EUR_CENTS = int(os.environ.get("PACK_PRICE_EUR_CENTS", "899"))

ROOT_DIR = Path(__file__).resolve().parents[3]
DOWNLOADS_DIR = ROOT_DIR / "site" / "static" / "downloads"


@router.get("/pay/{pack_slug}")
async def create_checkout_and_redirect(pack_slug: str):
    if not STRIPE_SECRET_KEY:
        # Stripe ist auf diesem Service nicht konfiguriert.
        raise HTTPException(
            status_code=500,
            detail="Payment service not configured (missing STRIPE_SECRET_KEY).",
        )

    zip_path = DOWNLOADS_DIR / f"{pack_slug}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Pack not found")

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {"name": f"SilentGPT Pack: {pack_slug}"},
                        "unit_amount": PACK_PRICE_EUR_CENTS,
                    },
                    "quantity": 1,
                }
            ],
            metadata={"pack_slug": pack_slug},
            success_url=(
                f"{BACKEND_BASE_URL}/download/{pack_slug}"
                "?session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{PUBLIC_SITE_URL}/products/{pack_slug}/",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")

    return RedirectResponse(session.url, status_code=303)

@router.get("/download/{pack_slug}")
async def download_pack(pack_slug: str, session_id: str = Query(...)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Payment service not configured (missing STRIPE_SECRET_KEY).",
        )

    # Falls Stripe {CHECKOUT_SESSION_ID} → {cs_...} einsetzt, Klammern entfernen
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
