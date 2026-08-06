"""Restoring from a snapshot has to be a command, not a runbook.

The hazard these tests pin is not hypothetical. With the database in WAL mode,
a writer that did not close cleanly (OOM kill, `kill -9`, a crash -- i.e. the
situation you are in when you reach for a backup) leaves a hot `-wal` beside
the database. Copy a snapshot over the database file and leave that `-wal`
there, and SQLite replays it on top: you get the *old* data back, and
`PRAGMA integrity_check` says "ok". The restore silently did not happen.

`test_a_naive_copy_silently_undoes_the_restore` demonstrates exactly that, so
the reason for every other guard in this module stays visible.
"""

import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from agentic_orchestrator.db.connection import Database
from agentic_orchestrator.db.models import Signal
from agentic_orchestrator.db.restore import (
    RestoreError,
    describe_snapshots,
    list_snapshots,
    restore_database,
    revert_restore,
)
from agentic_orchestrator.timeutil import utcnow

SNAPSHOT_ROWS = 1
POST_SNAPSHOT_ROWS = 400


def _seed(db_path: Path, count: int, note: str, start: int = 0) -> None:
    db = Database(f"sqlite:///{db_path}")
    db.create_tables()
    session = db.get_session()
    try:
        for i in range(start, start + count):
            session.add(
                Signal(
                    id=f"{note}-{i}",
                    source="rss",
                    category="ai",
                    title=f"{note} {i}",
                    score=0.5,
                    collected_at=utcnow(),
                )
            )
        session.commit()
    finally:
        session.close()
        db.engine.dispose()


def _snapshot(db_path: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(str(db_path))
    try:
        out = sqlite3.connect(str(dest))
        try:
            src.backup(out)
        finally:
            out.close()
    finally:
        src.close()


def _leave_a_hot_wal(db_path: Path, rows: int) -> None:
    """Write `rows` more rows from a process that is then killed, so the WAL
    survives uncheckpointed -- what a crashed writer leaves behind."""
    script = f"""
import sqlite3, time
conn = sqlite3.connect({str(db_path)!r})
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA wal_autocheckpoint=0")
for i in range({rows}):
    conn.execute(
        "INSERT INTO signals (id, source, category, title, score) VALUES (?,?,?,?,?)",
        (f"post-{{i}}", "rss", "ai", f"post {{i}}", 0.5),
    )
conn.commit()
print("WROTE", flush=True)
time.sleep(60)
"""
    proc = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, text=True)
    assert proc.stdout.readline().strip() == "WROTE", "writer subprocess failed to write"
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait()
    time.sleep(0.2)
    assert (db_path.parent / (db_path.name + "-wal")).exists(), "expected a hot WAL"


def _count(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    finally:
        conn.close()


@pytest.fixture
def scenario(tmp_path):
    """A database whose writer was killed after the snapshot was taken."""
    live = tmp_path / "orchestrator.db"
    snap = tmp_path / "backup" / "orchestrator-20260806-000000.db"

    _seed(live, SNAPSHOT_ROWS, "snapshotted")
    _snapshot(live, snap)
    _leave_a_hot_wal(live, POST_SNAPSHOT_ROWS)

    # Deliberately do NOT read the row count here: opening and cleanly closing
    # a connection checkpoints the WAL into the main file and deletes it,
    # which would quietly dismantle the scenario every test below depends on.
    return {"live": live, "snapshot": snap, "url": f"sqlite:///{live}"}


class TestTheHazard:
    def test_a_naive_copy_silently_undoes_the_restore(self, scenario):
        """Why restore-db exists. This is the documented old procedure."""
        shutil.copy(scenario["snapshot"], scenario["live"])

        conn = sqlite3.connect(str(scenario["live"]))
        try:
            restored_rows = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            conn.close()

        # The old rows came back from the WAL ...
        assert restored_rows == SNAPSHOT_ROWS + POST_SNAPSHOT_ROWS
        # ... and nothing looks wrong.
        assert integrity == "ok"


class TestRestore:
    def test_restore_actually_restores_past_a_hot_wal(self, scenario):
        result = restore_database(source=scenario["snapshot"], url=scenario["url"])

        assert _count(scenario["live"]) == SNAPSHOT_ROWS
        assert result.row_counts["signals"] == SNAPSHOT_ROWS
        assert not (scenario["live"].parent / (scenario["live"].name + "-wal")).exists()

    def test_no_sidecar_survives_the_restore(self, scenario):
        """The guarantee, stated as a postcondition rather than a mechanism.

        Opening the old database on the way through (the writer check, the
        copy-aside) usually makes SQLite checkpoint and clean up by itself, so
        the explicit sweep often removes nothing. That is fine -- what must
        hold is that nothing is left behind for SQLite to replay, whichever
        step got there first."""
        live = scenario["live"]
        stale_journal = live.with_name(live.name + "-journal")
        stale_journal.write_bytes(b"leftover rollback journal")

        result = restore_database(source=scenario["snapshot"], url=scenario["url"])

        for suffix in ("-wal", "-shm", "-journal"):
            assert not live.with_name(live.name + suffix).exists(), suffix
        assert result.removed_sidecars is not None  # reported, whether or not it fired
        assert _count(live) == SNAPSHOT_ROWS

    def test_the_restored_database_is_usable_by_the_app(self, scenario):
        restore_database(source=scenario["snapshot"], url=scenario["url"])

        db = Database(scenario["url"])
        session = db.get_session()
        try:
            assert session.query(Signal).count() == SNAPSHOT_ROWS
        finally:
            session.close()
            db.engine.dispose()

    def test_the_previous_database_is_kept_and_can_be_put_back(self, scenario):
        result = restore_database(source=scenario["snapshot"], url=scenario["url"])

        assert result.pre_restore_copy is not None
        assert result.pre_restore_copy.exists()
        # The copy captured the WAL contents, not just the main file.
        assert _count(result.pre_restore_copy) == SNAPSHOT_ROWS + POST_SNAPSHOT_ROWS

        revert_restore(result.pre_restore_copy, url=scenario["url"])
        assert _count(scenario["live"]) == SNAPSHOT_ROWS + POST_SNAPSHOT_ROWS

    def test_newest_snapshot_is_chosen_by_default(self, tmp_path):
        live = tmp_path / "orchestrator.db"
        _seed(live, 5, "live")
        backups = tmp_path / "backup"
        _snapshot(live, backups / "orchestrator-20260101-000000.db")
        _seed(live, 3, "extra", start=100)
        _snapshot(live, backups / "orchestrator-20260605-000000.db")

        assert [p.name for p in list_snapshots(f"sqlite:///{live}")][0] == (
            "orchestrator-20260605-000000.db"
        )
        result = restore_database(url=f"sqlite:///{live}")
        assert result.restored_from.name == "orchestrator-20260605-000000.db"
        assert _count(live) == 8


class TestRefusals:
    """Every refusal must leave the database exactly as it was."""

    def test_missing_snapshot(self, scenario):
        with pytest.raises(RestoreError, match="not found"):
            restore_database(source=scenario["live"].parent / "nope.db", url=scenario["url"])
        assert _count(scenario["live"]) == SNAPSHOT_ROWS + POST_SNAPSHOT_ROWS

    def test_corrupt_snapshot(self, scenario):
        bad = scenario["live"].parent / "backup" / "orchestrator-20990101-000000.db"
        bad.write_bytes(b"this is not a database" * 100)

        with pytest.raises(RestoreError, match="quick_check"):
            restore_database(source=bad, url=scenario["url"])
        assert _count(scenario["live"]) == SNAPSHOT_ROWS + POST_SNAPSHOT_ROWS

    def test_empty_snapshot_is_refused(self, tmp_path):
        live = tmp_path / "orchestrator.db"
        _seed(live, 5, "live")
        empty = tmp_path / "backup" / "orchestrator-20260101-000000.db"
        empty.parent.mkdir(parents=True, exist_ok=True)
        _seed(tmp_path / "scratch.db", 0, "none")
        _snapshot(tmp_path / "scratch.db", empty)

        with pytest.raises(RestoreError, match="no rows"):
            restore_database(source=empty, url=f"sqlite:///{live}")
        assert _count(live) == 5

    def test_no_snapshots_at_all(self, tmp_path):
        live = tmp_path / "orchestrator.db"
        _seed(live, 5, "live")

        with pytest.raises(RestoreError, match="No snapshots"):
            restore_database(url=f"sqlite:///{live}")
        assert _count(live) == 5

    def test_active_writer_blocks_the_restore(self, scenario):
        holder = sqlite3.connect(str(scenario["live"]))
        holder.execute("BEGIN IMMEDIATE")
        try:
            with pytest.raises(RestoreError, match="writing to the database"):
                restore_database(source=scenario["snapshot"], url=scenario["url"])
        finally:
            holder.rollback()
            holder.close()

    def test_force_overrides_the_writer_check(self, scenario):
        holder = sqlite3.connect(str(scenario["live"]))
        holder.execute("BEGIN IMMEDIATE")
        try:
            result = restore_database(source=scenario["snapshot"], url=scenario["url"], force=True)
            assert result.row_counts["signals"] == SNAPSHOT_ROWS
        finally:
            holder.rollback()
            holder.close()

    def test_non_sqlite_url_is_refused(self):
        with pytest.raises(RestoreError, match="not a file-backed"):
            restore_database(url="postgresql://localhost/app")


class TestListing:
    def test_describe_reports_contents_and_health(self, scenario):
        described = describe_snapshots(scenario["url"])

        assert len(described) == 1
        assert described[0]["healthy"] is True
        assert described[0]["row_counts"]["signals"] == SNAPSHOT_ROWS
        assert described[0]["size_bytes"] > 0
