"""The retention sweep must actually prune, and must not orphan provenance.

Ideas and Plans are never deleted and both reference the debate session (and,
for the migration-seeded path, the trend) they came from, with no ON DELETE
policy on either foreign key. The sweep used to delete parents unconditionally,
so with SQLite foreign keys on it raised `FOREIGN KEY constraint failed` --
and because both sweeps shared one transaction, retention pruned nothing at
all while logging one warning every four hours.
"""

from datetime import timedelta

import pytest

from agentic_orchestrator.db.connection import Database
from agentic_orchestrator.db.models import DebateMessage, DebateSession, Idea, Plan, Trend
from agentic_orchestrator.db.repositories import DebateRepository, TrendRepository
from agentic_orchestrator.timeutil import utcnow

OLD = 200  # days: comfortably past the 180-day retention window


@pytest.fixture
def session(tmp_path):
    """A real file database so SQLite's foreign key enforcement is live."""
    db = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
    db.create_tables()
    s = db.get_session()
    yield s
    s.close()


def _old_trend(session, trend_id: str) -> Trend:
    trend = Trend(
        id=trend_id,
        period="24h",
        name=f"Trend {trend_id}",
        score=1.0,
        analyzed_at=utcnow() - timedelta(days=OLD),
    )
    session.add(trend)
    return trend


def _old_session(session, session_id: str) -> DebateSession:
    debate = DebateSession(
        id=session_id,
        topic=f"Topic {session_id}",
        phase="divergence",
        started_at=utcnow() - timedelta(days=OLD),
    )
    session.add(debate)
    return debate


def _idea(session, idea_id: str, **links) -> Idea:
    idea = Idea(
        id=idea_id,
        title=f"Idea {idea_id}",
        summary="s",
        source_type="debate",
        **links,
    )
    session.add(idea)
    return idea


class TestTrendRetention:
    def test_unreferenced_old_trends_are_pruned(self, session):
        _old_trend(session, "t-free")
        session.commit()

        assert TrendRepository(session).delete_older_than(days=180) == 1
        session.commit()
        assert session.query(Trend).count() == 0

    def test_a_trend_an_idea_came_from_is_kept(self, session):
        _old_trend(session, "t-used")
        session.flush()
        _idea(session, "i-1", source_trend_id="t-used")
        session.commit()

        repo = TrendRepository(session)
        assert repo.delete_older_than(days=180) == 0
        session.commit()

        assert session.query(Trend).count() == 1
        assert repo.count_older_than_still_referenced(days=180) == 1

    def test_referenced_trend_does_not_block_the_others(self, session):
        _old_trend(session, "t-used")
        _old_trend(session, "t-free")
        session.flush()
        _idea(session, "i-1", source_trend_id="t-used")
        session.commit()

        assert TrendRepository(session).delete_older_than(days=180) == 1
        session.commit()
        assert [t.id for t in session.query(Trend).all()] == ["t-used"]


class TestDebateSessionRetention:
    def test_unreferenced_old_sessions_and_messages_are_pruned(self, session):
        _old_session(session, "d-free")
        session.flush()
        session.add(
            DebateMessage(
                id="m-1",
                session_id="d-free",
                agent_id="a",
                agent_name="A",
                message_type="initial_idea",
                content="hi",
            )
        )
        session.commit()

        assert DebateRepository(session).delete_older_than(days=180) == 1
        session.commit()
        assert session.query(DebateSession).count() == 0
        assert session.query(DebateMessage).count() == 0

    def test_a_session_an_idea_came_from_is_kept(self, session):
        _old_session(session, "d-used")
        session.flush()
        _idea(session, "i-1", debate_session_id="d-used")
        session.commit()

        repo = DebateRepository(session)
        assert repo.delete_older_than(days=180) == 0
        session.commit()

        assert session.query(DebateSession).count() == 1
        assert repo.count_older_than_still_referenced(days=180) == 1

    def test_a_session_a_plan_came_from_is_kept(self, session):
        _old_session(session, "d-used")
        session.flush()
        _idea(session, "i-1")
        session.flush()
        session.add(Plan(id="p-1", idea_id="i-1", title="Plan", debate_session_id="d-used"))
        session.commit()

        assert DebateRepository(session).delete_older_than(days=180) == 0
        session.commit()
        assert session.query(DebateSession).count() == 1

    def test_referenced_session_does_not_block_the_others(self, session):
        """The whole point: one referenced parent used to abort the sweep."""
        _old_session(session, "d-used")
        _old_session(session, "d-free")
        session.flush()
        _idea(session, "i-1", debate_session_id="d-used")
        session.commit()

        assert DebateRepository(session).delete_older_than(days=180) == 1
        session.commit()
        assert [d.id for d in session.query(DebateSession).all()] == ["d-used"]

    def test_recent_sessions_are_untouched(self, session):
        session.add(
            DebateSession(id="d-new", topic="fresh", phase="divergence", started_at=utcnow())
        )
        session.commit()

        assert DebateRepository(session).delete_older_than(days=180) == 0
        session.commit()
        assert session.query(DebateSession).count() == 1
