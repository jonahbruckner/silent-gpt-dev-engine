# automations/bots/twitter_bot.py
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

# Wie viele Tweets pro Run?
TWITTER_POSTS_PER_RUN = int(os.getenv("TWITTER_POSTS_PER_RUN", "2"))
TWITTER_DRY_RUN = os.getenv("TWITTER_DRY_RUN", "true").lower() == "true"


def select_items_for_twitter(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtert Queue-Items für Twitter/X.
    Erwartet items mit "platform": "twitter".
    """
    return [it for it in items if str(it.get("platform", "")).lower() == "twitter"]


def send_to_twitter(item: Dict[str, Any]):
    """
    Placeholder für echten Twitter/X API-Call.
    Aktuell: nur Logging (DRY RUN).
    """
    text = item.get("text", "")
    if TWITTER_DRY_RUN:
        logger.info(f"[twitter_bot] DRY RUN – would post Tweet:\n{text}\n")
        return

    # TODO: Hier später echten X/Twitter-API-Call einbauen
    # z.B. mit tweepy oder offiziellem v2 Client.
    # Für jetzt lassen wir es bei DRY RUN.
    raise NotImplementedError("Live Twitter posting not implemented yet.")


def main():
    logger.info("[twitter_bot] Starting run")

    queue_path = find_latest_queue_file()
    if not queue_path:
        logger.warning("[twitter_bot] No queue file found. Exiting.")
        return

    items = load_queue(queue_path)
    twitter_items = select_items_for_twitter(items)
    if not twitter_items:
        logger.info("[twitter_bot] No twitter items in queue. Exiting.")
        return

    sent_path, sent_ids = load_sent_ids("twitter")

    # filter out already sent
    unsent = []
    for it in twitter_items:
        item_id = make_item_id(it)
        if item_id in sent_ids:
            continue
        it["_id"] = item_id
        unsent.append(it)

    if not unsent:
        logger.info("[twitter_bot] No unsent twitter items. Exiting.")
        return

    # Nur N pro Run
    to_send = unsent[:TWITTER_POSTS_PER_RUN]
    logger.info(f"[twitter_bot] Will send {len(to_send)} tweets (of {len(unsent)} unsent).")

    for it in to_send:
        try:
            send_to_twitter(it)
            sent_ids.add(it["_id"])
        except Exception as e:
            logger.error(f"[twitter_bot] Error sending tweet: {e}")

    save_sent_ids(sent_path, sent_ids)
    logger.info("[twitter_bot] Done.")


if __name__ == "__main__":
    main()
