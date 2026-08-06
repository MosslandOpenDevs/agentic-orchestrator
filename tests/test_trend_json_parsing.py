"""Tests for the trend-analysis LLM plumbing that silently produced 0 trends.

Two production defects, both observed live on 2026-08-05, are pinned here:

1. **Context truncation.** No request ever sent ``num_ctx``, so the shared
   Ollama server loaded gemma3:4b at its own 4096 default. The trends prompt
   alone is ~3,300 tokens; generation stopped at exactly
   ``prompt_eval + eval == 4096`` with ``done_reason="length"`` and nobody
   noticed — the provider dropped ``done_reason`` on the floor.

2. **Brittle parsing.** The extractor demanded a *closed* ```` ```json ````
   fence (truncation eats the closing fence), and gemma3:4b regularly emits
   curly “smart quotes” as JSON string delimiters, which ``json.loads``
   rejects mid-document. Either defect alone discarded the entire response.

The parser tests run against ``TrendAnalyzer`` without a router or config —
parsing is pure string work and must stay that way.
"""

import json
import logging

import httpx
import pytest

from agentic_orchestrator.providers.ollama import (
    DEFAULT_NUM_CTX,
    OllamaConfig,
    OllamaProvider,
    OllamaResponse,
)
from agentic_orchestrator.trends.analyzer import TrendAnalyzer


def make_analyzer() -> TrendAnalyzer:
    """Parser-only instance: no router, no config.yaml I/O."""
    return TrendAnalyzer.__new__(TrendAnalyzer)


def trend_obj(n: int, score: float = 8.0) -> dict:
    return {
        "topic": f"Trend number {n} with a sufficiently descriptive title",
        "keywords": ["ai", "web3"],
        "score": score,
        "sources": ["rss"],
        "article_count": 3,
        "sample_headlines": [f"Headline {n}"],
        "category": "ai",
        "summary": f"Summary of trend {n}.",
        "web3_relevance": "High",
        "idea_seeds": [f"Idea {n}"],
    }


def wrap(trends: list[dict]) -> str:
    return json.dumps({"trends": trends}, ensure_ascii=False)


class TestParserHappyPaths:
    def test_clean_fenced_json(self):
        response = f"```json\n{wrap([trend_obj(1), trend_obj(2, 9.5)])}\n```"
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert len(trends) == 2
        assert trends[0].score == 9.5  # sorted best-first

    def test_prose_preamble_before_fence(self):
        """The model narrates before the fence; production shape."""
        response = (
            "Okay, here's the JSON object analyzing the provided news "
            "headlines, focusing on top trends:\n\n"
            f"```json\n{wrap([trend_obj(1)])}\n```\n\nLet me know if"
        )
        assert len(make_analyzer()._parse_trends_response(response, "24h")) == 1

    def test_plain_fence_without_json_tag(self):
        response = f"```\n{wrap([trend_obj(1)])}\n```"
        assert len(make_analyzer()._parse_trends_response(response, "24h")) == 1

    def test_raw_json_no_fence_with_prose(self):
        response = f"Here is the analysis: {wrap([trend_obj(1)])} Hope this helps!"
        assert len(make_analyzer()._parse_trends_response(response, "24h")) == 1


class TestParserDefectTolerance:
    def test_smart_quote_string_delimiters(self):
        """gemma3:4b emits “…” as JSON delimiters; observed live 2026-08-05."""
        body = wrap([trend_obj(1)]).replace('"Summary of trend 1."', "“Summary of trend 1.”")
        response = f"```json\n{body}\n```"
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert len(trends) == 1
        assert trends[0].summary == "Summary of trend 1."

    def test_smart_quotes_inside_values_are_preserved_when_json_is_valid(self):
        """Repair must never fire on well-formed JSON: content stays intact."""
        t = trend_obj(1)
        t["summary"] = "He said “hello” and left."
        response = f"```json\n{wrap([t])}\n```"
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert trends[0].summary == "He said “hello” and left."

    def test_trailing_commas(self):
        body = wrap([trend_obj(1)]).replace(
            '"idea_seeds": ["Idea 1"]}', '"idea_seeds": ["Idea 1"],}'
        )
        response = f"```json\n{body}\n```"
        assert len(make_analyzer()._parse_trends_response(response, "24h")) == 1

    def test_missing_closing_fence_complete_json(self):
        """Fence never closed but the JSON itself is whole."""
        response = f"```json\n{wrap([trend_obj(1), trend_obj(2)])}"
        assert len(make_analyzer()._parse_trends_response(response, "24h")) == 2

    def test_stacked_defects_smart_quotes_unbalanced_brace_no_fence_close(self):
        """Worst observed combination, all at once.

        Smart-quote delimiters blind the balanced-brace scanner to string
        boundaries, so an unmatched '{' inside a value makes it give up; the
        prose preamble sinks the raw-response layer; the missing closing fence
        sinks the strict fence layer. Salvage must still recover the array.
        """
        t = trend_obj(1)
        body = wrap([t]).replace('"Summary of trend 1."', "“Summary of trend 1 {unclosed brace”")
        response = f"Okay, here's the JSON:\n```json\n{body}"
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert len(trends) == 1
        assert "{unclosed brace" in trends[0].summary

    def test_truncated_tail_salvages_complete_objects(self):
        """Cut off mid-string in object 3: objects 1-2 must survive."""
        full = json.dumps({"trends": [trend_obj(1), trend_obj(2), trend_obj(3)]}, indent=2)
        cut = full.find('"Summary of trend 3')
        response = f"```json\n{full[: cut + 12]}"
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert len(trends) == 2

    def test_production_failure_shape_end_to_end(self):
        """Prose + fence + smart quotes + truncation, all at once."""
        body = json.dumps({"trends": [trend_obj(1), trend_obj(2), trend_obj(3)]}, indent=2)
        body = body.replace('"Summary of trend 1."', "“Summary of trend 1.”")
        cut = body.find('"web3_relevance": "High"', body.find('"Summary of trend 3'))
        response = (
            "Okay, here’s the JSON object analyzing the provided news headlines:\n"
            f"```json\n{body[:cut]}"
        )
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert len(trends) == 2

    def test_garbage_falls_back_to_numbered_list(self):
        response = "1. **AI agents everywhere**\n2. **DeFi revival**\nno json here"
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert len(trends) == 2
        assert trends[0].topic == "AI agents everywhere"

    def test_valid_json_without_trends_key(self):
        assert make_analyzer()._parse_trends_response('```json\n{"a": 1}\n```', "24h") == []

    def test_empty_response(self):
        assert make_analyzer()._parse_trends_response("", "24h") == []


class TestBalancedExtraction:
    def test_braces_inside_strings_do_not_confuse_the_scanner(self):
        t = trend_obj(1)
        t["summary"] = 'Uses {curly} braces and an escaped quote \\" inside.'
        response = f"noise {wrap([t])} trailing {{ noise"
        trends = make_analyzer()._parse_trends_response(response, "24h")

        assert len(trends) == 1
        assert "{curly}" in trends[0].summary


class TestAnalyzerOutputBudget:
    async def test_route_is_called_with_explicit_max_tokens(self):
        """Unset, Ollama's only stop is the context window — the 2026-08 bug."""
        from agentic_orchestrator.timeutil import utcnow
        from agentic_orchestrator.trends.models import FeedItem

        captured = {}

        class FakeRouter:
            async def route(self, **kwargs):
                captured.update(kwargs)

                class R:
                    content = '```json\n{"trends": []}\n```'
                    model = "gemma3:4b"

                return R()

        analyzer = make_analyzer()
        analyzer._router = FakeRouter()
        analyzer.dry_run = False
        item = FeedItem(
            title="t", link="l", summary="s", source="rss", category="ai", published=utcnow()
        )
        await analyzer.analyze_trends([item], "24h")

        assert captured.get("max_tokens") == 4096


class FakeAsyncClient:
    """Stands in for httpx.AsyncClient; records the request payload."""

    captured: dict = {}
    reply: dict = {}
    # The request timeout is a constructor kwarg, not part of the payload —
    # capture it too, or a dropped per-call timeout is invisible to tests.
    init_kwargs: dict = {}

    def __init__(self, *args, **kwargs):
        FakeAsyncClient.init_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None):
        FakeAsyncClient.captured = {"url": url, "payload": json}
        request = httpx.Request("POST", url)
        return httpx.Response(200, json=FakeAsyncClient.reply, request=request)


@pytest.fixture()
def fake_ollama(monkeypatch):
    monkeypatch.setattr("agentic_orchestrator.providers.ollama.httpx.AsyncClient", FakeAsyncClient)
    FakeAsyncClient.captured = {}
    FakeAsyncClient.init_kwargs = {}
    FakeAsyncClient.reply = {"response": "ok", "done": True, "done_reason": "stop"}
    return FakeAsyncClient


class TestProviderNumCtx:
    async def test_generate_always_sends_num_ctx(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={}))
        await provider.generate("hello")

        options = fake_ollama.captured["payload"]["options"]
        assert options["num_ctx"] == DEFAULT_NUM_CTX

    async def test_num_ctx_configurable_via_throttle_config(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={"num_ctx": 32768}))
        await provider.generate("hello")

        assert fake_ollama.captured["payload"]["options"]["num_ctx"] == 32768

    async def test_chat_sends_num_ctx_too(self, fake_ollama):
        fake_ollama.reply = {"message": {"content": "ok"}, "done": True}
        provider = OllamaProvider(OllamaConfig(throttle={}))
        await provider.chat([{"role": "user", "content": "hi"}])

        assert fake_ollama.captured["payload"]["options"]["num_ctx"] == DEFAULT_NUM_CTX

    async def test_max_tokens_still_maps_to_num_predict(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={}))
        await provider.generate("hello", max_tokens=4096)

        assert fake_ollama.captured["payload"]["options"]["num_predict"] == 4096

    async def test_per_call_num_ctx_beats_the_throttle_default(self, fake_ollama):
        # Small-prompt tasks (idea scoring) must be able to stay on the
        # server's already-resident small instance: on 2026-08-05 every 16k
        # KV-cache load hung ~30 min on the congested shared GPU while the
        # 4k instance answered in <1s, starving backlog triage.
        provider = OllamaProvider(OllamaConfig(throttle={"num_ctx": 16384}))
        await provider.generate("hello", num_ctx=4096)

        assert fake_ollama.captured["payload"]["options"]["num_ctx"] == 4096

    async def test_num_ctx_none_keeps_the_throttle_default(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={"num_ctx": 16384}))
        await provider.generate("hello", num_ctx=None)

        assert fake_ollama.captured["payload"]["options"]["num_ctx"] == 16384


class TestProviderTimeout:
    """`throttling.ollama.request_timeout` is sized for the longest task (a
    debate turn, 1800s). A short task that inherits it waits 30 minutes to
    learn the backend is wedged — which on 2026-08-06 turned one hung GPU
    into a 3.5-hour backlog run that consumed nothing and blocked deploys.
    """

    async def test_default_timeout_comes_from_the_throttle_config(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={"request_timeout": 1800}))
        await provider.generate("hello")

        assert fake_ollama.init_kwargs["timeout"] == 1800

    async def test_per_call_timeout_beats_the_throttle_default(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={"request_timeout": 1800}))
        await provider.generate("hello", timeout=120)

        assert fake_ollama.init_kwargs["timeout"] == 120

    async def test_timeout_none_keeps_the_throttle_default(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={"request_timeout": 1800}))
        await provider.generate("hello", timeout=None)

        assert fake_ollama.init_kwargs["timeout"] == 1800

    async def test_router_plumbs_timeout_to_ollama(self, fake_ollama):
        """A timeout override dropped anywhere in the router silently
        restores the 30-minute hang — pin the plumb, both directions."""
        from agentic_orchestrator.llm.hierarchy import LLMHierarchy
        from agentic_orchestrator.llm.router import HybridLLMRouter

        class FakeBudget:
            def get_budget_status(self):
                return {"can_use_api": False}

            def should_use_local(self):
                return True

            def estimate_cost(self, *a):
                return 0.0

        router = HybridLLMRouter.__new__(HybridLLMRouter)
        router.local_only = True
        router.ollama = OllamaProvider(OllamaConfig(throttle={"request_timeout": 1800}))
        router.claude = None
        router.openai = None
        router.hierarchy = LLMHierarchy()
        router.budget = FakeBudget()

        await router.route(prompt="p", force_local=True, timeout=120)
        assert fake_ollama.init_kwargs["timeout"] == 120

        await router.route(prompt="p", force_local=True)
        assert fake_ollama.init_kwargs["timeout"] == 1800

    async def test_scorer_sends_a_short_timeout_end_to_end(self, fake_ollama):
        """The whole point: an IdeaScorer call must reach the wire with its
        own short budget, not the 1800s debate one."""
        from agentic_orchestrator.llm.hierarchy import LLMHierarchy
        from agentic_orchestrator.llm.router import HybridLLMRouter
        from agentic_orchestrator.scoring import IdeaScorer

        class FakeBudget:
            def get_budget_status(self):
                return {"can_use_api": False}

            def should_use_local(self):
                return True

            def estimate_cost(self, *a):
                return 0.0

        router = HybridLLMRouter.__new__(HybridLLMRouter)
        router.local_only = True
        router.ollama = OllamaProvider(OllamaConfig(throttle={"request_timeout": 1800}))
        router.claude = None
        router.openai = None
        router.hierarchy = LLMHierarchy()
        router.budget = FakeBudget()

        fake_ollama.reply = {
            "response": '{"feasibility": 7, "relevance": 7, "novelty": 7, "impact": 7}',
            "done": True,
            "done_reason": "stop",
        }
        await IdeaScorer(router=router).score_idea("an idea")

        assert fake_ollama.init_kwargs["timeout"] == IdeaScorer.SCORING_TIMEOUT
        assert IdeaScorer.SCORING_TIMEOUT < 1800
        # The 4k pin must survive alongside the new timeout.
        assert fake_ollama.captured["payload"]["options"]["num_ctx"] == 4096


class TestStructuredOutputs:
    """Ollama's `format` field: grammar-constrained decoding (since v0.5.0).

    With a schema attached the model physically cannot emit the failure
    shapes the lenient parser tolerates — this is the transport-level fix,
    with the parser retained as defense in depth.
    """

    async def test_format_schema_lands_in_the_generate_payload(self, fake_ollama):
        schema = {"type": "object", "required": ["trends"]}
        provider = OllamaProvider(OllamaConfig(throttle={}))
        await provider.generate("hello", format_schema=schema)

        assert fake_ollama.captured["payload"]["format"] == schema

    async def test_no_schema_means_no_format_field(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={}))
        await provider.generate("hello")

        assert "format" not in fake_ollama.captured["payload"]

    async def test_chat_supports_format_schema_too(self, fake_ollama):
        fake_ollama.reply = {"message": {"content": "ok"}, "done": True}
        schema = {"type": "object"}
        provider = OllamaProvider(OllamaConfig(throttle={}))
        await provider.chat([{"role": "user", "content": "hi"}], format_schema=schema)

        assert fake_ollama.captured["payload"]["format"] == schema

    async def test_router_plumbs_response_schema_to_ollama(self, fake_ollama):
        """A schema dropped in the router would fail silently — pin the plumb."""
        from agentic_orchestrator.llm.hierarchy import LLMHierarchy
        from agentic_orchestrator.llm.router import HybridLLMRouter

        class FakeBudget:
            def get_budget_status(self):
                return {"can_use_api": False}

            def should_use_local(self):
                return True

            def estimate_cost(self, *a):
                return 0.0

        router = HybridLLMRouter.__new__(HybridLLMRouter)
        router.local_only = True
        router.ollama = OllamaProvider(OllamaConfig(throttle={}))
        router.claude = None
        router.openai = None
        router.hierarchy = LLMHierarchy()
        router.budget = FakeBudget()

        schema = {"type": "object", "required": ["trends"]}
        await router.route(prompt="p", force_local=True, response_schema=schema)

        assert fake_ollama.captured["payload"]["format"] == schema

    async def test_router_plumbs_num_ctx_to_ollama(self, fake_ollama):
        """A num_ctx override dropped in the router silently reintroduces
        the 16k-load hang the override exists to avoid — pin the plumb."""
        from agentic_orchestrator.llm.hierarchy import LLMHierarchy
        from agentic_orchestrator.llm.router import HybridLLMRouter

        class FakeBudget:
            def get_budget_status(self):
                return {"can_use_api": False}

            def should_use_local(self):
                return True

            def estimate_cost(self, *a):
                return 0.0

        router = HybridLLMRouter.__new__(HybridLLMRouter)
        router.local_only = True
        router.ollama = OllamaProvider(OllamaConfig(throttle={"num_ctx": 16384}))
        router.claude = None
        router.openai = None
        router.hierarchy = LLMHierarchy()
        router.budget = FakeBudget()

        await router.route(prompt="p", force_local=True, num_ctx=4096)
        assert fake_ollama.captured["payload"]["options"]["num_ctx"] == 4096

        await router.route(prompt="p", force_local=True)
        assert fake_ollama.captured["payload"]["options"]["num_ctx"] == 16384

    async def test_no_task_pins_its_own_num_ctx(self):
        """One context size for the whole pipeline — no per-task override.

        The shared Ollama host serves ONE model instance at a time, and each
        distinct num_ctx is a distinct instance. A task that pins its own
        size therefore evicts whatever is resident and pays a ~4.5s reload,
        and the next caller evicts it straight back. v0.6.18 pinned scoring
        to 4,096 on the belief that 16k loads hung indefinitely; re-measured
        2026-08-06 that did not reproduce (non-resident load: 4.46s), and
        the pin had become the thing breaking the single-instance
        convergence agreed with the other service on the host.

        If a task genuinely needs a different window, change the global
        `throttling.ollama.num_ctx` and tell whoever shares the host —
        do not add a second size.
        """
        from agentic_orchestrator.scoring import IdeaScorer

        captured = {}

        class FakeRouter:
            async def route(self, **kwargs):
                captured.update(kwargs)

                class R:
                    content = (
                        '{"feasibility": 6, "relevance": 6, "novelty": 6,'
                        ' "impact": 6, "reasoning": "ok"}'
                    )
                    model = "gemma3:4b"

                return R()

        scorer = IdeaScorer(router=FakeRouter())
        await scorer.score_idea("idea content")

        assert captured.get("num_ctx") is None, (
            "scoring must not pin a per-call num_ctx — it would evict the "
            "shared instance on every call"
        )
        assert not hasattr(IdeaScorer, "SCORING_NUM_CTX")

    async def test_analyzer_sends_its_trends_schema(self):
        from agentic_orchestrator.timeutil import utcnow
        from agentic_orchestrator.trends.models import FeedItem

        captured = {}

        class FakeRouter:
            async def route(self, **kwargs):
                captured.update(kwargs)

                class R:
                    content = '{"trends": []}'
                    model = "gemma3:4b"

                return R()

        analyzer = make_analyzer()
        analyzer._router = FakeRouter()
        analyzer.dry_run = False
        item = FeedItem(
            title="t", link="l", summary="s", source="rss", category="ai", published=utcnow()
        )
        await analyzer.analyze_trends([item], "24h")

        assert captured.get("response_schema") == TrendAnalyzer.TRENDS_RESPONSE_SCHEMA

    def test_schema_matches_what_the_parser_reads(self):
        """Every field the parser consumes must exist in the schema, so the
        grammar never forbids a field the pipeline stores."""
        item_props = TrendAnalyzer.TRENDS_RESPONSE_SCHEMA["properties"]["trends"]["items"][
            "properties"
        ]
        parser_fields = {
            "topic",
            "keywords",
            "score",
            "sources",
            "article_count",
            "sample_headlines",
            "category",
            "summary",
            "web3_relevance",
            "idea_seeds",
        }
        assert parser_fields == set(item_props)

    def test_bare_constrained_json_parses(self):
        """Constrained output is pure JSON: no fence, no prose. The parser's
        raw layer must take it as-is."""
        response = wrap([trend_obj(1), trend_obj(2)])
        assert len(make_analyzer()._parse_trends_response(response, "24h")) == 2


class TestTruncationDetection:
    async def test_done_reason_is_captured(self, fake_ollama):
        fake_ollama.reply = {"response": "cut", "done": True, "done_reason": "length"}
        provider = OllamaProvider(OllamaConfig(throttle={}))
        result = await provider.generate("hello")

        assert result.done_reason == "length"
        assert result.truncated is True

    async def test_natural_stop_is_not_truncated(self, fake_ollama):
        provider = OllamaProvider(OllamaConfig(throttle={}))
        result = await provider.generate("hello")

        assert result.truncated is False

    async def test_done_false_counts_as_truncated(self):
        assert OllamaResponse(content="x", model="m", done=False).truncated is True

    async def test_truncation_emits_a_warning(self, fake_ollama, caplog):
        """The 4096-window cut-off ran for weeks without a single log line."""
        fake_ollama.reply = {
            "response": "cut off mid-json",
            "done": True,
            "done_reason": "length",
            "prompt_eval_count": 3298,
            "eval_count": 798,
        }
        provider = OllamaProvider(OllamaConfig(throttle={}))
        with caplog.at_level(logging.WARNING):
            await provider.generate("hello")

        assert any("TRUNCATED" in r.message for r in caplog.records)
