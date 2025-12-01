import os
import sys
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session
from app.models.content import ContentItem

PACKS_DIR = os.path.join(ROOT_DIR, "content", "packs")
MIN_ITEMS_PER_TOPIC = 15  # only build packs if enough material


def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def run():
    ensure_dir(PACKS_DIR)

    with get_session() as session:
        items = session.exec(
            select(ContentItem).where(ContentItem.status == "published")
        ).all()

        if not items:
            print("[build_packs] No published items to pack.")
            return

        by_topic = defaultdict(list)
        for item in items:
            tags = (item.tags or "").split(",")
            for t in tags:
                t = t.strip()
                if t:
                    by_topic[t].append(item)

        for topic, topic_items in by_topic.items():
            if len(topic_items) < MIN_ITEMS_PER_TOPIC:
                continue

            slug = topic.replace(" ", "-").lower()
            filename = os.path.join(PACKS_DIR, f"{slug}-pack.md")

            print(f"[build_packs] Building pack for topic={topic} -> {filename}")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# {topic.title()} Recipes Pack\n\n")
                for item in topic_items:
                    f.write(f"## {item.title}\n\n")
                    f.write((item.body_md or "").strip())
                    f.write("\n\n---\n\n")

    print("[build_packs] Done.")


if __name__ == "__main__":
    run()
