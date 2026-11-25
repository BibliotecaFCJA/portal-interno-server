from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

import os
import sys

def get_base_path():
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    print("BASE PATH:", base_path)
    return base_path

BASE_DIR = get_base_path()
DB_PATH = os.path.join(BASE_DIR, "emprestimos.db")


engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=True,
    future=True
)

@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

metadata = MetaData()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()