# automations/bots/substack_bot.py
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

SUBSTACK_POSTS_PER_RUN = int(os.getenv("SUBSTACK_POSTS_PER_RUN", "1"))
SUBSTACK_DRY_RUN = os.getenv("SUBSTACK_DRY_RUN", "true").lower() == "true"


def select_items_for_substack(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtert Queue-Items für Substack.
    Erwartet items mit "platform": "substack".
    """
    return [it for it in items if str(it.get("platform", "")).lower() == "substack"]


def send_to_substack(item: Dict[str, Any]):
    """
    Placeholder für echten Substack-API-/Mail-Call.
    Aktuell: nur Logging (DRY RUN).
    """
    text = item.get("text", "")
    if SUBSTACK_DRY_RUN:
        logger.info(f"[substack_bot] DRY RUN – would post Substack teaser:\n{text}\n")
        return

    # TODO: Substack API oder E-Mail-Flow einbauen
    raise NotImplementedError("Live Substack posting not implemented yet.")


def main():
    logger.info("[substack_bot] Starting run")

    queue_path = find_latest_queue_file()
    if not queue_path:
        logger.warning("[substack_bot] No queue file found. Exiting.")
        return

    items = load_queue(queue_path)
    substack_items = select_items_for_substack(items)
    if not substack_items:
        logger.info("[substack_bot] No Substack items in queue. Exiting.")
        return

    sent_path, sent_ids = load_sent_ids("substack")

    unsent = []
    for it in substack_items:
        item_id = make_item_id(it)
        if item_id in sent_ids:
            continue
        it["_id"] = item_id
        unsent.append(it)

    if not unsent:
        logger.info("[substack_bot] No unsent Substack items. Exiting.")
        return

    to_send = unsent[:SUBSTACK_POSTS_PER_RUN]
    logger.info(f"[substack_bot] Will send {len(to_send)} Substack posts (of {len(unsent)} unsent).")

    for it in to_send:
        try:
            send_to_substack(it)
            sent_ids.add(it["_id"])
        except Exception as e:
            logger.error(f"[substack_bot] Error sending Substack post: {e}")

    save_sent_ids(sent_path, sent_ids)
    logger.info("[substack_bot] Done.")


if __name__ == "__main__":
    main()
