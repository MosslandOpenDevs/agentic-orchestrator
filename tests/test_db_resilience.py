"""Tests for database-loss resilience (2026-07 /status 500 incident).

Covers the three hardening layers:
- /status graceful degradation (200 + status="degraded" instead of a 500)
- startup schema self-heal (FastAPI lifespan creates missing tables)
- rolling SQLite backups (snapshot, skip rules, pruning, interval)
"""

import os
import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import agentic_orchestrator.api.main as api_main
from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.backup import (
    backup_database,
    list_backups,
    maybe_backup_database,
)
from agentic_orchestrator.db.connection import Database


@pytest.fixture
def tableless_client():
    """Client whose DB session points at an engine with NO tables created."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # noqa: N806

    def override_get_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestStatusDegradation:
    """/status must degrade to 200, never hard-500, when the DB is broken."""

    def test_status_200_degraded_when_tables_missing(self, tableless_client):
        response = tableless_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["components"]["database"]["status"] == "unhealthy"

    def test_status_keeps_widget_contract_when_degraded(self, tableless_client):
        """The moss.land governance widget consumes these exact stats fields."""
        stats = tableless_client.get("/status").json()["stats"]
        assert stats["agents_active"] == 34
        assert stats["ideas_generated"] == 0
        assert stats["debates_today"] == 0
        assert stats["signals_today"] == 0
        assert stats["plans_created"] == 0


class TestStartupSelfHeal:
    """The lifespan hook must turn an empty DB file into a working schema."""

    def test_lifespan_creates_missing_tables(self, tmp_path, monkeypatch):
        db_file = tmp_path / "empty.db"
        db_file.touch()  # 0-byte file: connectable, but has no tables
        db = Database(f"sqlite:///{db_file}")
        monkeypatch.setattr(api_main, "get_db", lambda: db)

        # Entering the context manager runs the lifespan (startup) hook.
        with TestClient(app) as client:
            response = client.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "operational"
            assert data["components"]["database"]["status"] == "healthy"
            assert data["stats"]["ideas_generated"] == 0

    def test_lifespan_survives_broken_database(self, monkeypatch):
        """A failing create_tables must not prevent the API from starting."""

        class BrokenDB:
            url = "sqlite:///nonexistent"

            def create_tables(self):
                raise RuntimeError("disk on fire")

        monkeypatch.setattr(api_main, "get_db", lambda: BrokenDB())
        with TestClient(app) as client:
            # Non-DB endpoint keeps working even though startup self-heal failed.
            assert client.get("/health").status_code == 200


def _make_populated_db(path, rows=3):
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE signals (id TEXT PRIMARY KEY)")
    conn.executemany("INSERT INTO signals VALUES (?)", [(f"sig-{i}",) for i in range(rows)])
    conn.commit()
    conn.close()


class TestBackup:
    """Rolling SQLite snapshot behavior."""

    def test_backup_creates_snapshot_with_data(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file, rows=3)

        dest = backup_database(url=f"sqlite:///{db_file}")

        assert dest is not None
        assert dest.parent == tmp_path / "backup"
        conn = sqlite3.connect(str(dest))
        assert conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0] == 3
        conn.close()

    def test_backup_skips_missing_file(self, tmp_path):
        assert backup_database(url=f"sqlite:///{tmp_path / 'gone.db'}") is None

    def test_backup_skips_empty_file(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        db_file.touch()
        assert backup_database(url=f"sqlite:///{db_file}") is None

    def test_backup_skips_schema_only_db(self, tmp_path):
        """A self-healed (tables but zero rows) DB must never be snapshotted,
        or it would rotate out the last good backups of real data."""
        db_file = tmp_path / "orchestrator.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE signals (id TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE ideas (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()

        assert backup_database(url=f"sqlite:///{db_file}") is None
        assert list_backups(tmp_path / "backup") == []

    def test_backup_skips_corrupt_file(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        db_file.write_bytes(b"this is not a sqlite database at all")
        assert backup_database(url=f"sqlite:///{db_file}") is None
        assert list_backups(tmp_path / "backup") == []

    def test_backup_skips_non_sqlite_url(self):
        assert backup_database(url="postgresql://user@host/db") is None

    def test_backup_skips_memory_url(self):
        assert backup_database(url="sqlite:///:memory:") is None

    def test_backup_prunes_oldest_beyond_keep(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        # Fabricate old snapshots whose names sort before any new one.
        old_names = [f"orchestrator-2020010{i}-000000.db" for i in range(1, 5)]
        for name in old_names:
            (backup_dir / name).write_bytes(b"old snapshot")

        dest = backup_database(url=f"sqlite:///{db_file}", keep=3)

        remaining = list_backups(backup_dir)
        assert dest is not None
        assert len(remaining) == 3
        assert remaining[-1] == dest  # newest survives
        assert (backup_dir / old_names[0]) not in remaining  # oldest pruned

    def test_maybe_backup_skips_when_recent_snapshot_exists(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        url = f"sqlite:///{db_file}"

        first = backup_database(url=url)
        assert first is not None
        # A snapshot from just now → within the 24h interval → skip.
        assert maybe_backup_database(url=url) is None

    def test_maybe_backup_creates_when_snapshot_is_stale(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        url = f"sqlite:///{db_file}"

        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        stale = backup_dir / "orchestrator-20200101-000000.db"
        stale.write_bytes(b"old snapshot")
        stale_time = os.path.getmtime(stale) - 26 * 3600
        os.utime(stale, (stale_time, stale_time))

        dest = maybe_backup_database(url=url)
        assert dest is not None
        assert dest != stale
        assert len(list_backups(backup_dir)) == 2

    def test_maybe_backup_none_for_non_sqlite(self):
        assert maybe_backup_database(url="postgresql://user@host/db") is None
