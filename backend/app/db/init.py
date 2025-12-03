# backend/app/db/init.py
from .session import init_db  # statt backend.app.db.session

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
