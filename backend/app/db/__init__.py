import os
from sqlmodel import SQLModel, create_engine, Session

# You can override this on Render with an env var DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

# Needed for SQLite; harmless for others
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)


def get_session() -> Session:
    """Return a new database session."""
    return Session(engine)


def init_db() -> None:
    """
    Import all models and create tables.
    This is called once at app startup.
    """
    # Import models so they are registered with SQLModel.metadata
    from ..models import content  # noqa: F401

    SQLModel.metadata.create_all(bind=engine)
