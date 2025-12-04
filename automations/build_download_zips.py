#!/usr/bin/env python3
import json
from pathlib import Path
import zipfile
from typing import Dict, Optional, List
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
BLOG_DIR = SITE_DIR / "content" / "blog"
DOWNLOADS_DIR = SITE_DIR / "static" / "downloads"


def ensure_dir(path: Path):
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)


def parse_slug_from_frontmatter(path: Path) -> Optional[str]:
    """
    Versucht, einen slug aus der Frontmatter zu lesen.

    Unterstützt:
    - TOML-Style mit +++ ... slug = "..."
    - YAML-Style mit --- ... slug: "..."
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    if not lines:
        return None

    first = lines[0].strip()
    if first.startswith("+++"):
        # TOML-artige Frontmatter
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
    elif first.startswith("---"):
        # YAML-artige Frontmatter
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("---"):
                break
            if line.startswith("slug:"):
                # slug: something
                parts = line.split(":", 1)
                if len(parts) == 2:
                    value = parts[1].strip().strip('"').strip("'")
                    return value

    return None


def build_slug_index() -> Dict[str, Path]:
    """
    Index von slug -> Markdown-Pfad anhand der Frontmatter.
    Nutzt parse_slug_from_frontmatter.
    """
    mapping: Dict[str, Path] = {}
    for md in BLOG_DIR.glob("*.md"):
        slug = parse_slug_from_frontmatter(md)
        if slug:
            mapping[slug] = md
    return mapping


def extract_items_from_pack_json(data: dict) -> List[dict]:
    """
    Unterstützt beide Varianten:
    - alte Packs:      data["items"]    = [{ "slug": "..." }, ...]
    - neue Weekly:     data["articles"] = [{ "slug": "..." , "date": "...", ...}, ...]
    Gibt eine Liste von Dicts mit mindestens dem Key "slug" zurück.
    """
    items = data.get("items")
    if items:
        return items

    articles = data.get("articles")
    if articles:
        normalized = []
        for art in articles:
            slug = (art.get("slug") or "").strip()
            if not slug:
                continue
            entry = {"slug": slug}
            if "date" in art:
                entry["date"] = art["date"]
            normalized.append(entry)
        return normalized

    return []


def parse_date_prefix(iso_str: str) -> Optional[str]:
    """
    Nimmt einen ISO-String (z.B. 2025-12-04T10:17:45.367076+00:00)
    und gibt 'YYYY-MM-DD' zurück, oder None bei Fehler.
    """
    if not iso_str:
        return None
    try:
        cleaned = iso_str.replace("Z", "+00:00") if iso_str.endswith("Z") else iso_str
        dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def find_article_md_path(
    slug: str,
    item: dict,
    slug_index: Dict[str, Path],
) -> Optional[Path]:
    """
    Versucht in dieser Reihenfolge:
    1. slug_index[slug]  (Frontmatter-slug-Treffer)
    2. date + slug -> YYYY-MM-DD-slug.md
    3. Fallback: Suche nach '*-slug.md'
    """
    # 1) Direkt über slug-Index (klassische alte Packs)
    if slug in slug_index:
        return slug_index[slug]

    # 2) Date + slug -> Dateiname auf Basis 'YYYY-MM-DD-<slug>.md'
    date_iso = item.get("date")
    date_prefix = parse_date_prefix(date_iso)
    if date_prefix:
        candidate = BLOG_DIR / f"{date_prefix}-{slug}.md"
        if candidate.exists():
            return candidate

    # 3) Fallback: irgendeine Datei, die auf '-slug.md' endet
    matches = sorted(BLOG_DIR.glob(f"*-{slug}.md"))
    if matches:
        return matches[0]

    return None


def build_zip_for_pack(json_path: Path, slug_index: Dict[str, Path]):
    data = json.loads(json_path.read_text(encoding="utf-8"))

    pack_slug = data.get("pack_slug") or data.get("slug") or json_path.stem
    items = extract_items_from_pack_json(data)

    if not items:
        print(f"[build_download_zips] Pack {pack_slug} has no items/articles, skipping.")
        return

    ensure_dir(DOWNLOADS_DIR)
    zip_path = DOWNLOADS_DIR / f"{pack_slug}.zip"

    title = data.get("title", pack_slug)

    readme = (
        f"SilentGPT Dev Engine – {title}\n"
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

            md_path = find_article_md_path(slug, item, slug_index)
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
        print("[build_download_zips] No blog posts with slugs found (frontmatter).")
        # Ist ok – wir haben noch Fallback über Date+Slug

    for json_path in sorted(PACKS_DIR.glob("*.json")):
        build_zip_for_pack(json_path, slug_index)


if __name__ == "__main__":
    run()
