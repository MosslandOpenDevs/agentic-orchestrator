"""The trend save loop must not hold the write lock, and must not lose the batch.

This is the same defect #4989 removed from ``signals/aggregator.py::_save_to_db``,
still alive in ``scheduler/tasks.py``'s trend writer, in a job that runs twelve
times a day. Two failures share one cause -- a transaction opened by
``TrendRepository.create()``'s flush and left open until after the loop:

**It held the one SQLite writer lock across network calls.** Each iteration
flushed a row and then awaited two translation round-trips before anything
committed, so the lock was held for the rest of the batch. The 30-minute signal
collector waits ``busy_timeout`` (30s) for that lock and then fails. Four
collection runs died this way in 2026-09, each at exactly HH:36:01 -- 30 seconds
after the save began.

**And a single failed write discarded everything.** SQLAlchemy locks a session
after a failed flush, so the ``except ... continue`` was not recovery: every
later row raised ``PendingRollbackError`` and the closing ``session.commit()``
failed with them, while ``saved_count`` went on reporting a number nobody had
stored.

Both are checked as behaviour rather than as source shape -- "there is a commit
inside the loop" is a property a refactor slides past, "another connection can
write while this loop is awaiting" is not.
"""

import sqlite3
from datetime import datetime

import pytest


@pytest.fixture
def wired(tmp_path, monkeypatch):
    """Drive the real ``_analyze_trends_async`` against a real SQLite file.

    Only the analyzer and the router are faked: everything about sessions,
    flushes, commits and the lock is the production path. The database has to
    be a file, not ``:memory:`` -- the failure under test is a file lock.
    """
    import agentic_orchestrator.db as db_pkg
    import agentic_orchestrator.llm as llm_pkg
    import agentic_orchestrator.trends as trends_pkg
    from agentic_orchestrator.db import connection as db_connection
    from agentic_orchestrator.db.connection import Database
    from agentic_orchestrator.db.repositories import SignalRepository
    from agentic_orchestrator.scheduler import tasks
    from agentic_orchestrator.trends.models import Trend, TrendAnalysis

    db_path = tmp_path / "orchestrator.db"
    database = Database(f"sqlite:///{db_path}")
    database.create_tables()
    monkeypatch.setattr(db_connection, "db", database)
    monkeypatch.setattr(db_pkg, "get_database", lambda: database)

    seed = database.get_session()
    SignalRepository(seed).create(
        {
            "id": "s-seed",
            "source": "rss",
            "category": "ai",
            "title": "A seed signal with a title long enough to pass validation",
            "url": "https://example.com/seed",
            "score": 1.0,
        }
    )
    seed.commit()
    seed.close()

    def _trend(i):
        return Trend(
            topic=f"Trend number {i}",
            keywords=[],
            score=float(10 - i),
            time_period="24h",
            sources=["rss"],
            article_count=1,
            sample_headlines=[],
            category="ai",
            summary=f"Summary {i}",
        )

    class FakeAnalyzer:
        def __init__(self, *a, **k):
            pass

        async def analyze_trends(self, items, period, max_trends=10):
            return TrendAnalysis(
                date=datetime(2026, 9, 10),
                period=period,
                trends=[_trend(i) for i in range(3)],
                raw_article_count=1,
                sources_analyzed=["rss"],
            )

    monkeypatch.setattr(trends_pkg, "TrendAnalyzer", FakeAnalyzer)
    monkeypatch.setattr(llm_pkg, "HybridLLMRouter", lambda *a, **k: object())
    return database, db_path, tasks


def _row_count(db_path, table="trends"):
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


class TestTheLockIsFreeWhileTheLoopAwaits:
    @pytest.mark.asyncio
    async def test_another_writer_is_not_blocked_during_translation(self, wired, monkeypatch):
        """The property production needed: someone else can write, mid-batch.

        Each translation await tries a real write from a *separate* connection
        with a 1-second timeout — a stand-in for the signal collector, which
        gets 30 and used to burn all of them. Every attempt that raises
        "database is locked" is recorded.
        """
        database, db_path, tasks = wired
        blocked = []

        async def _probe(text):
            probe = sqlite3.connect(str(db_path), timeout=1.0)
            try:
                probe.execute("BEGIN IMMEDIATE")
                probe.rollback()
            except sqlite3.OperationalError as e:
                blocked.append(str(e))
            finally:
                probe.close()
            return (text, None)

        monkeypatch.setattr(tasks, "_ensure_bilingual", _probe)
        monkeypatch.setattr(tasks, "_ensure_bilingual_name", _probe)

        await tasks._analyze_trends_async()

        # The loop must actually have run, or "nothing was blocked" is vacuous.
        assert _row_count(db_path) == 3
        assert blocked == [], blocked


class TestOneFailedWriteDoesNotDiscardTheBatch:
    @pytest.mark.asyncio
    async def test_the_rows_that_worked_are_still_there(self, wired, monkeypatch):
        """Fail the middle write; the other two must survive.

        Without the rollback, the failure poisons the session: row 3 raises
        PendingRollbackError, the closing commit raises too, and the table ends
        up with zero rows while the log claims otherwise.
        """
        database, db_path, tasks = wired

        async def _identity(text):
            return (text, None)

        monkeypatch.setattr(tasks, "_ensure_bilingual", _identity)
        monkeypatch.setattr(tasks, "_ensure_bilingual_name", _identity)

        from agentic_orchestrator.db.repositories import TrendRepository

        real_create = TrendRepository.create
        calls = {"n": 0}

        def _create(self, data):
            calls["n"] += 1
            if calls["n"] == 2:
                # A real flush failure, not a raise before the write: this has
                # to leave the session in the state the bug depended on.
                data = {**data, "period": None}  # period is NOT NULL
            return real_create(self, data)

        monkeypatch.setattr(TrendRepository, "create", _create)

        await tasks._analyze_trends_async()

        assert calls["n"] == 3, "the loop stopped early instead of continuing"
        assert _row_count(db_path) == 2

    @pytest.mark.asyncio
    async def test_a_total_loss_is_not_reported_at_info(self, wired, monkeypatch, caplog):
        """ "Saved 0 trends" at INFO is what a lost batch looked like."""
        database, db_path, tasks = wired

        async def _identity(text):
            return (text, None)

        monkeypatch.setattr(tasks, "_ensure_bilingual", _identity)
        monkeypatch.setattr(tasks, "_ensure_bilingual_name", _identity)

        from agentic_orchestrator.db.repositories import TrendRepository

        real_create = TrendRepository.create

        def _always_fail(self, data):
            return real_create(self, {**data, "period": None})

        monkeypatch.setattr(TrendRepository, "create", _always_fail)

        with caplog.at_level("WARNING"):
            await tasks._analyze_trends_async()

        assert _row_count(db_path) == 0
        assert any(
            "Saved NO trends" in record.message
            for record in caplog.records
            if record.levelname == "WARNING"
        ), [r.message for r in caplog.records]
