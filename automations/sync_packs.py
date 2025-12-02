import yaml
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data" / "packs.yaml"
CONTENT_DIR = ROOT / "site" / "content" / "products"
STATIC_PACKS_DIR = ROOT / "site" / "static" / "packs"

BASE_URL = "https://steady-lollipop-79396b.netlify.app"

def main():
    packs = yaml.safe_load(DATA.read_text(encoding="utf-8"))

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_PACKS_DIR.mkdir(parents=True, exist_ok=True)

    for pack in packs:
        slug = pack["slug"]
        # 1) Product-Markdown erzeugen
        md_path = CONTENT_DIR / f"{slug}.md"
        md_path.write_text(render_product_md(pack), encoding="utf-8")

        # 2) JSON für Backend erzeugen (z.B. für Download-Links, Meta etc.)
        json_path = STATIC_PACKS_DIR / f"{slug}.json"
        json_path.write_text(render_pack_json(pack), encoding="utf-8")

def render_product_md(pack):
    fm = [
        "+++",
        f'title = "{pack["title"]}"',
        f'slug = "{pack["slug"]}"',
        'date = "2025-12-02T12:00:23.001376+00:00"',  # oder dynamisch
        f'description = "{pack["short_description"]}"',
        f'pack_slug = "{pack["slug"]}"',
        f'price_label = "{pack.get("price_label", "8,99 €")}"',
        'type = "products"',
        "+++",
        "",
    ]
    body = []
    body.append(pack["long_description"])
    body.append("")
    body.append("## Included articles")
    body.append("")
    for article_slug in pack["article_slugs"]:
        url = f"/blog/{article_slug}/"
        body.append(f'- <a href="{url}">{article_slug}</a>')
    body.append("")
    return "\n".join(fm + body)

def render_pack_json(pack):
    return json.dumps(
        {
            "slug": pack["slug"],
            "title": pack["title"],
            "price_label": pack.get("price_label", "8,99 €"),
            "article_slugs": pack["article_slugs"],
        },
        indent=2,
        ensure_ascii=False,
    )

if __name__ == "__main__":
    main()
