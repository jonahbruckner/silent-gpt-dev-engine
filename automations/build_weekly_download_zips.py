import json
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Projekt-Root = eine Ebene über /automations
ROOT_DIR = Path(__file__).resolve().parents[1]

WEEKLY_DIR = ROOT_DIR / "data" / "packs" / "weekly"
BLOG_DIR = ROOT_DIR / "site" / "content" / "blog"
DOWNLOADS_DIR = ROOT_DIR / "site" / "static" / "downloads"
TMP_DIR = ROOT_DIR / ".tmp" / "weekly_zips"


def find_latest_weekly_file() -> Path:
    """Nimmt die neueste weekly-JSON-Datei in data/packs/weekly."""
    files = sorted(WEEKLY_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No weekly pack JSON found in {WEEKLY_DIR}")
    latest = files[-1]
    logger.info("[weekly_zips] Using weekly file: %s", latest)
    return latest


def load_weekly_data(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "packs" not in data or not data["packs"]:
        raise ValueError(f"No packs found in weekly file {path}")
    return data


def parse_date_prefix(iso_str: str, fallback_prefix: str) -> str:
    """Erzeugt YYYY-MM-DD aus ISO-String; bei Fehler fallback."""
    if not iso_str:
        return fallback_prefix
    try:
        # ISO mit oder ohne Z, mit Offset -> robust parsen
        cleaned = iso_str.replace("Z", "+00:00") if iso_str.endswith("Z") else iso_str
        dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        logger.warning("[weekly_zips] Failed to parse date '%s', using fallback '%s'",
                       iso_str, fallback_prefix)
        return fallback_prefix


def build_zip_for_pack(weekly_meta: dict, pack: dict, weekly_date_str: str) -> Path:
    """Baut ein ZIP für ein einzelnes Pack."""
    pack_slug = pack["slug"]
    out_zip = DOWNLOADS_DIR / f"{pack_slug}.zip"

    # tmp-Ordner für dieses Pack aufräumen & neu anlegen
    pack_tmp_dir = TMP_DIR / pack_slug
    shutil.rmtree(pack_tmp_dir, ignore_errors=True)
    pack_tmp_dir.mkdir(parents=True, exist_ok=True)

    # 1) pack.json – Metadaten ins ZIP legen
    pack_meta = {
        "slug": pack_slug,
        "title": pack.get("title"),
        "short_title": pack.get("short_title"),
        "category": pack.get("category"),
        "price_eur": pack.get("price_eur"),
        "week": pack.get("week"),
        "year": pack.get("year"),
        "generated_at": pack.get("generated_at") or weekly_meta.get("generated_at"),
        "articles": pack.get("articles", []),
    }
    (pack_tmp_dir / "pack.json").write_text(
        json.dumps(pack_meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 2) README.txt – kurzes Intro
    readme_lines = [
        f"{pack_meta['title'] or pack_slug}",
        "",
        "Dieses ZIP wurde automatisch von der SilentGPT Dev Engine generiert.",
        "Es enthält kuratierte Artikel aus der angegebenen Woche.",
        "",
        "Struktur:",
        "- pack.json : Metadaten zum Pack (Slug, Titel, Artikel, Woche, Jahr)",
        "- articles/ : Markdown-Dateien der Artikel",
        "",
        "Hinweis:",
        "Die Inhalte sind für den persönlichen/Team-Gebrauch gedacht. "
        "Bitte teile den Download-Link nicht öffentlich.",
        "",
    ]
    (pack_tmp_dir / "README.txt").write_text(
        "\n".join(readme_lines),
        encoding="utf-8",
    )

    # 3) Artikel einsammeln
    articles_tmp_dir = pack_tmp_dir / "articles"
    articles_tmp_dir.mkdir(exist_ok=True)

    for art in pack.get("articles", []):
        slug = art["slug"]
        date_iso = art.get("date") or weekly_meta.get("date")
        date_prefix = parse_date_prefix(date_iso, weekly_date_str)

        filename = f"{date_prefix}-{slug}.md"
        src = BLOG_DIR / filename
        dst = articles_tmp_dir / filename

        if not src.exists():
            logger.warning(
                "[weekly_zips] Article file not found for slug=%s expected=%s",
                slug,
                src,
            )
            continue

        shutil.copy2(src, dst)
        logger.info("[weekly_zips] Added article -> %s", dst)

    # 4) ZIP bauen
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in pack_tmp_dir.rglob("*"):
            arcname = path.relative_to(pack_tmp_dir)
            zf.write(path, arcname)

    logger.info("[weekly_zips] Built ZIP -> %s", out_zip)

    return out_zip


def main():
    latest = find_latest_weekly_file()
    weekly_data = load_weekly_data(latest)

    weekly_date = weekly_data.get("date")
    weekly_date_prefix = parse_date_prefix(weekly_date, latest.stem)

    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    built = []

    for pack in weekly_data["packs"]:
        slug = pack["slug"]
        logger.info("[weekly_zips] Building ZIP for pack=%s", slug)
        zip_path = build_zip_for_pack(weekly_data, pack, weekly_date_prefix)
        built.append(zip_path)

    logger.info("[weekly_zips] Done. Built %d ZIP(s).", len(built))


if __name__ == "__main__":
    main()
