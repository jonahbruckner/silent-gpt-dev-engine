# backend/app/api/metrics.py
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/metrics", tags=["metrics"])

ROOT_DIR = Path(__file__).resolve().parents[3]
METRICS_DIR = ROOT_DIR / "data" / "metrics"
SALES_FILE = METRICS_DIR / "sales_by_pack.json"
EVENTS_FILE = METRICS_DIR / "stripe_events.jsonl"


@router.get("/sales")
def get_sales_summary():
    """
    Liefert Aggregat pro Pack aus sales_by_pack.json.
    Struktur: { pack_slug: { total_sales, total_amount, currency, last_sale_at, ... }, ... }
    """
    if not SALES_FILE.exists():
        return {}

    try:
        data = json.loads(SALES_FILE.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/latest")
def get_latest_events(limit: int = 10):
    """
    Gibt die letzten Stripe-Events aus stripe_events.jsonl zurück.
    """
    if not EVENTS_FILE.exists():
        return []

    try:
        lines = EVENTS_FILE.read_text(encoding="utf-8").strip().split("\n")
        events = [json.loads(line) for line in lines if line.strip()]
        return events[-limit:]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
