#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone
from typing import List

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session, init_db
from app.models.content import ContentItem

from openai import OpenAI

init_db()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
MAX_ITEMS = int(os.environ.get("QA_MAX_ITEMS", "20"))

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

ADMIN_CONTENT_DIR = os.path.join(ROOT_DIR, "site", "content", "admin")
REPORT_PATH = os.path.join(ADMIN_CONTENT_DIR, "content-qa-report.md")


def static_checks(item: ContentItem) -> List[str]:
    issues: List[str] = []
    title = (item.title or "").strip()
    body = (item.body_md or "").strip()

    if len(title) < 20:
        issues.append("Title is very short (< 20 characters).")
    if len(title) > 120:
        issues.append("Title is quite long (> 120 characters).")
    if len(body) < 300:
        issues.append("Body seems very short (< 300 characters).")
    if "```" not in body:
        issues.append(
            "No code block found (```), consider adding at least one code example."
        )
    if "# " not in body and "## " not in body:
        issues.append(
            "No headings found in body, consider structuring with # / ## headings."
        )
    return issues


def llm_review(item: ContentItem) -> str:
    if not client:
        return "LLM review skipped (OPENAI_API_KEY not set)."

    prompt = (
        "You are an editorial assistant for technical programming tutorials.\n\n"
        "Review the following micro-tutorial and list up to 5 specific improvement "
        "suggestions as bullet points (not paragraphs). Focus on clarity, structure, "
        "missing details and potential confusion.\n\n"
        f"Title: {item.title}\n\n"
        "Markdown body:\n"
        "```markdown\n"
        f"{item.body_md}\n"
        "```markdown"
    )

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You provide concise, actionable editorial feedback.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


def fetch_items() -> List[ContentItem]:
    with get_session() as session:
        stmt = (
            select(ContentItem)
            .where(ContentItem.status == "published")
            .order_by(ContentItem.created_at.desc())
            .limit(MAX_ITEMS)
        )
        return session.exec(stmt).all()


def ensure_admin_dir():
    if not os.path.isdir(ADMIN_CONTENT_DIR):
        os.makedirs(ADMIN_CONTENT_DIR, exist_ok=True)


def run():
    ensure_admin_dir()
    items = fetch_items()
    if not items:
        print("[qa_check_content] No published items found.")
        return

    lines: List[str] = []
    lines.append("+++")
    lines.append('title = "Content QA Report"')
    lines.append(f'date = "{datetime.now(timezone.utc).isoformat()}"')
    lines.append('slug = "content-qa-report"')
    lines.append('type = "admin"')
    lines.append("+++")
    lines.append("")
    lines.append("# Content QA Report")
    lines.append("")
    lines.append(
        f"Automatisch generierter QA-Report für die letzten {len(items)} "
        f"veröffentlichten Artikel."
    )
    lines.append("")

    for item in items:
        lines.append(f"## {item.title}")
        lines.append("")
        static_issues = static_checks(item)
        if static_issues:
            lines.append("**Static checks:**")
            for issue in static_issues:
                lines.append(f"- {issue}")
        else:
            lines.append(
                "**Static checks:** Keine offensichtlichen Probleme gefunden."
            )
        lines.append("")

        review_text = llm_review(item)
        lines.append("**LLM review:**")
        lines.append("")
        lines.append(review_text)
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[qa_check_content] QA report written to {REPORT_PATH}")


if __name__ == "__main__":
    run()
