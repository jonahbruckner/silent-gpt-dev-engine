import os, sys
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # repo root
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from app.db import get_session
from app.models.content import ContentItem

POST_DIR = "../site/posts/"

def run():
    with get_session() as session:
        items = session.query(ContentItem).filter_by(status="reviewed").limit(5).all()

        for item in items:
            file_path = POST_DIR + f"{item.id}-{item.title.replace(' ', '-')}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(item.body_md)
            
            item.status = "published"
        session.commit()

    os.system("cd ../site && git add . && git commit -m 'new posts' && git push")
