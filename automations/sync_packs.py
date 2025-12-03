#!/usr/bin/env python
import json
from pathlib import Path
from datetime import datetime, timezone

# Pfade im Repo
ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
PRODUCTS_DIR = SITE_DIR / "content" / "products"

START_MARK = "<!-- AUTO-GENERATED-ARTICLES-START -->"
END_MARK = "<!-- AUTO-GENERATED-ARTICLES-END -->"


def render_articles(items):
    """Erzeuge den Included-Articles-Block mit Marker."""
    lines = []
    lines.append(START_MARK)
    lines.append("")
    lines.append("## Included articles")
    lines.append("")
    for item in items:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        if not title or not url:
            continue
        lines.append(f'- <a href="{url}">{title}</a>')
    lines.append("")
    lines.append(END_MARK)
    lines.append("")
    return "\n".join(lines)


def create_new_product_md(pack_json, md_path: Path):
    slug = pack_json["pack_slug"]
    title = pack_json.get("title", slug)
    description = pack_json.get("description", "")
    now_iso = datetime.now(timezone.utc).isoformat()

    articles_block = render_articles(pack_json.get("items", []))

    frontmatter = [
        "+++",
        f'title = "{title}"',
        f'slug = "{slug}"',
        f'date = "{now_iso}"',
        f'description = "{description}"',
        f'pack_slug = "{slug}"',
        'price_label = "8,99 €"',
        'type = "products"',
        "+++",
        "",
    ]

    body = [
        f"# {title}",
        "",
        description,
        "",
        articles_block,
    ]

    md_path.write_text("\n".join(frontmatter + body), encoding="utf-8")
    print(f"[sync_packs] created product file {md_path.relative_to(ROOT_DIR)}")


def update_existing_product_md(pack_json, md_path: Path):
    """Nur den Included-Articles-Block ersetzen/anhängen."""
    text = md_path.read_text(encoding="utf-8")
    items = pack_json.get("items", [])
    articles_block = render_articles(items)

    if START_MARK in text and END_MARK in text:
        # bestehenden Block ersetzen
        pre, rest = text.split(START_MARK, 1)
        _, post = rest.split(END_MARK, 1)
        new_text = pre + articles_block + post
    else:
        # Block ans Ende anhängen
        if not text.endswith("\n"):
            text += "\n"
        new_text = text + "\n" + articles_block

    md_path.write_text(new_text, encoding="utf-8")
    print(f"[sync_packs] updated articles for {md_path.relative_to(ROOT_DIR)}")


def run():
    if not PACKS_DIR.exists():
        print(f"[sync_packs] no packs dir {PACKS_DIR}")
        return

    for json_file in sorted(PACKS_DIR.glob("*.json")):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        slug = data.get("pack_slug")
        if not slug:
            print(f"[sync_packs] skip {json_file.name}: missing pack_slug")
            continue

        md_path = PRODUCTS_DIR / f"{slug}.md"
        if md_path.exists():
            update_existing_product_md(data, md_path)
        else:
            create_new_product_md(data, md_path)


if __name__ == "__main__":
    run()
