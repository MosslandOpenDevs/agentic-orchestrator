"""Freshness weighting must never rewrite the stored signal score.

`_apply_time_decay_to_signals` used to multiply `Signal.score` in place on a
live ORM object and let the surrounding `session.commit()` persist it. Because
the trend task runs every two hours, an old signal's score was multiplied by
0.2 again and again (1.0 -> 0.2 -> 0.04 -> ...), destroying the value the API
sorts and filters on -- to weight an analysis that never received it.
"""

from datetime import timedelta

from agentic_orchestrator.db.connection import Database
from agentic_orchestrator.db.models import Signal
from agentic_orchestrator.scheduler.tasks import (
    _apply_time_decay_to_signals,
    _calculate_time_decay,
)
from agentic_orchestrator.timeutil import utcnow


def _signal(**kwargs) -> Signal:
    defaults = {
        "id": "sig-1",
        "source": "rss",
        "title": "A signal",
        "category": "ai",
        "score": 1.0,
        "collected_at": utcnow(),
    }
    return Signal(**{**defaults, **kwargs})


class TestStoredScoreIsUntouched:
    def test_score_survives_a_single_pass(self):
        now = utcnow()
        signal = _signal(score=0.8, collected_at=now - timedelta(hours=72))

        _apply_time_decay_to_signals([signal], now)

        assert signal.score == 0.8

    def test_repeated_passes_do_not_compound(self):
        """The old code turned 1.0 into 0.2, then 0.04, then 0.008 ..."""
        now = utcnow()
        signal = _signal(score=1.0, collected_at=now - timedelta(hours=72))

        for _ in range(5):
            _apply_time_decay_to_signals([signal], now)

        assert signal.score == 1.0
        assert signal.effective_score == 0.2

    def test_weight_is_transient_and_never_persisted(self, tmp_path):
        db = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
        db.create_tables()

        now = utcnow()
        session = db.get_session()
        try:
            session.add(_signal(score=1.0, collected_at=now - timedelta(hours=72)))
            session.commit()

            stored = session.query(Signal).all()
            _apply_time_decay_to_signals(stored, now)
            session.commit()  # the trend task commits after weighting
        finally:
            session.close()

        reader = db.get_session()
        try:
            reloaded = reader.query(Signal).one()
            assert reloaded.score == 1.0
            # The weight is a plain attribute, so it does not round-trip.
            assert not hasattr(reloaded, "time_decay")
        finally:
            reader.close()


class TestWeighting:
    def test_effective_score_is_score_times_decay(self):
        now = utcnow()
        signal = _signal(score=0.5, collected_at=now - timedelta(hours=30))

        _apply_time_decay_to_signals([signal], now)

        assert signal.time_decay == 0.4
        assert signal.effective_score == 0.2

    def test_missing_score_is_treated_as_zero(self):
        now = utcnow()
        signal = _signal(score=None)

        _apply_time_decay_to_signals([signal], now)

        assert signal.score is None
        assert signal.effective_score == 0.0

    def test_fresh_signals_outrank_stale_ones_of_equal_score(self):
        """What the weighting is for: ordering the batch handed to the LLM."""
        now = utcnow()
        fresh = _signal(id="fresh", score=0.5, collected_at=now - timedelta(minutes=10))
        stale = _signal(id="stale", score=0.5, collected_at=now - timedelta(hours=72))

        batch = [stale, fresh]
        _apply_time_decay_to_signals(batch, now)
        batch.sort(key=lambda s: s.effective_score, reverse=True)

        assert [s.id for s in batch] == ["fresh", "stale"]

    def test_decay_schedule_matches_the_documented_buckets(self):
        now = utcnow()
        expected = {
            0.5: 1.0,
            3: 0.9,
            9: 0.8,
            18: 0.6,
            36: 0.4,
            100: 0.2,
        }
        for age_hours, decay in expected.items():
            assert _calculate_time_decay(now - timedelta(hours=age_hours), now) == decay
