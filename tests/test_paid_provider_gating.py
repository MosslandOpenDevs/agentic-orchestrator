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
from contextlib import contextmanager
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

    # Also used when this ledger is handed to the real HybridLLMRouter.
    def should_use_local(self):
        return not self.can_use_api

    def estimate_cost(self, model, input_tokens, output_tokens):
        return 0.0


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
        # Bound to the method body: splitting to EOF would let
        # `_complete_with_retry(` in any *later* function satisfy the assert.
        override = source.split("    def complete(")[1]
        override = re.split(r"\n(?=\S|    def )", override)[0]

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

    def test_gemini_primary_success_is_metered(self, ledger):
        # The fallback test exercises only the error branch. The normal case
        # — primary model answers — must be metered too, or the override
        # leaks spend on every successful Gemini call.
        provider = self._gemini(usage={"prompt_tokens": 11, "completion_tokens": 4})

        provider.complete([Message(role="user", content="hi")])

        assert ledger.recorded == [("gemini", "gemini-3-pro", 11, 4)]

    def test_gemini_is_budget_checked(self, monkeypatch):
        # Nothing else asserts that Gemini's overridden complete() consults
        # the cap at all — it could meter perfectly and still spend past it.
        spent = FakeLedger(can_use_api=False)
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: spent))
        provider = self._gemini()

        with pytest.raises(BudgetExhaustedError):
            provider.complete([Message(role="user", content="hi")])

        assert provider.requests == []

    @staticmethod
    def _gemini(usage=None):
        """A GeminiProvider with its network call replaced, nothing else."""
        from agentic_orchestrator.providers.gemini import GeminiProvider

        provider = GeminiProvider.__new__(GeminiProvider)
        BaseProvider.__init__(
            provider,
            model="gemini-3-pro",
            fallback_model="gemini-3-flash",
            retry_config=RetryConfig(max_retries=0, initial_backoff=0),
        )
        provider.secondary_fallback = None
        provider.requests = []
        usage = usage or {"prompt_tokens": 11, "completion_tokens": 4}

        def fake_request(messages, model, **kwargs):
            provider.requests.append(model)
            return CompletionResponse(content="ok", model=model, provider="gemini", usage=usage)

        provider._make_request = fake_request
        return provider


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


class TestRealLedgerWiring:
    """No stubs. Pre-merge review found every other test replaces
    ``_budget_controller``, so the one seam where the guards meet the real
    ``BudgetController`` was never executed — the feature could have been
    inert end to end and all tests would still pass. These use a real
    controller against a real (temporary) SQLite ledger."""

    @pytest.fixture
    def real_ledger(self, tmp_path, monkeypatch):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        import agentic_orchestrator.llm.budget as budget_mod
        from agentic_orchestrator.db.models import Base

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)  # noqa: N806

        class TempDB:
            @contextmanager
            def session(self):
                session = Session()
                try:
                    yield session
                    session.commit()
                finally:
                    session.close()

        monkeypatch.setattr(budget_mod, "db", TempDB())
        # Keep BudgetController's mkdir out of the repo tree.
        monkeypatch.chdir(tmp_path)
        return engine

    def rows(self, engine):
        from sqlalchemy import text

        with engine.connect() as conn:
            return conn.execute(
                text("SELECT provider, model, input_tokens, output_tokens, cost_usd FROM api_usage")
            ).fetchall()

    def test_a_billed_completion_reaches_the_real_api_usage_table(self, real_ledger):
        # The end-to-end claim: legacy spend becomes visible in /usage.
        SpyProvider().complete([Message(role="user", content="hi")])

        rows = self.rows(real_ledger)
        assert len(rows) == 1
        provider, model, input_tokens, output_tokens, cost = rows[0]
        assert (provider, model, input_tokens, output_tokens) == (
            "spy",
            "gpt-5.2-chat-latest",
            1000,
            500,
        )
        # 1000 in / 500 out on gpt-5.2-chat-latest at $2.50/$10.00 per M.
        assert cost == pytest.approx(0.0025 + 0.005)

    def test_a_real_spent_budget_refuses_the_call(self, real_ledger, monkeypatch):
        from agentic_orchestrator.llm.budget import BudgetController

        # Blow past the daily cap through the real recording path.
        monkeypatch.setenv("DAILY_BUDGET_USD", "0.001")
        BudgetController().record_usage(
            provider="openai", model="gpt-5.2-chat-latest", input_tokens=500_000, output_tokens=0
        )
        provider = SpyProvider()

        with pytest.raises(BudgetExhaustedError):
            provider.complete([Message(role="user", content="hi")])

        assert provider.requests == 0

    def test_the_lazy_import_seam_actually_resolves(self, real_ledger):
        # _budget_controller lazily imports llm.budget to dodge a circular
        # import (llm/__init__ -> router -> providers.base). If that ever
        # breaks it returns None and both guards silently no-op.
        from agentic_orchestrator.llm.budget import BudgetController

        assert isinstance(SpyProvider()._budget_controller(), BudgetController)

    def test_the_ledger_is_built_once_per_provider(self, real_ledger, monkeypatch):
        # Two constructions per completion re-read and re-parse config.yaml.
        builds = []
        original = BaseProvider._budget_controller

        def counting():
            builds.append(1)
            return original()

        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(counting))
        provider = SpyProvider()
        provider.complete([Message(role="user", content="hi")])
        provider.complete([Message(role="user", content="hi")])

        assert len(builds) == 1


class TestClaudeCliIsNotBudgetGated:
    """Claude Code CLI bills a subscription, not the API budget.

    ``_record_usage`` already skips it (no token usage), so gating it on a
    spent API cap would refuse a call that can never move the ledger —
    breaking a documented manual workflow to protect nothing.
    """

    @staticmethod
    def claude(mode):
        from agentic_orchestrator.providers.claude import ClaudeProvider

        provider = ClaudeProvider.__new__(ClaudeProvider)
        BaseProvider.__init__(
            provider, model="opus", retry_config=RetryConfig(max_retries=0, initial_backoff=0)
        )
        provider._mode = mode
        provider.calls = []

        def fake_request(messages, model, **kwargs):
            provider.calls.append(model)
            usage = None if mode == "cli" else {"prompt_tokens": 9, "completion_tokens": 2}
            return CompletionResponse(content="answer", model=model, provider="claude", usage=usage)

        provider._make_request = fake_request
        return provider

    def test_cli_mode_still_answers_on_a_spent_budget(self, monkeypatch):
        spent = FakeLedger(can_use_api=False)
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: spent))
        provider = self.claude("cli")

        result = provider.complete([Message(role="user", content="hi")])

        assert result.content == "answer"
        assert provider.calls == ["opus"]
        assert spent.recorded == []  # and still writes nothing

    def test_api_mode_is_refused_on_a_spent_budget(self, monkeypatch):
        spent = FakeLedger(can_use_api=False)
        monkeypatch.setattr(BaseProvider, "_budget_controller", staticmethod(lambda: spent))
        provider = self.claude("api")

        with pytest.raises(BudgetExhaustedError):
            provider.complete([Message(role="user", content="hi")])

        assert provider.calls == []

    def test_check_and_record_agree_on_what_is_billed(self):
        # The invariant behind both tests above: anything _record_usage
        # would skip, _check_budget must not block.
        assert SpyProvider().bills_to_api_ledger() is True
        assert self.claude("cli").bills_to_api_ledger() is False
        assert self.claude("api").bills_to_api_ledger() is True

    def test_unresolvable_mode_is_treated_as_billed(self):
        # No CLI and no key: mode resolution raises. Fail safe (assume
        # billed) and let the real request surface the error.
        from agentic_orchestrator.providers.claude import ClaudeProvider

        provider = ClaudeProvider.__new__(ClaudeProvider)
        BaseProvider.__init__(provider, model="opus")
        provider._mode = None
        provider.prefer_cli = False
        provider.api_key = None

        assert provider.bills_to_api_ledger() is True


class TestRouterDoesNotDoubleCount:
    """Drives the real HybridLLMRouter, not just a provider's generate().

    The original test built an OpenAIProvider by hand and awaited
    ``generate()`` directly, so it pinned only "OpenAIProvider.generate does
    not reach _record_usage" — never that the router records exactly once,
    and never Claude, the router's other paid provider.
    """

    @staticmethod
    def router(provider_attr, provider, budget):
        from agentic_orchestrator.llm.hierarchy import LLMHierarchy
        from agentic_orchestrator.llm.router import HybridLLMRouter

        router = HybridLLMRouter.__new__(HybridLLMRouter)
        router.local_only = False
        router.ollama = SimpleNamespace(
            generate=lambda **kw: _async(
                SimpleNamespace(content="local", input_tokens=0, output_tokens=0)
            )
        )
        router.claude = None
        router.openai = None
        setattr(router, provider_attr, provider)
        router.hierarchy = LLMHierarchy()
        router.budget = budget
        router.paid_tiers = {
            "debate": {
                "enabled": True,
                "provider": provider_attr,
                "model": "gpt-5.4-mini" if provider_attr == "openai" else "claude-sonnet-4",
            }
        }
        return router

    @pytest.mark.parametrize(
        "attr,model", [("openai", "gpt-5.4-mini"), ("claude", "claude-sonnet-4")]
    )
    def test_router_records_exactly_once_and_never_via_the_legacy_hook(
        self, attr, model, monkeypatch
    ):
        legacy_writes = []
        monkeypatch.setattr(
            BaseProvider,
            "_record_usage",
            lambda self, m, r: legacy_writes.append((self.provider_name, m)),
        )
        budget = FakeLedger()
        provider = RealishProvider(attr, model)
        router = self.router(attr, provider, budget)

        response = asyncio.run(router.route(prompt="p", paid_tier="debate"))

        assert response.provider == attr
        assert response.model == model
        # Recorded once, by the router — not by the legacy hook.
        assert budget.recorded == [(attr, model, 120, 60)]
        assert legacy_writes == []
        # And the call really went through generate(), the router's entry.
        assert provider.generate_calls == 1


def _async(value):
    async def coro():
        return value

    return coro()


class RealishProvider(BaseProvider):
    """A paid provider with the real generate() -> _make_request shape."""

    def __init__(self, name, model):
        self.provider_name = name
        super().__init__(model=model, retry_config=RetryConfig(max_retries=0, initial_backoff=0))
        self.generate_calls = 0

    def _make_request(self, messages, model, **kwargs):
        return CompletionResponse(
            content="api reply",
            model=model,
            provider=self.provider_name,
            usage={"prompt_tokens": 120, "completion_tokens": 60},
        )

    async def generate(self, prompt, model=None, system=None, temperature=0.7, max_tokens=4096):
        # Mirrors ClaudeProvider/OpenAIProvider.generate: straight to
        # _make_request, bypassing complete()/_complete_with_retry.
        self.generate_calls += 1
        response = self._make_request([Message(role="user", content=prompt)], model or self.model)
        usage = response.usage or {}
        return {
            "content": response.content,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }

    def is_available(self):
        return True
