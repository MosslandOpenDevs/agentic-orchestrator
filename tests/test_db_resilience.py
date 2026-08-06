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


class TestReadinessProbe:
    """/ready is what the deployer gates on.

    /health answers 200 whenever the process is alive -- it did so throughout
    the 2026-07 incident while every DB-backed endpoint returned 500, which is
    exactly the state an auto-deploy must not record as a success.
    """

    def test_ready_200_when_the_database_serves(self, tmp_path, monkeypatch):
        db = Database(f"sqlite:///{tmp_path / 'ok.db'}")
        db.create_tables()
        monkeypatch.setattr(api_main, "get_db", lambda: db)

        response = TestClient(app).get("/ready")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"]["database"] == "ok"

    def test_ready_503_when_the_schema_is_missing(self, tmp_path, monkeypatch):
        db_file = tmp_path / "empty.db"
        db_file.touch()  # connectable, but no tables
        monkeypatch.setattr(api_main, "get_db", lambda: Database(f"sqlite:///{db_file}"))

        response = TestClient(app).get("/ready")

        assert response.status_code == 503
        assert response.json()["detail"]["checks"]["database"].startswith("unavailable")

    def test_liveness_still_answers_when_readiness_does_not(self, tmp_path, monkeypatch):
        db_file = tmp_path / "empty.db"
        db_file.touch()
        monkeypatch.setattr(api_main, "get_db", lambda: Database(f"sqlite:///{db_file}"))
        client = TestClient(app)

        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503


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
        existing backups untouched (corrupt source protection).

        It also has to be distinguishable from "nothing to back up": returning
        None here told scripts/deploy.sh there was simply no data to snapshot,
        so it deployed without a restore point in the one state where a restore
        point matters most."""
        db_file = tmp_path / "orchestrator.db"
        _make_populated_db(db_file)
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        prev = backup_dir / "orchestrator-20250101-000000.db"
        prev.write_bytes(b"good old snapshot")

        monkeypatch.setattr(db_backup, "_quick_check_ok", lambda p: False)
        with pytest.raises(db_backup.BackupIntegrityError):
            backup_database(url=f"sqlite:///{db_file}")

        assert list_backups(backup_dir) == [prev]  # old backup retained
        assert list(backup_dir.glob("*.tmp")) == []

    def test_backup_db_exits_1_when_the_source_is_corrupt(self, monkeypatch):
        """Exit 2 means "nothing worth snapshotting" and lets the deploy
        proceed; a corrupt database must not take that path."""

        def boom():
            raise db_backup.BackupIntegrityError("source likely corrupt")

        monkeypatch.setattr(db_backup, "backup_database", boom)
        monkeypatch.setattr(sys, "argv", ["scheduler", "backup-db"])

        with pytest.raises(SystemExit) as excinfo:
            sched_main.main()

        assert excinfo.value.code == 1

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

    def test_backup_db_exits_2_when_there_is_nothing_to_back_up(self, monkeypatch):
        """Distinct from a failure (1): deploy.sh refuses to deploy when the
        snapshot fails, but an empty database is not a failure."""
        monkeypatch.setattr(db_backup, "backup_database", lambda: None)
        monkeypatch.setattr(sys, "argv", ["scheduler", "backup-db"])

        with pytest.raises(SystemExit) as excinfo:
            sched_main.main()

        assert excinfo.value.code == 2


class TestFileDatabaseSessionIsolation:
    """A file database must not put every Session on one shared connection.

    With ``StaticPool`` on a file URL (the pre-fix behaviour) every Session in
    the process shared one DBAPI connection and therefore one transaction: a
    rollback anywhere discarded everyone else's uncommitted writes, and a long
    project generation held the whole API inside its transaction.
    """

    def test_sessions_get_separate_connections(self, tmp_path):
        db = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
        db.create_tables()

        s1, s2 = db.get_session(), db.get_session()
        try:
            # Compare the DBAPI connections, not the per-checkout proxies.
            assert (
                s1.connection().connection.driver_connection
                is not s2.connection().connection.driver_connection
            )
        finally:
            s1.close()
            s2.close()

    def test_one_sessions_rollback_cannot_discard_anothers_write(self, tmp_path):
        from agentic_orchestrator.db.models import Signal

        db = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
        db.create_tables()

        writer, other = db.get_session(), db.get_session()
        try:
            writer.add(Signal(id="sig-1", source="rss", title="t", category="ai"))
            writer.flush()

            # Uncommitted work is invisible to a different session ...
            assert other.query(Signal).filter(Signal.id == "sig-1").count() == 0
            # ... and rolling that session back must not touch the writer.
            other.rollback()
            writer.commit()
        finally:
            writer.close()
            other.close()

        reader = db.get_session()
        try:
            assert reader.query(Signal).filter(Signal.id == "sig-1").count() == 1
        finally:
            reader.close()

    def test_file_database_uses_wal_and_waits_for_locks(self, tmp_path):
        from sqlalchemy import text

        db = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
        db.create_tables()

        session = db.get_session()
        try:
            assert session.execute(text("PRAGMA journal_mode")).scalar() == "wal"
            assert session.execute(text("PRAGMA busy_timeout")).scalar() == 30_000
            # The FK enforcement the retention sweeps rely on stays on.
            assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1
        finally:
            session.close()

    def test_a_busy_database_does_not_break_connecting(self, tmp_path):
        """The WAL migration must not be able to take the API down.

        Production is still in `delete` journal mode, so the first connection
        after this ships attempts the switch -- and SQLite does not run the
        busy handler for a journal-mode change, so it fails instantly if any
        of the eight PM2 processes holds a lock. Raising inside the connect
        hook escapes pool.connect(), which would break ensure_schema() and
        every request that needs a new connection."""
        import sqlite3

        from sqlalchemy import text

        db_file = tmp_path / "orchestrator.db"
        seed = sqlite3.connect(str(db_file))
        seed.execute("CREATE TABLE t (x)")
        seed.commit()
        assert seed.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        seed.execute("BEGIN IMMEDIATE")  # hold the write lock
        seed.execute("INSERT INTO t VALUES (1)")

        db = Database(f"sqlite:///{db_file}")
        session = db.get_session()
        try:
            # Connecting succeeds; the migration simply has not happened yet.
            assert session.execute(text("PRAGMA journal_mode")).scalar() == "delete"
            assert session.execute(text("PRAGMA busy_timeout")).scalar() == 30_000
        finally:
            session.close()
            db.engine.dispose()

        seed.rollback()
        seed.close()

        # Once the contention clears, the next connection migrates it.
        later = Database(f"sqlite:///{db_file}")
        session = later.get_session()
        try:
            assert session.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        finally:
            session.close()
            later.engine.dispose()

    def test_in_memory_database_still_shares_its_one_connection(self):
        """``:memory:`` *is* its connection -- a second one is a second, empty
        database, so StaticPool must stay for it."""
        db = Database("sqlite:///:memory:")
        db.create_tables()

        s1, s2 = db.get_session(), db.get_session()
        try:
            assert (
                s1.connection().connection.driver_connection
                is s2.connection().connection.driver_connection
            )
        finally:
            s1.close()
            s2.close()
