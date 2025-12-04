# automations/sync_microsites.py
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

SELECTED_DIR = BASE_DIR / "drafts" / "selected"
RAW_QUESTIONS_DIR = BASE_DIR / "data" / "raw_questions"

# Default Content Dirs (per ENV überschreibbar)
MAIN_SITE_CONTENT_DIR = Path(
    os.getenv("MAIN_SITE_CONTENT_DIR", BASE_DIR / "site" / "content" / "blog")
)

MICROSITE_DIRS = {
    "python-data": Path(os.getenv("MICROSITE_PYTHON_DATA_DIR", BASE_DIR / "site-python-data" / "content" / "blog")),
    "fastapi-backend": Path(os.getenv("MICROSITE_FASTAPI_BACKEND_DIR", BASE_DIR / "site-fastapi-backend" / "content" / "blog")),
    "rag-ai": Path(os.getenv("MICROSITE_RAG_AI_DIR", BASE_DIR / "site-rag-ai" / "content" / "blog")),
    "cloud-devops": Path(os.getenv("MICROSITE_CLOUD_DEVOPS_DIR", BASE_DIR / "site-cloud-devops" / "content" / "blog")),
    "automation-tools": Path(os.getenv("MICROSITE_AUTOMATION_TOOLS_DIR", BASE_DIR / "site-automation-tools" / "content" / "blog")),
}

# Tag → Microsite Mapping
TAG_MICROSITE_MAP = {
    "python": "python-data",
    "pandas": "python-data",
    "dataframe": "python-data",

    "fastapi": "fastapi-backend",
    "api": "fastapi-backend",
    "backend": "fastapi-backend",

    "rag": "rag-ai",
    "retrieval": "rag-ai",
    "vector": "rag-ai",
    "embedding": "rag-ai",

    "devops": "cloud-devops",
    "docker": "cloud-devops",
    "kubernetes": "cloud-devops",
    "ci": "cloud-devops",

    "automation": "automation-tools",
    "airflow": "automation-tools",
    "prefect": "automation-tools",
    "orchestration": "automation-tools",
}


def get_today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_selected_drafts(today_str: str) -> List[Dict[str, Any]]:
    day_dir = SELECTED_DIR / today_str
    if not day_dir.exists():
        logger.warning(f"[sync_microsites] No selected drafts for {today_str} at {day_dir}")
        return []

    items = []
    for f in sorted(day_dir.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            qid = f.stem
            items.append({"id": qid, "path": f, "content": content})
        except Exception as e:
            logger.error(f"[sync_microsites] Failed to load {f}: {e}")
    return items


def load_question_meta(today_str: str, question_id: str) -> Dict[str, Any]:
    meta_path = RAW_QUESTIONS_DIR / today_str / f"{question_id}.json"
    if not meta_path.exists():
        logger.warning(f"[sync_microsites] No raw_questions meta for {question_id} at {meta_path}")
        return {
            "id": question_id,
            "tags": [],
            "source": "unknown",
            "date": today_str,
        }

    try:
        with meta_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        logger.error(f"[sync_microsites] Failed to load meta for {question_id}: {e}")
        data = {"id": question_id, "tags": [], "source": "error", "date": today_str}

    if "id" not in data:
        data["id"] = question_id
    if "date" not in data:
        data["date"] = today_str

    return data


def extract_title_from_markdown(content: str, default: str) -> str:
    """
    Nimmt die erste H1-Zeile als Titel. Fallback: default.
    """
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("#\t"):
            return line[2:].strip()
    return default


def determine_microsites_from_tags(tags: List[str]) -> List[str]:
    """
    Mappt Tags (lowercased) auf Microsite-Slugs.
    """
    microsites = set()
    for tag in tags or []:
        t = str(tag).lower()
        if t in TAG_MICROSITE_MAP:
            microsites.add(TAG_MICROSITE_MAP[t])
    return sorted(microsites)


def build_front_matter(
    title: str,
    today_str: str,
    tags: List[str],
    question_id: str,
    source_engine: str,
    microsite_slug: Optional[str] = None,
) -> str:
    """
    Erzeugt eine Hugo-kompatible YAML Front Matter.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    # Titel escapen -> doppelte Anführungszeichen raus, einfache drin lassen
    safe_title = title.replace('"', "'")

    # Tags lowercased & unique
    tag_list = sorted(set(str(t).lower() for t in (tags or [])))

    lines = [
        "---",
        f'title: "{safe_title}"',
        f"date: {now_iso}",
        "tags:",
    ]

    for t in tag_list:
        lines.append(f"  - {t}")

    lines.extend(
        [
            f"original_id: {question_id}",
            f"source_engine: {source_engine}",
        ]
    )

    if microsite_slug:
        lines.append(f"microsite: {microsite_slug}")

    lines.append("---")
    lines.append("")  # Leerzeile

    return "\n".join(lines)

def write_post(
    base_dir: Path,
    slug: str,
    title: str,
    body_md: str,
    today_str: str,
    tags: List[str],
    question_id: str,
    source_engine: str,
    microsite_slug: Optional[str] = None,
):
    """
    Schreibt einen Blogpost in das gegebene Content-Verzeichnis.
    Dateiname: {today}-{slug}.md
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{today_str}-{slug}.md"
    out_path = base_dir / filename

    front_matter = build_front_matter(
        title=title,
        today_str=today_str,
        tags=tags,
        question_id=question_id,
        source_engine=source_engine,
        microsite_slug=microsite_slug,
    )

    content = front_matter + body_md.lstrip()
    out_path.write_text(content, encoding="utf-8")

    logger.info(f"[sync_microsites] Wrote post -> {out_path}")


def slugify(value: str) -> str:
    """
    Sehr einfache Slug-Funktion: lower, spaces -> '-', nur alphanumerisch + '-'.
    """
    import re

    value = value.strip().lower()
    value = value.replace(" ", "-")
    value = re.sub(r"[^a-z0-9\-]+", "", value)
    value = re.sub(r"-+", "-", value)
    return value[:80] or "post"


def main():
    today_str = get_today_str()
    logger.info(f"[sync_microsites] Starting for {today_str}")

    drafts = load_selected_drafts(today_str)
    if not drafts:
        logger.warning("[sync_microsites] No selected drafts found. Exiting.")
        return

    for item in drafts:
        qid = item["id"]
        body_md = item["content"]

        # Engine-Header ist HTML-Kommentar in der ersten Zeile
        source_engine = "unknown"
        first_line = body_md.splitlines()[0].strip() if body_md.splitlines() else ""
        if first_line.startswith("<!--") and "engine:" in first_line:
            # z.B. <!-- engine: gpt-fallback | created_at: ... -->
            try:
                part = first_line.split("engine:")[1]
                source_engine = part.split("|")[0].strip()
            except Exception:
                pass

        meta = load_question_meta(today_str, qid)
        tags = meta.get("tags", [])
        title = extract_title_from_markdown(body_md, default=f"Post {qid}")
        slug = slugify(title)

        # 1) Hauptseite – immer
        write_post(
            base_dir=MAIN_SITE_CONTENT_DIR,
            slug=slug,
            title=title,
            body_md=body_md,
            today_str=today_str,
            tags=tags,
            question_id=qid,
            source_engine=source_engine,
            microsite_slug=None,
        )

        # 2) Microsites – abhängig von Tags
        microsites = determine_microsites_from_tags(tags)
        if not microsites:
            logger.info(f"[sync_microsites] No microsite routing for {qid} (tags={tags})")
            continue

        for ms in microsites:
            content_dir = MICROSITE_DIRS.get(ms)
            if not content_dir:
                logger.warning(f"[sync_microsites] No content dir configured for microsite '{ms}'")
                continue

            write_post(
                base_dir=content_dir,
                slug=slug,
                title=title,
                body_md=body_md,
                today_str=today_str,
                tags=tags,
                question_id=qid,
                source_engine=source_engine,
                microsite_slug=ms,
            )

    logger.info("[sync_microsites] Done.")


if __name__ == "__main__":
    main()
