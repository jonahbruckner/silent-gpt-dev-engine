import os, sys
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # repo root
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
from app.db import get_session
from app.models.content import RawQuestion, ContentItem

