import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request

import stripe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    stripe.api_key = None

# ROOT_DIR analog zu payments.py
ROOT_DIR = Path(__file__).resolve().parents[3]
METRICS_DIR = ROOT_DIR / "data" / "metrics"
EVENTS_FILE = METRICS_DIR / "stripe_events.jsonl"
SALES_FILE = METRICS_DIR / "sales_by_pack.json"


def ensure_metrics_dir():
    METRICS_DIR.mkdir(parents=True, exist_ok=True)


def append_event_line(event_data: dict):
    ensure_metrics_dir()
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event_data, ensure_ascii=False) + "\n")


def update_sales_aggregate(pack_slug: str, amount: int, currency: str):
    """
    amount: in kleinster Einheit (z.B. cents)
    currency: 'eur'
    """
    ensure_metrics_dir()
    data = {}
    if SALES_FILE.exists():
        try:
            data = json.loads(SALES_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    pack_stats = data.get(pack_slug) or {
        "pack_slug": pack_slug,
        "currency": currency,
        "total_amount": 0,
        "total_sales": 0,
        "last_sale_at": None,
    }

    pack_stats["total_amount"] += amount
    pack_stats["total_sales"] += 1
    pack_stats["currency"] = currency
    pack_stats["last_sale_at"] = datetime.now(timezone.utc).isoformat()

    data[pack_slug] = pack_stats

    SALES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    if not STRIPE_WEBHOOK_SECRET:
        logger.error("[webhooks] STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")

    payload = await request.body()
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        # Invalid payload
        logger.warning("[webhooks] Invalid payload: %s", e)
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.warning("[webhooks] Invalid signature: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    logger.info("[webhooks] Received event type=%s", event_type)

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]

        pack_slug = (session.get("metadata") or {}).get("pack_slug")
        session_id = session.get("id")
        amount_total = session.get("amount_total") or 0
        currency = session.get("currency") or "eur"
        customer_email = session.get("customer_details", {}).get("email")
        created_ts = session.get("created")

        created_iso = None
        if created_ts is not None:
            created_iso = datetime.fromtimestamp(created_ts, tz=timezone.utc).isoformat()

        event_record = {
            "event_type": event_type,
            "session_id": session_id,
            "pack_slug": pack_slug,
            "amount_total": amount_total,
            "currency": currency,
            "customer_email": customer_email,
            "created_at": created_iso,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }

        append_event_line(event_record)
        if pack_slug:
            update_sales_aggregate(pack_slug, amount_total, currency)

        logger.info(
            "[webhooks] Recorded checkout.session.completed for pack=%s, amount=%s %s",
            pack_slug,
            amount_total,
            currency,
        )

    # du kannst später weitere Event-Typen ergänzen, z.B. invoice.payment_failed etc.

    return {"status": "ok"}
