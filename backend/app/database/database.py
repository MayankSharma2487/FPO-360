import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base  # noqa: F401 - single canonical Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

try:
    conn = engine.connect()
    print("✅ Database Connected Successfully")
    conn.close()

except Exception as e:
    print(e)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()