"""Tests for the paid-provider kill switch and ledger (PR #2957 review).

Two disjoint paths reach a paid model, and until now only one was governed::

    router path   HybridLLMRouter.route() -> provider.generate()
                  -> _make_request()                    [gated + metered]
    legacy path   stage/backlog @property -> provider.complete()
                  -> _complete_with_retry() -> _make_request()   [neither]

The legacy path is the state machine (``ao step`` / ``ao loop``) and the
GitHub backlog orchestrator (``ao backlog run`` / ``process``). It builds
providers straight from ``create_*_provider``, so it consulted neither
``MOSS_LOCAL_LLM_ONLY`` nor ``BudgetController``. No PM2 job reaches it, but
both API keys sit in the server's ``.env``, so a manual ``ao`` run could
spend without limit or trace — on ``gpt-5.2-chat-latest`` ($2.50/$10.00 per
M), 3.3x the debate tier's ``gpt-5.4-mini``.

These tests pin the contract: the kill switch stops construction, every
billed completion on the legacy path lands in the ledger exactly once, the
budget cap is enforced before the call, and neither guard can break a call
when the ledger itself is down.
"""

import asyncio
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentic_orchestrator.providers.base import (
    BaseProvider,
    BudgetExhaustedError,
    CompletionResponse,
    Message,
    PaidProviderBlockedError,
    QuotaExhaustedError,
    RetryConfig,
    enforce_local_only,
    local_llm_only,
)

PAID_FACTORIES = ("claude", "openai", "gemini")


def import_factory(provider: str):
    module = __import__(f"agentic_orchestrator.providers.{provider}", fromlist=["create"])
    return getattr(module, f"create_{provider}_provider")


class FakeLedger:
    """Stand-in for BudgetController with a controllable cap."""

    def __init__(self, can_use_api=True, record_raises=False):
        self.can_use_api = can_use_api
        self.record_raises = record_raises
        self.recorded = []
        self.status_reads = 0

    def get_budget_status(self):
        self.status_reads += 1
        return {
            "can_use_api": self.can_use_api,
            "status": "ok",
            "daily": {"total_cost": 1.9, "daily_limit": 2.0},
            "monthly": {"total_cost": 99.0, "monthly_limit": 100.0},
        }

    def record_usage(self, provider, model, input_tokens, output_tokens):
        if self.record_raises:
            raise RuntimeError("no such table: api_usage")
        self.recorded.append((provider, model, input_tokens, output_tokens))
        return {}


class SpyProvider(BaseProvider):
    """Minimal paid provider: counts requests, returns fixed token usage."""

    provider_name = "spy"

    def __init__(self, usage=None, **kwargs):
        kwargs.setdefault("model", "gpt-5.2-chat-latest")
        # No sleeping between retries in tests.
        kwargs.setdefault("retry_config", RetryConfig(max_retries=0, initial_backoff=0))
        super().__init__(**kwargs)
        self._usage = {"prompt_tokens": 1000, "completion_tokens": 500} if usage is None else usage
        self.requests = 0

    def _make_request(self, messages, model, **kwargs):
        self.requests += 1
        return CompletionResponse(
            content="reply",
            model=model,
            provider=self.provider_name,
            usage=self._usage,
        )

    def is_available(self):
        return True


@pytest.fixture
def ledger(monkeypatch):
    """Attach a fake ledger to every provider instance."""
    fake = FakeLedger()
    monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: fake))
    return fake


@pytest.fixture(autouse=True)
def kill_switch_engaged(monkeypatch):
    """Default every test to the production-safe state (switch on)."""
    monkeypatch.delenv("MOSS_LOCAL_LLM_ONLY", raising=False)


class TestKillSwitchAtConstruction:
    """MOSS_LOCAL_LLM_ONLY must stop the legacy path, not just the router."""

    @pytest.mark.parametrize("provider", PAID_FACTORIES)
    def test_factory_refuses_while_the_switch_is_engaged(self, provider):
        with pytest.raises(PaidProviderBlockedError) as excinfo:
            import_factory(provider)()

        # The message has to tell an operator which switch to flip; this is
        # raised on a server shell, far from this code.
        assert "MOSS_LOCAL_LLM_ONLY" in str(excinfo.value)

    @pytest.mark.parametrize("provider", PAID_FACTORIES)
    def test_switch_off_allows_construction(self, provider, monkeypatch):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")

        assert import_factory(provider)() is not None

    @pytest.mark.parametrize("provider", PAID_FACTORIES)
    def test_dry_run_is_exempt(self, provider):
        # Dry-run providers return canned text and never reach the network.
        # Blocking them would break `--dry-run`, the safe way to rehearse
        # the legacy pipeline.
        assert import_factory(provider)(dry_run=True).dry_run is True

    def test_unset_flag_fails_closed(self):
        # The variable is absent on a fresh checkout and on any machine that
        # forgot it. Absent must mean "no spend".
        assert local_llm_only() is True
        with pytest.raises(PaidProviderBlockedError):
            enforce_local_only("openai")

    @pytest.mark.parametrize("value", ["false", "False", "FALSE", "0", "no", "off"])
    def test_recognized_off_values(self, value, monkeypatch):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", value)
        assert local_llm_only() is False
        enforce_local_only("openai")  # does not raise

    @pytest.mark.parametrize("value", ["true", "1", "yes", "", "maybe", "FALSE ", "nope"])
    def test_anything_else_keeps_the_switch_engaged(self, value, monkeypatch):
        # A typo'd value must not silently unlock spending.
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", value)
        assert local_llm_only() is True
        with pytest.raises(PaidProviderBlockedError):
            enforce_local_only("openai")

    @pytest.mark.parametrize("value", ["false", "true", "0", "junk"])
    def test_router_and_factories_read_one_flag_one_way(self, value, monkeypatch):
        # Before this change the router parsed the env var inline and the
        # factories ignored it entirely. If these two ever disagree, one
        # entry point spends while the other believes it is local-only.
        from agentic_orchestrator.llm.router import HybridLLMRouter

        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", value)
        router = HybridLLMRouter.__new__(HybridLLMRouter)
        HybridLLMRouter.__init__(router)

        assert router.local_only is local_llm_only()


class TestLegacyPathIsMetered:
    """Every billed completion on the legacy path reaches /usage — once."""

    def test_complete_records_usage(self, ledger, monkeypatch):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")
        provider = SpyProvider()

        provider.complete([Message(role="user", content="hi")])

        assert ledger.recorded == [("spy", "gpt-5.2-chat-latest", 1000, 500)]

    def test_chat_helper_is_metered_too(self, ledger):
        # `chat()` is the convenience wrapper the stages actually call.
        SpyProvider().chat("hi")

        assert ledger.recorded == [("spy", "gpt-5.2-chat-latest", 1000, 500)]

    def test_router_path_is_not_double_counted(self, ledger):
        # The router reaches _make_request through generate() and records
        # usage itself. If the legacy hook also fired there, every debate
        # turn would be billed to the ledger twice and the cap would bite at
        # half the real spend.
        from agentic_orchestrator.providers.openai import OpenAIProvider

        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider._client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kw: SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(content="hi"), finish_reason="stop"
                            )
                        ],
                        usage=SimpleNamespace(
                            prompt_tokens=10, completion_tokens=5, total_tokens=15
                        ),
                        model="gpt-5.4-mini",
                    )
                )
            )
        )
        provider.model = "gpt-5.4-mini"

        asyncio.run(provider.generate("hello", max_tokens=16))

        assert ledger.recorded == []

    def test_dry_run_is_never_recorded(self, ledger):
        # complete() short-circuits to a canned response before any request.
        SpyProvider(dry_run=True).complete([Message(role="user", content="hi")])

        assert ledger.recorded == []
        assert ledger.status_reads == 0

    def test_zero_token_response_is_not_recorded(self, ledger):
        # Claude's CLI mode reports no usage — it bills against the Claude
        # Code subscription, not the API. Recording zero-token rows would
        # inflate the request count in /usage without adding cost.
        SpyProvider(usage={}).complete([Message(role="user", content="hi")])

        assert ledger.recorded == []

    def test_ledger_write_failure_does_not_break_the_call(self, monkeypatch):
        # Metering is observability, not correctness: a broken api_usage
        # table must not take down `ao backlog run`.
        broken = FakeLedger(record_raises=True)
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: broken))

        result = SpyProvider().complete([Message(role="user", content="hi")])

        assert result.content == "reply"

    def test_unreachable_ledger_does_not_break_the_call(self, monkeypatch):
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: None))

        assert SpyProvider().complete([Message(role="user", content="hi")]).content == "reply"


class TestBudgetCeiling:
    """The cap is checked before the request, not discovered after it."""

    def test_exhausted_budget_refuses_before_spending(self, monkeypatch):
        spent = FakeLedger(can_use_api=False)
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: spent))
        provider = SpyProvider()

        with pytest.raises(BudgetExhaustedError):
            provider.complete([Message(role="user", content="hi")])

        assert provider.requests == 0  # refused, not billed-then-refused

    def test_refusal_names_the_numbers(self, monkeypatch):
        spent = FakeLedger(can_use_api=False)
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: spent))

        with pytest.raises(BudgetExhaustedError) as excinfo:
            SpyProvider().complete([Message(role="user", content="hi")])

        message = str(excinfo.value)
        assert "2.00" in message and "100.00" in message

    def test_budget_error_is_a_quota_error(self):
        # The state machine already pauses and alerts on QuotaExhaustedError
        # (stages/quality.py). Subclassing gets a spent budget that handling
        # for free instead of a raw traceback.
        assert issubclass(BudgetExhaustedError, QuotaExhaustedError)
        assert BudgetExhaustedError("x").quota_type == "budget"

    def test_budget_refusal_is_not_retried(self, monkeypatch):
        # _complete_with_retry re-raises QuotaExhaustedError without backoff;
        # retrying a spent budget would just stall the run.
        spent = FakeLedger(can_use_api=False)
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: spent))
        provider = SpyProvider(retry_config=RetryConfig(max_retries=3, initial_backoff=0))

        with pytest.raises(BudgetExhaustedError):
            provider.complete([Message(role="user", content="hi")])

        assert spent.status_reads == 1

    def test_unreadable_status_fails_open(self, monkeypatch):
        # A broken DB should not take down the pipeline; the kill switch and
        # the provider's own quota errors remain as backstops.
        class Unreadable(FakeLedger):
            def get_budget_status(self):
                raise RuntimeError("database is locked")

        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: Unreadable()))

        assert SpyProvider().complete([Message(role="user", content="hi")]).content == "reply"


class TestGeminiOverriddenComplete:
    """Gemini overrides complete() and never calls super() — the trap."""

    def test_gemini_complete_still_routes_through_the_guarded_path(self):
        # Governing BaseProvider.complete() alone would have left Gemini
        # ungated and unmetered. _complete_with_retry is the shared floor.
        source = Path("src/agentic_orchestrator/providers/gemini.py").read_text()
        override = source.split("    def complete(")[1]

        assert "super().complete(" not in override
        assert "_complete_with_retry(" in override

    def test_gemini_multi_level_fallback_is_metered(self, ledger, monkeypatch):
        from agentic_orchestrator.providers.gemini import GeminiProvider

        provider = GeminiProvider.__new__(GeminiProvider)
        BaseProvider.__init__(
            provider,
            model="gemini-3-pro",
            fallback_model="gemini-3-flash",
            retry_config=RetryConfig(max_retries=0, initial_backoff=0),
        )
        provider.secondary_fallback = None
        calls = []

        def fake_request(messages, model, **kwargs):
            calls.append(model)
            if model == "gemini-3-pro":
                from agentic_orchestrator.providers.base import ModelNotAvailableError

                raise ModelNotAvailableError("gone", provider="gemini", model=model)
            return CompletionResponse(
                content="ok",
                model=model,
                provider="gemini",
                usage={"prompt_tokens": 7, "completion_tokens": 3},
            )

        monkeypatch.setattr(provider, "_make_request", fake_request)

        provider.complete([Message(role="user", content="hi")])

        # Only the model that actually answered is billed.
        assert calls == ["gemini-3-pro", "gemini-3-flash"]
        assert ledger.recorded == [("gemini", "gemini-3-flash", 7, 3)]


class TestSourceInvariants:
    """Structural pins so a new paid path cannot slip through ungated."""

    def test_every_paid_factory_calls_the_gate(self):
        for provider in PAID_FACTORIES:
            source = Path(f"src/agentic_orchestrator/providers/{provider}.py").read_text()
            factory = source.split(f"def create_{provider}_provider(")[1]
            assert "enforce_local_only(" in factory, f"{provider} factory is ungated"

    def test_paid_providers_are_only_built_via_factories_or_the_router(self):
        # Direct construction bypasses the factory gate. The router is the
        # one legitimate exception: it builds providers itself but guards
        # with `if self.local_only: return` in _init_api_providers.
        offenders = []
        for path in Path("src/agentic_orchestrator").rglob("*.py"):
            if path.parts[-2] == "providers" or path.name == "router.py":
                continue
            source = path.read_text()
            for match in re.findall(r"\b(Claude|OpenAI|Gemini)Provider\(", source):
                offenders.append(f"{path}: {match}Provider(")

        assert offenders == [], f"paid providers built outside the gate: {offenders}"

    def test_router_guards_its_own_direct_construction(self):
        source = Path("src/agentic_orchestrator/llm/router.py").read_text()
        init = source.split("def _init_api_providers(")[1].split("async def")[0]

        assert "if self.local_only:" in init
        assert "return" in init

    def test_the_three_reported_call_sites_are_covered(self):
        # The sites pre-merge review of PR #2957 flagged. They reach paid
        # models only through the factories, so the gate covers them; this
        # fails loudly if one is rewritten to construct a provider directly.
        for path in (
            "src/agentic_orchestrator/backlog.py",
            "src/agentic_orchestrator/stages/planning.py",
            "src/agentic_orchestrator/stages/quality.py",
        ):
            source = Path(path).read_text()
            assert re.search(r"create_(claude|openai|gemini)_provider\(", source)
            assert not re.search(r"\b(Claude|OpenAI|Gemini)Provider\(", source)
