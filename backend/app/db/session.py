import os
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Für psycopg3: SQLAlchemy-Dialekt auf postgresql+psycopg umstellen,
# falls nur "postgres://" oder "postgresql://" gesetzt ist.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, echo=False)


def get_session() -> Session:
    """Gibt eine SQLModel-Session zurück, die von allen Jobs genutzt wird."""
    return Session(engine)


def init_db() -> None:
    """Erstellt alle Tabellen, falls sie noch nicht existieren."""
    SQLModel.metadata.create_all(engine)
