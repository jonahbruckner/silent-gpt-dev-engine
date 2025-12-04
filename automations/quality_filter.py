# automations/quality_filter.py
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from llm_client import score_article_with_gpt, generate_social_snippets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

DRAFTS_DIR = BASE_DIR / "drafts" / "local"
SELECTED_DIR = BASE_DIR / "drafts" / "selected"
SOCIAL_QUEUE_DIR = BASE_DIR / "data" / "social_queue"

TOP_N = int(os.getenv("QUALITY_TOP_N", "8"))
MIN_OVERALL_SCORE = float(os.getenv("QUALITY_MIN_SCORE", "6.5"))


def load_drafts_for_today(today_str: str):
    day_dir = DRAFTS_DIR / today_str
    if not day_dir.exists():
        logger.warning(f"[quality_filter] No drafts directory for {today_str} at {day_dir}")
        return []

    items = []
    for f in sorted(day_dir.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            qid = f.stem
            items.append({"id": qid, "path": f, "content": content})
        except Exception as e:
            logger.error(f"[quality_filter] Failed to load {f}: {e}")
    return items


def save_selected_draft(item, today_str: str):
    out_dir = SELECTED_DIR / today_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{item['id']}.md"
    out_path.write_text(item["content"], encoding="utf-8")
    logger.info(f"[quality_filter] Saved selected draft -> {out_path}")


def save_social_queue(snippets, today_str: str):
    out_dir = SOCIAL_QUEUE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today_str}.json"

    payload = {
        "date": today_str,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "items": snippets,
    }

    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[quality_filter] Social queue saved -> {out_path}")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info(f"[quality_filter] Starting for {today}")

    drafts = load_drafts_for_today(today)
    if not drafts:
        logger.warning("[quality_filter] No drafts found. Exiting.")
        return

    scored_items = []
    all_snippets = []

    for item in drafts:
        qid = item["id"]
        content = item["content"]

        # Question-Meta für Scoring/Snippets – minimaler Default, später kannst du hier Tags etc. reinziehen
        question_meta = {
            "id": qid,
            "source": "raw_questions",
            "date": today,
        }

        try:
            logger.info(f"[quality_filter] Scoring {qid} ...")
            score = score_article_with_gpt(content, question_meta)
            item["score"] = score
            scored_items.append(item)

            logger.info(f"[quality_filter] Generating social snippets for {qid} ...")
            snippets = generate_social_snippets(content, question_meta)
            for s in snippets:
                s["question_id"] = qid
                s["article_date"] = today
            all_snippets.extend(snippets)

        except Exception as e:
            logger.error(f"[quality_filter] Error scoring {qid}: {e}")

    # Sortieren nach overall_score
    scored_items.sort(key=lambda x: x["score"]["overall_score"], reverse=True)
    selected = [i for i in scored_items if i["score"]["overall_score"] >= MIN_OVERALL_SCORE]
    selected = selected[:TOP_N]

    logger.info(
        f"[quality_filter] Total drafts: {len(drafts)}, "
        f"scored: {len(scored_items)}, selected: {len(selected)}"
    )

    for item in selected:
        save_selected_draft(item, today)

    if all_snippets:
        save_social_queue(all_snippets, today)
    else:
        logger.warning("[quality_filter] No social snippets generated.")


if __name__ == "__main__":
    main()
