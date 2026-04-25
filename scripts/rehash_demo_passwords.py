# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-05-05
# ============================================

"""
scripts/rehash_demo_passwords.py
Run once after seeding the database to replace the placeholder
password hashes with valid bcrypt hashes of 'Password123#'.

Usage:
    cd hcbs/
    python -m scripts.rehash_demo_passwords
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.user import User

DEMO_PASSWORD = "Password123#"


def main():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        real_hash = hash_password(DEMO_PASSWORD)

        for user in users:
            user.password_hash = real_hash

        db.commit()
        print(f"Updated {len(users)} user(s) with valid bcrypt hash for '{DEMO_PASSWORD}'")
    finally:
        db.close()


if __name__ == "__main__":
    main()
