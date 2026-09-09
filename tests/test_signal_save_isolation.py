"""One failing signal must not take the collection run with it.

`_save_to_db` used to flush the whole batch into a single transaction and
catch per-signal exceptions inside the loop. Catching them is not the same as
recovering: SQLAlchemy locks a session after a failed flush, so the first
failure turned every remaining signal into `PendingRollbackError` and the
closing commit then discarded the entire run.

Production hit it four times in 2026-09 (09-02 06:36, 09-05 18:36, 09-06
12:36, 09-09 00:36 UTC) and nowhere in the retained signals logs before that
(they cover 2026-08-05 and 2026-08-10 onward) -- each at
HH:36:01, exactly `busy_timeout` after the save began, every one while the
6-hourly debate held the write lock. Each incident logged ~560 errors, all
naming the same signal, and stored nothing.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import OperationalError

from agentic_orchestrator.adapters.base import SignalData


@pytest.fixture
def aggregator(tmp_path, monkeypatch):
    import agentic_orchestrator.signals.aggregator as aggregator_module
    from agentic_orchestrator.db import connection as db_connection
    from agentic_orchestrator.db.connection import Database
    from agentic_orchestrator.signals.aggregator import SignalAggregator

    database = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
    database.create_tables()
    monkeypatch.setattr(db_connection, "db", database)
    monkeypatch.setattr(aggregator_module, "db", database)

    agg = SignalAggregator(adapters=[])
    agg._test_db = database
    return agg


def _signals(n: int):
    return [
        SignalData(
            source="rss",
            category="ai",
            title=f"Story number {i} about something specific",
            url=f"https://example.com/{i}",
        )
        for i in range(n)
    ]


def _stored(agg):
    from agentic_orchestrator.db.models import Signal

    session = agg._test_db.get_session()
    try:
        return {row.url for row in session.query(Signal).all()}
    finally:
        session.close()


def _fail_on_flush(monkeypatch, url: str):
    """Make this one signal fail *inside* the flush, as a real write error does.

    Raising from the repository before it touches the session would not
    reproduce the bug at all. It is the failed flush that locks the session,
    and that is precisely what turned one unwritable row into a lost run --
    so a test that raises early passes just as happily on the broken code.
    A NOT NULL violation on `title` fails where the real INSERT failed.
    """
    from agentic_orchestrator.db.repositories import SignalRepository

    real_create = SignalRepository.create

    def create(self, signal_data):
        if signal_data["url"] == url:
            signal_data = {**signal_data, "title": None}
        return real_create(self, signal_data)

    monkeypatch.setattr(SignalRepository, "create", create)


def _lock_on(monkeypatch, url: str):
    """Make this signal hit the 'database is locked' path."""
    from agentic_orchestrator.db.repositories import SignalRepository

    real_create = SignalRepository.create

    def create(self, signal_data):
        if signal_data["url"] == url:
            raise OperationalError("INSERT", {}, Exception("database is locked"))
        return real_create(self, signal_data)

    monkeypatch.setattr(SignalRepository, "create", create)


class TestOneBadRowDoesNotLoseTheRun:
    @pytest.mark.asyncio
    async def test_signals_after_the_failure_are_still_saved(self, aggregator, monkeypatch):
        """The whole point: the batch survives a row that cannot be written."""
        signals = _signals(6)
        _fail_on_flush(monkeypatch, "https://example.com/2")

        saved = await aggregator._save_to_db(signals)

        stored = _stored(aggregator)
        assert saved == 5
        assert stored == {f"https://example.com/{i}" for i in (0, 1, 3, 4, 5)}

    @pytest.mark.asyncio
    async def test_signals_before_the_failure_are_kept(self, aggregator, monkeypatch):
        """A rollback must discard the failed row, not its committed siblings."""
        signals = _signals(4)
        _fail_on_flush(monkeypatch, "https://example.com/3")

        await aggregator._save_to_db(signals)

        assert "https://example.com/0" in _stored(aggregator)

    @pytest.mark.asyncio
    async def test_the_run_does_not_raise(self, aggregator, monkeypatch):
        """It used to propagate out of the context manager and fail the task."""
        _fail_on_flush(monkeypatch, "https://example.com/0")

        await aggregator._save_to_db(_signals(3))


class TestDatabaseUnavailableStopsEarly:
    """A locked database is one answer for every remaining row, not N answers."""

    @pytest.mark.asyncio
    async def test_lock_contention_keeps_what_was_already_saved(self, aggregator, monkeypatch):
        signals = _signals(5)
        _lock_on(monkeypatch, "https://example.com/3")

        saved = await aggregator._save_to_db(signals)

        assert saved == 3
        assert _stored(aggregator) == {f"https://example.com/{i}" for i in (0, 1, 2)}

    @pytest.mark.asyncio
    async def test_it_does_not_retry_every_remaining_row(self, aggregator, monkeypatch):
        """Each retry re-pays busy_timeout for the same answer."""
        from agentic_orchestrator.db.repositories import SignalRepository

        attempts = []
        real_create = SignalRepository.create

        def create(self, signal_data):
            attempts.append(signal_data["url"])
            if signal_data["url"] == "https://example.com/1":
                raise OperationalError("INSERT", {}, Exception("database is locked"))
            return real_create(self, signal_data)

        monkeypatch.setattr(SignalRepository, "create", create)

        await aggregator._save_to_db(_signals(8))

        assert attempts == ["https://example.com/0", "https://example.com/1"]


class TestRevisionUpdatesAreCommittedToo:
    """The revision branch writes without going through repo.create().

    It is the only path that produces `updated_count`, it is the SignalMap
    revision path, and its commit is as load-bearing as the one on the create
    path: without it the refreshed row rides on the closing batch commit and
    dies with any later failure in the same run.
    """

    def _signalmap(self, revision: int, title: str):
        return SignalData(
            source="signalmap",
            category="ai",
            title=title,
            url="https://signalmap.moss.land/r/1",
            external_id="rec-1",
            raw_data={"revision": revision, "epoch": "e1"},
            metadata={"revision": revision, "epoch": "e1"},
        )

    @pytest.mark.asyncio
    async def test_a_revision_survives_a_later_failure_in_the_same_batch(
        self, aggregator, monkeypatch
    ):
        await aggregator._save_to_db([self._signalmap(1, "First writing of the record")])

        _fail_on_flush(monkeypatch, "https://example.com/0")
        await aggregator._save_to_db(
            [self._signalmap(2, "Revised writing of the same record"), _signals(1)[0]]
        )

        from agentic_orchestrator.db.models import Signal

        session = aggregator._test_db.get_session()
        try:
            stored = session.query(Signal).filter(Signal.source == "signalmap").one()
            assert stored.title == "Revised writing of the same record"
        finally:
            session.close()


class TestHealthyPathUnchanged:
    @pytest.mark.asyncio
    async def test_a_clean_batch_saves_every_row(self, aggregator):
        saved = await aggregator._save_to_db(_signals(5))

        assert saved == 5
        assert len(_stored(aggregator)) == 5

    @pytest.mark.asyncio
    async def test_a_signal_already_stored_is_not_rewritten(self, aggregator):
        await aggregator._save_to_db(_signals(3))

        saved = await aggregator._save_to_db(_signals(3))

        assert saved == 0
        assert len(_stored(aggregator)) == 3
