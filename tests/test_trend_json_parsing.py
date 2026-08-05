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

    def __init__(self, *args, **kwargs):
        pass

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
