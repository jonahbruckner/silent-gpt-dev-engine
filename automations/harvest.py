import requests
from app.db import get_session
from app.models.content import RawQuestion
import os, sys
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # repo root
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)



TAGS = ["python", "fastapi", "docker", "asyncio"]

def run():
    for tag in TAGS:
        url = f"https://api.stackexchange.com/2.3/questions?order=desc&sort=creation&tagged={tag}&site=stackoverflow"
        data = requests.get(url).json()

        with get_session() as session:
            for q in data.get("items", []):
                raw = RawQuestion(
                    source="stackoverflow",
                    source_id=str(q["question_id"]),
                    title=q["title"],
                    body=q.get("body_markdown", ""),
                    tags=",".join(q["tags"]),
                    url=q["link"]
                )
                session.add(raw)
            session.commit()

if __name__ == "__main__":
    run()
