import os
import sys
from datetime import datetime
from typing import Dict, List

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session
from app.models.content import ContentItem
from app.db import init_db

# Wohin geschrieben wird
STATIC_PACKS_DIR = os.path.join(ROOT_DIR, "site", "static", "packs")
PRODUCTS_DIR = os.path.join(ROOT_DIR, "site", "content", "products")

# Mindestanzahl Artikel pro Pack
MIN_ITEMS_PER_PACK = 5

init_db()


def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def slugify(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("?", "")
        .replace("#", "")
        .replace(":", "")
    )


# Sehr einfache Keyword-Heuristik für Themen
TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "python-data": ["python", "pandas", "numpy", "dataframe"],
    "fastapi-backend": ["fastapi", "api", "backend"],
    "ai-rag": ["rag", "langchain", "vector", "embedding", "llm"],
    "devops-docker": ["docker", "kubernetes", "container", "deploy"],
    "testing": ["pytest", "unit test", "testing"],
}


def categorize_item(item: ContentItem) -> List[str]:
    """
    Gibt eine Liste von Topics zurück, zu denen dieser Artikel passt.
    Basis: sehr simple Keyword-Suche in Titel + Body.
    """
    text = ((item.title or "") + " " + (item.body_md or "")).lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            topics.append(topic)
    return topics


def fetch_published_items(limit: int = 200) -> List[ContentItem]:
    with get_session() as session:
        q = (
            select(ContentItem)
            .where(ContentItem.status == "published")
            .order_by(ContentItem.created_at.desc())
            .limit(limit)
        )
        return session.exec(q).all()


def build_packs():
    print("[build_packs] Starting...")
    ensure_dir(STATIC_PACKS_DIR)
    ensure_dir(PRODUCTS_DIR)

    items = fetch_published_items()

    if not items:
        print("[build_packs] No published items found, nothing to do.")
        return

    # Bucket: topic -> list[ContentItem]
    buckets: Dict[str, List[ContentItem]] = {}

    for item in items:
        topics = categorize_item(item)
        if not topics:
            continue
        for topic in topics:
            buckets.setdefault(topic, []).append(item)

    if not buckets:
        print("[build_packs] No items matched any topic keywords.")
        return

    generated_packs = 0

    for topic, topic_items in buckets.items():
        if len(topic_items) < MIN_ITEMS_PER_PACK:
            print(
                f"[build_packs] Topic '{topic}' has only {len(topic_items)} items "
                f"(min {MIN_ITEMS_PER_PACK}), skipping."
            )
            continue

        # Für jetzt: ein Pack pro Topic
        topic_slug = slugify(topic)
        pack_slug = f"{topic_slug}-pack-1"
        pack_title = {
            "python-data": "Python Data Engineering Pack #1",
            "fastapi-backend": "FastAPI Backend Pack #1",
            "ai-rag": "AI & RAG Troubleshooting Pack #1",
            "devops-docker": "DevOps & Docker Pack #1",
            "testing": "Testing & Pytest Pack #1",
        }.get(topic, f"{topic.title()} Pack #1")

        description = (
            f"A curated bundle of {len(topic_items)} SilentGPT micro-tutorials "
            f"on {topic.replace('-', ' ')}."
        )

        # JSON-Datei für Programmatische Nutzung
        json_path = os.path.join(STATIC_PACKS_DIR, f"{pack_slug}.json")

        pack_items = []
        for item in topic_items:
            created = item.created_at or datetime.utcnow()
            slug = slugify(item.title or f"post-{item.id}")
            pack_items.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "slug": slug,
                    "created_at": created.isoformat(),
                    "url": f"/blog/{slug}/",
                }
            )

        import json

        pack_data = {
            "pack_slug": pack_slug,
            "topic": topic,
            "title": pack_title,
            "description": description,
            "generated_at": datetime.utcnow().isoformat(),
            "items": pack_items,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(pack_data, f, ensure_ascii=False, indent=2)

        print(f"[build_packs] Wrote JSON pack: {json_path}")

        # Markdown-Product-Page für Hugo unter /products
        md_path = os.path.join(PRODUCTS_DIR, f"{pack_slug}.md")
        safe_title = pack_title.replace('"', '\\"')
        safe_desc = description.replace('"', '\\"')

        front_matter_lines = [
            "+++",
            f'title = "{safe_title}"',
            f'slug = "{pack_slug}"',
            f'date = "{datetime.utcnow().isoformat()}"',
            f'description = "{safe_desc}"',
            f'pack_slug = "{pack_slug}"',
            "+++",
            "",
        ]

        body_lines = [
            f"# {pack_title}",
            "",
            description,
            "",
            "## Included articles",
            "",
        ]

        for item in topic_items:
            slug = slugify(item.title or f"post-{item.id}")
            url = f"/blog/{slug}/"
            body_lines.append(f"- [{item.title}]({url})")

        body = "\n".join(body_lines) + "\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(front_matter_lines))
            f.write(body)

        print(f"[build_packs] Wrote product page: {md_path}")
        generated_packs += 1

    print(f"[build_packs] Done. Generated {generated_packs} packs.")


if __name__ == "__main__":
    build_packs()
