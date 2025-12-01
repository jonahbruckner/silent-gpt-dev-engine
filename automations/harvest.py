import os
import sys
from typing import List

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))   # silent-gpt-dev-engine/
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

import requests
from sqlmodel import select
from app.db import get_session
from app.models.content import RawQuestion

from app.db import init_db
init_db()

STACKOVERFLOW_BASE = "https://api.stackexchange.com/2.3/questions"
TAGS: List[str] = ["python", "fastapi", "docker", "asyncio"]


def fetch_questions_for_tag(tag: str, pagesize: int = 20):
    params = {
        "order": "desc",
        "sort": "creation",
        "tagged": tag,
        "site": "stackoverflow",
        "pagesize": pagesize,
        "filter": "default",
    }
    resp = requests.get(STACKOVERFLOW_BASE, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])


def run():
    with get_session() as session:
        for tag in TAGS:
            print(f"[harvest] Fetching questions for tag={tag}")
            items = fetch_questions_for_tag(tag)

            for q in items:
                source_id = str(q["question_id"])

                # Skip if already stored
                existing = session.exec(
                    select(RawQuestion).where(
                        RawQuestion.source == "stackoverflow",
                        RawQuestion.source_id == source_id,
                    )
                ).first()
                if existing:
                    continue

                raw = RawQuestion(
                    source="stackoverflow",
                    source_id=source_id,
                    title=q.get("title", ""),
                    body=q.get("body", "") or q.get("body_markdown", "") or "",
                    tags=",".join(q.get("tags", [])),
                    url=q.get("link", ""),
                    status="new",
                )
                session.add(raw)

        session.commit()
        print("[harvest] Done.")


if __name__ == "__main__":
    run()
