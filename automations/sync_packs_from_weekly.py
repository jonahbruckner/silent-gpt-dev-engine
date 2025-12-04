# automations/sync_packs_from_weekly.py
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

WEEKLY_PACKS_DIR = BASE_DIR / "data" / "packs" / "weekly"

PACKS_CONTENT_DIR = Path(
    os.getenv("PACKS_CONTENT_DIR", BASE_DIR / "site" / "content" / "products")
)
PACKS_STATIC_DIR = Path(
    os.getenv("PACKS_STATIC_DIR", BASE_DIR / "site" / "static" / "packs")
)

STRIPE_CATEGORY_PRICE_FILE = BASE_DIR / "data" / "stripe" / "category_price_ids.json"


def find_latest_weekly_file() -> Optional[Path]:
    if not WEEKLY_PACKS_DIR.exists():
        logger.warning(f"[sync_packs_from_weekly] Weekly dir not found: {WEEKLY_PACKS_DIR}")
        return None

    candidates = sorted(WEEKLY_PACKS_DIR.glob("*.json"))
    if not candidates:
        logger.warning(f"[sync_packs_from_weekly] No weekly pack files in {WEEKLY_PACKS_DIR}")
        return None

    return candidates[-1]


def load_weekly_packs(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"[sync_packs_from_weekly] Failed to load {path}: {e}")
        raise

    packs = data.get("packs", [])
    if not isinstance(packs, list):
        raise ValueError(f"[sync_packs_from_weekly] Invalid packs structure in {path}")

    return data


def load_stripe_category_prices() -> Dict[str, str]:
    """
    Lädt Stripe-Price-IDs pro Kategorie aus:
    data/stripe/category_price_ids.json

    Struktur:
    {
      "fastapi-backend": "price_xxx",
      "python-data": "price_yyy",
      ...
    }
    """
    if not STRIPE_CATEGORY_PRICE_FILE.exists():
        logger.warning(
            f"[sync_packs_from_weekly] Stripe category price file not found: {STRIPE_CATEGORY_PRICE_FILE}"
        )
        return {}

    try:
        data = json.loads(STRIPE_CATEGORY_PRICE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Stripe category price file must contain a JSON object")
        return {str(k): str(v) for k, v in data.items()}
    except Exception as e:
        logger.error(f"[sync_packs_from_weekly] Failed to load Stripe category prices: {e}")
        return {}


def yaml_escape(s: str) -> str:
    if s is None:
        return ""
    s = str(s).replace('"', "'")
    return s


def build_product_front_matter(
    pack: Dict[str, Any],
    weekly_date: str,
    stripe_price_id: Optional[str],
) -> str:
    """
    Erzeugt Hugo-Front-Matter für ein Produkt-Paket.
    """
    title = yaml_escape(pack.get("title", pack.get("slug")))
    slug = yaml_escape(pack.get("slug"))
    short_title = yaml_escape(pack.get("short_title", title))
    category = yaml_escape(pack.get("category", "misc"))
    price_eur = pack.get("price_eur", 29)
    week = pack.get("week")
    year = pack.get("year")

    articles: List[Dict[str, Any]] = pack.get("articles", [])

    lines = [
        "---",
        f'title: "{title}"',
        f"slug: {slug}",
        f'short_title: "{short_title}"',
        f"price_eur: {price_eur}",
        f"category: {category}",
        "product_type: weekly_pack",
        f"weekly_date: {weekly_date}",
    ]

    if week is not None:
        lines.append(f"week: {week}")
    if year is not None:
        lines.append(f"year: {year}")

    if stripe_price_id:
        lines.append(f"stripe_price_id: {stripe_price_id}")

    lines.append("included_articles:")

    for art in articles:
        lines.append(f"  - original_id: {art.get('original_id')}")
        lines.append(f'    slug: "{yaml_escape(art.get("slug"))}"')
        lines.append(f'    title: "{yaml_escape(art.get("title"))}"')
        lines.append(f'    date: "{yaml_escape(art.get("date"))}"')
        tags = art.get("tags", []) or []
        lines.append("    tags:")
        for t in tags:
            lines.append(f"      - {yaml_escape(t)}")

    lines.append("---")
    lines.append("")  # Leerzeile

    return "\n".join(lines)


def build_product_body(pack: Dict[str, Any]) -> str:
    """
    Sehr einfache Auto-Beschreibung für das Produkt.
    """
    title = pack.get("title", "")
    category = pack.get("category", "")
    articles = pack.get("articles", [])
    article_count = len(articles)

    body_lines = [
        f"{title}",
        "",
        f"Dieses wöchentliche Pack bündelt {article_count} Artikel aus der Kategorie **{category}**.",
        "",
        "Du bekommst:",
        "",
        "- Kuratierten Content der letzten Woche",
        "- Fokus auf praxisnahe, umsetzbare Beispiele",
        "- Saubere Projektstrukturen und Best Practices",
        "",
        "### Enthaltene Artikel",
        "",
    ]

    for art in articles:
        atitle = art.get("title", "")
        aslug = art.get("slug", "")
        body_lines.append(f"- **{atitle}** (`{aslug}`)")

    body_lines.append("")
    body_lines.append(
        "_Dieses Pack wurde automatisch aus den besten Artikeln der Woche generiert._"
    )
    body_lines.append("")

    return "\n".join(body_lines)


def write_product_markdown(
    pack: Dict[str, Any],
    weekly_date: str,
    stripe_price_id: Optional[str],
):
    PACKS_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    slug = pack.get("slug")
    if not slug:
        raise ValueError("Pack has no slug")

    md_path = PACKS_CONTENT_DIR / f"{slug}.md"

    front = build_product_front_matter(pack, weekly_date, stripe_price_id)
    body = build_product_body(pack)

    content = front + body

    md_path.write_text(content, encoding="utf-8")
    logger.info(f"[sync_packs_from_weekly] Wrote product markdown -> {md_path}")


def write_product_json(
    pack: Dict[str, Any],
    weekly_date: str,
    stripe_price_id: Optional[str],
):
    PACKS_STATIC_DIR.mkdir(parents=True, exist_ok=True)
    slug = pack.get("slug")
    if not slug:
        raise ValueError("Pack has no slug")

    json_path = PACKS_STATIC_DIR / f"{slug}.json"

    payload = {
        "slug": pack.get("slug"),
        "title": pack.get("title"),
        "short_title": pack.get("short_title"),
        "category": pack.get("category"),
        "price_eur": pack.get("price_eur"),
        "week": pack.get("week"),
        "year": pack.get("year"),
        "weekly_date": weekly_date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": pack.get("articles", []),
    }

    if stripe_price_id:
        payload["stripe_price_id"] = stripe_price_id

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[sync_packs_from_weekly] Wrote product JSON -> {json_path}")


def main():
    latest = find_latest_weekly_file()
    if not latest:
        logger.warning("[sync_packs_from_weekly] No weekly pack file found. Exiting.")
        return

    logger.info(f"[sync_packs_from_weekly] Using weekly file: {latest}")
    data = load_weekly_packs(latest)
    weekly_date = data.get("date") or latest.stem

    packs = data.get("packs", [])
    if not packs:
        logger.warning(f"[sync_packs_from_weekly] No packs in weekly file {latest}. Exiting.")
        return

    stripe_prices = load_stripe_category_prices()
    if not stripe_prices:
        logger.warning("[sync_packs_from_weekly] No Stripe category prices loaded. Packs will have no stripe_price_id.")

    for pack in packs:
        try:
            category = str(pack.get("category", "")).strip()
            stripe_price_id = stripe_prices.get(category)
            if not stripe_price_id:
                logger.warning(
                    f"[sync_packs_from_weekly] No Stripe price for category '{category}'. "
                    f"Pack {pack.get('slug')} will have no stripe_price_id."
                )

            write_product_markdown(pack, weekly_date, stripe_price_id)
            write_product_json(pack, weekly_date, stripe_price_id)
        except Exception as e:
            logger.error(f"[sync_packs_from_weekly] Error processing pack {pack.get('slug')}: {e}")

    logger.info("[sync_packs_from_weekly] Done.")


if __name__ == "__main__":
    main()
