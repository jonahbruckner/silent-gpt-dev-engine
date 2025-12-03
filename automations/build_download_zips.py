#!/usr/bin/env python3
import os
import json
from pathlib import Path
import zipfile
from typing import Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
BLOG_DIR = SITE_DIR / "content" / "blog"
DOWNLOADS_DIR = SITE_DIR / "static" / "downloads"


def ensure_dir(path: Path):
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)


def parse_slug_from_frontmatter(path: Path) -> Optional[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    if not lines or not lines[0].strip().startswith("+++"):
        return None

    for line in lines[1:]:
        line = line.strip()
        if line.startswith("+++"):
            break
        if line.startswith("slug"):
            # slug = "something"
            parts = line.split("=", 1)
            if len(parts) == 2:
                value = parts[1].strip().strip('"')
                return value
    return None


def build_slug_index() -> Dict[str, Path]:
    mapping: Dict[str, Path] = {}
    for md in BLOG_DIR.glob("*.md"):
        slug = parse_slug_from_frontmatter(md)
        if slug:
            mapping[slug] = md
    return mapping


def build_zip_for_pack(json_path: Path, slug_index: Dict[str, Path]):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    pack_slug = data.get("pack_slug") or json_path.stem
    items = data.get("items") or []
    if not items:
        print(f"[build_download_zips] Pack {pack_slug} has no items, skipping.")
        return

    ensure_dir(DOWNLOADS_DIR)
    zip_path = DOWNLOADS_DIR / f"{pack_slug}.zip"

    readme = (
        f"SilentGPT Dev Engine – {data.get('title', pack_slug)}\n"
        "\n"
        "Dieses ZIP enthält alle Artikel dieses Packs als Markdown-Dateien\n"
        "sowie die JSON-Definition des Packs.\n"
        "\n"
        "Du kannst die Dateien z.B. in deinem eigenen Wissens- oder Doku-System\n"
        "weiterverwenden.\n"
    )

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # README
        zf.writestr("README.txt", readme)

        # Pack-JSON
        zf.write(json_path, arcname=f"{pack_slug}.json")

        # Articles
        for item in items:
            slug = (item.get("slug") or "").strip()
            if not slug:
                continue
            md_path = slug_index.get(slug)
            if not md_path:
                print(
                    f"[build_download_zips] Warning: No blog post found for slug '{slug}' "
                    f"(pack {pack_slug})."
                )
                continue
            zf.write(md_path, arcname=f"articles/{md_path.name}")

    print(f"[build_download_zips] Wrote {zip_path}")


def run():
    if not PACKS_DIR.is_dir():
        print(f"[build_download_zips] Packs dir not found: {PACKS_DIR}")
        return
    if not BLOG_DIR.is_dir():
        print(f"[build_download_zips] Blog dir not found: {BLOG_DIR}")
        return

    slug_index = build_slug_index()
    if not slug_index:
        print("[build_download_zips] No blog posts with slugs found.")
        return

    for json_path in sorted(PACKS_DIR.glob("*.json")):
        build_zip_for_pack(json_path, slug_index)


if __name__ == "__main__":
    run()
