# ============================================================================
# app/database/database.py - Database Configuration
# ============================================================================
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging

from .models import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./farmbot_market.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

@contextmanager
def get_db_session():
    """Get database session with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()

def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()