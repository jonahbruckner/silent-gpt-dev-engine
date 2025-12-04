# automations/weekly_pack_builder.py
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# Hauptblog-Content-Verzeichnis (Hugo)
MAIN_SITE_CONTENT_DIR = Path(
    os.getenv("MAIN_SITE_CONTENT_DIR", "site/content/blog")
)

# Tag -> Pack-Kategorie
PACK_CATEGORY_MAP = {
    "python": "python-data",
    "pandas": "python-data",
    "dataframe": "python-data",

    "fastapi": "fastapi-backend",
    "api": "fastapi-backend",
    "backend": "fastapi-backend",

    "rag": "rag-ai",
    "retrieval": "rag-ai",
    "vector": "rag-ai",
    "embedding": "rag-ai",

    "devops": "cloud-devops",
    "docker": "cloud-devops",
    "kubernetes": "cloud-devops",
    "ci": "cloud-devops",

    "automation": "automation-tools",
    "airflow": "automation-tools",
    "prefect": "automation-tools",
    "orchestration": "automation-tools",
}


def parse_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Sehr einfacher YAML-Front-Matter Parser für unsere eigene Struktur.
    Erwartet:
    ---
    key: value
    tags:
      - fastapi
      - python
    ...
    ---
    <body>
    """
    lines = text.splitlines()
    if not lines or not lines[0].strip().startswith("---"):
        return {}, text

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip().startswith("---"))
    except StopIteration:
        return {}, text

    header_lines = lines[1:end]
    body = "\n".join(lines[end + 1 :])

    data: Dict[str, Any] = {}
    tags: List[str] = []
    in_tags = False

    for line in header_lines:
        if not line.strip():
            continue

        if line.strip().startswith("tags:"):
            in_tags = True
            continue

        if in_tags and line.startswith("  -"):
            tag = line.split("-", 1)[1].strip()
            tags.append(tag)
            continue

        # falls weitere Liste-Typen kommen würden: ignorieren
        if line.startswith("  -") and not in_tags:
            continue

        if ":" in line and not line.startswith("  "):
            in_tags = False
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            data[key] = val

    if tags:
        data["tags"] = tags

    return data, body


def categorize_post(tags: List[str]) -> List[str]:
    """
    Mappt Tags (lowercase) auf Pack-Kategorien.
    Ein Post kann in mehrere Kategorien fallen.
    """
    cats = set()
    for t in tags or []:
        key = str(t).lower()
        if key in PACK_CATEGORY_MAP:
            cats.add(PACK_CATEGORY_MAP[key])
    return sorted(cats)


def load_recent_posts(days: int = 7) -> List[Dict[str, Any]]:
    """
    Lädt Blogposts aus dem Hauptblog der letzten X Tage.
    """
    base = BASE_DIR / MAIN_SITE_CONTENT_DIR
    if not base.exists():
        logger.warning(f"[weekly_pack_builder] Content dir not found: {base}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    posts: List[Dict[str, Any]] = []

    for md in base.glob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"[weekly_pack_builder] Failed to read {md}: {e}")
            continue

        meta, body = parse_front_matter(text)
        date_str = meta.get("date")
        if not date_str:
            continue

        try:
            dt = datetime.fromisoformat(date_str)
        except Exception:
            logger.warning(f"[weekly_pack_builder] Invalid date in {md}: {date_str}")
            continue

        if dt < cutoff:
            continue

        tags = meta.get("tags", [])
        posts.append(
            {
                "path": md,
                "meta": meta,
                "body": body,
                "date": dt,
                "tags": tags,
            }
        )

    logger.info(f"[weekly_pack_builder] Loaded {len(posts)} posts from last {days} days.")
    return posts


def build_weekly_packs(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Baut Pack-Objekte aus einer Menge von Posts.
    """
    today = datetime.now(timezone.utc).date()
    year, week, _ = today.isocalendar()

    posts_by_cat: Dict[str, List[Dict[str, Any]]] = {}

    for p in posts:
        cats = categorize_post(p["tags"])
        if not cats:
            continue
        for cat in cats:
            posts_by_cat.setdefault(cat, []).append(p)

    TITLE_MAP = {
        "python-data": "Python Data Engineering Pack",
        "fastapi-backend": "FastAPI Backend Pack",
        "rag-ai": "RAG & AI Retrieval Pack",
        "cloud-devops": "Cloud & DevOps Pack",
        "automation-tools": "Automation Tools Pack",
    }

    PRICE_MAP = {
        "python-data": 29,
        "fastapi-backend": 29,
        "rag-ai": 39,
        "cloud-devops": 29,
        "automation-tools": 29,
    }

    packs: List[Dict[str, Any]] = []

    for cat, cat_posts in posts_by_cat.items():
        if not cat_posts:
            continue

        title_base = TITLE_MAP.get(cat, cat.title())
        title = f"{title_base} – Week {week}/{year}"
        slug = f"{cat}-pack-{year}-w{week:02d}"
        price = PRICE_MAP.get(cat, 29)

        articles = []
        # Neueste zuerst
        for p in sorted(cat_posts, key=lambda x: x["date"], reverse=True):
            meta = p["meta"]
            fname = p["path"].name
            # Dateiname: YYYY-MM-DD-<slug>.md
            parts = fname.split("-", 3)
            if len(parts) >= 4:
                file_slug = parts[3].rsplit(".", 1)[0]
            else:
                file_slug = fname.rsplit(".", 1)[0]

            articles.append(
                {
                    "original_id": meta.get("original_id"),
                    "slug": file_slug,
                    "title": meta.get("title"),
                    "date": meta.get("date"),
                    "tags": meta.get("tags", []),
                }
            )

        pack = {
            "slug": slug,
            "category": cat,
            "title": title,
            "short_title": title_base,
            "price_eur": price,
            "week": week,
            "year": year,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "articles": articles,
        }
        packs.append(pack)

    logger.info(f"[weekly_pack_builder] Built {len(packs)} packs.")
    return packs


def save_weekly_packs(packs: List[Dict[str, Any]]):
    today = datetime.now(timezone.utc).date().isoformat()
    out_dir = BASE_DIR / "data" / "packs" / "weekly"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.json"

    payload = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "packs": packs,
    }

    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[weekly_pack_builder] Saved weekly packs -> {out_path}")


def main():
    posts = load_recent_posts(days=int(os.getenv("WEEKLY_PACK_DAYS", "7")))
    if not posts:
        logger.warning("[weekly_pack_builder] No posts found in recent window. Exiting.")
        return

    packs = build_weekly_packs(posts)
    if not packs:
        logger.warning("[weekly_pack_builder] No packs built. Exiting.")
        return

    save_weekly_packs(packs)


if __name__ == "__main__":
    main()
