"""The debate must open on the best trend of the batch, not the worst.

Measured across 152 trend batches in production, the highest-scoring trend was
picked 0 times and the lowest-scoring trend was picked 59 out of 59. Three
correct-looking pieces composed into that:

1. the analyzer emits trends score-descending,
2. the writer stamped ``analyzed_at = utcnow()`` per row inside the save loop,
   so each row landed a couple of seconds after the previous one,
3. ``TrendRepository.get_latest`` orders by (analyzed_at DESC, score DESC).

With every stamp distinct, the score tiebreak in (3) is unreachable and the
batch comes back exactly reversed. Nothing errors; the debate just spends its
paid tier on the weakest trend available.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_orchestrator.db.models import Base
from agentic_orchestrator.db.repositories import DebateRepository, TrendRepository
from agentic_orchestrator.scheduler.tasks import _select_debate_trend

BATCH_AT = datetime(2026, 8, 18, 6, 15, 0)


class FakeTrend:
    """Stands in for a Trend row; only ``score`` and ``name`` are read here."""

    def __init__(self, name, score):
        self.name = name
        self.score = score


@pytest.fixture
def trend_repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield TrendRepository(session)
    session.close()


@pytest.fixture
def debate_repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield DebateRepository(session)
    session.close()


def write_batch(repo, scores, *, stagger=False):
    """Write one analysis batch, score-descending, as the analyzer emits it.

    ``stagger=True`` reproduces the old per-row ``utcnow()`` stamp.
    """
    for i, score in enumerate(sorted(scores, reverse=True)):
        repo.create(
            {
                "id": f"t{i}",
                "period": "24h",
                "name": f"Trend scoring {score}",
                "score": score,
                "analyzed_at": BATCH_AT + timedelta(seconds=3 * i) if stagger else BATCH_AT,
            }
        )


class TestSelectDebateTrend:
    def test_picks_the_highest_scoring_trend(self):
        # The exact 06:15 batch that debate 4bf66a4f drew from, in the order
        # `get_latest` handed it over: worst first.
        trends = [
            FakeTrend("Agentrhq's Webcmd", 8.7),
            FakeTrend("Provenance and HASH", 8.9),
            FakeTrend("OpenAI agent tooling", 9.5),
            FakeTrend("Claude Code v2 /design Skill", 9.8),
        ]

        assert _select_debate_trend(trends).score == 9.8

    def test_picks_the_highest_score_regardless_of_position(self):
        for position in range(4):
            trends = [FakeTrend(f"t{i}", 5.0) for i in range(4)]
            trends[position] = FakeTrend("winner", 9.9)
            assert _select_debate_trend(trends).name == "winner"

    def test_no_trends_yields_none_rather_than_raising(self):
        """The caller falls back to signal-based topics on None; an IndexError
        here would abort the debate run instead."""
        assert _select_debate_trend([]) is None

    def test_a_missing_score_does_not_win_by_accident(self):
        trends = [FakeTrend("unscored", None), FakeTrend("scored", 6.0)]

        assert _select_debate_trend(trends).name == "scored"


class TestGetLatestOrdering:
    def test_one_timestamp_per_batch_surfaces_the_best_trend_first(self, trend_repo):
        """What the writer's batch stamp buys: the score tiebreak becomes
        reachable, so every consumer of ``get_latest`` -- not just the debate
        topic picker -- reads the batch in quality order."""
        write_batch(trend_repo, [9.8, 9.5, 8.9, 8.7])

        latest = trend_repo.get_latest(period="24h", limit=5)

        assert [t.score for t in latest] == [9.8, 9.5, 8.9, 8.7]

    def test_per_row_stamps_invert_the_batch(self, trend_repo):
        """The defect itself, reproduced from its inputs.

        This documents the mechanism; it does NOT stop the writer going back to
        stamping inside the loop -- it never touches the writer. What holds the
        writer down is ``TestTheWriterStampsOnce`` below, which reads the
        source, and the picker is held by ``TestTheDebatePicksByScore``.
        """
        write_batch(trend_repo, [9.8, 9.5, 8.9, 8.7], stagger=True)

        latest = trend_repo.get_latest(period="24h", limit=5)

        assert [t.score for t in latest] == [8.7, 8.9, 9.5, 9.8]
        # And this is exactly why the picker no longer trusts position.
        assert _select_debate_trend(latest).score == 9.8


class TestTheWriterStampsOnce:
    """Reverting the writer to a per-row ``utcnow()`` left the whole suite green.

    ``_run_trends_async`` needs an analyzer, an LLM and a populated signals
    table to drive end to end, so the invariant is checked where it lives: the
    save loop must not mint a timestamp per row. A source check is a blunt
    instrument, but a blunt instrument beats the nothing that was here.
    """

    @staticmethod
    def _save_loop() -> str:
        from agentic_orchestrator.scheduler import tasks

        source = Path(tasks.__file__).read_text(encoding="utf-8")
        start = source.index("for trend in analysis.trends:")
        return source[start : source.index("session.commit()", start)]

    def test_the_batch_timestamp_is_taken_before_the_loop(self):
        from agentic_orchestrator.scheduler import tasks

        source = Path(tasks.__file__).read_text(encoding="utf-8")
        loop_start = source.index("for trend in analysis.trends:")
        preamble = source[source.index("analysis = await analyzer.analyze_trends") : loop_start]

        assert "analyzed_at = utcnow()" in preamble

    def test_no_timestamp_is_minted_inside_the_loop(self):
        body = self._save_loop()

        assert "utcnow()" not in body, (
            "a per-row stamp makes every analyzed_at distinct, which puts the score "
            "tiebreak in get_latest out of reach and hands the batch back reversed"
        )
        assert '"analyzed_at": analyzed_at' in body


class TestTheDebatePicksByScore:
    """The topic picker, held at its call site rather than only as a helper."""

    def test_the_debate_task_selects_by_score_not_position(self):
        from agentic_orchestrator.scheduler import tasks

        source = Path(tasks.__file__).read_text(encoding="utf-8")

        assert "_select_debate_trend(" in source
        assert "recent_trends," in source
        assert (
            "top_trend = recent_trends[0]" not in source
        ), "position-based selection is what picked the batch's worst trend 59/59 times"

    def test_the_debate_task_gives_the_picker_its_history(self):
        """The rerun check is only as good as what it is compared against; a
        call site that forgets ``recent_topics`` disables it silently."""
        from agentic_orchestrator.scheduler import tasks

        source = Path(tasks.__file__).read_text(encoding="utf-8")

        assert "recent_topics=debate_repo.get_recent_topics(" in source

    def test_the_helper_and_the_repository_agree_on_a_real_batch(self, trend_repo):
        """End to end over the two pieces that actually compose in production."""
        write_batch(trend_repo, [9.8, 9.5, 8.9, 8.7], stagger=True)

        picked = _select_debate_trend(trend_repo.get_latest(period="24h", limit=5))

        assert picked.score == 9.8


class TestTheDebateDoesNotReopenYesterdaysStory:
    """Score alone has no memory, and trends are re-analysed every two hours.

    A loud story therefore keeps re-entering the batch at the top and wins the
    6-hourly pick again and again. Measured over 2026-08-18..26: the GPT-5
    Agent SDK headline seeded eight separate debates, Nvidia AVO took all four
    slots of 08-22 and Faraday three of 08-23 — while ~45 distinct trends
    landed every day. Each rerun spent a paid debate restating the previous
    one, and the promotion reviewer then, correctly, called the output
    re-expressions of a single axis. 21 days, 0 promotions.

    Tuned towards over-flagging, unlike ``backlog.clustering`` next door: a
    wrong merge there deletes an idea, a wrong flag here costs the second-best
    trend of forty-five.
    """

    GPT5 = "GPT-5 Agent SDK Launch Accelerates Autonomous AI Workflow Automation Across Industries"
    GPT5_AGAIN = (
        "OpenAI GPT-5 Agent SDK Launch Accelerates Autonomous AI Workflow Automation "
        "Across Decentralized Applications"
    )
    ZCASH = (
        "Grayscale Launches First Zcash ETF, Token Soars - Institutional Adoption Drives Inflows"
    )

    def debated(self, name):
        """A stored topic, in the shape ``_generate_debate_topic_from_trend`` writes."""
        return f"[AI] {name} - Mossland 전략적 대응 방안"

    def test_the_top_trend_is_skipped_when_it_reruns_a_recent_debate(self):
        trends = [FakeTrend(self.GPT5_AGAIN, 9.8), FakeTrend(self.ZCASH, 8.5)]

        picked = _select_debate_trend(trends, recent_topics=[self.debated(self.GPT5)])

        assert picked.name == self.ZCASH

    def test_without_history_the_highest_score_still_wins(self):
        trends = [FakeTrend(self.GPT5_AGAIN, 9.8), FakeTrend(self.ZCASH, 8.5)]

        assert _select_debate_trend(trends).name == self.GPT5_AGAIN

    def test_a_new_subject_is_not_skipped_for_sharing_tech_vocabulary(self):
        """Every headline in this corpus says "AI", "agent" and "launch". The
        term weights are learned from the batch, so those carry ~no signal and
        the rare words decide."""
        trends = [FakeTrend(self.ZCASH, 9.8)]

        picked = _select_debate_trend(trends, recent_topics=[self.debated(self.GPT5)])

        assert picked.name == self.ZCASH

    def test_an_all_rerun_batch_still_opens_a_debate(self):
        """A repeated debate is a waste; no debate is a hole in the day's
        output. The picker degrades to the old behaviour rather than to None,
        which the caller would turn into a signal-derived topic."""
        trends = [FakeTrend(self.GPT5_AGAIN, 9.8), FakeTrend(self.GPT5, 9.5)]

        picked = _select_debate_trend(trends, recent_topics=[self.debated(self.GPT5)])

        assert picked.name == self.GPT5_AGAIN

    def test_the_decoration_around_a_stored_topic_is_not_what_matches(self):
        """Stored topics all carry ``[CATEGORY]`` and the same Korean suffix.
        Comparing those would make every candidate look like every topic."""
        from agentic_orchestrator.scheduler.tasks import _debate_topic_subject

        assert _debate_topic_subject(self.debated(self.ZCASH)) == self.ZCASH

    def test_a_zero_threshold_disables_the_check(self):
        trends = [FakeTrend(self.GPT5_AGAIN, 9.8), FakeTrend(self.ZCASH, 8.5)]

        picked = _select_debate_trend(
            trends, recent_topics=[self.debated(self.GPT5)], repeat_threshold=0
        )

        assert picked.name == self.GPT5_AGAIN

    def test_history_comes_back_newest_first_and_bounded(self, debate_repo):
        for i in range(12):
            debate_repo.create_session(
                {
                    "id": f"d{i}",
                    "topic": self.debated(f"Story number {i}"),
                    "phase": "divergence",
                    "status": "completed",
                    "started_at": BATCH_AT + timedelta(hours=i),
                }
            )

        topics = debate_repo.get_recent_topics(limit=8)

        assert len(topics) == 8
        assert topics[0] == self.debated("Story number 11")

    def test_a_crashed_session_still_counts_as_having_spent_its_topic(self, debate_repo):
        debate_repo.create_session(
            {
                "id": "d-failed",
                "topic": self.debated(self.GPT5),
                "phase": "divergence",
                "status": "failed",
                "started_at": BATCH_AT,
            }
        )

        assert debate_repo.get_recent_topics() == [self.debated(self.GPT5)]
