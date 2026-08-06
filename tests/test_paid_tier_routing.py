"""Tests for the paid-tier LLM routing (v0.6.19).

The debate is the one task allowed to spend money (config
``llm.paid_tiers.debate`` → gpt-5.4-mini); everything else stays on local
Ollama. These tests pin the safety contract: flipping
``MOSS_LOCAL_LLM_ONLY=false`` alone spends nothing, every missing
precondition (tier disabled, provider absent, budget exhausted,
force_local, explicit model) degrades to local rather than failing, and
the four debate call sites actually carry the tier tag.

The degradation is deliberate but no longer silent: see
``TestDegradationIsVisible`` for the WARNING contract added after the
2026-08-06 incident, where a stale PM2 env ran a full day of debates on
local gemma with nothing anywhere reporting it.
"""

import asyncio
import logging
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentic_orchestrator.llm.budget import BudgetController
from agentic_orchestrator.llm.hierarchy import LLMHierarchy
from agentic_orchestrator.llm.router import (
    HybridLLMRouter,
    describe_paid_tier,
    paid_tier_report,
)

DEBATE_TIER = {"debate": {"enabled": True, "provider": "openai", "model": "gpt-5.4-mini"}}


class FakeBudget:
    def __init__(self, can_use_api=True):
        self.can_use_api = can_use_api
        self.recorded = []

    def get_budget_status(self):
        return {"can_use_api": self.can_use_api, "status": "ok"}

    def should_use_local(self):
        return not self.can_use_api

    def estimate_cost(self, model, input_tokens, output_tokens):
        return 0.0

    def record_usage(self, provider, model, input_tokens, output_tokens):
        self.recorded.append((provider, model, input_tokens, output_tokens))
        return {}


class FakeOpenAI:
    def __init__(self):
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        return {"content": "api reply", "input_tokens": 100, "output_tokens": 40}


class BrokenOpenAI:
    """A paid provider whose calls fail (rate limit, 400, network)."""

    def __init__(self):
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("429 rate limited")


class FlakyOpenAI:
    """Fails the first `fail_times` calls, then succeeds."""

    def __init__(self, fail_times=1):
        self.fail_times = fail_times
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) <= self.fail_times:
            raise RuntimeError("503 upstream")
        return {"content": "api reply", "input_tokens": 100, "output_tokens": 40}


class FakeOllama:
    def __init__(self):
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content="local reply", input_tokens=0, output_tokens=0)


def make_router(
    paid_tiers=None,
    openai=None,
    local_only=False,
    budget=None,
):
    router = HybridLLMRouter.__new__(HybridLLMRouter)
    router.local_only = local_only
    router.ollama = FakeOllama()
    router.claude = None
    router.openai = openai
    router.hierarchy = LLMHierarchy()
    router.budget = budget if budget is not None else FakeBudget()
    router.paid_tiers = paid_tiers or {}
    return router


def route(router, **kwargs):
    return asyncio.run(router.route(prompt="p", **kwargs))


class TestPaidTierRouting:
    def test_debate_tier_reaches_the_api_model(self):
        api = FakeOpenAI()
        budget = FakeBudget()
        router = make_router(paid_tiers=DEBATE_TIER, openai=api, budget=budget)

        response = route(router, paid_tier="debate")

        assert response.provider == "openai"
        assert response.model == "gpt-5.4-mini"
        assert api.calls and api.calls[0]["model"] == "gpt-5.4-mini"
        assert budget.recorded == [("openai", "gpt-5.4-mini", 100, 40)]
        assert router.ollama.calls == []

    def test_flag_alone_spends_nothing(self):
        # THE safety pin: local_only=False with a live provider and budget,
        # but no paid_tier on the call -> still local. Flipping the env flag
        # must never be sufficient to spend money.
        api = FakeOpenAI()
        router = make_router(paid_tiers=DEBATE_TIER, openai=api)

        response = route(router)

        assert response.provider == "ollama"
        assert api.calls == []

    def test_local_only_mode_kills_the_tier(self):
        # In local-only mode route() forces force_local=True, which must
        # absorb the tier even if a provider object were somehow present.
        api = FakeOpenAI()
        router = make_router(paid_tiers=DEBATE_TIER, openai=api, local_only=True)

        response = route(router, paid_tier="debate")

        assert response.provider == "ollama"
        assert api.calls == []

    def test_exhausted_budget_degrades_to_local(self):
        api = FakeOpenAI()
        router = make_router(
            paid_tiers=DEBATE_TIER, openai=api, budget=FakeBudget(can_use_api=False)
        )

        response = route(router, paid_tier="debate")

        assert response.provider == "ollama"
        assert api.calls == []

    def test_disabled_or_unknown_tier_stays_local(self):
        api = FakeOpenAI()
        disabled = {"debate": {**DEBATE_TIER["debate"], "enabled": False}}
        router = make_router(paid_tiers=disabled, openai=api)
        assert route(router, paid_tier="debate").provider == "ollama"

        router = make_router(paid_tiers={}, openai=api)
        assert route(router, paid_tier="debate").provider == "ollama"
        assert api.calls == []

    def test_missing_provider_stays_local(self):
        # Tier enabled in config but MOSS_LOCAL_LLM_ONLY never initialized
        # the provider (or no key): fall back to local, don't crash.
        router = make_router(paid_tiers=DEBATE_TIER, openai=None)

        response = route(router, paid_tier="debate")

        assert response.provider == "ollama"

    def test_explicit_model_and_force_local_beat_the_tier(self):
        api = FakeOpenAI()
        router = make_router(paid_tiers=DEBATE_TIER, openai=api)

        assert route(router, paid_tier="debate", model="gemma3:4b").model == "gemma3:4b"
        assert route(router, paid_tier="debate", force_local=True).provider == "ollama"
        assert api.calls == []


class TestSpendAccounting:
    """The budget ledger is the only spend control — it must stay truthful."""

    def test_failed_paid_call_never_degrades_to_local(self):
        # A pinned tier must NOT become a local call on failure. Degrading a
        # debate turn to gemma3:4b mid-round mixes two models' output quality
        # invisibly AND pushes load onto the congested Ollama path the tier
        # exists to escape. It retries itself briefly, then raises; the
        # scheduler's next cron tick is the real retry.
        budget = FakeBudget()
        api = BrokenOpenAI()
        router = make_router(paid_tiers=DEBATE_TIER, openai=api, budget=budget)
        router._paid_tier_retries = 2
        router._paid_tier_backoff = 0.0

        with pytest.raises(RuntimeError):
            route(router, paid_tier="debate")

        assert router.ollama.calls == []  # never touched local
        assert budget.recorded == []  # nothing billed
        assert len(api.calls) == 3  # first attempt + 2 retries

    def test_paid_tier_retry_can_recover_without_touching_local(self):
        budget = FakeBudget()
        api = FlakyOpenAI(fail_times=1)
        router = make_router(paid_tiers=DEBATE_TIER, openai=api, budget=budget)
        router._paid_tier_retries = 2
        router._paid_tier_backoff = 0.0

        response = route(router, paid_tier="debate")

        assert response.provider == "openai"
        assert router.ollama.calls == []
        assert budget.recorded == [("openai", "gpt-5.4-mini", 100, 40)]

    def test_untagged_calls_keep_their_local_fallback(self):
        # Only the pinned tier loses the fallback. An ordinary call that
        # selected a model and failed still degrades as before.
        router = make_router(paid_tiers=DEBATE_TIER, openai=FakeOpenAI())
        assert route(router).provider == "ollama"

    def test_config_budget_limits_are_actually_enforced(self):
        # The config.yaml `budget:` block was decorative until v0.6.19:
        # limits came only from env vars whose defaults happened to match,
        # so raising the file's numbers for the paid tier changed nothing
        # and the tier would have degraded to local part-way through a day.
        import yaml

        configured = yaml.safe_load(Path("config.yaml").read_text())["budget"]
        controller = BudgetController()

        assert controller.budget.daily_limit_usd == configured["daily_limit_usd"]
        assert controller.budget.monthly_limit_usd == configured["monthly_limit_usd"]

    def test_env_var_overrides_the_config_file(self, monkeypatch):
        monkeypatch.setenv("DAILY_BUDGET_USD", "7.5")
        assert BudgetController().budget.daily_limit_usd == 7.5

    def test_unreadable_budget_value_falls_back_to_the_default(self, monkeypatch):
        monkeypatch.setenv("DAILY_BUDGET_USD", "not-a-number")
        assert BudgetController().budget.daily_limit_usd == 1.0


class TestMalformedConfig:
    def test_malformed_tier_is_dropped_at_load(self, monkeypatch):
        # A one-line YAML typo (`debate: true`) must not reach route(),
        # where `tier.get(...)` on a bool raises AttributeError outside the
        # try/fallback block — killing the debate instead of degrading it.
        import yaml

        monkeypatch.setattr(
            yaml,
            "safe_load",
            lambda *a, **kw: {"llm": {"paid_tiers": {"debate": True, "good": {"enabled": False}}}},
        )
        loaded = HybridLLMRouter._load_paid_tiers()

        assert "debate" not in loaded
        assert loaded["good"] == {"enabled": False}

    def test_real_config_tiers_are_well_formed(self):
        assert all(isinstance(v, dict) for v in HybridLLMRouter._load_paid_tiers().values())

    def test_malformed_tier_degrades_instead_of_raising(self):
        api = FakeOpenAI()
        for junk in (True, "gpt-5.4-mini", ["gpt-5.4-mini"]):
            router = make_router(paid_tiers={"debate": junk}, openai=api)
            assert route(router, paid_tier="debate").provider == "ollama"
        assert api.calls == []


class TestRegistryAndPricing:
    def test_tier_model_is_registered_with_its_provider(self):
        # Without this entry the router would resolve provider "ollama" for
        # gpt-5.4-mini and send the OpenAI model name to Ollama (404).
        config = LLMHierarchy().get_model_config("gpt-5.4-mini")
        assert config is not None
        assert config.provider == "openai"

    def test_pricing_table_knows_the_tier_model(self):
        controller = BudgetController()
        cost = controller.estimate_cost("gpt-5.4-mini", 1_000_000, 1_000_000)
        assert cost == 0.75 + 4.50


class TestOpenAIProviderParams:
    def test_generate_sends_max_completion_tokens_not_max_tokens(self):
        # GPT-5-family models 400 on the legacy `max_tokens` ("Use
        # 'max_completion_tokens' instead" — verified live 2026-08-06).
        # With the wrong parameter the router silently falls back to local
        # gemma and the paid debate tier becomes a no-op.
        from agentic_orchestrator.providers.openai import OpenAIProvider

        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(message=SimpleNamespace(content="hi"), finish_reason="stop")
                    ],
                    usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                    model="gpt-5.4-mini",
                )

        provider = OpenAIProvider.__new__(OpenAIProvider)
        # `client` is a lazy property backed by `_client`
        provider._client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        provider.model = "gpt-5.4-mini"

        result = asyncio.run(provider.generate("hello", max_tokens=512))

        assert captured["max_completion_tokens"] == 512
        assert "max_tokens" not in captured
        assert result["content"] == "hi"

    def test_generate_does_not_block_the_event_loop(self):
        # The OpenAI SDK client is synchronous; called directly from the
        # coroutine it would stall every other task on the loop, serializing
        # a debate round's concurrent agents (the Ollama path it replaces is
        # genuinely async). Pinned by running a heartbeat alongside a call
        # that sleeps in its synchronous body.
        import time

        from agentic_orchestrator.providers.openai import OpenAIProvider

        class SlowCompletions:
            def create(self, **kwargs):
                time.sleep(0.3)
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(message=SimpleNamespace(content="hi"), finish_reason="stop")
                    ],
                    usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                    model="gpt-5.4-mini",
                )

        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider._client = SimpleNamespace(chat=SimpleNamespace(completions=SlowCompletions()))
        provider.model = "gpt-5.4-mini"

        async def scenario():
            ticks = 0

            async def heartbeat():
                nonlocal ticks
                while True:
                    await asyncio.sleep(0.01)
                    ticks += 1

            beat = asyncio.ensure_future(heartbeat())
            await provider.generate("hello", max_tokens=16)
            beat.cancel()
            return ticks

        # A blocking call yields ~0 ticks; an offloaded one yields many.
        assert asyncio.run(scenario()) > 5

    def test_empty_completion_raises_instead_of_returning_blank(self):
        # GPT-5-family models spend reasoning tokens against
        # max_completion_tokens and can return finish_reason="length" with
        # no text — billed all the same. Returning it silently would feed an
        # empty turn into the debate; raising lets the router fall back.
        from agentic_orchestrator.providers.base import ProviderError
        from agentic_orchestrator.providers.openai import OpenAIProvider

        class EmptyCompletions:
            def create(self, **kwargs):
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(message=SimpleNamespace(content=""), finish_reason="length")
                    ],
                    usage=SimpleNamespace(
                        prompt_tokens=900, completion_tokens=2000, total_tokens=2900
                    ),
                    model="gpt-5.4-mini",
                )

        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider._client = SimpleNamespace(chat=SimpleNamespace(completions=EmptyCompletions()))
        provider.model = "gpt-5.4-mini"

        try:
            asyncio.run(provider.generate("hello", max_tokens=2000))
        except ProviderError as e:
            assert "empty completion" in str(e)
        else:
            raise AssertionError("expected ProviderError for an empty completion")

    def test_client_disables_sdk_retries(self):
        # The SDK default (max_retries=2) silently re-sends on timeouts and
        # 429/5xx; OpenAI bills every server-side attempt but only the
        # returned one reaches record_usage, so the ledger under-counts.
        source = Path("src/agentic_orchestrator/providers/openai.py").read_text()
        assert "max_retries=0" in source


class TestDebateCallSitesCarryTheTier:
    def test_every_debate_route_call_is_tier_tagged(self):
        # Source invariant: the four debate LLM calls (divergence,
        # convergence, planning, quality gate) must all name the tier —
        # an untagged call silently runs the debate on gemma3:4b again.
        source = Path("src/agentic_orchestrator/debate/multi_stage.py").read_text()
        route_calls = len(re.findall(r"\.route\(", source))
        tier_tags = source.count('paid_tier="debate"')
        assert route_calls == 4
        assert tier_tags == 4


class TestDegradationIsVisible:
    """The degradation must stay, but it must never be silent (2026-08-06).

    For a full day every debate ran on local gemma3:4b because PM2 handed the
    scheduler a stale ``MOSS_LOCAL_LLM_ONLY=true``. Nothing surfaced it: the
    fallback is by design, so there was no error, no alert, and ``/status``
    reported healthy. The only evidence was a $0.00 ledger. These tests pin
    the fix — every non-caller reason is announced at WARNING, exactly once,
    and names the switch an operator has to flip.
    """

    @staticmethod
    def _warnings(caplog):
        return [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]

    def test_local_only_degradation_warns_and_names_the_flag(self, caplog):
        router = make_router(paid_tiers=DEBATE_TIER, openai=FakeOpenAI(), local_only=True)

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            assert route(router, paid_tier="debate").provider == "ollama"

        warnings = self._warnings(caplog)
        assert len(warnings) == 1
        assert "MOSS_LOCAL_LLM_ONLY" in warnings[0]
        assert "debate" in warnings[0]

    def test_exhausted_budget_degradation_warns(self, caplog):
        router = make_router(
            paid_tiers=DEBATE_TIER, openai=FakeOpenAI(), budget=FakeBudget(can_use_api=False)
        )

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            route(router, paid_tier="debate")

        assert "budget" in self._warnings(caplog)[0].lower()

    def test_disabled_tier_degradation_warns(self, caplog):
        disabled = {"debate": {**DEBATE_TIER["debate"], "enabled": False}}
        router = make_router(paid_tiers=disabled, openai=FakeOpenAI())

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            route(router, paid_tier="debate")

        assert "disabled" in self._warnings(caplog)[0]

    def test_missing_provider_degradation_warns(self, caplog):
        router = make_router(paid_tiers=DEBATE_TIER, openai=None)

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            route(router, paid_tier="debate")

        assert "unavailable" in self._warnings(caplog)[0]

    def test_active_tier_says_nothing(self, caplog):
        router = make_router(paid_tiers=DEBATE_TIER, openai=FakeOpenAI())

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            assert route(router, paid_tier="debate").provider == "openai"

        assert self._warnings(caplog) == []

    def test_caller_override_is_not_a_warning(self, caplog):
        # Passing an explicit model / force_local is the documented per-call
        # opt-out. Warning on it would train operators to ignore the channel.
        router = make_router(paid_tiers=DEBATE_TIER, openai=FakeOpenAI())

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            route(router, paid_tier="debate", model="gemma3:4b")
            route(router, paid_tier="debate", force_local=True)

        assert self._warnings(caplog) == []

    def test_warning_is_emitted_once_not_per_call(self, caplog):
        # One debate routes ~38 calls. The operator needs the fact once.
        router = make_router(paid_tiers=DEBATE_TIER, openai=FakeOpenAI(), local_only=True)

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            for _ in range(5):
                route(router, paid_tier="debate")

        assert len(self._warnings(caplog)) == 1

    def test_broken_ledger_does_not_break_the_diagnostics(self, caplog):
        # The reason lookup reads the budget. If the ledger is down it must
        # degrade to "reason unknown" and keep going -- diagnostics may not
        # raise into a debate that is otherwise fine.
        class ExplodingBudget(FakeBudget):
            def get_budget_status(self):
                raise RuntimeError("ledger down")

        router = make_router(paid_tiers=DEBATE_TIER, openai=None, budget=ExplodingBudget())

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator.llm.router"):
            router._warn_tier_degraded("debate", caller_model=None, caller_forced_local=False)

        # Still reports the precondition it could see (no provider), not the
        # ledger it could not.
        assert "unavailable" in self._warnings(caplog)[0]

    def test_router_built_without_init_still_routes(self):
        # make_router() bypasses __init__, as may any caller poking at the
        # public paid_tiers attribute. A missing diagnostics attribute must
        # not become an AttributeError on the hot path.
        router = make_router(paid_tiers=DEBATE_TIER, openai=None)
        assert not hasattr(router, "_degraded_tiers_warned")
        assert route(router, paid_tier="debate").provider == "ollama"


class TestPaidTierReport:
    """The endpoint-facing view, shared with route() so they cannot drift."""

    def test_reason_precedence_reports_the_first_switch_to_flip(self):
        tier = {"enabled": True, "provider": "openai", "model": "gpt-5.4-mini"}

        # Every case below breaks EVERY remaining precondition at once, so the
        # branches are genuinely in contention and the assertion pins the
        # ordering rather than just "some reason came back". Reordering any two
        # arms of describe_paid_tier must fail this test.

        # Kill switch outranks everything else: it is the operator's first fix.
        killed = describe_paid_tier(
            "debate",
            {**tier, "enabled": False},
            local_only=True,
            provider_ready=False,
            budget_ok=False,
        )
        assert killed["active"] is False
        assert "MOSS_LOCAL_LLM_ONLY" in killed["reason"]

        # With the switch off, the next unmet precondition surfaces in turn.
        assert (
            "disabled"
            in describe_paid_tier(
                "debate",
                {**tier, "enabled": False},
                local_only=False,
                provider_ready=False,
                budget_ok=False,
            )["reason"]
        )
        assert (
            "unavailable"
            in describe_paid_tier(
                "debate", tier, local_only=False, provider_ready=False, budget_ok=False
            )["reason"]
        )
        assert (
            "budget"
            in describe_paid_tier(
                "debate", tier, local_only=False, provider_ready=True, budget_ok=False
            )["reason"].lower()
        )

        healthy = describe_paid_tier(
            "debate", tier, local_only=False, provider_ready=True, budget_ok=True
        )
        assert healthy["active"] is True and healthy["reason"] is None

    def test_unchecked_preconditions_do_not_fabricate_a_failure(self):
        # /status cannot afford a ledger read; "not checked" must not read as
        # "exhausted", or the endpoint would cry wolf on every request.
        state = describe_paid_tier(
            "debate",
            {"enabled": True, "provider": "openai", "model": "gpt-5.4-mini"},
            local_only=False,
            provider_ready=True,
            budget_ok=None,
        )
        assert state["active"] is True

    def test_report_flags_the_real_config_as_degraded_under_the_kill_switch(self, monkeypatch):
        # End to end against the shipped config.yaml: the debate tier is
        # enabled there, so engaging the kill switch must show up as degraded
        # rather than as a healthy all-local system.
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "true")
        report = paid_tier_report()
        assert report["status"] == "degraded"
        assert report["local_only"] is True
        assert "debate" in report["degraded_tiers"]
        assert "MOSS_LOCAL_LLM_ONLY" in report["paid_tiers"]["debate"]["reason"]

    def test_report_is_healthy_when_the_tier_can_actually_spend(self, monkeypatch):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        report = paid_tier_report(budget_ok=True)
        assert report["status"] == "healthy"
        assert report["degraded_tiers"] == []
        assert report["paid_tiers"]["debate"]["model"] == "gpt-5.4-mini"

    def test_config_is_parsed_once_per_process_not_per_request(self, monkeypatch):
        # /status is public, unauthenticated, uncached and `async def` on a
        # single-instance app. Re-reading and YAML-parsing the 22 KB
        # config.yaml per request put ~8 ms of blocking CPU on the event loop
        # -- several times the rest of the handler. Same contract as the RSS
        # feed list: a config edit takes effect on restart.
        import agentic_orchestrator.llm.router as router_mod

        monkeypatch.setattr(router_mod, "_PAID_TIERS_CACHE", None)
        loads = []
        real = HybridLLMRouter._load_paid_tiers

        def counting_load():
            loads.append(1)
            return real()

        monkeypatch.setattr(HybridLLMRouter, "_load_paid_tiers", staticmethod(counting_load))
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "true")

        for _ in range(10):
            paid_tier_report()

        assert len(loads) == 1, f"config.yaml parsed {len(loads)}x for 10 requests"

    def test_caching_the_parse_does_not_freeze_the_verdict(self, monkeypatch):
        # Only the file parse is cached. If the verdict were cached too, the
        # endpoint would keep reporting healthy after the kill switch was
        # engaged -- i.e. the monitoring added to catch a silently dead tier
        # would itself go silently stale.
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        assert paid_tier_report(budget_ok=True)["status"] == "healthy"

        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "true")
        assert paid_tier_report(budget_ok=True)["status"] == "degraded"

        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")
        assert paid_tier_report(budget_ok=False)["status"] == "degraded"
        assert paid_tier_report(budget_ok=True)["status"] == "healthy"

    def test_every_configured_tier_is_reported_not_just_debate(self):
        # The report iterates config, so a tier added later (v0.6.22 added
        # `review` for second-pass promotion) is covered with no code change.
        # A hardcoded "debate" would leave the new tier unobservable.
        from agentic_orchestrator.llm.router import _cached_paid_tiers

        configured = set(_cached_paid_tiers())
        assert "debate" in configured
        assert configured == set(paid_tier_report()["paid_tiers"])

    def test_missing_api_key_is_reported_without_touching_the_network(self, monkeypatch):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        report = paid_tier_report()
        assert report["status"] == "degraded"
        assert "OPENAI_API_KEY" in report["paid_tiers"]["debate"]["reason"]
