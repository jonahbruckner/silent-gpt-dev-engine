import datetime as dt
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "site" / "content" / "blog"
PACKS_FILE = ROOT / "site" / "data" / "packs.yaml"


def list_all_post_slugs():
    slugs = []

    for path in BLOG_DIR.rglob("*.md"):
        # Beispiele:
        # site/content/blog/foo-bar.md      → slug: foo-bar
        # site/content/blog/foo-bar/index.md → slug: foo-bar
        rel = path.relative_to(BLOG_DIR)
        if rel.name == "index.md":
            slug = rel.parent.as_posix()
        else:
            slug = rel.stem
        slugs.append(slug)

    return sorted(set(slugs))


def load_packs():
    if not PACKS_FILE.exists():
        return []

    with open(PACKS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def slugs_used_in_packs(packs):
    used = set()
    for p in packs:
        for s in p.get("article_slugs", []):
            used.add(s)
    return used


def generate_report():
    all_posts = list_all_post_slugs()
    packs = load_packs()
    used = slugs_used_in_packs(packs)

    unused = [s for s in all_posts if s not in used]

    lines = []
    today = dt.date.today().isoformat()

    lines.append(f"# Weekly Pack Report – {today}")
    lines.append("")
    lines.append("## Blogposts not in any pack yet")
    lines.append("")

    if not unused:
        lines.append("_Great! All posts are assigned to packs._")
    else:
        for slug in unused:
            url = f"/blog/{slug}/"
            lines.append(f"- [{slug}]({url})")

    # Optional: Übersicht, welche Packs wie viele Artikel haben
    lines.append("")
    lines.append("## Pack coverage overview")
    lines.append("")
    for p in packs:
        count = len(p.get("article_slugs", []))
        lines.append(f"- **{p['title']}** (`{p['slug']}`): {count} articles")

    return "\n".join(lines)


def run():
    report = generate_report()
    print(report)

    # Optional: automatisch ins Repo schreiben
    out_dir = ROOT / "site" / "content" / "admin"
    out_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    out_file = out_dir / f"weekly-pack-report-{today}.md"
    out_file.write_text(report, encoding="utf-8")

    print(f"\n[report_unpacked_posts] Report written to {out_file}")


if __name__ == "__main__":
    run()
