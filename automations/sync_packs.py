#!/usr/bin/env python3
"""
Sync pack JSON files into Hugo product markdown files.

- Reads:  site/static/packs/*.json
- Writes: site/content/products/<pack_slug>.md

What it does:
- Ensures front matter keys: slug, pack_slug, title, description, topic, type
- Regenerates the '## Included articles' section from JSON items
- Leaves your long description / other sections untouched
"""

from pathlib import Path
import json
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent  # repo root
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
PRODUCTS_DIR = SITE_DIR / "content" / "products"


# ---------- Helpers for front matter ----------

def parse_front_matter(text: str):
    """Return (frontmatter_dict, body_text). Values stay as raw TOML strings."""
    if not text.startswith("+++\n"):
        return {}, text

    # cut first +++ line
    _, rest = text.split("+++\n", 1)
    fm_text, body = rest.split("+++\n", 1)

    data = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data, body.lstrip("\n")


def render_front_matter(data: dict) -> str:
    """Render dict back into +++ ... +++ front matter."""
    lines = ["+++"]
    for key, value in data.items():
        lines.append(f"{key} = {value}")
    lines.append("+++")
    return "\n".join(lines) + "\n\n"


def set_str(data: dict, key: str, value: str | None):
    """Set a string key in TOML front matter (with quotes)."""
    if value is None:
        return
    data[key] = f'"{value}"'


# ---------- Body helpers ----------

def build_included_section(items: list[dict]) -> str:
    """Return markdown '## Included articles' block from items."""
    lines = ["## Included articles", ""]
    for item in items:
        url = item["url"]
        title = item["title"]
        lines.append(f'- <a href="{url}">{title}</a>')
    lines.append("")  # trailing newline
    return "\n".join(lines)


def update_body_with_items(body: str, items: list[dict]) -> str:
    """Replace or append the Included articles section in the body."""
    marker = "## Included articles"
    section = build_included_section(items)

    if marker in body:
        head, _ = body.split(marker, 1)
        # head already contains everything up to the marker
        head = head.rstrip() + "\n\n"
        return head + section + "\n"
    else:
        body = body.rstrip() + "\n\n"
        return body + section + "\n"


# ---------- Main sync logic ----------

def sync_pack(json_path: Path):
    with json_path.open(encoding="utf-8") as f:
        pack = json.load(f)

    pack_slug = pack["pack_slug"]
    title = pack["title"]
    description = pack.get("description", "")
    topic = pack.get("topic", "")

    md_path = PRODUCTS_DIR / f"{pack_slug}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)

    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        fm, body = parse_front_matter(text)
    else:
        fm = {}
        body = ""

    # front matter defaults / overrides
    set_str(fm, "slug", pack_slug)
    set_str(fm, "pack_slug", pack_slug)
    set_str(fm, "title", title)
    set_str(fm, "description", description)
    set_str(fm, "topic", topic)
    set_str(fm, "type", "products")
    # price_label lässt du weiter manuell steuern → wird NICHT angefasst

    # Body: nur Included-Section anfassen
    body = update_body_with_items(body or "", pack["items"])

    new_text = render_front_matter(fm) + body
    md_path.write_text(new_text, encoding="utf-8")
    print(f"[sync_packs] Updated {md_path.relative_to(ROOT_DIR)}")


def run():
    if not PACKS_DIR.exists():
        print(f"[sync_packs] No packs dir at {PACKS_DIR}")
        return

    for json_path in sorted(PACKS_DIR.glob("*.json")):
        sync_pack(json_path)

    print("[sync_packs] Done.")


if __name__ == "__main__":
    run()
