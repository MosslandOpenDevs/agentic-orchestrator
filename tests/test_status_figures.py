"""What the public figures on ``/status`` are allowed to mean.

Two failures live here, and neither one fails loudly.

The first is a window. ``signals_today`` counts from 00:00 UTC, which is 09:00
in Seoul, so for the first hours of a Korean working day it reports a number
near zero while ingestion is running perfectly. A consumer that renders it as
"24h" is not merely mislabelled — measured 2026-09-09 it showed 225 against
1,402 actually collected in the preceding day, and the shape of the error is
"the pipeline looks dead every morning".

The second is a partition. ``ideas_generated`` and ``plans_created`` are
lifetime counts over tables from which nothing is ever deleted, so they only
grow; rendered under the word "Active" they read 3,282 where 24 ideas were
actually open. A cumulative counter cannot answer a liveness question, which is
the Q2 report's own objection to them.

Both are fixed by *adding* fields, never by changing what an existing key means:
this endpoint is what the links.moss.land registry points at, and its readers
are not all enumerable from inside this repository.

``plans_created`` had one value corrected, and that is not a change of meaning:
the key still means "plans created". It had also been counting rows that were
never plans; rows with status ``placeholder`` are left out.
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

import agentic_orchestrator.api.main as api_main
from agentic_orchestrator.api.main import app
from agentic_orchestrator.db.connection import Database
from agentic_orchestrator.db.models import (
    NON_PLAN_STATUSES,
    OPEN_IDEA_STATUSES,
    OPEN_PLAN_STATUSES,
    DebateSession,
    Idea,
    Plan,
)
from agentic_orchestrator.timeutil import utcnow

# Every idea status any scheduled path actually writes, and which side of the
# partition it belongs on. "duplicate" is written by the debate cycle's
# clustering gate (scheduler/tasks.py) and is deliberately absent from the
# IdeaStatus enum, which is exactly why it is easy to forget here.
WRITTEN_IDEA_STATUSES = {
    "pending": "open",
    "scored": "open",
    "promoted": "decided",
    "archived": "decided",
    "duplicate": "decided",
}

# Three sides, not two: a placeholder is neither waiting nor decided, it is a
# row that was never a plan. Filing it under "decided" would pass an open/decided
# check while meaning the wrong thing.
WRITTEN_PLAN_STATUSES = {
    "draft": "open",
    "approved": "decided",
    "rejected": "decided",
    "placeholder": "not_a_plan",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = Database(f"sqlite:///{tmp_path / 'figures.db'}")
    db.create_tables()
    monkeypatch.setattr(api_main, "get_db", lambda: db)
    return TestClient(app), db


def _seed(db, *, signals=(), debates=(), ideas=(), plans=()):
    """Seed rows at explicit ages/statuses. Returns nothing; assertions read HTTP."""
    from agentic_orchestrator.db.models import Signal

    now = utcnow()
    session = db.get_session()
    for i, hours_ago in enumerate(signals):
        stamp = now - timedelta(hours=hours_ago)
        session.add(
            Signal(
                id=f"sig-{i}",
                source="rss",
                category="ai",
                title=f"Seeded signal {i} with a title long enough to look real",
                # Both clocks, or the test is not exercising the one it names:
                # created_at defaults to now, which would put every seeded row
                # inside the rolling window regardless of its age.
                collected_at=stamp,
                created_at=stamp,
            )
        )
    for i, hours_ago in enumerate(debates):
        session.add(
            DebateSession(
                id=f"deb-{i}",
                phase="divergence",
                topic=f"Seeded debate {i}",
                started_at=now - timedelta(hours=hours_ago),
            )
        )
    for i, status in enumerate(ideas):
        session.add(
            Idea(
                id=f"idea-{i}",
                title=f"Seeded idea {i}",
                summary="A seeded summary",
                source_type="debate",
                status=status,
            )
        )
    for i, status in enumerate(plans):
        session.add(Plan(id=f"plan-{i}", idea_id="idea-0", title=f"Seeded plan {i}", status=status))
    session.commit()
    session.close()


class TestTheRollingWindowIsRolling:
    def test_a_signal_from_before_utc_midnight_is_in_24h_but_not_today(self, client, monkeypatch):
        """The whole point: the two fields must be able to disagree.

        The clock is pinned just after UTC midnight, which is the moment the
        midnight-anchored figure is at its most misleading — and 09:00 in the
        timezone of the people who read the dashboard.
        """
        c, db = client
        just_after_midnight = utcnow().replace(hour=0, minute=5, second=0, microsecond=0)
        monkeypatch.setattr(api_main, "utcnow", lambda: just_after_midnight)

        # One signal 2 hours ago (yesterday, still inside the rolling window),
        # one 1 minute ago (today).
        session = db.get_session()
        from agentic_orchestrator.db.models import Signal

        session.add(
            Signal(
                id="yesterday",
                source="rss",
                category="ai",
                title="Collected before midnight but well within 24 hours",
                collected_at=just_after_midnight - timedelta(hours=2),
                created_at=just_after_midnight - timedelta(hours=2),
            )
        )
        session.add(
            Signal(
                id="today",
                source="rss",
                category="ai",
                title="Collected a minute into the new UTC day",
                collected_at=just_after_midnight - timedelta(minutes=1),
                created_at=just_after_midnight - timedelta(minutes=1),
            )
        )
        session.commit()
        session.close()

        stats = c.get("/status").json()["stats"]
        assert stats["signals_today"] == 1
        assert stats["signals_24h"] == 2

    def test_the_window_actually_ends(self, client):
        """A 25-hour-old row is in neither figure — this is a window, not a total."""
        c, db = client
        _seed(db, signals=(0.1, 5, 25))

        stats = c.get("/status").json()["stats"]
        assert stats["signals_24h"] == 2

    def test_the_rolling_window_measures_the_ingest_clock(self, client):
        """``signals_24h`` means the same thing here as it does on /adapters.

        The two columns come apart for exactly one source: SignalMap sets
        ``collected_at`` to the upstream event time, so a record about
        something that happened last week is ingested today. That is real
        ingest work, and a throughput figure measured on the publisher's clock
        would not see it at all. ``/adapters`` already made this choice; two
        endpoints publishing a field of the same name against different clocks
        is the defect this endpoint's change exists to end.
        """
        from agentic_orchestrator.db.models import Signal

        c, db = client
        now = utcnow()
        session = db.get_session()
        session.add(
            Signal(
                id="backfilled",
                source="signalmap",
                category="ai",
                title="An event from last week, ingested a minute ago",
                collected_at=now - timedelta(days=7),
                created_at=now - timedelta(minutes=1),
            )
        )
        session.commit()
        session.close()

        stats = c.get("/status").json()["stats"]
        assert stats["signals_24h"] == 1, "ingest happened; the throughput figure must see it"
        assert stats["signals_today"] == 0, "the event did not occur today; that field says so"

    def test_debates_have_the_same_pair(self, client, monkeypatch):
        c, db = client
        just_after_midnight = utcnow().replace(hour=0, minute=5, second=0, microsecond=0)
        monkeypatch.setattr(api_main, "utcnow", lambda: just_after_midnight)

        session = db.get_session()
        session.add(
            DebateSession(
                id="deb-yesterday",
                phase="divergence",
                topic="Started before midnight",
                started_at=just_after_midnight - timedelta(hours=3),
            )
        )
        session.commit()
        session.close()

        stats = c.get("/status").json()["stats"]
        assert stats["debates_today"] == 0
        assert stats["debates_24h"] == 1


class TestOpenIsNotTotal:
    def test_open_counts_exclude_every_decided_status(self, client):
        c, db = client
        _seed(
            db,
            ideas=("scored", "pending", "promoted", "archived", "duplicate"),
            plans=("draft", "approved", "rejected"),
        )

        stats = c.get("/status").json()["stats"]
        assert stats["ideas_generated"] == 5
        assert stats["ideas_open"] == 2
        assert stats["plans_created"] == 3
        assert stats["plans_open"] == 1

    def test_a_placeholder_is_neither_created_nor_open(self, client):
        """A placeholder row was never a plan, so no plan figure counts it.

        ``plans_open`` leaves it out through the partition alone;
        ``plans_created`` was a bare COUNT(*) and did not.
        """
        c, db = client
        _seed(db, ideas=("promoted",), plans=("draft", "approved", "rejected", "placeholder"))
        session = db.get_session()
        # Guard: the row is really there, so the figures below exclude it
        # rather than never seeing it.
        assert session.query(Plan).filter(Plan.status == "placeholder").count() == 1
        session.close()

        stats = c.get("/status").json()["stats"]
        assert stats["plans_created"] == 3
        assert stats["plans_open"] == 1

    def test_every_status_the_pipeline_writes_is_classified(self):
        """The partition must cover the vocabulary, not just the enum.

        ``duplicate`` is written by scheduler/tasks.py and is not an IdeaStatus
        member, so a partition derived from the enum alone would silently count
        it as open.
        """
        for status, side in WRITTEN_IDEA_STATUSES.items():
            assert (status in OPEN_IDEA_STATUSES) == (side == "open"), status
        for status, side in WRITTEN_PLAN_STATUSES.items():
            assert (status in OPEN_PLAN_STATUSES) == (side == "open"), status
            assert (status in NON_PLAN_STATUSES) == (side == "not_a_plan"), status
        assert not set(OPEN_PLAN_STATUSES) & set(NON_PLAN_STATUSES)

    def test_the_triage_queue_and_the_public_partition_agree(self):
        """Two deliberately separate tuples that must not drift apart unnoticed.

        They are not aliased: one is "what may triage consume", the other is
        "what is undecided", and coupling them would let a change to triage's
        appetite silently move a published figure. Order is irrelevant, and
        this asserts on sets so it cannot pass by accident of ordering.
        """
        from agentic_orchestrator.scheduler.backlog_triage import TRIAGE_STATUSES

        assert set(TRIAGE_STATUSES) == set(OPEN_IDEA_STATUSES)


class TestTheContractSurvives:
    def test_no_existing_key_disappeared(self, client):
        """Fields are added here, never renamed: external readers exist."""
        c, _ = client
        stats = c.get("/status").json()["stats"]
        for key in (
            "signals_today",
            "debates_today",
            "ideas_generated",
            "plans_created",
            "agents_active",
            "last_signal_at",
        ):
            assert key in stats, key

    def test_the_new_keys_are_zero_not_absent_when_degraded(self, tmp_path, monkeypatch):
        """0 is a measurement; a missing key is a parse error at the consumer.

        /status must answer 200 with zeroed stats when the database is broken —
        that is the documented degraded contract — and the new fields have to
        take part in it.
        """
        db_file = tmp_path / "empty.db"
        db_file.touch()
        monkeypatch.setattr(api_main, "get_db", lambda: Database(f"sqlite:///{db_file}"))
        body = TestClient(app).get("/status").json()

        assert body["status"] == "degraded"
        for key in ("signals_24h", "debates_24h", "ideas_open", "plans_open"):
            assert body["stats"][key] == 0, key


class TestPipelineLiveFindsARunningDebate:
    """``/pipeline/live`` filtered on a status string nothing has ever written.

    The scheduler writes ``"active"`` and ``DebateSessionStatus.ACTIVE`` is
    ``"active"``; the filter said ``"in-progress"``. It matched zero rows on
    every call, so the "processing now" list never mentioned a debate —
    including during the ~15 minutes every six hours when a debate is the only
    thing the system is doing. The frontend found and fixed its own copy of the
    same wrong literal; the backend kept it.
    """

    def test_an_active_debate_appears_in_processing(self, client):
        c, db = client
        session = db.get_session()
        session.add(
            DebateSession(
                id="running",
                phase="divergence",
                topic="A debate that is running right now",
                status="active",
                started_at=utcnow(),
            )
        )
        session.commit()
        session.close()

        processing = c.get("/pipeline/live").json()["processing"]
        assert any(item["type"] == "DEBATE" for item in processing), processing

    def test_an_orphaned_debate_does_not(self, client):
        """A SIGKILLed debate stays `active` until the next 6-hourly cycle.

        The rendered item carries no timestamp — `time_ago` is the round
        counter — so without a recency bound an orphan is indistinguishable
        from a live debate on a list headed "processing now". The bound is the
        same 90 minutes the debate task's own startup recovery sweep uses.
        This became reachable only when the status literal above was fixed.
        """
        c, db = client
        session = db.get_session()
        session.add(
            DebateSession(
                id="orphan",
                phase="divergence",
                topic="Killed hours ago, never marked failed",
                status="active",
                started_at=utcnow() - timedelta(hours=3),
            )
        )
        session.commit()
        session.close()

        processing = c.get("/pipeline/live").json()["processing"]
        assert not any(item["type"] == "DEBATE" for item in processing), processing

    def test_a_finished_debate_does_not(self, client):
        c, db = client
        session = db.get_session()
        session.add(
            DebateSession(
                id="done",
                phase="planning",
                topic="A debate that finished",
                status="completed",
                started_at=utcnow(),
            )
        )
        session.commit()
        session.close()

        processing = c.get("/pipeline/live").json()["processing"]
        assert not any(item["type"] == "DEBATE" for item in processing), processing
