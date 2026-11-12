import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base  # noqa: F401 - single canonical Base

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def check_database_connection():
    """Check connectivity without writing driver errors or secrets to stdout."""
    try:
        with engine.connect():
            logger.info("Database connectivity check succeeded")
            return True
    except Exception:
        logger.error("Database connectivity check failed during initialization")
        return False


check_database_connection()

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()