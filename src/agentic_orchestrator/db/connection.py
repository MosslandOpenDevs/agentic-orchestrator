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

# How long a blocked SQLite writer waits for the lock before giving up.
SQLITE_BUSY_TIMEOUT_MS = 30_000


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

            in_memory = self._is_in_memory()

            engine_kwargs = {
                "connect_args": {"check_same_thread": False},
                "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            }
            if in_memory:
                # An in-memory database lives *inside* its connection: open a
                # second one and you get a second, empty database. StaticPool
                # (one connection, reused) is the only thing that works.
                engine_kwargs["poolclass"] = StaticPool
            # A file database must NOT use StaticPool. Every Session would
            # share the one connection and therefore one transaction, so a
            # rollback in any request discards every other request's
            # uncommitted writes -- and one long project generation would hold
            # the whole API in its transaction. Let SQLAlchemy pool normally.

            self.engine = create_engine(self.url, **engine_kwargs)

            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                if not in_memory:
                    # Sessions now hold separate connections, so concurrency is
                    # real: WAL lets readers run while the writer commits, and
                    # busy_timeout makes a blocked writer wait rather than
                    # raise "database is locked".
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
                cursor.close()

    def _is_in_memory(self) -> bool:
        """True for SQLite URLs that name a memory database."""
        return ":memory:" in self.url or "mode=memory" in self.url

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
