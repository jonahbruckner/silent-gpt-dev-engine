"""
Stripe Checkout + Download-Endpoints für SilentGPT Packs.

Unterstützt zwei Flows:

1) Legacy-Link-Flow (ohne Stripe Price-ID):
   - GET /pay/{pack_slug}
     -> Erstellt Stripe Checkout Session mit price_data (Betrag aus PACK_PRICE_EUR_CENTS)
     -> HTTP 303 Redirect direkt zu Stripe Checkout

2) Neuer API-Flow (mit Stripe Price-ID aus Pack-JSON):
   - POST /api/checkout/session
     -> Erwartet JSON { "price_id": "...", "pack_slug": "..." }
     -> Liefert {"id": "...", "url": "..."} zurück
     -> Frontend leitet auf session.url weiter

3) Download-Endpunkt:
   - GET /download/{pack_slug}?session_id=...
     -> Validiert Stripe-Session und liefert ZIP-Datei
"""

import os
from pathlib import Path

import stripe
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel

router = APIRouter(tags=["payments"])

# Stripe nur konfigurieren, wenn der Key gesetzt ist.
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    # Kein harter Fehler beim Import – wichtig für Services,
    # die Stripe gar nicht nutzen (z. B. lokale Dev-Instanz).
    stripe.api_key = None

PUBLIC_SITE_URL = os.environ.get(
    "PUBLIC_SITE_URL",
    "https://example-netlify-site.netlify.app",
).rstrip("/")

BACKEND_BASE_URL = os.environ.get(
    "BACKEND_BASE_URL",
    "https://example-backend.onrender.com",
).rstrip("/")

# Legacy-Festpreis (nur für /pay/{pack_slug} verwendet)
PACK_PRICE_EUR_CENTS = int(os.environ.get("PACK_PRICE_EUR_CENTS", "899"))

ROOT_DIR = Path(__file__).resolve().parents[3]
DOWNLOADS_DIR = ROOT_DIR / "site" / "static" / "downloads"


# ---------------------------
# 1) Neuer JSON-Checkout-Flow
# ---------------------------

class CheckoutRequest(BaseModel):
    price_id: str   # Stripe price_xxx
    pack_slug: str  # z.B. fastapi-backend-pack-2025-w49


@router.post("/api/checkout/session")
async def create_checkout_session(payload: CheckoutRequest):
    """
    Neuer Checkout-Endpoint für Frontend/JS-Flow.

    Erwartet:
      {
        "price_id": "price_xxx",
        "pack_slug": "fastapi-backend-pack-2025-w49"
      }

    Antwort:
      {
        "id": "cs_xxx",
        "url": "https://checkout.stripe.com/..."
      }
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Payment service not configured (missing STRIPE_SECRET_KEY).",
        )

    try:
        success_url = (
            f"{PUBLIC_SITE_URL}/thank-you/"
            f"?pack={payload.pack_slug}&session_id={{CHECKOUT_SESSION_ID}}"
        )
        cancel_url = f"{PUBLIC_SITE_URL}/products/{payload.pack_slug}/"

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price": payload.price_id,
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "pack_slug": payload.pack_slug,
                "price_id": payload.price_id,
            },
        )

        return {"id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {e}")


# ---------------------------
# 2) Bestehender /pay/{pack_slug}-Flow
# ---------------------------

@router.get("/pay/{pack_slug}")
async def create_checkout_and_redirect(pack_slug: str):
    """
    Legacy-Flow:
    - Prüft, ob es ein ZIP zum Pack gibt
    - Erstellt Checkout Session mit price_data (PACK_PRICE_EUR_CENTS)
    - Redirect direkt zu Stripe
    """
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
                f"{PUBLIC_SITE_URL}/thank-you/"
                f"?pack={pack_slug}&session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{PUBLIC_SITE_URL}/products/{pack_slug}/",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")

    return RedirectResponse(session.url, status_code=303)


# ---------------------------
# 3) Download-Endpoint (bleibt)
# ---------------------------

@router.get("/download/{pack_slug}")
async def download_pack(pack_slug: str, session_id: str = Query(...)):
    """
    Prüft Stripe-Checkout-Session und liefert ZIP-File,
    falls Zahlung abgeschlossen und Pack-Slug übereinstimmt.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Payment service not configured (missing STRIPE_SECRET_KEY).",
        )

    # Falls Stripe {CHECKOUT_SESSION_ID} → cs_... einsetzt, Klammern entfernen
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
