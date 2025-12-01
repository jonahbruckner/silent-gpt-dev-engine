import os
import sys
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session
from app.models.content import ContentItem

POSTS_DIR = os.path.join(ROOT_DIR, "site", "posts")
MAX_POSTS_PER_RUN = 3  # balanced: up to 3/day

from app.db import init_db
init_db()

def slugify(title: str) -> str:
    return (
        title.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("?", "")
        .replace("#", "")
        .replace(":", "")
    )


def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def run():
    ensure_dir(POSTS_DIR)

    with get_session() as session:
        q = (
            select(ContentItem)
            .where(ContentItem.status.in_(("draft", "reviewed")))
            .limit(MAX_POSTS_PER_RUN)
        )
        items = session.exec(q).all()

        if not items:
            print("[publish_blog] No draft/reviewed content to publish.")
            return

        for item in items:
            created = item.created_at or datetime.utcnow()
            date_str = created.strftime("%Y-%m-%d")
            slug = slugify(item.title or f"post-{item.id}")
            filename = f"{date_str}-{slug}-{item.id}.md"
            path = os.path.join(POSTS_DIR, filename)

            print(f"[publish_blog] Writing {path}")
            with open(path, "w", encoding="utf-8") as f:
                f.write(item.body_md or "")

            item.status = "published"

        session.commit()
        print("[publish_blog] Marked items as published.")

    # Optional: auto-git-commit; comment out if Netlify handles differently
    try:
        os.system(
            f'cd "{os.path.join(ROOT_DIR, "site")}" && git add . && '
            'git commit -m "auto: new posts" && git push'
        )
        print("[publish_blog] Git push done.")
    except Exception as e:
        print(f"[publish_blog] Git push failed: {e}")


if __name__ == "__main__":
    run()
