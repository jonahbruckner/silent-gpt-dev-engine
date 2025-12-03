#!/usr/bin/env python
"""
Sync product pages with pack JSON files.

- Liest alle JSON-Dateien aus site/static/packs/*.json
- Aktualisiert die entsprechenden Markdown-Dateien in site/content/products/*.md:
    - setzt/aktualisiert die `description` im Frontmatter (kurzer Teaser)
    - überschreibt den Block ab der ersten "## Included articles" Überschrift
      mit einer automatisch generierten Liste der Artikel aus dem JSON

Voraussetzungen:
- Die JSON-Dateien enthalten mindestens:
    {
      "pack_slug": "ai-rag-pack-1",
      "description": "...",
      "items": [
        {"title": "...", "url": "/blog/..."}, ...
      ]
    }

Aufruf (vom Ordner `site/` aus):
    python ../automations/sync_packs.py
"""

import json
import os
from pathlib import Path


def find_repo_root() -> Path:
    """Bestimme Repo-Root relativ zu dieser Datei."""
    here = Path(__file__).resolve()
    # /.../automations/sync_packs.py -> Repo-Root = parent
    return here.parent.parent


ROOT_DIR = find_repo_root()
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
PRODUCTS_DIR = SITE_DIR / "content" / "products"


def load_pack_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def update_frontmatter_description(text: str, new_desc: str) -> str:
    """
    Ersetze oder füge `description = "..."` im TOML-Frontmatter ein.
    Frontmatter ist zwischen den ersten beiden '+++' Blöcken.
    """
    # Frontmatter-Grenzen finden
    first = text.find("+++")
    if first == -1:
        # Kein Frontmatter -> unverändert lassen
        return text

    second = text.find("+++", first + 3)
    if second == -1:
        return text

    header = text[first:second + 3]
    body = text[second + 3 :]

    # Header Zeilenweise bearbeiten
    lines = header.splitlines()
    desc_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("description"):
            desc_line_idx = i
            break

    desc_value = f'description = "{new_desc}"'

    if desc_line_idx is not None:
        lines[desc_line_idx] = desc_value
    else:
        # Vor der schließenden +++ einfügen (aber nach der ersten Zeile)
        # Header hat typischerweise:
        # +++
        # title = ...
        # ...
        # +++
        insert_at = max(1, len(lines) - 1)
        lines.insert(insert_at, desc_value)

    new_header = "\n".join(lines)
    return new_header + body


def generate_included_block(items: list[dict]) -> str:
    """
    Erzeuge den kompletten Block:

    ## Included articles

    - <a href="...">Title</a>
    ...
    """
    lines = []
    lines.append("## Included articles")
    lines.append("")
    for item in items:
        title = item.get("title", "Untitled")
        url = item.get("url") or item.get("slug") or "#"

        # Sicherstellen, dass URL mit / beginnt, falls nur slug übergeben wurde
        if not url.startswith("http") and not url.startswith("/"):
            url = f"/blog/{url}/"

        lines.append(f'- <a href="{url}">{title}</a>')

    lines.append("")  # trailing newline
    return "\n".join(lines)


def replace_included_section(body: str, new_block: str) -> str:
    """
    Ersetze ab der ersten Zeile '## Included articles' bis zum Ende
    durch `new_block`. So werden doppelte / alte Blöcke entfernt.
    """
    marker = "## Included articles"
    idx = body.find(marker)
    if idx == -1:
        # Marker fehlt -> Block einfach ans Ende dranhängen
        body = body.rstrip() + "\n\n" + new_block + "\n"
        return body

    # Alles vor dem Marker behalten
    prefix = body[:idx].rstrip()
    return prefix + "\n\n" + new_block + "\n"


def sync_pack(pack: dict) -> None:
    pack_slug = pack.get("pack_slug")
    if not pack_slug:
        print(f"[sync_packs] Skipping JSON without pack_slug: {pack}")
        return

    md_path = PRODUCTS_DIR / f"{pack_slug}.md"
    if not md_path.exists():
        print(f"[sync_packs] WARNING: product file not found for {pack_slug}: {md_path}")
        return

    print(f"[sync_packs] Updating product for pack: {pack_slug}")

    text = md_path.read_text(encoding="utf-8")

    # 1) description im Frontmatter aktualisieren (kurzer Teaser)
    if pack.get("description"):
        text = update_frontmatter_description(text, pack["description"])

    # 2) Included-Block aus Items generieren
    items = pack.get("items", [])
    included_block = generate_included_block(items)

    # Text in Frontmatter + Body splitten, damit wir nur den Body anfassen
    first = text.find("+++")
    second = text.find("+++", first + 3) if first != -1 else -1
    if first != -1 and second != -1:
        header = text[:second + 3]
        body = text[second + 3 :]
    else:
        header = ""
        body = text

    new_body = replace_included_section(body, included_block)

    new_text = header + new_body
    md_path.write_text(new_text, encoding="utf-8")


def run() -> None:
    if not PACKS_DIR.exists():
        print(f"[sync_packs] Packs dir not found: {PACKS_DIR}")
        return

    json_files = sorted(PACKS_DIR.glob("*.json"))
    if not json_files:
        print(f"[sync_packs] No JSON packs found in {PACKS_DIR}")
        return

    print(f"[sync_packs] Found {len(json_files)} pack JSON files.")
    for jf in json_files:
        try:
            pack = load_pack_json(jf)
            sync_pack(pack)
        except Exception as exc:
            print(f"[sync_packs] ERROR processing {jf.name}: {exc}")


if __name__ == "__main__":
    run()
