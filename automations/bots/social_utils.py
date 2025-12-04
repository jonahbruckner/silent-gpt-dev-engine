from pathlib import Path
import logging
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Projektroot: zwei Ebenen hoch von bots/
BASE_DIR = Path(__file__).resolve().parents[2]

SOCIAL_QUEUE_DIR = BASE_DIR / "data" / "social_queue"
SOCIAL_SENT_DIR = BASE_DIR / "data" / "social_sent"



def find_latest_queue_file() -> Optional[Path]:
    """
    Sucht die neueste social_queue-Datei (YYYY-MM-DD.json).
    """
    if not SOCIAL_QUEUE_DIR.exists():
        logger.warning(f"[social_utils] No social_queue dir at {SOCIAL_QUEUE_DIR}")
        return None

    candidates = sorted(SOCIAL_QUEUE_DIR.glob("*.json"))
    if not candidates:
        logger.warning(f"[social_utils] No queue files in {SOCIAL_QUEUE_DIR}")
        return None

    return candidates[-1]


def load_queue(path: Path) -> List[Dict[str, Any]]:
    """
    Lädt die Queue-Datei und gibt die items-Liste zurück.
    Struktur:
    {
      "date": "YYYY-MM-DD",
      "created_at": "...",
      "items": [...]
    }
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"[social_utils] Failed to load queue {path}: {e}")
        return []

    items = data.get("items", [])
    if not isinstance(items, list):
        logger.error(f"[social_utils] Queue file {path} has invalid 'items' field.")
        return []

    return items


def make_item_id(item: Dict[str, Any]) -> str:
    """
    Baut eine stabile ID aus platform + text.
    """
    platform = str(item.get("platform", "")).strip().lower()
    text = str(item.get("text", "")).strip()
    base = f"{platform}|{text}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def load_sent_ids(platform: str) -> Tuple[Path, set]:
    """
    Lädt gesendete IDs aus data/social_sent/{platform}.json.
    """
    SOCIAL_SENT_DIR.mkdir(parents=True, exist_ok=True)
    path = SOCIAL_SENT_DIR / f"{platform}.json"

    if not path.exists():
        return path, set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ids = set(data.get("ids", []))
        return path, ids
    except Exception as e:
        logger.error(f"[social_utils] Failed to load sent-log for {platform}: {e}")
        return path, set()


def save_sent_ids(path: Path, ids: set):
    """
    Speichert gesendete IDs.
    """
    payload = {"ids": sorted(ids)}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(f"[social_utils] Updated sent-log -> {path}")
