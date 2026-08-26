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
import logging
from types import SimpleNamespace

import pytest

from agentic_orchestrator.scoring.second_pass import (
    CONFIRM,
    DEMOTE,
    ORG_PROFILE_ABSENT,
    REJECT,
    UNAVAILABLE,
    ReviewVerdict,
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


class TestTheConfirmBarIsReachable:
    """3,166 DEMOTE, 2 REJECT, zero CONFIRM — the gate's entire life.

    Measured 2026-08-26 across every production log the reviewer ever wrote.
    Its own independent score never exceeded 6.8 in 3,168 trials. Promotion
    stopped on 2026-08-05 and plan creation on 2026-08-06 while debates kept
    running four times a day at ~$2.3/day, because BOTH promotion paths — the
    debate cycle and backlog triage — route through this one object.

    Duplication was not what did it. Of the demote reasons, 75.6% cited a
    1-2 week MVP scope that could not be verified and 45.9% a weak connection
    to Mossland; only 20.0% mentioned duplication at all. The top two were
    questions the reviewer had no way to answer — and "cannot tell" reads as
    "no". These tests pin the three properties that make the bar answerable;
    they cannot pin the model's behaviour, which is what
    ``log_cycle_summary`` is for.
    """

    def test_the_org_profile_reaches_the_prompt(self):
        """45.9% of demotes cited weak Mossland relevance in a prompt that
        never said what Mossland is."""
        router = FakeRouter('{"verdict": "confirm", "reason": "r"}')
        reviewer = SecondPassReviewer(router, {"org_profile": "MOC 토큰과 DAO 거버넌스"})

        asyncio.run(reviewer.review(title="t", content="c", local_score=8.0))

        assert "MOC 토큰과 DAO 거버넌스" in router.calls[0]["prompt"]

    def test_an_unset_profile_disarms_the_criterion_instead_of_sinking_it(self):
        """Left to itself the model answers an ungrounded relevance question
        with "unclear", which lands as a demote. With no profile configured
        the prompt has to say so and take the criterion off the table."""
        router = FakeRouter('{"verdict": "confirm", "reason": "r"}')
        reviewer = SecondPassReviewer(router, {"org_profile": "   "})

        asyncio.run(reviewer.review(title="t", content="c", local_score=8.0))
        prompt = router.calls[0]["prompt"]

        assert ORG_PROFILE_ABSENT in prompt
        assert "감점하지 마세요" in prompt

    def test_the_prompt_does_not_demand_the_next_stages_output(self):
        """Promotion is what SENDS an idea to the planning stage that writes
        the execution plan. Requiring a verified 1-2 week MVP scope first made
        the output of planning the entry price of reaching it — 75.6% of
        demotes cited exactly that. The idea text usually DOES carry an
        mvp_scope (the divergence template mandates one); what the reviewer
        cannot do is verify it, so the instruction has to cover both."""
        router = FakeRouter('{"verdict": "confirm", "reason": "r"}')
        reviewer = SecondPassReviewer(router)

        asyncio.run(reviewer.review(title="t", content="c", local_score=8.0))
        prompt = router.calls[0]["prompt"]

        assert "적혀 있어도 지금 검증할 수 없다는 이유로 demote하지 마세요" in prompt

    def test_the_prompt_does_not_undersell_what_a_confirm_costs(self):
        """The correction must not overshoot into the mirror-image error.

        Rebalancing away from "a wrong demote is cheap" is right, but claiming
        a confirm only ever buys a draft for a human to approve is equally
        false: on the debate path the FIRST promoted idea of a cycle carries
        the debate's own final_plan and is written with ``status="approved"``
        whenever its local score clears ``auto_generate.min_score``
        (tasks.py). No human sees it. Only ``auto_generate.enabled: false``
        stops that plan from scaffolding a project, and that switch is meant
        to come back on."""
        router = FakeRouter('{"verdict": "confirm", "reason": "r"}')
        reviewer = SecondPassReviewer(router)

        asyncio.run(reviewer.review(title="t", content="c", local_score=8.0))
        prompt = router.calls[0]["prompt"]

        assert "사람 승인 없이 확정되기도 하므로" in prompt

    def test_the_prompt_states_what_a_demote_actually_costs(self):
        """It used to tell the reviewer a wrong demote is cheap. The code says
        otherwise: triage turns each DEMOTE into a strike and archives the idea
        permanently at two (``backlog.triage.max_strikes``). A judge given a
        false cost model will not calibrate."""
        router = FakeRouter('{"verdict": "confirm", "reason": "r"}')
        reviewer = SecondPassReviewer(router)

        asyncio.run(reviewer.review(title="t", content="c", local_score=8.0))
        prompt = router.calls[0]["prompt"]

        assert "영구 아카이브" in prompt
        assert (
            "훨씬 비쌉니다" not in prompt
        ), "the one-sided cost claim is what the 0% confirm rate was calibrated to"

    def test_the_gate_still_needs_an_explicit_confirm(self):
        """Rebalancing the prompt must not touch the fail-closed property.
        Nothing but CONFIRM promotes, and absence never does."""
        for content in (
            '{"verdict": "demote", "reason": "r"}',
            '{"verdict": "reject", "reason": "r"}',
            "not json at all",
        ):
            _, verdict = review(FakeRouter(content))
            assert verdict.promotes is False


class TestNothingConfirmedIsSaidOutLoud:
    """``GET /usage`` reported ``no_confirmations`` for 21 days and nobody read
    it. An endpoint is a pull; this is the push, from the process that did the
    reviewing, into the log an operator already tails when output goes quiet.
    """

    @staticmethod
    def _cycle(verdicts, config=None):
        reviewer = SecondPassReviewer(FakeRouter(None), config)
        for verdict in verdicts:
            reviewer._record(ReviewVerdict(verdict))
        return reviewer

    def test_a_cycle_that_confirms_nothing_is_an_error(self, caplog):
        reviewer = self._cycle([DEMOTE] * 8)

        with caplog.at_level(logging.ERROR):
            reviewer.log_cycle_summary("debate cycle")

        assert reviewer.starved is True
        assert "NOTHING was confirmed" in caplog.text
        assert "promotion_review" in caplog.text

    def test_one_confirmation_is_enough_to_stay_quiet(self):
        assert self._cycle([CONFIRM] + [DEMOTE] * 20).starved is False

    def test_a_short_cycle_is_not_an_incident(self):
        """Three demotes in a row is an ordinary Tuesday. The signal has to
        mean something when it fires."""
        assert self._cycle([DEMOTE] * 3).starved is False

    def test_unavailable_verdicts_do_not_make_a_cycle_look_decisive(self):
        """A provider outage is not a gate refusing candidates. Counting it as
        one would report every outage as a stalled pipeline."""
        assert self._cycle([UNAVAILABLE] * 20).starved is False

    def test_the_threshold_is_configurable(self):
        assert self._cycle([DEMOTE] * 2, {"starvation_min_reviews": 2}).starved is True
