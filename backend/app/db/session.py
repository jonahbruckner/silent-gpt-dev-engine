from sqlmodel import Session, create_engine

engine = create_engine("sqlite:///./db.sqlite3")

def get_session():
    return Session(engine)
