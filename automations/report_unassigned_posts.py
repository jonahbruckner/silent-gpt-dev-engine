#!/usr/bin/env python3
"""
Report blog posts that are not used in any pack JSON.

- Reads pack json: site/static/packs/*.json
- Reads blogs:      site/content/blog/*.md
- Writes admin md:  site/content/admin/unassigned-posts.md

Also prints a warning for posts that probably have a duplicate H1 heading
(Title in front matter + same '# Title' as first content line).
"""

from pathlib import Path
import json
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
BLOG_DIR = SITE_DIR / "content" / "blog"
ADMIN_DIR = SITE_DIR / "content" / "admin"


def parse_front_matter(text: str):
    if not text.startswith("+++\n"):
        return {}, text

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
        data[key.strip()] = value.strip().strip('"')
    return data, body.lstrip("\n")


def collect_assigned_slugs() -> set[str]:
    slugs: set[str] = set()
    if not PACKS_DIR.exists():
        return slugs

    for json_path in PACKS_DIR.glob("*.json"):
        with json_path.open(encoding="utf-8") as f:
            pack = json.load(f)
        for item in pack.get("items", []):
            url = item.get("url", "")
            # /blog/slug/  -> slug
            slug = url.strip("/").split("/")[-1]
            if slug:
                slugs.add(slug)
    return slugs


def collect_blog_posts():
    posts = []
    duplicate_h1 = []

    if not BLOG_DIR.exists():
        return posts, duplicate_h1

    for md_path in sorted(BLOG_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fm, body = parse_front_matter(text)
        slug = fm.get("slug") or md_path.stem
        title = fm.get("title", md_path.stem)

        # check duplicate H1
        first_content_line = ""
        for line in body.splitlines():
            if line.strip():
                first_content_line = line.strip()
                break

        if first_content_line.startswith("# "):
            heading = first_content_line[2:].strip()
            if heading.lower() == title.lower():
                duplicate_h1.append((slug, title))

        posts.append((slug, title, md_path))
    return posts, duplicate_h1


def write_admin_markdown(unassigned):
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ADMIN_DIR / "unassigned-posts.md"

    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    lines = [
        "+++",
        'title = "Unassigned blog posts"',
        'slug = "unassigned-posts"',
        f'date = "{now}"',
        'type = "admin"',
        "+++",
        "",
        "# Unassigned blog posts",
        "",
    ]

    if not unassigned:
        lines.append("All blog posts are currently assigned to packs. 🎉")
    else:
        lines.append(
            "The following blog posts are currently **not** part of any product pack:"
        )
        lines.append("")
        for slug, title in unassigned:
            lines.append(f"- [{title}](/blog/{slug}/)")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report_unassigned_posts] Wrote {out_path.relative_to(ROOT_DIR)}")


def run():
    assigned = collect_assigned_slugs()
    posts, duplicate_h1 = collect_blog_posts()

    unassigned = [(slug, title) for slug, title, _ in posts if slug not in assigned]

    write_admin_markdown(unassigned)

    if unassigned:
        print("\n[report_unassigned_posts] Unassigned posts:")
        for slug, title in unassigned:
            print(f"  - {slug}  :: {title}")
    else:
        print("\n[report_unassigned_posts] All posts assigned to packs. 🎉")

    if duplicate_h1:
        print("\n[report_unassigned_posts] Posts with probable duplicate H1:")
        print("  (Title in front matter + same '# Title' at top of body)")
        for slug, title in duplicate_h1:
            print(f"  - {slug}  :: {title}")
        print("  → Du kannst in diesen Dateien die erste '#'-Überschrift entfernen.")
    else:
        print("\n[report_unassigned_posts] No duplicate H1 headings detected.")


if __name__ == "__main__":
    run()
