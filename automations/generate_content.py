import os, sys
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # repo root
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
from app.db import get_session
from app.models.content import RawQuestion, ContentItem
from app.services.gpt import generate_tutorial_md

def run():
    with get_session() as session:
        raw_items = session.query(RawQuestion).filter_by(status="new").limit(10).all()

        for raw in raw_items:
            md = generate_tutorial_md(raw.title, raw.body)

            content = ContentItem(
                raw_id=raw.id,
                type="tutorial",
                title=raw.title,
                body_md=md,
                tags=raw.tags,
                status="draft"
            )
            session.add(content)
            raw.status = "processed"
        session.commit()
