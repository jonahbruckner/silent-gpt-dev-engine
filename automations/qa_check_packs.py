#!/usr/bin/env python3
"""
Pack QA für SilentGPT Dev Engine.

- Prüft alle JSON-Packs unter site/static/packs
- Validiert:
    - Items vorhanden?
    - Jeder Item-Slug hat einen Blogpost (.md)?
    - Download-ZIP existiert?
    - price_label konsistent zu PACK_PRICE_EUR_CENTS?
- Schreibt einen Admin-Report nach: site/content/admin/pack-qa-report.md
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
BLOG_DIR = SITE_DIR / "content" / "blog"
DOWNLOADS_DIR = SITE_DIR / "static" / "downloads"
ADMIN_CONTENT_DIR = SITE_DIR / "content" / "admin"
REPORT_PATH = ADMIN_CONTENT_DIR / "pack-qa-report.md"

PACK_PRICE_EUR_CENTS = int(os.getenv("PACK_PRICE_EUR_CENTS", "899"))


def parse_slug_from_frontmatter(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    if not lines or not lines[0].strip().startswith("+++"):
        return None
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("+++"):
            break
        if line.startswith("slug"):
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


def expected_price_label() -> str:
    euro = PACK_PRICE_EUR_CENTS / 100
    return f"{euro:.2f} €".replace(".", ",")


def run():
    if not PACKS_DIR.is_dir():
        print(f"[qa_check_packs] Packs dir not found: {PACKS_DIR}")
        return
    if not BLOG_DIR.is_dir():
        print(f"[qa_check_packs] Blog dir not found: {BLOG_DIR}")
        return

    ADMIN_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    slug_index = build_slug_index()
    if not slug_index:
        print("[qa_check_packs] No blog posts with slugs found.")
        return

    exp_price_label = expected_price_label()

    packs = sorted(PACKS_DIR.glob("*.json"))
    if not packs:
        print(f"[qa_check_packs] No pack JSONs in {PACKS_DIR}")
        return

    lines: List[str] = []
    lines.append("+++")
    lines.append('title = "Pack QA Report"')
    lines.append(f'date = "{datetime.now(timezone.utc).isoformat()}"')
    lines.append('slug = "pack-qa-report"')
    lines.append('type = "admin"')
    lines.append("+++")
    lines.append("")
    lines.append("# Pack QA Report")
    lines.append("")
    lines.append(
        f"Automatisch generierter QA-Report für {len(packs)} Packs "
        f"unter site/static/packs."
    )
    lines.append("")
    lines.append(f"*Erwartetes price_label gemäß PACK_PRICE_EUR_CENTS: `{exp_price_label}`*")
    lines.append("")

    for json_path in packs:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        pack_slug = data.get("pack_slug") or json_path.stem
        title = data.get("title", pack_slug)
        price_label = data.get("price_label", "")
        items = data.get("items") or []

        lines.append(f"## {title} (`{pack_slug}`)")
        lines.append("")
        issues: List[str] = []

        # Items vorhanden?
        if not items:
            issues.append("Pack enthält keine Items.")

        # price_label Konsistenz
        if price_label != exp_price_label:
            issues.append(
                f"price_label = `{price_label}` weicht von erwartetem Wert "
                f"`{exp_price_label}` ab (PACK_PRICE_EUR_CENTS={PACK_PRICE_EUR_CENTS})."
            )

        # ZIP vorhanden?
        zip_path = DOWNLOADS_DIR / f"{pack_slug}.zip"
        if not zip_path.is_file():
            issues.append(f"Download-ZIP nicht gefunden: {zip_path}")

        # Blog-Posts für Items
        missing_posts: List[str] = []
        for it in items:
            slug = (it.get("slug") or "").strip()
            if not slug:
                missing_posts.append("(leer)")
                continue
            if slug not in slug_index:
                missing_posts.append(slug)

        if missing_posts:
            issues.append(
                f"{len(missing_posts)} Item-Slugs haben keinen passenden Blogpost: "
                + ", ".join(missing_posts)
            )

        if issues:
            lines.append("**Issues:**")
            for issue in issues:
                lines.append(f"- {issue}")
        else:
            lines.append("**Issues:** Keine offensichtlichen Probleme gefunden.")
        lines.append("")
        lines.append("---")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[qa_check_packs] QA report written to {REPORT_PATH}")


if __name__ == "__main__":
    run()
