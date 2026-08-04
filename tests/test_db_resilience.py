"""Tests for database-loss resilience (2026-07 /status 500 incident).

Covers the three hardening layers:
- /status graceful degradation (200 + status="degraded" instead of a 500)
- startup schema self-heal (FastAPI lifespan creates missing tables)
- rolling SQLite backups (snapshot, skip rules, pruning, interval)
"""

import os
import sqlite3
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import agentic_orchestrator.api.main as api_main
import agentic_orchestrator.db.backup as db_backup
import agentic_orchestrator.scheduler.__main__ as sched_main
from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.backup import (
    backup_database,
    list_backups,
    maybe_backup_database,
)
from agentic_orchestrator.db.connection import Database, ensure_schema


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

    def test_maybe_backup_creates_first_snapshot_when_no_backup_dir(self, tmp_path):
        """Fresh deployment: data/backup/ does not exist yet — the health
        task's very first call must create it and take snapshot #1."""
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)

        assert not (tmp_path / "backup").exists()
        dest = maybe_backup_database(url=f"sqlite:///{db_file}")

        assert dest is not None
        assert list_backups(tmp_path / "backup") == [dest]

    def test_maybe_backup_creates_first_snapshot_when_dir_empty(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        (tmp_path / "backup").mkdir()

        dest = maybe_backup_database(url=f"sqlite:///{db_file}")

        assert dest is not None
        assert list_backups(tmp_path / "backup") == [dest]

    def test_copy_failure_leaves_no_partial_and_next_tick_retries(self, tmp_path, monkeypatch):
        """An aborted copy must leave nothing that gates the interval or
        occupies a retention slot; the next health tick retries immediately."""
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        url = f"sqlite:///{db_file}"
        backup_dir = tmp_path / "backup"

        def boom(src_conn, dest_conn):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(db_backup, "_copy_database", boom)
        with pytest.raises(sqlite3.OperationalError):
            backup_database(url=url)

        assert list_backups(backup_dir) == []
        assert list(backup_dir.glob("*.tmp")) == []

        monkeypatch.undo()  # restore the real copy
        # The failed attempt must NOT count as "fresh snapshot exists".
        dest = maybe_backup_database(url=url)
        assert dest is not None

    def test_integrity_failed_snapshot_is_discarded(self, tmp_path, monkeypatch):
        """A snapshot failing PRAGMA quick_check must be deleted, keeping
        existing backups untouched (corrupt source protection)."""
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        prev = backup_dir / "orchestrator-20250101-000000.db"
        prev.write_bytes(b"good old snapshot")

        monkeypatch.setattr(db_backup, "_quick_check_ok", lambda p: False)
        assert backup_database(url=f"sqlite:///{db_file}") is None

        assert list_backups(backup_dir) == [prev]  # old backup retained
        assert list(backup_dir.glob("*.tmp")) == []

    def test_stale_tmp_leftovers_are_cleaned_up(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        leftover = backup_dir / "orchestrator-20250101-000000.db.tmp"
        leftover.write_bytes(b"crashed mid-copy")

        dest = backup_database(url=f"sqlite:///{db_file}")

        assert dest is not None
        assert not leftover.exists()

    def test_tmp_files_do_not_gate_the_interval(self, tmp_path):
        """A partial .tmp file must be invisible to list_backups, so it can
        never suppress backups for 24h."""
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        (backup_dir / "orchestrator-20250101-000000.db.tmp").write_bytes(b"partial")

        assert list_backups(backup_dir) == []


def _make_history_db(path, ideas=0, with_signals=True):
    """A DB with history rows (ideas) and optionally a live signals table."""
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE ideas (id TEXT PRIMARY KEY)")
    conn.executemany("INSERT INTO ideas VALUES (?)", [(f"i{k}",) for k in range(ideas)])
    if with_signals:
        conn.execute("CREATE TABLE signals (id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO signals VALUES ('s1')")
    conn.commit()
    conn.close()


class TestRegressionAwarePruning:
    """A wiped-and-auto-refilled DB must never rotate out pre-incident backups."""

    def test_history_regression_skips_prune(self, tmp_path):
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        # Newest existing snapshot holds rich history (50 ideas).
        prev = backup_dir / "orchestrator-20250101-000000.db"
        _make_history_db(prev, ideas=50, with_signals=False)
        # An even older snapshot that keep=1 would normally prune.
        older = backup_dir / "orchestrator-20240101-000000.db"
        older.write_bytes(b"ancient snapshot")

        # Source DB: the post-incident shape — signals refilled by the
        # pipeline, history nearly gone (1 idea vs 50).
        db_file = tmp_path / "orchestrator.db"
        _make_history_db(db_file, ideas=1, with_signals=True)

        dest = backup_database(url=f"sqlite:///{db_file}", keep=1)

        remaining = list_backups(backup_dir)
        assert dest is not None  # the new snapshot is still written...
        assert prev in remaining  # ...but the rich snapshot survives
        assert older in remaining  # and nothing at all was pruned
        assert len(remaining) == 3

    def test_prune_proceeds_when_history_is_stable(self, tmp_path):
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        prev = backup_dir / "orchestrator-20250101-000000.db"
        _make_history_db(prev, ideas=30, with_signals=False)

        db_file = tmp_path / "orchestrator.db"
        _make_history_db(db_file, ideas=40, with_signals=True)

        dest = backup_database(url=f"sqlite:///{db_file}", keep=1)

        assert list_backups(backup_dir) == [dest]  # normal rotation resumed

    def test_small_baselines_never_trigger_the_guard(self, tmp_path):
        """Below REGRESSION_MIN_BASELINE the ratio is noise, not a signal."""
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        prev = backup_dir / "orchestrator-20250101-000000.db"
        _make_history_db(prev, ideas=5, with_signals=False)  # tiny baseline

        db_file = tmp_path / "orchestrator.db"
        _make_history_db(db_file, ideas=1, with_signals=True)

        dest = backup_database(url=f"sqlite:///{db_file}", keep=1)

        assert list_backups(backup_dir) == [dest]

    def test_garbage_previous_snapshot_does_not_block_pruning(self, tmp_path):
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        (backup_dir / "orchestrator-20250101-000000.db").write_bytes(b"not sqlite")

        db_file = tmp_path / "orchestrator.db"
        _make_history_db(db_file, ideas=1, with_signals=True)

        dest = backup_database(url=f"sqlite:///{db_file}", keep=1)

        assert list_backups(backup_dir) == [dest]


class TestEnsureSchema:
    """Boot-race retry semantics of db.connection.ensure_schema."""

    def test_retries_transient_race_then_succeeds(self, tmp_path):
        db_file = tmp_path / "orchestrator.db"
        real = Database(f"sqlite:///{db_file}")

        class FlakyDB:
            calls = 0

            def create_tables(self):
                FlakyDB.calls += 1
                if FlakyDB.calls == 1:
                    # What a boot-race loser sees.
                    raise sqlite3.OperationalError("table signals already exists")
                real.create_tables()

        assert ensure_schema(FlakyDB(), attempts=3, delay_seconds=0) is True
        conn = sqlite3.connect(str(db_file))
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        assert "signals" in tables

    def test_gives_up_without_raising(self):
        class BrokenDB:
            def create_tables(self):
                raise RuntimeError("disk on fire")

        assert ensure_schema(BrokenDB(), attempts=2, delay_seconds=0) is False


class TestSchedulerCLI:
    """Dispatch-level guarantees of python -m agentic_orchestrator.scheduler."""

    def test_task_commands_ensure_schema_first(self, monkeypatch):
        calls = []
        monkeypatch.setattr(sched_main, "ensure_schema", lambda: calls.append("schema"))
        monkeypatch.setattr(sched_main, "health_check", lambda: calls.append("task"))
        monkeypatch.setattr(sys, "argv", ["scheduler", "health-check"])

        sched_main.main()

        assert calls == ["schema", "task"]

    def test_backup_db_never_mutates_via_ensure_schema(self, monkeypatch, tmp_path, capsys):
        """backup-db is read-only: the schema self-heal must NOT run, or it
        would write into the very database it is about to snapshot."""
        calls = []
        monkeypatch.setattr(sched_main, "ensure_schema", lambda: calls.append("schema"))
        monkeypatch.setattr(db_backup, "backup_database", lambda: tmp_path / "snap.db")
        monkeypatch.setattr(sys, "argv", ["scheduler", "backup-db"])

        sched_main.main()

        assert calls == []
        assert "Backup written" in capsys.readouterr().out

    def test_backup_db_exits_nonzero_when_nothing_backed_up(self, monkeypatch):
        monkeypatch.setattr(db_backup, "backup_database", lambda: None)
        monkeypatch.setattr(sys, "argv", ["scheduler", "backup-db"])

        with pytest.raises(SystemExit) as excinfo:
            sched_main.main()

        assert excinfo.value.code == 1
