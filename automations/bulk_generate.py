# automations/bulk_generate.py
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from llm_client import generate_local_article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_QUESTIONS_DIR = BASE_DIR / "data" / "raw_questions"
DRAFTS_DIR = BASE_DIR / "drafts" / "local"


def load_questions_for_today(today_str: str):
    """
    Erwartet Dateien wie:
    data/raw_questions/2025-12-04/*.json
    mit Struktur pro Datei:
    {
      "id": "q_2025_0001",
      "question": "How do I ...?",
      "tags": ["fastapi", "python"],
      ...
    }
    """
    day_dir = RAW_QUESTIONS_DIR / today_str
    if not day_dir.exists():
        logger.warning(f"[bulk_generate] No questions directory for {today_str} at {day_dir}")
        return []

    items = []
    for f in sorted(day_dir.glob("*.json")):
        try:
            with f.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                items.append(data)
        except Exception as e:
            logger.error(f"[bulk_generate] Failed to load {f}: {e}")
    return items


def save_draft(question_id: str, content_md: str, today_str: str):
    out_dir = DRAFTS_DIR / today_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{question_id}.md"
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(content_md)
    logger.info(f"[bulk_generate] Saved draft -> {out_path}")


def main():
    # timezone-aware replacement für datetime.utcnow()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info(f"[bulk_generate] Starting for {today}")

    questions = load_questions_for_today(today)
    if not questions:
        logger.warning("[bulk_generate] No questions found. Exiting.")
        return

    generated_count = 0
    for q in questions:
        qid = q.get("id") or q.get("question_id")
        qtext = q.get("question") or q.get("title") or ""

        if not qid or not qtext:
            logger.warning(f"[bulk_generate] Skipping invalid question: {q}")
            continue

        try:
            logger.info(f"[bulk_generate] Generating draft for {qid} ...")
            article_md = generate_local_article(
                question_id=qid,
                question_text=qtext,
                engine_label="local-llm",
            )
            save_draft(qid, article_md, today)
            generated_count += 1
        except Exception as e:
            logger.error(f"[bulk_generate] Error for {qid}: {e}")

    logger.info(f"[bulk_generate] Done. Generated drafts: {generated_count}")


if __name__ == "__main__":
    main()
