#!/usr/bin/env python3
"""
Automated pack builder for SilentGPT Dev Engine.

- Liest veröffentlichte ContentItems aus der DB
- Gruppiert sie nach groben Themen (Topic-Keywords)
- Schreibt:
    - JSON-Packs nach: site/static/packs/<pack_slug>.json
    - Produktseiten nach: site/content/products/<pack_slug>.md
- Commited & pusht Änderungen (nur Packs + Products) auf main

Dieses Skript läuft bei dir auf Render als eigener Job (build_packs)
und kann auch lokal ausgeführt werden, wenn DATABASE_URL gesetzt ist.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, List
import subprocess
import json
from pathlib import Path

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
        .replace(",", "")
        .replace("’", "")
        .replace("“", "")
        .replace("”", "")
    )


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


# Sehr einfache Keyword-Heuristik für Themen
TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "python-data": ["python", "pandas", "numpy", "dataframe"],
    "fastapi-backend": ["fastapi", "api", "backend"],
    "ai-rag": ["rag", "langchain", "vector", "embedding", "llm"],
    "devops-docker": ["docker", "kubernetes", "container", "deploy"],
    "testing": ["pytest", "unit test", "testing"],
}

# Pack-Metadaten pro Topic:
# - pack_title: H1 Titel & JSON title
# - short_description: wird in Frontmatter als description verwendet (1 Satz)
# - long_description: steht im Body unter der H1 (3+ Sätze, Marketing)
# - price_label: wird im Frontmatter genutzt und im Layout angezeigt
PACK_META: Dict[str, Dict[str, str]] = {
    "ai-rag": {
        "pack_title": "AI & RAG Troubleshooting Pack #1",
        "short_description": (
            "A curated bundle of SilentGPT micro-tutorials for debugging and improving "
            "your retrieval-augmented generation systems."
        ),
        "long_description": (
            "This pack gives you a focused collection of real-world RAG issues and their fixes. "
            "Du lernst, wie du Embeddings, Vektorsuche, Kontextfenster und Prompting aufeinander "
            "abstimmst, um stabile Antworten zu bekommen – statt zufälliger Halluzinationen. "
            "Ideal, wenn du an produktionsnahen RAG-Pipelines arbeitest und weniger Zeit mit "
            "Trial-and-Error verschwenden willst."
        ),
        "price_label": "8,99 €",
    },
    "fastapi-backend": {
        "pack_title": "FastAPI Backend Pack #1",
        "short_description": (
            "Patterns and recipes for shipping production-ready FastAPI services faster."
        ),
        "long_description": (
            "Dieses Pack bündelt Best Practices für FastAPI-Backends, von Routing und Settings "
            "über Background-Jobs bis hin zur Integration mit Datenbanken und externen Services. "
            "Du bekommst konkrete Snippets und Lösungswege, die in echten Projekten funktionieren, "
            "statt generischer Hello-World-Beispiele. Perfekt, wenn du dein nächstes Backend "
            "stabil und wartbar aufsetzen willst."
        ),
        "price_label": "8,99 €",
    },
    "python-data": {
        "pack_title": "Python Data Engineering Pack #1",
        "short_description": (
            "SilentGPT micro-tutorials for cleaning, transforming and automating data workflows in Python."
        ),
        "long_description": (
            "Dieses Pack fokussiert sich auf typische Data-Engineering-Alltagsaufgaben mit Python: "
            "Daten einlesen, bereinigen, transformieren, validieren und automatisiert weiterverarbeiten. "
            "Die Beispiele sind praxisnah gehalten und orientieren sich an wiederkehrenden Problemen, "
            "die in BI-, Analytics- und Engineering-Teams ständig auftauchen. Ideal, wenn du deine "
            "Daten-Pipelines robuster und automatisierter machen willst."
        ),
        "price_label": "8,99 €",
    },
    "devops-docker": {
        "pack_title": "DevOps & Docker Pack #1",
        "short_description": (
            "A compact set of Docker and deployment patterns for modern backend services."
        ),
        "long_description": (
            "Hier findest du kompakte How-tos rund um Containerisierung, lokale Entwicklungsumgebungen "
            "und einfache Deployment-Setups. Der Fokus liegt darauf, Services reproduzierbar zu machen, "
            "statt sie jedes Mal manuell zu konfigurieren. Ideal für Entwickler:innen, die ihre Projekte "
            "ohne großen Overhead bereitstellen möchten."
        ),
        "price_label": "8,99 €",
    },
    "testing": {
        "pack_title": "Testing & Pytest Pack #1",
        "short_description": (
            "Practical testing patterns with pytest to make your Python code more reliable."
        ),
        "long_description": (
            "Dieses Pack vermittelt dir praxiserprobte Patterns für Tests mit pytest: von einfachen "
            "Unit-Tests über Fixtures bis hin zu strukturierten Test-Suiten für größere Projekte. "
            "Du lernst, wie du Tests so schreibst, dass sie dir wirklich helfen, statt nur Pflichtprogramm "
            "für das CI zu sein."
        ),
        "price_label": "8,99 €",
    },
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
    ensure_dir(STATIC_PACKS_DIR)
    ensure_dir(PRODUCTS_DIR)

    items = fetch_published_items()

    if not items:
        print("[build_packs] No published items found, nothing to do.")
        return

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
    now_iso = datetime.now(timezone.utc).isoformat()

    for topic, topic_items in buckets.items():
        if len(topic_items) < MIN_ITEMS_PER_PACK:
            print(
                f"[build_packs] Topic '{topic}' has only {len(topic_items)} items "
                f"(min {MIN_ITEMS_PER_PACK}), skipping."
            )
            continue

        topic_slug = slugify(topic)
        pack_slug = f"{topic_slug}-pack-1"

        meta = PACK_META.get(topic, {})
        pack_title = meta.get("pack_title") or f"{topic.title()} Pack #1"
        short_desc = meta.get(
            "short_description",
            f"A curated bundle of {len(topic_items)} SilentGPT micro-tutorials on {topic.replace('-', ' ')}.",
        )
        long_desc = meta.get(
            "long_description",
            short_desc,
        )
        price_label = meta.get("price_label", "8,99 €")

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

        front_matter_lines = [
            "+++",
            f'title = "{safe_title}"',
            f'slug = "{pack_slug}"',
            f'date = "{now_iso}"',
            f'description = "{safe_desc}"',
            f'pack_slug = "{pack_slug}"',
            f'topic = "{topic}"',
            f'price_label = "{price_label}"',
            'type = "products"',
            "+++",
            "",
        ]

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
