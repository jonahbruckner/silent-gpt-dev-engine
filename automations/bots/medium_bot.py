# automations/bots/medium_bot.py
import os
import logging
from typing import List, Dict, Any

from .social_utils import (
    find_latest_queue_file,
    load_queue,
    make_item_id,
    load_sent_ids,
    save_sent_ids,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEDIUM_POSTS_PER_RUN = int(os.getenv("MEDIUM_POSTS_PER_RUN", "2"))
MEDIUM_DRY_RUN = os.getenv("MEDIUM_DRY_RUN", "true").lower() == "true"


def select_items_for_medium(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtert Queue-Items für Medium.
    Erwartet items mit "platform": "medium".
    """
    return [it for it in items if str(it.get("platform", "")).lower() == "medium"]


def send_to_medium(item: Dict[str, Any]):
    """
    Placeholder für echten Medium-API-Call.
    Aktuell: nur Logging (DRY RUN).
    """
    text = item.get("text", "")
    if MEDIUM_DRY_RUN:
        logger.info(f"[medium_bot] DRY RUN – would post Medium description:\n{text}\n")
        return

    # TODO: Medium API-Call einbauen
    raise NotImplementedError("Live Medium posting not implemented yet.")


def main():
    logger.info("[medium_bot] Starting run")

    queue_path = find_latest_queue_file()
    if not queue_path:
        logger.warning("[medium_bot] No queue file found. Exiting.")
        return

    items = load_queue(queue_path)
    medium_items = select_items_for_medium(items)
    if not medium_items:
        logger.info("[medium_bot] No Medium items in queue. Exiting.")
        return

    sent_path, sent_ids = load_sent_ids("medium")

    unsent = []
    for it in medium_items:
        item_id = make_item_id(it)
        if item_id in sent_ids:
            continue
        it["_id"] = item_id
        unsent.append(it)

    if not unsent:
        logger.info("[medium_bot] No unsent Medium items. Exiting.")
        return

    to_send = unsent[:MEDIUM_POSTS_PER_RUN]
    logger.info(f"[medium_bot] Will send {len(to_send)} Medium posts (of {len(unsent)} unsent).")

    for it in to_send:
        try:
            send_to_medium(it)
            sent_ids.add(it["_id"])
        except Exception as e:
            logger.error(f"[medium_bot] Error sending Medium post: {e}")

    save_sent_ids(sent_path, sent_ids)
    logger.info("[medium_bot] Done.")


if __name__ == "__main__":
    main()
