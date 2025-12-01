import os, sys
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # repo root
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
from app.db import get_session
from app.models.content import ContentItem

PACK_TOPICS = ["fastapi", "docker", "asyncio"]

def run():
    with get_session() as session:
        for topic in PACK_TOPICS:
            items = session.query(ContentItem).filter(ContentItem.tags.contains(topic)).all()
            if len(items) < 20:
                continue
        
            filename = f"../content/packs/{topic}-pack.md"
            with open(filename, "w", encoding="utf-8") as f:
                for item in items:
                    f.write(f"# {item.title}\n\n{item.body_md}\n\n---\n")

    print("📦 Packs generated.")
