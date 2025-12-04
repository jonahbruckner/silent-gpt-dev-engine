# automations/bots/devto_bot.py
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

DEVTO_POSTS_PER_RUN = int(os.getenv("DEVTO_POSTS_PER_RUN", "2"))
DEVTO_DRY_RUN = os.getenv("DEVTO_DRY_RUN", "true").lower() == "true"


def select_items_for_devto(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtert Queue-Items für dev.to.
    Erwartet items mit "platform": "devto".
    """
    return [it for it in items if str(it.get("platform", "")).lower() == "devto"]


def send_to_devto(item: Dict[str, Any]):
    """
    Placeholder für echten dev.to API-Call.
    Aktuell: nur Logging (DRY RUN).
    """
    text = item.get("text", "")
    if DEVTO_DRY_RUN:
        logger.info(f"[devto_bot] DRY RUN – would post Dev.to description:\n{text}\n")
        return

    # TODO: dev.to API-Call einbauen
    raise NotImplementedError("Live dev.to posting not implemented yet.")


def main():
    logger.info("[devto_bot] Starting run")

    queue_path = find_latest_queue_file()
    if not queue_path:
        logger.warning("[devto_bot] No queue file found. Exiting.")
        return

    items = load_queue(queue_path)
    devto_items = select_items_for_devto(items)
    if not devto_items:
        logger.info("[devto_bot] No dev.to items in queue. Exiting.")
        return

    sent_path, sent_ids = load_sent_ids("devto")

    unsent = []
    for it in devto_items:
        item_id = make_item_id(it)
        if item_id in sent_ids:
            continue
        it["_id"] = item_id
        unsent.append(it)

    if not unsent:
        logger.info("[devto_bot] No unsent dev.to items. Exiting.")
        return

    to_send = unsent[:DEVTO_POSTS_PER_RUN]
    logger.info(f"[devto_bot] Will send {len(to_send)} Dev.to posts (of {len(unsent)} unsent).")

    for it in to_send:
        try:
            send_to_devto(it)
            sent_ids.add(it["_id"])
        except Exception as e:
            logger.error(f"[devto_bot] Error sending Dev.to post: {e}")

    save_sent_ids(sent_path, sent_ids)
    logger.info("[devto_bot] Done.")


if __name__ == "__main__":
    main()
