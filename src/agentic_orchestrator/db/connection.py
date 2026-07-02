"""
Database connection management for Agentic Orchestrator.

Supports both SQLite (development) and PostgreSQL (production).
"""

import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from .models import Base

logger = logging.getLogger(__name__)


class Database:
    """
    Database connection manager.

    Supports:
    - SQLite for development/testing
    - PostgreSQL for production
    """

    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv(
            "DATABASE_URL",
            f"sqlite:///{Path(__file__).parent.parent.parent.parent / 'data' / 'orchestrator.db'}",
        )

        self._init_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _init_engine(self):
        """Initialize the database engine based on URL type."""
        if self.url.startswith("postgresql"):
            # PostgreSQL with connection pooling
            self.engine = create_engine(
                self.url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )
        else:
            # SQLite
            # Ensure data directory exists
            if "sqlite:///" in self.url:
                db_path = self.url.replace("sqlite:///", "")
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

            self.engine = create_engine(
                self.url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )

            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all tables in the database. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Usage:
            with db.session() as session:
                session.query(Model).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """
        Get a new session for manual management.

        Remember to call session.close() when done!
        """
        return self.SessionLocal()

    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        from sqlalchemy import text

        try:
            with self.session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


# Global database instance
db = Database()


def init_database(url: Optional[str] = None) -> Database:
    """
    Initialize the database with optional custom URL.

    Args:
        url: Database URL (SQLite or PostgreSQL)

    Returns:
        Database instance
    """
    global db
    db = Database(url)
    db.create_tables()
    return db


def get_db() -> Database:
    """Get the global database instance."""
    return db


def ensure_schema(
    database: Optional[Database] = None,
    attempts: int = 3,
    delay_seconds: float = 1.0,
) -> bool:
    """Idempotently create any missing tables, retrying briefly.

    ``create_tables()`` is CREATE TABLE IF NOT EXISTS, so this is a no-op on a
    healthy database and turns a missing/emptied SQLite file into an
    empty-but-working one (2026-07 incident). Several PM2 processes can boot
    simultaneously and race the CREATEs on a fresh file — losers may see
    "table already exists" or transient lock errors, which resolve on retry.

    Never raises; returns False when the schema could not be guaranteed so
    callers can decide how loudly to complain.
    """
    target = database or get_db()
    for attempt in range(1, attempts + 1):
        try:
            target.create_tables()
            return True
        except Exception:
            if attempt == attempts:
                logger.exception(
                    "Could not ensure database schema after %d attempts; "
                    "DB-backed work may fail",
                    attempts,
                )
                return False
            time.sleep(delay_seconds)
    return False
