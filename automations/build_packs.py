import os
import sys
from datetime import datetime, timezone
from typing import Dict, List
import subprocess
import json
from pathlib import Path
import zipfile

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
STATIC_DOWNLOADS_DIR = os.path.join(ROOT_DIR, "site", "static", "downloads")  # NEU

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

def build_zip_packs():
    """
    Erzeugt für alle vorhandenen JSON-Packs ein ZIP in site/static/downloads.
    Struktur:
      downloads/<slug>.zip
        <slug>.json
        <slug>.md (falls vorhanden)
    """
    print("[build_packs] Building ZIP packs...")

    ensure_dir(STATIC_DOWNLOADS_DIR)

    if not os.path.isdir(STATIC_PACKS_DIR):
        print(f"[build_packs] PACKS_DIR {STATIC_PACKS_DIR} existiert nicht – breche ZIP-Build ab.")
        return

    json_files = [f for f in os.listdir(STATIC_PACKS_DIR) if f.endswith(".json")]
    if not json_files:
        print(f"[build_packs] Keine JSON-Packs in {STATIC_PACKS_DIR} gefunden – nichts zu tun.")
        return

    for filename in json_files:
        slug = filename[:-5]  # ".json" abschneiden
        json_path = os.path.join(STATIC_PACKS_DIR, filename)
        md_path = os.path.join(PRODUCTS_DIR, f"{slug}.md")
        zip_path = os.path.join(STATIC_DOWNLOADS_DIR, f"{slug}.zip")

        print(f"[build_packs] Erzeuge ZIP für Pack '{slug}' -> {zip_path}")

        try:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # JSON ins ZIP
                zf.write(json_path, arcname=f"{slug}.json")

                # Markdown-Produktseite ins ZIP (falls vorhanden)
                if os.path.isfile(md_path):
                    zf.write(md_path, arcname=f"{slug}.md")
                else:
                    print(f"[build_packs] Warnung: Kein Markdown für {slug} gefunden ({md_path})")

            size_kb = os.path.getsize(zip_path) / 1024
            print(f"[build_packs] ZIP erstellt: {zip_path} ({size_kb:.1f} KB)")

        except Exception as e:
            print(f"[build_packs] Fehler beim Erzeugen von {zip_path}: {e}")

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
    print("[build_packs] Adding packs/products/downloads to git...")
    subprocess.run(
        [
            "git",
            "add",
            "site/static/packs",
            "site/content/products",
            "site/static/downloads",
        ],
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
            "description": description,
            "generated_at": now_iso,
            "items": pack_items,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(pack_data, f, ensure_ascii=False, indent=2)

        print(f"[build_packs] Wrote JSON pack: {json_path}")

        # Product-Page (Markdown)
        md_path = os.path.join(PRODUCTS_DIR, f"{pack_slug}.md")
        safe_title = pack_title.replace('"', '\\"')
        safe_desc = description.replace('"', '\\"')

        front_matter_lines = [
            "+++",
            f'title = "{safe_title}"',
            f'slug = "{pack_slug}"',
            f'date = "{now_iso}"',
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
        # NEU: ZIPs bauen, bevor wir committen
        build_zip_packs()

        try:
            run_git_commands()
        except Exception as e:
            print(f"[build_packs] Git push failed: {e}")


if __name__ == "__main__":
    build_packs()
