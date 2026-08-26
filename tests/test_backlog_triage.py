"""Tests for backlog triage — the consumer that matches idea production.

Before triage, ~85% of debate ideas landed in ``scored`` and nothing ever
touched them again: production had no consumer, so the backlog (and its
GitHub mirror) only grew. These tests pin the triage contract: every touched
idea moves toward a terminal state (promoted|archived) within ``max_strikes``
touches, oldest ideas drain first, fresh ideas are left alone, and an LLM
outage never hands out strikes.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_orchestrator.db.models import Base
from agentic_orchestrator.db.repositories import (
    IdeaRepository,
    PlanRepository,
    TrendRepository,
)
from agentic_orchestrator.scheduler.backlog_triage import run_backlog_triage

NOW = datetime(2026, 8, 5, 12, 0, 0)


@dataclass
class FakeScore:
    total: float
    feasibility: float = 6.0
    relevance: float = 6.0
    novelty: float = 6.0
    impact: float = 6.0
    reasoning: str = "test verdict"


# The scorer's transport-error fallback: flat 5.0 with no reasoning.
FALLBACK_SCORE = FakeScore(
    total=5.0, feasibility=5.0, relevance=5.0, novelty=5.0, impact=5.0, reasoning=""
)


class FakeScorer:
    """Scripted scorer: maps a title substring to (score, decision)."""

    def __init__(self, script=None, raise_for=()):
        self.script = script or {}
        self.raise_for = set(raise_for)
        self.calls = []

    async def score_and_decide(self, idea_content, context=""):
        self.calls.append(idea_content)
        for key in self.raise_for:
            if key in idea_content:
                raise RuntimeError("boom")
        for key, verdict in self.script.items():
            if key in idea_content:
                return verdict
        return FakeScore(total=5.5), "pending"


@pytest.fixture()
def repos():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield (
        IdeaRepository(session),
        PlanRepository(session),
        TrendRepository(session),
        session,
    )
    session.close()


def make_idea(
    idea_repo,
    session,
    idea_id,
    title,
    status="scored",
    age_days=3,
    extra_metadata=None,
    github_issue_id=None,
):
    idea = idea_repo.create(
        {
            "id": idea_id,
            "title": title,
            "summary": f"summary of {title}",
            "source_type": "debate",
            "status": status,
            "score": 5.0,
            "extra_metadata": extra_metadata,
            "github_issue_id": github_issue_id,
        }
    )
    idea.created_at = NOW - timedelta(days=age_days)
    # Commit like production does: triage candidates are always committed
    # rows, and triage's per-idea rollback must not be able to undo them.
    session.commit()
    return idea


def triage(idea_repo, plan_repo, trend_repo, scorer, config=None, reviewer=None):
    return asyncio.run(
        run_backlog_triage(
            idea_repo=idea_repo,
            plan_repo=plan_repo,
            trend_repo=trend_repo,
            scorer=scorer,
            config=config,
            now=NOW,
            reviewer=reviewer,
        )
    )


class TestDecisions:
    def test_promote_creates_draft_plan(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "great idea")
        scorer = FakeScorer({"great idea": (FakeScore(total=8.2), "promote")})

        stats = triage(idea_repo, plan_repo, trend_repo, scorer)

        assert stats["promoted"] == 1
        idea = idea_repo.get_by_id("i1")
        assert idea.status == "promoted"
        assert idea.score == 8.2
        assert idea.extra_metadata["triage"]["last_decision"] == "promote"
        plans = plan_repo.get_by_idea("i1")
        assert len(plans) == 1
        assert plans[0].status == "draft"  # human approval required, never auto
        assert plans[0].github_issue_id is None  # no new mirror issue
        assert plans[0].extra_metadata["promoted_by"] == "backlog_triage"

    def test_archive_records_verdict(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "weak idea")
        scorer = FakeScorer({"weak idea": (FakeScore(total=2.5), "archive")})

        stats = triage(idea_repo, plan_repo, trend_repo, scorer)

        assert stats["archived"] == 1
        idea = idea_repo.get_by_id("i1")
        assert idea.status == "archived"
        triage_record = idea.extra_metadata["triage"]
        assert triage_record["last_score"] == 2.5
        assert "reason" in triage_record
        assert plan_repo.get_by_idea("i1") == []

    def test_middle_band_strikes_then_strikes_out(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "meh idea")
        scorer = FakeScorer({"meh idea": (FakeScore(total=5.5), "pending")})

        first = triage(idea_repo, plan_repo, trend_repo, scorer, {"max_strikes": 2})
        assert first["strikes"] == 1
        idea = idea_repo.get_by_id("i1")
        assert idea.status == "scored"  # still in the backlog after one strike
        assert idea.extra_metadata["triage"]["strikes"] == 1

        second = triage(idea_repo, plan_repo, trend_repo, scorer, {"max_strikes": 2})
        assert second["strike_outs"] == 1
        idea = idea_repo.get_by_id("i1")
        assert idea.status == "archived"  # terminal within max_strikes touches
        assert idea.extra_metadata["triage"]["strikes"] == 2
        assert "never reached promotion" in idea.extra_metadata["triage"]["reason"]

    def test_triage_record_preserves_existing_metadata(self, repos):
        # The JSON column is replaced wholesale on write — a careless triage
        # record must not clobber the debate-time auto_score audit trail.
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(
            idea_repo,
            session,
            "i1",
            "meh idea",
            extra_metadata={"auto_score": {"total": 5.0}, "debate_topic": "T"},
        )
        scorer = FakeScorer({"meh idea": (FakeScore(total=5.5), "pending")})

        triage(idea_repo, plan_repo, trend_repo, scorer)

        idea = idea_repo.get_by_id("i1")
        assert idea.extra_metadata["auto_score"] == {"total": 5.0}
        assert idea.extra_metadata["debate_topic"] == "T"
        assert idea.extra_metadata["triage"]["strikes"] == 1

    def test_scorer_fallback_gives_no_strike(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "any idea")
        scorer = FakeScorer({"any idea": (FALLBACK_SCORE, "pending")})

        stats = triage(idea_repo, plan_repo, trend_repo, scorer)

        assert stats["scorer_unavailable"] == 1
        assert stats["strikes"] == 0
        idea = idea_repo.get_by_id("i1")
        assert idea.status == "scored"
        assert not (idea.extra_metadata or {}).get("triage")

    def test_sustained_scorer_outage_aborts_the_run(self, repos):
        """2026-08-06: a wedged Ollama failed every scoring call, and triage
        ground through its whole quota one dead call at a time — consuming
        nothing while holding moss-ao-backlog "online" long enough to block
        every back-end deploy. A sustained outage must end the run early."""
        idea_repo, plan_repo, trend_repo, session = repos
        for n in range(10):
            make_idea(idea_repo, session, f"i{n}", f"idea {n}", age_days=10 - n)
        scorer = FakeScorer()  # every call returns the flat-5.0 fallback
        scorer.script = {"idea": (FALLBACK_SCORE, "pending")}

        stats = triage(
            idea_repo, plan_repo, trend_repo, scorer, {"max_consecutive_scorer_failures": 3}
        )

        assert stats["aborted"] == 1
        assert stats["scorer_unavailable"] == 3
        assert len(scorer.calls) == 3, "must stop calling a backend that is down"
        assert stats["examined"] == 3

    def test_an_isolated_hiccup_does_not_abort_the_run(self, repos):
        """The breaker counts consecutive failures, not cumulative ones.

        Two failures SEPARATED by a success, against a threshold of 2: a
        cumulative counter trips here and a consecutive one does not, so this
        fails if the reset is ever dropped. (An earlier version of this test
        used a single failure, which a cumulative counter also survives — it
        pinned nothing.)
        """
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "flaky alpha", age_days=9)
        make_idea(idea_repo, session, "i2", "solid beta", age_days=8)
        make_idea(idea_repo, session, "i3", "flaky gamma", age_days=7)
        make_idea(idea_repo, session, "i4", "solid delta", age_days=6)
        scorer = FakeScorer(
            {
                "flaky alpha": (FALLBACK_SCORE, "pending"),
                "flaky gamma": (FALLBACK_SCORE, "pending"),
                "solid beta": (FakeScore(total=2.0), "archive"),
                "solid delta": (FakeScore(total=2.0), "archive"),
            }
        )

        stats = triage(
            idea_repo, plan_repo, trend_repo, scorer, {"max_consecutive_scorer_failures": 2}
        )

        assert stats["aborted"] == 0
        assert stats["examined"] == 4, "the run must reach every candidate"
        assert stats["scorer_unavailable"] == 2
        assert stats["archived"] == 2

    def test_a_responding_backend_means_the_ideas_are_poison_not_the_gpu(self, repos):
        """The breaker must not fire on unscoreable ideas.

        `score_idea` catches a per-idea parse failure and returns the SAME
        flat 5.0 with no reasoning that a dead transport does, and the
        fallback branch writes nothing to the row. Triage takes the oldest
        first, so aborting on three unscoreable head-of-queue ideas would
        abort every future run at the same three and the backlog would never
        drain again. When the probe says the backend is alive, the run
        continues and the rest of the quota is consumed.
        """
        idea_repo, plan_repo, trend_repo, session = repos
        for n in range(3):
            make_idea(idea_repo, session, f"p{n}", f"poison {n}", age_days=10 - n)
        make_idea(idea_repo, session, "good", "healthy idea", age_days=5)

        class LiveRouter:
            def __init__(self):
                self.probes = 0

            async def route(self, **kwargs):
                self.probes += 1
                return object()

        scorer = FakeScorer(
            {
                "poison": (FALLBACK_SCORE, "pending"),
                "healthy idea": (FakeScore(total=2.0), "archive"),
            }
        )
        scorer.router = LiveRouter()

        stats = triage(
            idea_repo, plan_repo, trend_repo, scorer, {"max_consecutive_scorer_failures": 3}
        )

        assert stats["aborted"] == 0, "a responding backend must not abort the run"
        assert stats["probe_cleared"] == 1
        assert scorer.router.probes == 1, "probe once, not per idea"
        assert stats["examined"] == 4
        assert stats["archived"] == 1, "the reachable idea must still be decided"
        session.expire_all()
        assert idea_repo.get_by_id("good").status == "archived"

    def test_a_dead_backend_still_aborts_when_the_probe_also_fails(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        for n in range(8):
            make_idea(idea_repo, session, f"i{n}", f"idea {n}", age_days=10 - n)

        class DeadRouter:
            def __init__(self):
                self.probes = 0

            async def route(self, **kwargs):
                self.probes += 1
                raise RuntimeError("Ollama timeout")

        scorer = FakeScorer({"idea": (FALLBACK_SCORE, "pending")})
        scorer.router = DeadRouter()

        stats = triage(
            idea_repo, plan_repo, trend_repo, scorer, {"max_consecutive_scorer_failures": 3}
        )

        assert stats["aborted"] == 1
        assert scorer.router.probes == 1
        assert stats["examined"] == 3
        assert len(scorer.calls) == 3

    def test_garbage_triage_config_falls_back_instead_of_raising(self, repos):
        """run_backlog_triage promises never to raise; the defaults merge only
        fills ABSENT keys, so a null/typo'd value must not take the run down."""
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "weak idea")
        scorer = FakeScorer({"weak idea": (FakeScore(total=2.0), "archive")})

        stats = triage(
            idea_repo,
            plan_repo,
            trend_repo,
            scorer,
            {
                "per_run": None,
                "max_strikes": "two",
                "max_consecutive_scorer_failures": None,
                "min_age_hours": "soon",
            },
        )

        assert stats["archived"] == 1
        assert stats["errors"] == 0

    def test_error_on_one_idea_does_not_stop_or_undo_the_rest(self, repos):
        # The succeeding idea is OLDER, so it is processed and committed
        # BEFORE the failure — the later rollback must not undo it. This is
        # the per-idea-commit pin: batching commits to the end of the run
        # would roll the first decision back with the failed one.
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "weak idea", age_days=5)
        make_idea(idea_repo, session, "i2", "explosive idea", age_days=4)
        scorer = FakeScorer(
            {"weak idea": (FakeScore(total=2.0), "archive")},
            raise_for=["explosive idea"],
        )

        stats = triage(idea_repo, plan_repo, trend_repo, scorer)

        assert stats["errors"] == 1
        assert stats["archived"] == 1
        session.expire_all()  # read committed DB state, not identity-map leftovers
        assert idea_repo.get_by_id("i1").status == "archived"
        assert idea_repo.get_by_id("i2").status == "scored"


class TestRealScorerShape:
    """Pin the fallback detector against the REAL IdeaScore, not the double.

    The FakeScore double above carries a ``reasoning`` field; if the real
    IdeaScore ever loses it (it did not have one originally), the detector's
    reasoning clause becomes vacuously true and every genuine flat-5.0
    verdict is misclassified as an LLM outage. This test fails in that
    world; the FakeScore-based tests alone do not.
    """

    def test_real_ideascore_discriminates_fallback_from_verdict(self):
        from agentic_orchestrator.scheduler.backlog_triage import _is_scorer_fallback
        from agentic_orchestrator.scoring import IdeaScore

        transport_fallback = IdeaScore(feasibility=5.0, relevance=5.0, novelty=5.0, impact=5.0)
        assert transport_fallback.reasoning == ""  # fallback paths use the default
        assert _is_scorer_fallback(transport_fallback) is True

        genuine_mediocre = IdeaScore(
            feasibility=5.0,
            relevance=5.0,
            novelty=5.0,
            impact=5.0,
            reasoning="평범한 아이디어 — 모든 축에서 중간 수준.",
        )
        assert _is_scorer_fallback(genuine_mediocre) is False

    def test_parse_carries_reasoning_through(self):
        from agentic_orchestrator.scoring import IdeaScorer

        score = IdeaScorer()._parse_score_response(
            '{"feasibility": 5, "relevance": 5, "novelty": 5, "impact": 5,'
            ' "reasoning": "solid but unremarkable"}'
        )
        assert score.reasoning == "solid but unremarkable"


class TestSelection:
    def test_fresh_ideas_are_left_alone(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "fresh idea", age_days=0)
        scorer = FakeScorer()

        stats = triage(idea_repo, plan_repo, trend_repo, scorer, {"min_age_hours": 24})

        assert stats["examined"] == 0
        assert scorer.calls == []

    def test_quota_drains_oldest_first(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        # Insertion order deliberately differs from age order — with rows
        # inserted old->new, SQLite's natural rowid order coincides with
        # created_at and losing the ORDER BY would go unnoticed.
        make_idea(idea_repo, session, "mid", "middle idea", age_days=5)
        make_idea(idea_repo, session, "new", "newest idea", age_days=2)
        make_idea(idea_repo, session, "old", "oldest idea", age_days=10)
        scorer = FakeScorer()

        stats = triage(idea_repo, plan_repo, trend_repo, scorer, {"per_run": 2})

        assert stats["examined"] == 2
        assert "oldest idea" in scorer.calls[0]
        assert "middle idea" in scorer.calls[1]

    def test_terminal_statuses_are_never_reevaluated(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "done idea", status="promoted")
        make_idea(idea_repo, session, "i2", "dead idea", status="archived")
        legacy = make_idea(idea_repo, session, "i3", "legacy idea", status="pending")
        scorer = FakeScorer({"legacy idea": (FakeScore(total=2.0), "archive")})

        stats = triage(idea_repo, plan_repo, trend_repo, scorer)

        assert stats["examined"] == 1  # only the legacy 'pending' row drains
        assert idea_repo.get_by_id(legacy.id).status == "archived"
        assert idea_repo.get_by_id("i1").status == "promoted"
        assert idea_repo.get_by_id("i2").status == "archived"

    def test_disabled_is_a_noop(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "any idea")
        scorer = FakeScorer()

        stats = triage(idea_repo, plan_repo, trend_repo, scorer, {"enabled": False})

        assert stats["examined"] == 0
        assert scorer.calls == []


class TestSecondPassGatesTriagePromotion:
    """Triage promotes far more than debates do; it needs the same gate.

    Until v0.6.24 the second pass covered the debate path only, while triage
    — 25 ideas every 4 hours — kept promoting on the local score alone. The
    local scorer is the one that returned exactly 8.00 for sixteen
    consecutive ideas in the 2026-08-06 live run.
    """

    def _reviewer(self, verdict, score=6.5):
        from agentic_orchestrator.scoring import second_pass as sp

        class Fixed(sp.SecondPassReviewer):
            def __init__(self):
                super().__init__(router=None, config={"max_reviews_per_cycle": 50})
                self.seen = []

            def should_review(self, local_score):
                return local_score >= 7.0 and self.reviews_used < 50

            async def review(self, title, content, local_score, context="", siblings=None):
                self.seen.append(title)
                if verdict == sp.UNAVAILABLE:
                    return sp.ReviewVerdict(sp.UNAVAILABLE, reason="stub outage")
                self.reviews_used += 1
                return sp.ReviewVerdict(verdict, reason="stub", score=score)

        return Fixed()

    def test_confirm_lets_the_promotion_through(self, repos):
        from agentic_orchestrator.scoring import second_pass as sp

        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "great idea")
        scorer = FakeScorer({"great idea": (FakeScore(total=8.2), "promote")})
        reviewer = self._reviewer(sp.CONFIRM, score=8.0)

        stats = triage(idea_repo, plan_repo, trend_repo, scorer, reviewer=reviewer)

        assert stats["promoted"] == 1
        assert idea_repo.get_by_id("i1").status == "promoted"
        assert reviewer.seen  # it really was reviewed

    def test_demote_holds_the_idea_and_counts_a_strike(self, repos):
        from agentic_orchestrator.scoring import second_pass as sp

        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "great idea")
        scorer = FakeScorer({"great idea": (FakeScore(total=8.2), "promote")})

        stats = triage(idea_repo, plan_repo, trend_repo, scorer, reviewer=self._reviewer(sp.DEMOTE))

        assert stats["promoted"] == 0
        assert stats["strikes"] == 1  # a real verdict still drives convergence
        assert idea_repo.get_by_id("i1").status == "scored"
        assert plan_repo.get_by_idea("i1") == []

    def test_reject_archives(self, repos):
        from agentic_orchestrator.scoring import second_pass as sp

        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "great idea")
        scorer = FakeScorer({"great idea": (FakeScore(total=8.2), "promote")})

        stats = triage(idea_repo, plan_repo, trend_repo, scorer, reviewer=self._reviewer(sp.REJECT))

        assert stats["archived"] == 1
        assert idea_repo.get_by_id("i1").status == "archived"

    def test_an_unavailable_reviewer_neither_promotes_nor_strikes(self, repos):
        # An outage must not promote unvetted ideas, and must not archive
        # them by attrition either. Same contract as the scorer fallback.
        from agentic_orchestrator.scoring import second_pass as sp

        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "great idea")
        scorer = FakeScorer({"great idea": (FakeScore(total=8.2), "promote")})

        stats = triage(
            idea_repo, plan_repo, trend_repo, scorer, reviewer=self._reviewer(sp.UNAVAILABLE)
        )

        assert stats["promoted"] == 0
        assert stats["strikes"] == 0
        assert stats["review_unavailable"] == 1
        idea = idea_repo.get_by_id("i1")
        assert idea.status == "scored"
        assert not (idea.extra_metadata or {}).get("triage")  # untouched

    def test_archive_and_strike_paths_do_not_need_a_review(self, repos):
        # Only promotions are gated — paying to review a rejection is waste.
        from agentic_orchestrator.scoring import second_pass as sp

        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "weak idea")
        scorer = FakeScorer({"weak idea": (FakeScore(total=2.0), "archive")})
        reviewer = self._reviewer(sp.CONFIRM)

        stats = triage(idea_repo, plan_repo, trend_repo, scorer, reviewer=reviewer)

        assert stats["archived"] == 1
        assert reviewer.seen == []

    def test_running_without_a_reviewer_warns(self, repos, caplog):
        idea_repo, plan_repo, trend_repo, session = repos
        make_idea(idea_repo, session, "i1", "any idea")

        with caplog.at_level("WARNING"):
            triage(idea_repo, plan_repo, trend_repo, FakeScorer())

        assert any("WITHOUT a second-pass reviewer" in r.message for r in caplog.records)


class TestTheReviewAllowanceIsTheRealQuota:
    """`per_run` is an upper bound; the decisive quota is the review allowance.

    Promotion needs a second-pass verdict, and the local scorer proposes
    promotion for very nearly everything it sees — measured on production, all
    25 candidates of a full cycle wanted review while only 20 could have one.
    The loop used to discover that one idea at a time, paying a local scoring
    call for each and discarding the result: exactly `per_run -
    max_reviews_per_cycle` wasted scorings per full cycle, six times a day, on
    a GPU shared with two other services. The pattern was deterministic in the
    logs — `examined=25` always produced `held=5`.

    Stopping early is safe because the feed is oldest-first: the untouched
    tail keeps its place and is examined first next cycle. Measured over 269
    held ideas, only three were ever held in a second cycle.
    """

    @staticmethod
    def _reviewer(allowance):
        """A reviewer that always demotes, so only the allowance limits it."""
        from agentic_orchestrator.scoring import second_pass as sp

        class Demoter(sp.SecondPassReviewer):
            def __init__(self):
                super().__init__(router=None, config={"max_reviews_per_cycle": allowance})

            async def review(self, title, content, local_score, context="", siblings=None):
                self.reviews_used += 1
                return sp.ReviewVerdict(sp.DEMOTE, reason="stub", score=6.0)

        return Demoter()

    @staticmethod
    def _six_candidates(idea_repo, session):
        for n in range(6):
            make_idea(idea_repo, session, f"i{n}", f"idea {n}", age_days=10 - n)

    def test_the_run_stops_once_the_allowance_is_spent(self, repos):
        idea_repo, plan_repo, trend_repo, session = repos
        self._six_candidates(idea_repo, session)
        scorer = FakeScorer({"idea": (FakeScore(total=8.0), "promote")})
        reviewer = self._reviewer(allowance=2)

        stats = triage(
            idea_repo,
            plan_repo,
            trend_repo,
            scorer,
            config={"per_run": 6, "min_age_hours": 0},
            reviewer=reviewer,
        )

        assert reviewer.reviews_used == 2
        assert stats["examined"] == 2
        assert stats["deferred"] == 4
        assert len(scorer.calls) == 2, "the local scorer was paid for work that was discarded"

    def test_the_deferred_tail_is_examined_first_next_cycle(self, repos):
        """Why stopping does not strand anything: the feed is oldest-first, so
        what was skipped is still the oldest thing there is."""
        idea_repo, plan_repo, trend_repo, session = repos
        self._six_candidates(idea_repo, session)
        scorer = FakeScorer({"idea": (FakeScore(total=8.0), "promote")})

        first = triage(
            idea_repo,
            plan_repo,
            trend_repo,
            scorer,
            config={"per_run": 6, "min_age_hours": 0, "max_strikes": 1},
            reviewer=self._reviewer(allowance=2),
        )
        seen_first = list(scorer.calls)
        scorer.calls.clear()
        second = triage(
            idea_repo,
            plan_repo,
            trend_repo,
            scorer,
            config={"per_run": 6, "min_age_hours": 0, "max_strikes": 1},
            reviewer=self._reviewer(allowance=2),
        )

        assert first["deferred"] == 4
        # Cycle 1 struck out its two (max_strikes=1 -> archived), so cycle 2
        # opens on what cycle 1 never reached.
        assert "idea 2" in scorer.calls[0]
        assert all("idea 2" not in c for c in seen_first)
        assert second["examined"] == 2

    def test_a_generous_allowance_lets_the_whole_quota_through(self, repos):
        """The stop is a consequence of the two knobs, not a new cap."""
        idea_repo, plan_repo, trend_repo, session = repos
        self._six_candidates(idea_repo, session)
        scorer = FakeScorer({"idea": (FakeScore(total=8.0), "promote")})

        stats = triage(
            idea_repo,
            plan_repo,
            trend_repo,
            scorer,
            config={"per_run": 6, "min_age_hours": 0},
            reviewer=self._reviewer(allowance=50),
        )

        assert stats["examined"] == 6
        assert stats["deferred"] == 0

    def test_without_a_reviewer_nothing_stops_early(self, repos):
        """No reviewer means no allowance to spend; the old behaviour stands."""
        idea_repo, plan_repo, trend_repo, session = repos
        self._six_candidates(idea_repo, session)

        stats = triage(
            idea_repo,
            plan_repo,
            trend_repo,
            FakeScorer({"idea": (FakeScore(total=8.0), "promote")}),
            config={"per_run": 6, "min_age_hours": 0},
            reviewer=None,
        )

        assert stats["examined"] == 6
        assert stats["deferred"] == 0
