#!/usr/bin/env python3
"""
Automated pack builder for SilentGPT Dev Engine.

- Liest veröffentlichte ContentItems aus der DB
- Mapped sie per Keywords auf Topics (aus pack_templates.yaml)
- Generiert pro Template:
    - JSON-Pack: site/static/packs/<pack_slug>.json
    - Produktseite: site/content/products/<pack_slug>.md
- Commitet & pusht Änderungen (nur Packs + Products) auf main.

Dieses Skript läuft bei dir auf Render als eigener Job (build_packs)
und kann auch lokal ausgeführt werden, wenn DATABASE_URL gesetzt ist.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any
import subprocess
import json
import re
import unicodedata

import yaml  # benötigt PyYAML

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session
from app.models.content import ContentItem
from app.db import init_db

MANUAL_PACK_SLUGS = {
    "fastapi-backend-pack-1",
}

# Wohin geschrieben wird
STATIC_PACKS_DIR = os.path.join(ROOT_DIR, "site", "static", "packs")
PRODUCTS_DIR = os.path.join(ROOT_DIR, "site", "content", "products")

# Fallback-Mindestanzahl Artikel pro Pack (falls Template nichts angibt)
DEFAULT_MIN_ITEMS_PER_PACK = 5

# Single Source of Truth für den Preis (in Cent)
# Kann z.B. auf Render als PACK_PRICE_EUR_CENTS=899 gesetzt werden
PACK_PRICE_EUR_CENTS = int(os.getenv("PACK_PRICE_EUR_CENTS", "899"))

# Pfad zur Template-Datei
PACK_TEMPLATES_PATH = os.path.join(ROOT_DIR, "automations", "pack_templates.yaml")

init_db()


def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def slugify(text: str) -> str:
    # 1. Normalize (entfernt z. B. Akzente, „ü“ → „u“)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # 2. Lowercase
    text = text.lower()

    # 3. Alles, was nicht a-z, 0-9 oder '-' ist, durch '-' ersetzen
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # 4. Mehrere '-' zu einem '-' zusammenfassen
    text = re.sub(r"-+", "-", text)

    # 5. Leading/trailing '-' entfernen
    text = text.strip("-")

    return text


def html_escape(text: str) -> str:
    """
    Sehr einfacher HTML-Escape für Inline-Links.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_pack_templates() -> List[Dict[str, Any]]:
    """
    Lädt die Pack-Blueprints aus pack_templates.yaml.
    """
    if not os.path.isfile(PACK_TEMPLATES_PATH):
        raise FileNotFoundError(
            f"Pack template file not found: {PACK_TEMPLATES_PATH}"
        )

    with open(PACK_TEMPLATES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    if not isinstance(data, list):
        raise ValueError("pack_templates.yaml must contain a top-level list")

    return data


def build_topic_keywords(templates: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Baut ein Topic->Keywords-Mapping aus den Templates.
    """
    mapping: Dict[str, List[str]] = {}
    for tpl in templates:
        topic = tpl.get("topic")
        if not topic:
            continue
        kws = tpl.get("keywords") or []
        mapping[topic] = [kw.lower() for kw in kws]
    return mapping


def categorize_item(
    item: ContentItem, topic_keywords: Dict[str, List[str]]
) -> List[str]:
    """
    Gibt eine Liste von Topics zurück, zu denen dieser Artikel passt.
    Basis: sehr simple Keyword-Suche in Titel + Body, gem. Templates.
    """
    text = ((item.title or "") + " " + (item.body_md or "")).lower()
    topics: List[str] = []
    for topic, keywords in topic_keywords.items():
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


def run_git_commands(commit_message: str = "auto: update packs"):
    """
    Commit & Push NUR der Änderungen unter site/static/packs und site/content/products.
    """

    repo_root = ROOT_DIR
    os.chdir(repo_root)
    print(f"[build_packs] Changed working directory to {repo_root}")

    # Auf main arbeiten
    subprocess.run(["git", "checkout", "-B", "main"], check=True)

    author_name = os.getenv("GIT_AUTHOR_NAME", "SilentGPT Bot")
    author_email = os.getenv(
        "GIT_AUTHOR_EMAIL",
        "243322325+jonahbruckner@users.noreply.github.com",
    )

    print(f"[build_packs] Configuring git user: {author_name} <{author_email}>")
    subprocess.run(["git", "config", "user.name", author_name], check=True)
    subprocess.run(["git", "config", "user.email", author_email], check=True)

    # Nur Packs/Products adden
    print("[build_packs] Adding packs/products to git...")
    subprocess.run(
        ["git", "add", "site/static/packs", "site/content/products"],
        check=True,
    )

    # Gibt es überhaupt Änderungen?
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        print("[build_packs] No changes to commit, skipping push.")
        return

    print(f"[build_packs] Committing with message: {commit_message!r}")
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    remote_url = os.getenv("GIT_REMOTE_URL")
    if not remote_url:
        print("[build_packs] GIT_REMOTE_URL not set – skipping push.")
        return

    print("[build_packs] Setting git remote 'origin' (URL from GIT_REMOTE_URL).")
    subprocess.run(
        ["git", "remote", "remove", "origin"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)

    print("[build_packs] Pushing to origin main...")
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("[build_packs] Git push completed.")


def build_packs():
    print("[build_packs] Starting...")

    templates = load_pack_templates()
    topic_keywords = build_topic_keywords(templates)

    ensure_dir(STATIC_PACKS_DIR)
    ensure_dir(PRODUCTS_DIR)

    items = fetch_published_items()

    if not items:
        print("[build_packs] No published items found, nothing to do.")
        return

    # Items nach Topics bucketen
    buckets: Dict[str, List[ContentItem]] = {}
    for item in items:
        topics = categorize_item(item, topic_keywords)
        if not topics:
            continue
        for topic in topics:
            buckets.setdefault(topic, []).append(item)

    if not buckets:
        print("[build_packs] No items matched any topic keywords from templates.")
        return

    generated_packs = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for tpl in templates:
        topic = tpl.get("topic")
        pack_slug = tpl.get("pack_slug")

    # ⛔ Skip manual packs
    if pack_slug in MANUAL_PACK_SLUGS:
        print(f"[build_packs] Skipping manual pack: {pack_slug}")
        continue

        if not topic or not pack_slug:
            print(f"[build_packs] Template missing topic/pack_slug, skipping: {tpl}")
            continue

        topic_items = buckets.get(topic, [])
        if not topic_items:
            print(f"[build_packs] No items for topic '{topic}', skipping.")
            continue

        min_items = int(tpl.get("min_items") or DEFAULT_MIN_ITEMS_PER_PACK)
        max_items = tpl.get("max_items")
        if max_items is not None:
            max_items = int(max_items)

        if len(topic_items) < min_items:
            print(
                f"[build_packs] Topic '{topic}' has only {len(topic_items)} items "
                f"(min {min_items}), skipping."
            )
            continue

        if max_items is not None and len(topic_items) > max_items:
            topic_items = topic_items[:max_items]

        pack_title = tpl.get("title") or f"{topic.title()} Pack #1"
        short_desc = tpl.get(
            "short_description",
            f"A curated bundle of {len(topic_items)} SilentGPT micro-tutorials on {topic.replace('-', ' ')}.",
        )
        long_desc = tpl.get("long_description", short_desc)
        hero_body = tpl.get("hero_body")

        # Preis-Label zentral aus PACK_PRICE_EUR_CENTS ableiten
        cents = PACK_PRICE_EUR_CENTS
        euro = cents / 100
        price_label = f"{euro:.2f} €".replace(".", ",")

        # JSON-Pack
        json_path = os.path.join(STATIC_PACKS_DIR, f"{pack_slug}.json")

        pack_items = []
        for item in topic_items:
            title = (item.title or "").strip()
            if not title:
                print(f"[build_packs] Skipping item {item.id} in JSON pack (empty title)")
                continue

            created = item.created_at or datetime.now(timezone.utc)
            slug = slugify(title or f"post-{item.id}")
            if not slug:
                slug = f"post-{item.id}"
            pack_items.append(
                {
                    "id": item.id,
                    "title": title,
                    "slug": slug,
                    "created_at": created.isoformat(),
                    "url": f"/blog/{slug}/",
                }
            )

        pack_data = {
            "pack_slug": pack_slug,
            "topic": topic,
            "title": pack_title,
            "description": short_desc,
            "long_description": long_desc,
            "price_label": price_label,
            "generated_at": now_iso,
            "items": pack_items,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(pack_data, f, ensure_ascii=False, indent=2)

        print(f"[build_packs] Wrote JSON pack: {json_path}")

        # Product-Page (Markdown)
        md_path = os.path.join(PRODUCTS_DIR, f"{pack_slug}.md")
        safe_title = pack_title.replace('"', '\\"')
        safe_desc = short_desc.replace('"', '\\"')
        safe_hero = hero_body.replace('"', '\\"') if hero_body else ""

        front_matter_lines = [
            "+++",
            f'title = "{safe_title}"',
            f'slug = "{pack_slug}"',
            f'date = "{now_iso}"',
            f'description = "{safe_desc}"',
            f'pack_slug = "{pack_slug}"',
            f'topic = "{topic}"',
            f'price_label = "{price_label}"',
        ]

        if hero_body:
            front_matter_lines.append(f'hero_body = "{safe_hero}"')

        front_matter_lines.append('type = "products"')
        front_matter_lines.append("+++")
        front_matter_lines.append("")

        body_lines = [
            f"# {pack_title}",
            "",
            long_desc,
            "",
            "## Included articles",
            "",
        ]

        for item in topic_items:
            title = (item.title or "").strip()
            if not title:
                print(f"[build_packs] Skipping item {item.id} in MD list (empty title)")
                continue

            slug = slugify(title or f"post-{item.id}")
            if not slug:
                slug = f"post-{item.id}"
            url = f"/blog/{slug}/"
            safe_title_html = html_escape(title)
            body_lines.append(f'- <a href="{url}">{safe_title_html}</a>')

        body = "\n".join(body_lines) + "\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(front_matter_lines))
            f.write(body)

        print(f"[build_packs] Wrote product page: {md_path}")
        generated_packs += 1

    print(f"[build_packs] Done. Generated {generated_packs} packs.")

    if generated_packs > 0:
        try:
            run_git_commands()
        except Exception as e:
            print(f"[build_packs] Git push failed: {e}")


if __name__ == "__main__":
    build_packs()
