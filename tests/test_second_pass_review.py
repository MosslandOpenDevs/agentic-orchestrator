"""Tests for the second-pass promotion review (v0.6.22).

The pipeline had an inversion: debates run on gpt-5.4-mini, but the gate
deciding whether their output became a plan — and then a scaffolded project —
was a local gemma3:4b re-score. On 2026-08-05 that scorer returned 8.0 for
twenty-two consecutive ideas and three of them each scaffolded a project.

Promotion now takes two signatures. The property these tests defend hardest
is the failure direction: when the reviewer cannot run, the idea must be
HELD, never promoted. Auto-approval and project generation are downstream of
promotion, so "promote when unsure" is the one behavior that turns a silent
outage into an unvetted project on disk.
"""

import asyncio
from types import SimpleNamespace

import pytest

from agentic_orchestrator.scoring.second_pass import (
    CONFIRM,
    DEMOTE,
    REJECT,
    UNAVAILABLE,
    SecondPassReviewer,
)


class FakeRouter:
    """Router stub: returns scripted content, or raises."""

    def __init__(self, content=None, provider="openai", model="gpt-5.4-mini", error=None):
        self.content = content
        self.provider = provider
        self.model = model
        self.error = error
        self.calls = []

    async def route(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.content, provider=self.provider, model=self.model)


def review(router, local_score=8.0, config=None):
    reviewer = SecondPassReviewer(router, config)
    return reviewer, asyncio.run(
        reviewer.review(
            title="x402-Powered Mossland Agent Paywall",
            content="A paywall for agent API access.",
            local_score=local_score,
        )
    )


class TestVerdicts:
    def test_confirm_allows_promotion(self):
        router = FakeRouter('{"verdict": "confirm", "reason": "specific and feasible", "score": 8}')

        _, verdict = review(router)

        assert verdict.verdict == CONFIRM
        assert verdict.promotes is True
        assert verdict.score == 8.0
        assert verdict.model == "gpt-5.4-mini"

    def test_demote_does_not_promote(self):
        router = FakeRouter('{"verdict": "demote", "reason": "too vague for a plan"}')

        _, verdict = review(router)

        assert verdict.verdict == DEMOTE
        assert verdict.promotes is False
        assert verdict.rejects is False

    def test_reject_is_distinguishable_from_demote(self):
        router = FakeRouter('{"verdict": "reject", "reason": "title is a JSON fragment"}')

        _, verdict = review(router)

        assert verdict.rejects is True
        assert verdict.promotes is False

    def test_fenced_json_is_parsed(self):
        router = FakeRouter(
            'Sure!\n```json\n{"verdict": "confirm", "reason": "ok", "score": 7.5}\n```'
        )

        _, verdict = review(router)

        assert verdict.promotes is True
        assert verdict.score == 7.5

    def test_prose_wrapped_json_is_salvaged(self):
        router = FakeRouter('Here is my review: {"verdict": "demote", "reason": "thin"} — done.')

        _, verdict = review(router)

        assert verdict.verdict == DEMOTE


class TestFailureAlwaysHolds:
    """Every way the reviewer can fail must land on "not promoted"."""

    def test_provider_error_does_not_promote(self):
        router = FakeRouter(error=RuntimeError("429 rate limited"))

        _, verdict = review(router)

        assert verdict.verdict == UNAVAILABLE
        assert verdict.promotes is False

    def test_unparseable_response_does_not_promote(self):
        router = FakeRouter("I think this one is pretty good, honestly.")

        _, verdict = review(router)

        assert verdict.verdict == UNAVAILABLE
        assert verdict.promotes is False

    def test_unknown_verdict_string_does_not_promote(self):
        router = FakeRouter('{"verdict": "maybe", "reason": "unsure"}')

        _, verdict = review(router)

        assert verdict.verdict == UNAVAILABLE
        assert verdict.promotes is False

    def test_a_review_that_degraded_to_local_is_not_a_second_opinion(self):
        # The paid tier degrades to local by design on any missing
        # precondition. A local answer here is the FIRST opinion twice, and
        # counting it would defeat the entire mechanism.
        router = FakeRouter(
            '{"verdict": "confirm", "reason": "looks good"}',
            provider="ollama",
            model="gemma3:4b",
        )

        _, verdict = review(router)

        assert verdict.verdict == UNAVAILABLE
        assert verdict.promotes is False

    def test_unavailable_verdicts_do_not_consume_the_budget(self):
        router = FakeRouter(error=RuntimeError("down"))

        reviewer, _ = review(router)

        assert reviewer.reviews_used == 0


class TestFunnel:
    def test_only_promotion_candidates_are_reviewed(self):
        reviewer = SecondPassReviewer(FakeRouter(), {"min_local_score": 7.0})

        assert reviewer.should_review(8.0) is True
        assert reviewer.should_review(7.0) is True
        assert reviewer.should_review(6.9) is False
        assert reviewer.should_review(3.0) is False

    def test_disabled_reviews_nothing(self):
        reviewer = SecondPassReviewer(FakeRouter(), {"enabled": False})
        assert reviewer.should_review(9.9) is False

    def test_per_cycle_cap_stops_further_reviews(self):
        router = FakeRouter('{"verdict": "confirm", "reason": "ok"}')
        reviewer = SecondPassReviewer(router, {"max_reviews_per_cycle": 2})

        for _ in range(2):
            assert reviewer.should_review(8.0) is True
            asyncio.run(reviewer.review(title="t", content="c", local_score=8.0))

        assert reviewer.reviews_used == 2
        assert reviewer.should_review(8.0) is False

    def test_the_review_goes_through_the_paid_tier(self):
        router = FakeRouter('{"verdict": "confirm", "reason": "ok"}')

        review(router, config={"paid_tier": "review"})

        assert router.calls[0]["paid_tier"] == "review"

    def test_the_prompt_warns_about_local_score_inflation(self):
        # The reviewer is shown the local score for context; without the
        # warning it anchors on it, which is the failure the second pass
        # exists to break.
        router = FakeRouter('{"verdict": "confirm", "reason": "ok"}')

        review(router, local_score=8.0)

        prompt = router.calls[0]["prompt"]
        assert "8.0" in prompt
        assert "22" in prompt or "후하게" in prompt


class TestConfigContract:
    def test_defaults_are_loaded_into_the_backlog_config(self):
        from agentic_orchestrator.scheduler.tasks import _load_backlog_config

        config = _load_backlog_config()["second_pass"]
        assert config["paid_tier"] == "review"
        assert config["min_local_score"] == 7.0
        assert config["enabled"] is True

    def test_the_review_tier_exists_in_the_paid_tier_allowlist(self):
        from agentic_orchestrator.llm.router import HybridLLMRouter

        tiers = HybridLLMRouter._load_paid_tiers()
        assert "review" in tiers, "second pass needs its own tier entry"
        assert tiers["review"]["provider"] == "openai"

    @pytest.mark.parametrize("verdict_name", [CONFIRM, DEMOTE, REJECT])
    def test_every_verdict_round_trips_to_metadata(self, verdict_name):
        router = FakeRouter(f'{{"verdict": "{verdict_name}", "reason": "r", "score": 6}}')

        _, verdict = review(router)

        as_dict = verdict.to_dict()
        assert as_dict["verdict"] == verdict_name
        assert as_dict["model"] == "gpt-5.4-mini"
