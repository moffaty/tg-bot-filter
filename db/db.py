from sqlmodel import create_engine, Session
from contextlib import contextmanager

engine = create_engine("sqlite+pysqlite:///memory.db", echo=True)


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
