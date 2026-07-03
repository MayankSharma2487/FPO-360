"""
backend/scripts/seed_roles.py

Standalone seed script. Run from the backend/ directory:
    python -m scripts.seed_roles
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.database.seed import seed_roles_and_permissions

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_roles_and_permissions(db)
    finally:
        db.close()