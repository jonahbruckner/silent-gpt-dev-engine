import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session, init_db
from app.models.content import RawQuestion, ContentItem

# NEW OpenAI client import
from openai import OpenAI

# init DB tables (in case web app didn't run first)
init_db()

# create OpenAI client (reads OPENAI_API_KEY from env)
client = OpenAI()

MAX_ITEMS_PER_RUN = 5  # balanced mode

TUTORIAL_SYSTEM_PROMPT = (
    "You are a senior Python backend engineer and educator. "
    "Create clear, practical micro-tutorials in Markdown."
)


def build_user_prompt(raw: RawQuestion) -> str:
    return f"""
I will give you a developer question. Create a micro-tutorial that:

1. Has an H1 title.
2. Short intro focusing on the problem.
3. Has sections: "Why this happens", "Step-by-step solution",
   "Example variation", "Common errors & fixes", "Cheat sheet summary".
4. Include at least one full code example.
5. Keep it under 1200 words.

Question title:
{raw.title}

Question body:
{raw.body}

Return Markdown only.
""".strip()


def generate_markdown(raw: RawQuestion) -> str:
    user_prompt = build_user_prompt(raw)

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": TUTORIAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )

    return resp.choices[0].message.content


def run():
    with get_session() as session:
        q = select(RawQuestion).where(RawQuestion.status == "new").limit(
            MAX_ITEMS_PER_RUN
        )
        raws = session.exec(q).all()

        if not raws:
            print("[generate_content] No new RawQuestion rows.")
            return

        for raw in raws:
            try:
                print(f"[generate_content] Generating content for id={raw.id}")
                md = generate_markdown(raw)

                item = ContentItem(
                    raw_id=raw.id,
                    type="tutorial",
                    title=raw.title,
                    body_md=md,
                    tags=raw.tags,
                    status="draft",
                )
                session.add(item)
                raw.status = "processed"
                time.sleep(0.5)
            except Exception as e:
                print(f"[generate_content] Error for raw_id={raw.id}: {e}")

        session.commit()
        print("[generate_content] Done.")


if __name__ == "__main__":
    run()
