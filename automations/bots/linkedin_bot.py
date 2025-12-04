# automations/bots/linkedin_bot.py
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

LINKEDIN_POSTS_PER_RUN = int(os.getenv("LINKEDIN_POSTS_PER_RUN", "1"))
LINKEDIN_DRY_RUN = os.getenv("LINKEDIN_DRY_RUN", "true").lower() == "true"


def select_items_for_linkedin(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtert Queue-Items für LinkedIn.
    Erwartet items mit "platform": "linkedin".
    """
    return [it for it in items if str(it.get("platform", "")).lower() == "linkedin"]


def send_to_linkedin(item: Dict[str, Any]):
    """
    Placeholder für echten LinkedIn-API-Call.
    Aktuell: nur Logging (DRY RUN).
    """
    text = item.get("text", "")
    if LINKEDIN_DRY_RUN:
        logger.info(f"[linkedin_bot] DRY RUN – would post LinkedIn post:\n{text}\n")
        return

    # TODO: Hier später echten LinkedIn-API-Call einbauen.
    raise NotImplementedError("Live LinkedIn posting not implemented yet.")


def main():
    logger.info("[linkedin_bot] Starting run")

    queue_path = find_latest_queue_file()
    if not queue_path:
        logger.warning("[linkedin_bot] No queue file found. Exiting.")
        return

    items = load_queue(queue_path)
    linkedin_items = select_items_for_linkedin(items)
    if not linkedin_items:
        logger.info("[linkedin_bot] No linkedin items in queue. Exiting.")
        return

    sent_path, sent_ids = load_sent_ids("linkedin")

    # Filter already sent
    unsent = []
    for it in linkedin_items:
        item_id = make_item_id(it)
        if item_id in sent_ids:
            continue
        it["_id"] = item_id
        unsent.append(it)

    if not unsent:
        logger.info("[linkedin_bot] No unsent linkedin items. Exiting.")
        return

    to_send = unsent[:LINKEDIN_POSTS_PER_RUN]
    logger.info(f"[linkedin_bot] Will send {len(to_send)} Linkedin posts (of {len(unsent)} unsent).")

    for it in to_send:
        try:
            send_to_linkedin(it)
            sent_ids.add(it["_id"])
        except Exception as e:
            logger.error(f"[linkedin_bot] Error sending LinkedIn post: {e}")

    save_sent_ids(sent_path, sent_ids)
    logger.info("[linkedin_bot] Done.")


if __name__ == "__main__":
    main()
