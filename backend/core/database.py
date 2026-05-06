# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
backend/core/database.py
SQLAlchemy engine, session factory, and declarative Base.

Usage in endpoints:
    from backend.core.database import get_db
    @router.get("/example")
    def example(db: Session = Depends(get_db)):
        ...
"""

from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore

from config.settings import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # reconnect on stale connections
    pool_size=10,
    max_overflow=20,
    echo=False,  # set True to log all SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency - yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
