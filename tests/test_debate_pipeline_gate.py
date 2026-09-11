"""Integration tests for the diversity gate inside the debate pipeline.

`tests/test_idea_clustering.py` proves the clustering algorithm is sound in
isolation. This file proves the *wiring* is: that
`_auto_score_and_save_ideas` actually consults the gate, that only cluster
representatives are scored, that the losers are persisted rather than
dropped, and that a plan row is written only for the one promotion that
carries the debate-wide `final_plan`.

That distinction matters here because every bug this gate exists to fix was
a wiring bug, not an algorithm bug: `result.all_ideas` ignored the
already-computed `selected_ideas`, and the single `final_plan` document was
copied byte-identically into every promoted plan (three plans of exactly
16,453 characters on 2026-08-05).

No LLM and no network: the scorer and translator are scripted, and a recorder
stands in for project generation.
"""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker

from agentic_orchestrator.db.models import Base, Idea, Plan
from agentic_orchestrator.db.repositories import IdeaRepository, PlanRepository
from agentic_orchestrator.debate.multi_stage import NO_PLAN_GENERATED
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
    """Strip every LLM/project dependency from the scoring task.

    The stand-ins RECORD rather than raise. The task wraps project generation
    in its own ``except Exception``, so a guard that raised there was swallowed
    and could never fail a test; tests assert on the record instead.
    """
    record = SimpleNamespace(project_calls=[])
    monkeypatch.setattr(tasks_mod, "_load_project_config", lambda: {"auto_generate": {}})

    async def _record_project(**kwargs):
        record.project_calls.append(kwargs["plan_id"])
        return False

    monkeypatch.setattr(tasks_mod, "_auto_generate_project", _record_project)
    return record


def golden_ideas():
    data = json.loads(GOLDEN_PATH.read_text())
    return [
        FakeIdea(
            title=item["title"],
            content=f"{item.get('core_analysis', '')} {item.get('proposal', '')}",
        )
        for item in data
    ]


def confirm_every_review(monkeypatch):
    """Every second-pass review CONFIRMs, so a fixture that scores high promotes."""
    from agentic_orchestrator.scoring import second_pass as sp

    class AlwaysConfirm(sp.SecondPassReviewer):
        async def review(self, title, content, local_score, context="", siblings=None):
            self.reviews_used += 1
            return sp.ReviewVerdict(sp.CONFIRM, reason="stub", score=8.0, model="m")

    monkeypatch.setattr(sp, "SecondPassReviewer", AlwaysConfirm)


def promoted_rows(session):
    return session.query(Idea).filter(Idea.status == "promoted").all()


def run_scoring(session, ideas, scorer, monkeypatch, final_plan=FINAL_PLAN, translator=None):
    """Drive _auto_score_and_save_ideas with everything external stubbed."""
    monkeypatch.setattr(tasks_mod, "IdeaScorer", lambda **kw: scorer, raising=False)

    import agentic_orchestrator.scoring as scoring_mod
    import agentic_orchestrator.translation as translation_pkg
    import agentic_orchestrator.translation.translator as translator_mod

    monkeypatch.setattr(scoring_mod, "IdeaScorer", lambda **kw: scorer)
    # The task imports ContentTranslator from the package, which bound its own
    # name at import time; patching only the module left the real translator in.
    stand_in = translator or PassthroughTranslator()
    monkeypatch.setattr(translator_mod, "ContentTranslator", lambda **kw: stand_in)
    monkeypatch.setattr(translation_pkg, "ContentTranslator", lambda **kw: stand_in)

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


class TestSecondPassGatesPromotion:
    """The strong model's work must not be graded only by the weak one."""

    def _reviewing(self, monkeypatch, verdict, provider="openai"):
        """Force every second-pass call to return one verdict."""
        from agentic_orchestrator.scoring import second_pass as sp

        class Fixed(sp.SecondPassReviewer):
            async def review(self, title, content, local_score, context="", siblings=None):
                if verdict == sp.UNAVAILABLE:
                    return sp.ReviewVerdict(sp.UNAVAILABLE, reason="stub outage")
                self.reviews_used += 1
                return sp.ReviewVerdict(verdict, reason="stub", score=8.0, model="gpt-5.4-mini")

        monkeypatch.setattr(sp, "SecondPassReviewer", Fixed)

    def test_confirm_lets_a_promotion_through(self, session, monkeypatch, no_external):
        from agentic_orchestrator.scoring import second_pass as sp

        self._reviewing(monkeypatch, sp.CONFIRM)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        promoted = IdeaRepository(session).get_by_status("promoted", limit=100)
        assert promoted
        assert promoted[0].extra_metadata["second_pass"]["verdict"] == sp.CONFIRM

    def test_an_unavailable_reviewer_holds_instead_of_promoting(
        self, session, monkeypatch, no_external
    ):
        # THE safety property. A silent reviewer outage must not become a
        # promotion, because promotion leads to a plan and a scaffolded
        # project with nothing having vetted the idea.
        from agentic_orchestrator.scoring import second_pass as sp

        self._reviewing(monkeypatch, sp.UNAVAILABLE)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        repo = IdeaRepository(session)
        assert repo.get_by_status("promoted", limit=100) == []
        assert repo.get_by_status("scored", limit=100), "held in the backlog, not lost"
        assert session.query(Plan).count() == 0

    def test_demote_holds_in_the_backlog(self, session, monkeypatch, no_external):
        from agentic_orchestrator.scoring import second_pass as sp

        self._reviewing(monkeypatch, sp.DEMOTE)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        repo = IdeaRepository(session)
        assert repo.get_by_status("promoted", limit=100) == []
        assert repo.get_by_status("scored", limit=100)

    def test_reject_archives_rather_than_holding(self, session, monkeypatch, no_external):
        from agentic_orchestrator.scoring import second_pass as sp

        self._reviewing(monkeypatch, sp.REJECT)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        repo = IdeaRepository(session)
        assert repo.get_by_status("promoted", limit=100) == []
        assert repo.get_by_status("archived", limit=100)

    def test_low_scoring_ideas_never_reach_the_paid_reviewer(
        self, session, monkeypatch, no_external
    ):
        from agentic_orchestrator.scoring import second_pass as sp

        seen = []

        class Counting(sp.SecondPassReviewer):
            async def review(self, title, content, local_score, context="", siblings=None):
                seen.append(title)
                return sp.ReviewVerdict(sp.CONFIRM, reason="stub")

        monkeypatch.setattr(sp, "SecondPassReviewer", Counting)

        # Everything scores 5.5 -> nothing is a promotion candidate.
        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=5.5), monkeypatch)

        assert seen == []


class TestThemeLimitsPromotions:
    """Five wordings of one idea must not become five plans.

    The tight clustering threshold deliberately under-merges — merging there
    deletes an idea, since only the representative proceeds. So a debate can
    legitimately emit four separate representatives that a human would call
    one theme (measured live 2026-08-06: four OpenZeppelin/Slither contract
    scanners among 16). Theme grouping is the recoverable half of the
    problem: at most one promotion per theme per cycle, and the losers keep
    their row and their backlog place.
    """

    def _confirm_everything(self, monkeypatch):
        from agentic_orchestrator.scoring import second_pass as sp

        class AlwaysConfirm(sp.SecondPassReviewer):
            async def review(self, title, content, local_score, context="", siblings=None):
                self.reviews_used += 1
                return sp.ReviewVerdict(sp.CONFIRM, reason="stub", score=8.0)

        monkeypatch.setattr(sp, "SecondPassReviewer", AlwaysConfirm)

    def test_a_theme_gets_at_most_one_promotion(self, session, monkeypatch, no_external):
        self._confirm_everything(monkeypatch)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        promoted = IdeaRepository(session).get_by_status("promoted", limit=100)
        themes = [
            (row.extra_metadata.get("theme") or {}).get("id")
            for row in promoted
            if row.extra_metadata
        ]
        named = [t for t in themes if t]
        assert len(named) == len(set(named)), f"a theme was promoted more than once: {themes}"

    def test_theme_siblings_reach_the_reviewer(self, session, monkeypatch, no_external):
        from agentic_orchestrator.scoring import second_pass as sp

        seen = []

        class Recording(sp.SecondPassReviewer):
            async def review(self, title, content, local_score, context="", siblings=None):
                seen.append(siblings or [])
                return sp.ReviewVerdict(sp.DEMOTE, reason="stub")

        monkeypatch.setattr(sp, "SecondPassReviewer", Recording)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        # At least one reviewed idea had same-theme company; the reviewer
        # cannot notice redundancy it is never shown.
        assert any(s for s in seen), "no siblings were ever passed to the reviewer"

    def test_theme_is_recorded_on_the_row_for_audit(self, session, monkeypatch, no_external):
        self._confirm_everything(monkeypatch)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        repo = IdeaRepository(session)
        rows = repo.get_by_status("promoted", limit=100) + repo.get_by_status("scored", limit=100)
        with_theme = [r for r in rows if (r.extra_metadata or {}).get("theme")]
        assert with_theme, "theme grouping must be auditable on the idea row"

    def test_disabling_theme_grouping_is_a_no_op(self, session, monkeypatch, no_external):
        # theme_threshold: 0 must not break the pipeline, just stop limiting.
        base = tasks_mod._load_backlog_config()
        monkeypatch.setattr(
            tasks_mod,
            "_load_backlog_config",
            lambda: {**base, "clustering": {**base["clustering"], "theme_threshold": 0}},
        )
        self._confirm_everything(monkeypatch)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        # Promotions still happen, capped only by max_per_cycle.
        assert IdeaRepository(session).get_by_status("promoted", limit=100)


class TestOnePlanPerDebate:
    """A plan row exists only where a plan document exists.

    Planning writes one document per debate. The first promotion carries it
    into a plan row; later promotions stay ``promoted`` with no plan row.
    Absence is counted with raw queries: PlanRepository leaves placeholder
    rows out, so an absence read through it would prove less.
    """

    def test_the_debate_plan_document_is_not_copied_into_every_promotion(
        self, session, monkeypatch, no_external
    ):
        # The 2026-08-05 signature: three plans, each 16,453 chars, all the
        # same document.
        confirm_every_review(monkeypatch)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        promoted = promoted_rows(session)
        assert len(promoted) >= 2, "the fixture must promote more than one idea"
        plans = session.query(Plan).all()
        assert len(plans) == 1, f"one plan document, one plan row; got {len(plans)}"
        assert plans[0].final_plan == FINAL_PLAN
        assert plans[0].idea_id in {row.id for row in promoted}
        # 8.5 clears the auto-approval floor, so generation is requested for
        # that plan and nothing else.
        assert no_external.project_calls == [plans[0].id]

    @pytest.mark.parametrize(("local_score", "status"), [(7.5, "draft"), (8.0, "approved")])
    def test_a_plan_is_approved_only_at_the_auto_generation_floor(
        self, session, monkeypatch, no_external, local_score, status
    ):
        # min_score defaults to 8.0. A draft waits for a person in
        # /plans/pending-approval; only an approved plan requests generation.
        confirm_every_review(monkeypatch)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=local_score), monkeypatch)

        assert promoted_rows(session), "the fixture must promote"
        plan = session.query(Plan).one()
        assert plan.status == status
        assert no_external.project_calls == ([plan.id] if status == "approved" else [])

    @pytest.mark.parametrize("final_plan", [None, "  \n", NO_PLAN_GENERATED])
    def test_no_plan_document_means_no_plan_row(
        self, session, monkeypatch, no_external, final_plan
    ):
        confirm_every_review(monkeypatch)

        run_scoring(
            session,
            golden_ideas(),
            ScriptedScorer({}, default=8.5),
            monkeypatch,
            final_plan=final_plan,
        )

        assert promoted_rows(session), "the fixture must promote"
        assert session.query(Plan).count() == 0
        assert no_external.project_calls == []

    def test_no_plan_row_lacks_a_document(self, session, monkeypatch, no_external):
        confirm_every_review(monkeypatch)

        run_scoring(session, golden_ideas(), ScriptedScorer({}, default=8.5), monkeypatch)

        assert len(promoted_rows(session)) >= 2, "later promotions must have been reached"
        lacking = session.query(Plan).filter(
            or_(Plan.final_plan.is_(None), func.trim(Plan.final_plan) == "")
        )
        assert lacking.count() == 0

    def test_a_failed_translation_keeps_the_document(self, session, monkeypatch, no_external):
        # A failed KO->EN translation returns "" rather than raising.
        class EnglishLost(PassthroughTranslator):
            async def ensure_bilingual(self, text):
                return ("", text) if text == FINAL_PLAN else (text, text)

        confirm_every_review(monkeypatch)

        run_scoring(
            session,
            golden_ideas(),
            ScriptedScorer({}, default=8.5),
            monkeypatch,
            translator=EnglishLost(),
        )

        plans = session.query(Plan).all()
        assert len(plans) == 1, "the fixture must write the plan row"
        assert plans[0].final_plan_ko == FINAL_PLAN, "the stand-in translator must be in use"
        assert plans[0].final_plan == FINAL_PLAN


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


class TestAPlanSurvivesTheNextIdeaFailing:
    """A committed idea must never be left without the plan it was promoted for.

    The idea row is committed as ``promoted`` at its own write. The plan used
    to be only flushed, with the loop's closing ``commit()`` making it durable
    -- so the ``rollback()`` in the per-idea ``except`` (added to stop a failed
    flush poisoning the rest of the batch) would take the previous iteration's
    plan with it. And the failure does not have to be exotic: the scorer, the
    second-pass reviewer and all three translations run *before* the next idea
    is created, so any of them raising lands in that handler while the previous
    plan is still uncommitted.

    Measured on SQLite before the fix: one promoted idea, zero plans.
    """

    def _reviewing_confirm(self, monkeypatch):
        from agentic_orchestrator.scoring import second_pass as sp

        class Fixed(sp.SecondPassReviewer):
            async def review(self, title, content, local_score, context="", siblings=None):
                self.reviews_used += 1
                return sp.ReviewVerdict(sp.CONFIRM, reason="stub", score=8.0, model="m")

        monkeypatch.setattr(sp, "SecondPassReviewer", Fixed)

    def test_the_plan_is_still_there(self, session, monkeypatch, no_external):
        self._reviewing_confirm(monkeypatch)

        class FailsOnTheSecondIdea(ScriptedScorer):
            """Promotes the first idea, then dies the way the real scorer can.

            Raising from `score_and_decide` puts the exception exactly where
            production puts it: inside the per-idea try, before that idea's
            row exists, with the previous idea's plan pending.
            """

            def __init__(self):
                super().__init__({}, default=8.5)
                self.calls = 0

            async def score_and_decide(self, idea_content: str, context: str = ""):
                self.calls += 1
                if self.calls == 2:
                    raise RuntimeError("Ollama timeout scoring the next idea")
                return await super().score_and_decide(idea_content, context)

        ideas = [
            FakeIdea(title="A first idea long enough to look like a real one", content="x"),
            FakeIdea(title="A completely unrelated second idea, also long enough", content="y"),
        ]
        scorer = FailsOnTheSecondIdea()

        run_scoring(session, ideas, scorer, monkeypatch)

        assert scorer.calls == 2, "the second idea has to have been reached"
        promoted = IdeaRepository(session).get_by_status("promoted", limit=10)
        plans = PlanRepository(session).get_all(limit=10)

        assert len(promoted) == 1
        assert len(plans) == 1, "a promoted idea was left with no plan"
        assert plans[0].idea_id == promoted[0].id


class TestAFailedPlanWriteDoesNotCostTheNextIdea:
    """A failed plan flush is rolled back where it failed.

    SQLAlchemy refuses every later statement on a session whose flush failed
    until it is rolled back. Without the rollback in the plan block, the next
    idea -- already scored, reviewed and translated -- meets that refusal at
    its own insert, and the per-idea handler rolls its row away.
    """

    def test_the_next_idea_keeps_its_row(self, session, monkeypatch, no_external):
        confirm_every_review(monkeypatch)
        failed_writes = []
        real_create = PlanRepository.create

        def create_a_row_that_cannot_flush(self, plan_data):
            failed_writes.append(plan_data["idea_id"])
            # plans.title is NOT NULL, so this flush raises IntegrityError.
            return real_create(self, {**plan_data, "title": None})

        monkeypatch.setattr(PlanRepository, "create", create_a_row_that_cannot_flush)
        ideas = [
            FakeIdea(title="A first idea long enough to look like a real one", content="x"),
            FakeIdea(title="A completely unrelated second idea, also long enough", content="y"),
        ]
        scorer = ScriptedScorer({}, default=8.5)

        run_scoring(session, ideas, scorer, monkeypatch)

        assert len(failed_writes) == 1, "the first promotion's plan write must have failed"
        assert len(scorer.scored_titles) == 2, "the second idea has to have been reached"
        assert session.query(Plan).count() == 0
        assert {row.title for row in session.query(Idea).all()} == {idea.title for idea in ideas}
