"""Tests for the paid-tier LLM routing (v0.6.19).

The debate is the one task allowed to spend money (config
``llm.paid_tiers.debate`` → gpt-5.4-mini); everything else stays on local
Ollama. These tests pin the safety contract: flipping
``MOSS_LOCAL_LLM_ONLY=false`` alone spends nothing, every missing
precondition (tier disabled, provider absent, budget exhausted,
force_local, explicit model) degrades to local silently, and the four
debate call sites actually carry the tier tag.
"""

import asyncio
import re
from pathlib import Path
from types import SimpleNamespace

from agentic_orchestrator.llm.budget import BudgetController
from agentic_orchestrator.llm.hierarchy import LLMHierarchy
from agentic_orchestrator.llm.router import HybridLLMRouter

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

    def test_failed_paid_call_falls_back_local_and_records_no_usage(self):
        budget = FakeBudget()
        router = make_router(paid_tiers=DEBATE_TIER, openai=BrokenOpenAI(), budget=budget)

        response = route(router, paid_tier="debate")

        assert response.provider == "ollama"  # debate degrades, never dies
        assert budget.recorded == []  # and nothing is billed to the ledger

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
