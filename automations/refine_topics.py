import os
import sys
from collections import Counter

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session
from app.models.content import ContentItem

from app.db import init_db
init_db()

def run():
    with get_session() as session:
        items = session.exec(select(ContentItem)).all()

    if not items:
        print("[refine_topics] No content items yet.")
        return

    counter = Counter()
    for item in items:
        tags = (item.tags or "").split(",")
        for t in tags:
            t = t.strip()
            if t:
                counter[t] += 1

    print("[refine_topics] Top tags so far:")
    for tag, count in counter.most_common(20):
        print(f"  {tag}: {count} items")


if __name__ == "__main__":
    run()
