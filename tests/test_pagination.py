"""Tests for DB-level pagination and the N+1 message-count fix (PR2 backend hardening).

These cover the behavior changed in the backend-hardening pass:
- /trends and /ideas?status= paginate at the SQL layer (offset/limit pushed into
  the query) and report `total` from a COUNT, not the page size.
- DebateSession message counts come from a single bulk COUNT...GROUP BY query
  instead of lazy-loading each session's messages (the former N+1).
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.models import Base, DebateMessage, DebateSession, Idea, Trend
from agentic_orchestrator.db.repositories import DebateRepository


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Local = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # noqa: N806
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        s = Local()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = override_get_session
    s = Local()
    yield s
    s.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    return TestClient(app)


def _add_trends(db, n, period="24h", category="crypto"):
    base = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(n):
        db.add(
            Trend(
                period=period,
                name=f"Trend {i}",
                description="d",
                score=float(i),
                signal_count=1,
                category=category,
                analyzed_at=base + timedelta(minutes=i),
            )
        )
    db.commit()


class TestTrendPagination:
    def test_offset_pages_do_not_overlap(self, client, db):
        _add_trends(db, 5)
        page1 = client.get("/trends?period=all&limit=2&offset=0").json()
        page2 = client.get("/trends?period=all&limit=2&offset=2").json()
        assert page1["total"] == 5
        assert page2["total"] == 5
        assert len(page1["trends"]) == 2
        assert len(page2["trends"]) == 2
        names1 = {t["name"] for t in page1["trends"]}
        names2 = {t["name"] for t in page2["trends"]}
        assert names1.isdisjoint(names2)

    def test_category_total_is_count_not_page_size(self, client, db):
        _add_trends(db, 4, category="crypto")
        _add_trends(db, 1, category="ai")
        body = client.get("/trends?category=crypto&limit=2&offset=0").json()
        assert body["total"] == 4  # full category count, not the 2 returned
        assert len(body["trends"]) == 2

    def test_period_total_is_count(self, client, db):
        _add_trends(db, 3, period="7d")
        body = client.get("/trends?period=7d&limit=1&offset=0").json()
        assert body["total"] == 3
        assert len(body["trends"]) == 1


class TestIdeaStatusPagination:
    def test_status_offset_slices_at_db_level(self, client, db):
        for i in range(5):
            db.add(
                Idea(
                    title=f"Idea {i}",
                    summary="s",
                    source_type="trend_based",
                    status="pending",
                    score=1.0,
                )
            )
        db.commit()
        page1 = client.get("/ideas?status=pending&limit=2&offset=0").json()
        page2 = client.get("/ideas?status=pending&limit=2&offset=2").json()
        assert page1["total"] == 5
        assert len(page1["ideas"]) == 2
        ids1 = {i["id"] for i in page1["ideas"]}
        ids2 = {i["id"] for i in page2["ideas"]}
        assert ids1.isdisjoint(ids2)


class TestMessageCountNoNPlusOne:
    def _make_sessions(self, db, counts):
        """Create sessions, each with `counts[i]` messages. Returns the sessions."""
        sessions = []
        for _ in counts:
            s = DebateSession(
                phase="divergence",
                round_number=1,
                max_rounds=3,
                status="completed",
            )
            db.add(s)
            db.commit()
            sessions.append(s)
        for s, c in zip(sessions, counts, strict=True):
            for _ in range(c):
                db.add(
                    DebateMessage(
                        session_id=s.id,
                        agent_id="a",
                        agent_name="A",
                        message_type="propose",
                        content="c",
                    )
                )
        db.commit()
        return sessions

    def test_bulk_count_matches_and_omits_zero(self, db):
        sessions = self._make_sessions(db, [2, 0, 1])
        repo = DebateRepository(db)
        counts = repo.count_messages_for_sessions([s.id for s in sessions])
        assert counts.get(sessions[0].id) == 2
        assert sessions[1].id not in counts  # zero-message sessions are absent
        assert counts.get(sessions[2].id) == 1

    def test_bulk_count_empty_input(self, db):
        repo = DebateRepository(db)
        assert repo.count_messages_for_sessions([]) == {}

    def test_debates_endpoint_reports_message_count(self, client, db):
        sessions = self._make_sessions(db, [3])
        body = client.get("/debates").json()
        target = next(d for d in body["debates"] if d["id"] == sessions[0].id)
        assert target["message_count"] == 3

    def test_idea_detail_nested_debate_message_count(self, client, db):
        """Regression: /ideas/{id} serializes nested debates; their message_count
        must reflect the loaded messages, not default to 0."""
        idea = Idea(
            title="Idea with debate",
            summary="s",
            source_type="debate",
            status="promoted",
            score=8.0,
        )
        db.add(idea)
        db.commit()
        sess = DebateSession(
            idea_id=idea.id,
            phase="planning",
            round_number=1,
            max_rounds=3,
            status="completed",
        )
        db.add(sess)
        db.commit()
        for _ in range(2):
            db.add(
                DebateMessage(
                    session_id=sess.id,
                    agent_id="a",
                    agent_name="A",
                    message_type="propose",
                    content="c",
                )
            )
        db.commit()
        body = client.get(f"/ideas/{idea.id}").json()
        assert len(body["debates"]) >= 1
        nested = body["debates"][0]
        assert nested["message_count"] == 2
        assert len(nested["messages"]) == 2
