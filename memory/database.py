"""Database connection management with PostgreSQL primary and SQLite development fallback."""

import logging
import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from memory.models import Base

load_dotenv()
logger = logging.getLogger("academic_risk.database")

DEFAULT_PG_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/academic_risk_db"
)

# Root-relative SQLite fallback path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "academic_risk.db"
DEFAULT_SQLITE_URL = os.getenv("SQLITE_FALLBACK_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

_engine = None
_SessionLocal = None
_is_postgres = False


def init_engine():
    """Attempt connecting to PostgreSQL; fall back smoothly to SQLite if unreachable."""
    global _engine, _SessionLocal, _is_postgres

    if _engine is not None:
        return _engine

    pg_candidate = DEFAULT_PG_URL
    try:
        # Quick connect timeout test
        test_engine = create_engine(
            pg_candidate,
            connect_args={"connect_timeout": 2},
            pool_pre_ping=True
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _engine = test_engine
        _is_postgres = True
        logger.info("Connected to primary PostgreSQL database: %s", pg_candidate.split("@")[-1])
    except Exception as e:
        logger.warning(
            "Primary PostgreSQL database unreachable (%s). Activating SQLite development fallback: %s",
            e,
            DEFAULT_SQLITE_URL
        )
        _engine = create_engine(
            DEFAULT_SQLITE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in DEFAULT_SQLITE_URL else {},
            pool_pre_ping=True
        )
        _is_postgres = False

    Base.metadata.create_all(bind=_engine)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_engine():
    """Retrieve or initialize the SQLAlchemy engine."""
    if _engine is None:
        init_engine()
    return _engine


def get_session_factory():
    """Retrieve or initialize the session maker."""
    if _SessionLocal is None:
        init_engine()
    return _SessionLocal


def is_postgres_active() -> bool:
    """Return True if connected to PostgreSQL; False if on SQLite fallback."""
    if _engine is None:
        init_engine()
    return _is_postgres


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI or standalone services to obtain a database session."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()
