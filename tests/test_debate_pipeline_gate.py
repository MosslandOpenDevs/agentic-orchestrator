"""Integration tests for the diversity gate inside the debate pipeline.

`tests/test_idea_clustering.py` proves the clustering algorithm is sound in
isolation. This file proves the *wiring* is: that
`_auto_score_and_save_ideas` actually consults the gate, that only cluster
representatives are scored and mirrored, that the losers are persisted
rather than dropped, and that exactly one plan per debate carries the
debate-wide `final_plan`.

That distinction matters here because every bug this gate exists to fix was
a wiring bug, not an algorithm bug: `result.all_ideas` ignored the
already-computed `selected_ideas`, and the single `final_plan` document was
copied byte-identically into every promoted plan (three plans of exactly
16,453 characters on 2026-08-05).

No LLM and no network: the scorer is scripted and the GitHub client is
absent, which is also what lets these run while the shared GPU is busy.
"""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_orchestrator.db.models import Base
from agentic_orchestrator.db.repositories import IdeaRepository, PlanRepository
from agentic_orchestrator.scheduler import tasks as tasks_mod

GOLDEN_PATH = Path(__file__).parent / "data" / "golden_debate_x402.json"
FINAL_PLAN = "# Debate-wide plan document\n" + ("x" * 500)


@dataclass
class FakeIdea:
    """Duck-type of debate.multi_stage.Idea as the scheduler consumes it."""

    title: str
    content: str = ""
    metadata: dict = field(default_factory=dict)


class ScriptedScorer:
    """Deterministic scorer: score comes from a per-title table."""

    def __init__(self, scores: dict, default: float = 5.5):
        self.scores = scores
        self.default = default
        self.scored_titles: list[str] = []

    async def score_and_decide(self, idea_content: str, context: str = ""):
        title_line = idea_content.split("\n", 1)[0].removeprefix("제목: ")
        self.scored_titles.append(title_line)
        total = self.default
        for needle, value in self.scores.items():
            if needle in title_line:
                total = value
                break
        decision = "promote" if total >= 7.0 else ("archive" if total < 4.0 else "pending")
        return _Score(total), decision


@dataclass
class _Score:
    total: float

    def to_dict(self):
        return {"total": self.total}


class PassthroughTranslator:
    async def ensure_bilingual(self, text):
        return text, text


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


@pytest.fixture()
def no_external(monkeypatch):
    """Strip every LLM/GitHub/project dependency from the scoring task."""
    monkeypatch.setattr(tasks_mod, "_load_project_config", lambda: {"auto_generate": {}})

    async def _no_project(**kwargs):
        raise AssertionError("project generation must not run in these tests")

    monkeypatch.setattr(tasks_mod, "_auto_generate_project", _no_project)


def golden_ideas():
    data = json.loads(GOLDEN_PATH.read_text())
    return [
        FakeIdea(
            title=item["title"],
            content=f"{item.get('core_analysis', '')} {item.get('proposal', '')}",
        )
        for item in data
    ]


def run_scoring(session, ideas, scorer, monkeypatch, final_plan=FINAL_PLAN):
    """Drive _auto_score_and_save_ideas with everything external stubbed."""
    monkeypatch.setattr(tasks_mod, "IdeaScorer", lambda **kw: scorer, raising=False)

    import agentic_orchestrator.scoring as scoring_mod
    import agentic_orchestrator.translation.translator as translator_mod

    monkeypatch.setattr(scoring_mod, "IdeaScorer", lambda **kw: scorer)
    monkeypatch.setattr(translator_mod, "ContentTranslator", lambda **kw: PassthroughTranslator())

    return asyncio.run(
        tasks_mod._auto_score_and_save_ideas(
            router=object(),
            ideas=ideas,
            topic="[CRYPTO] x402 Protocol",
            context="test context",
            debate_session_id="sess-test",
            db_session=session,
            final_plan_content=final_plan,
        )
    )


class TestGateIsActuallyWired:
    def test_only_cluster_representatives_are_scored(self, session, monkeypatch, no_external):
        ideas = golden_ideas()
        scorer = ScriptedScorer({})

        run_scoring(session, ideas, scorer, monkeypatch)

        # 24 ideas in, far fewer scored: the LLM is not paid to score eight
        # wordings of one idea. (The exact count is the clustering module's
        # business; the wiring's business is that it is < 24.)
        assert 0 < len(scorer.scored_titles) < len(ideas)

    def test_losers_are_persisted_not_dropped(self, session, monkeypatch, no_external):
        ideas = golden_ideas()

        run_scoring(session, ideas, ScriptedScorer({}), monkeypatch)

        repo = IdeaRepository(session)
        duplicates = repo.get_by_status("duplicate", limit=500)
        # Every idea survives somewhere: representative rows + duplicate rows
        # must together account for the whole batch.
        non_dup = [
            row
            for status in ("scored", "promoted", "archived", "pending")
            for row in repo.get_by_status(status, limit=500)
        ]
        assert len(duplicates) + len(non_dup) == len(ideas)
        assert duplicates, "the gate must keep near-duplicates for audit"
        for row in duplicates:
            assert row.extra_metadata["duplicate_of"]
            assert row.github_issue_id is None  # never mirrored

    def test_duplicate_rows_point_at_a_real_representative(self, session, monkeypatch, no_external):
        run_scoring(session, golden_ideas(), ScriptedScorer({}), monkeypatch)

        repo = IdeaRepository(session)
        live_ids = {
            row.id
            for status in ("scored", "promoted", "archived", "pending")
            for row in repo.get_by_status(status, limit=500)
        }
        for row in repo.get_by_status("duplicate", limit=500):
            assert row.extra_metadata["duplicate_of"] in live_ids

    def test_disabling_the_gate_restores_the_old_behavior(self, session, monkeypatch, no_external):
        # The gate is a config switch, and turning it off must be a true
        # no-op path rather than a differently-broken one.
        base = tasks_mod._load_backlog_config()
        monkeypatch.setattr(
            tasks_mod,
            "_load_backlog_config",
            lambda: {**base, "clustering": {**base["clustering"], "enabled": False}},
        )
        ideas = golden_ideas()
        scorer = ScriptedScorer({})

        run_scoring(session, ideas, scorer, monkeypatch)

        assert len(scorer.scored_titles) == len(ideas)
        assert IdeaRepository(session).get_by_status("duplicate", limit=500) == []


class TestOnePlanPerDebate:
    def test_the_debate_plan_document_is_not_copied_into_every_promotion(
        self, session, monkeypatch, no_external
    ):
        # The 2026-08-05 signature: three plans, each 16,453 chars, all the
        # same document. At most ONE plan may carry it.
        ideas = golden_ideas()
        # Force several promotions from distinct clusters.
        scorer = ScriptedScorer({}, default=8.5)

        run_scoring(session, ideas, scorer, monkeypatch)

        plans = PlanRepository(session).get_all(limit=100)
        with_document = [p for p in plans if p.final_plan]
        assert len(with_document) <= 1, (
            "only one plan per debate may carry the debate-wide final_plan; "
            f"got {len(with_document)}"
        )
        if with_document:
            assert with_document[0].final_plan == FINAL_PLAN

    def test_a_plan_without_the_document_is_never_auto_approved(
        self, session, monkeypatch, no_external
    ):
        # Auto-approval is what triggers project generation; approving a
        # plan with no document scaffolds a project from nothing.
        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        for plan in PlanRepository(session).get_all(limit=100):
            if not plan.final_plan:
                assert plan.status != "approved"


class TestFailureModes:
    def test_gate_helper_survives_ideas_with_no_usable_fields(self):
        # The helper is the layer that must absorb anything odd rather than
        # take the debate down with it. Three attribute-less objects read as
        # three empty titles, which legitimately cluster together — the
        # contract under test is "does not raise, loses nothing", not a
        # particular cluster count.
        broken = [object(), object(), object()]

        grouped = tasks_mod._cluster_debate_ideas(broken, {"enabled": True})

        accounted = sum(1 + len(g["duplicates"]) for g in grouped)
        assert accounted == len(broken)
        assert all(g["representative"] in broken for g in grouped)

    def test_gate_helper_falls_open_when_clustering_raises(self, monkeypatch):
        # A clustering failure must degrade to "every idea is unique", which
        # is exactly the pre-gate behavior — never an exception, because the
        # gate is an optimisation and the debate's output is not.
        import agentic_orchestrator.scheduler.idea_clustering as clustering_mod

        def boom(*args, **kwargs):
            raise RuntimeError("clustering exploded")

        monkeypatch.setattr(clustering_mod, "cluster_ideas", boom)
        ideas = golden_ideas()[:5]

        grouped = tasks_mod._cluster_debate_ideas(ideas, {"enabled": True})

        assert len(grouped) == len(ideas)
        assert all(g["duplicates"] == [] for g in grouped)

    def test_single_idea_batch_skips_clustering_entirely(self):
        one = [FakeIdea(title="A Single Idea About Agent Payment Rails")]
        grouped = tasks_mod._cluster_debate_ideas(one, {"enabled": True})
        assert len(grouped) == 1
        assert grouped[0]["representative"] is one[0]
