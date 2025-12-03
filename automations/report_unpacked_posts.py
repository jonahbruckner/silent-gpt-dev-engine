#!/usr/bin/env python
"""
Create a markdown report listing all blog posts that are not part of any pack.

Usage (from repo root):

    python automations/report_unpacked_posts.py
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "site"
BLOG_DIR = SITE_DIR / "content" / "blog"
PACKS_DIR = SITE_DIR / "static" / "packs"
ADMIN_DIR = SITE_DIR / "content" / "admin"
REPORT_PATH = ADMIN_DIR / "unpacked-posts.md"


def parse_toml_frontmatter(path: Path) -> dict:
    """
    Very small TOML/toml-ish frontmatter parser for files that look like:

    +++
    title = "..."
    date = "..."
    slug = "..."
    +++
    """
    text = path.read_text(encoding="utf-8")

    if not text.startswith("+++"):
        return {}

    end_idx = text.find("+++", 3)
    if end_idx == -1:
        return {}

    header = text[3:end_idx].strip()
    meta: dict[str, str] = {}

    for line in header.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        meta[key] = value

    return meta


def collect_blog_posts():
    posts = []
    if not BLOG_DIR.exists():
        return posts

    for md in sorted(BLOG_DIR.glob("*.md")):
        meta = parse_toml_frontmatter(md)
        if not meta:
            continue
        slug = meta.get("slug") or md.stem
        title = meta.get("title") or md.stem
        date = meta.get("date", "")

        posts.append(
            {
                "slug": slug,
                "title": title,
                "date": date,
                "path": md,
            }
        )
    return posts


def collect_packed_slugs():
    packed = set()

    if not PACKS_DIR.exists():
        return packed

    for jf in PACKS_DIR.glob("*.json"):
        data = json.loads(jf.read_text(encoding="utf-8"))
        items = data.get("items", [])
        for item in items:
            slug = item.get("slug")
            if slug:
                packed.add(slug)
    return packed


def write_report(unpacked_posts):
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)

    now_iso = datetime.now(timezone.utc).isoformat()

    frontmatter = [
        "+++",
        'title = "Unpacked Posts Overview"',
        'slug = "unpacked-posts"',
        f'date = "{now_iso}"',
        "+++",
        "",
    ]

    body = [
        "# Blogposts not in any pack",
        "",
        f"Total: **{len(unpacked_posts)}** posts",
        "",
    ]

    if not unpacked_posts:
        body.append("Great! All posts are assigned to at least one pack. 🎉")
    else:
        for post in unpacked_posts:
            slug = post["slug"]
            title = post["title"]
            date = post.get("date", "")
            url = f"/blog/{slug}/"

            body.append(f"- [{title}]({url})  ")
            if date:
                body.append(f"  - Date: `{date}`")
            else:
                body.append("  - Date: _unknown_")

    REPORT_PATH.write_text("\n".join(frontmatter + body) + "\n", encoding="utf-8")
    print(f"[report_unpacked_posts] wrote report to {REPORT_PATH.relative_to(ROOT_DIR)}")


def run():
    posts = collect_blog_posts()
    packed_slugs = collect_packed_slugs()

    unpacked = [p for p in posts if p["slug"] not in packed_slugs]

    print(
        f"[report_unpacked_posts] {len(posts)} total posts, "
        f"{len(unpacked)} not in any pack."
    )

    write_report(unpacked)


if __name__ == "__main__":
    run()
