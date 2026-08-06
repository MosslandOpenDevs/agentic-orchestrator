"""Tests for the Ollama in-flight concurrency cap (v0.6.21).

``throttling.ollama.max_concurrent_requests`` was dead config: the throttle
held its lock only to update state and released it before the HTTP call, so
it spaced request *starts* by ``min_request_interval`` and then let every
caller sit on the GPU at once. A divergence round fans out 8 agents through
``asyncio.gather``; all 8 reached the single shared GPU together, which is
the load pattern behind the KV-cache stalls that killed three debates on
2026-08-05.

These tests measure the peak number of simultaneously in-flight requests
against a fake transport — the only way to tell a real semaphore from a
setting nobody reads.
"""

import asyncio

import pytest

from agentic_orchestrator.providers.ollama import OllamaConfig, OllamaProvider


class InFlightRecorder:
    """Fake httpx.AsyncClient that records concurrent request depth."""

    peak = 0
    current = 0
    hold_seconds = 0.05

    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, *args, **kwargs):
        type(self).current += 1
        type(self).peak = max(type(self).peak, type(self).current)
        await asyncio.sleep(type(self).hold_seconds)
        type(self).current -= 1
        return _FakeResponse()

    @classmethod
    def reset(cls):
        cls.peak = 0
        cls.current = 0


class _FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"response": "ok", "done": True, "done_reason": "stop"}


@pytest.fixture()
def recorder(monkeypatch):
    monkeypatch.setattr("agentic_orchestrator.providers.ollama.httpx.AsyncClient", InFlightRecorder)
    InFlightRecorder.reset()
    return InFlightRecorder


def make_provider(limit):
    return OllamaProvider(
        OllamaConfig(
            throttle={
                "max_concurrent_requests": limit,
                "min_request_interval": 0,
                "requests_before_cooling": 10_000,
                "request_timeout": 10,
            }
        )
    )


async def fan_out(provider, n=8):
    await asyncio.gather(*[provider.generate(f"prompt {i}") for i in range(n)])


class TestConcurrencyCap:
    @pytest.mark.parametrize("limit", [1, 2, 4])
    def test_peak_in_flight_never_exceeds_the_configured_limit(self, recorder, limit):
        asyncio.run(fan_out(make_provider(limit)))
        assert recorder.peak <= limit

    def test_the_default_of_one_serialises_a_divergence_round(self, recorder):
        # 8 concurrent agents is exactly what a production divergence round
        # fans out. Before the semaphore this measured 8.
        asyncio.run(fan_out(make_provider(1), n=8))
        assert recorder.peak == 1

    def test_every_request_still_completes(self, recorder):
        provider = make_provider(2)

        async def run():
            return await asyncio.gather(*[provider.generate(f"p{i}") for i in range(6)])

        results = asyncio.run(run())
        assert len(results) == 6
        assert all(r.content == "ok" for r in results)

    def test_zero_or_missing_limit_disables_the_cap(self, recorder):
        # An explicit 0 means "no cap" rather than "block everything" — a
        # semaphore of 0 would deadlock the pipeline.
        asyncio.run(fan_out(make_provider(0)))
        assert recorder.peak > 1

    def test_chat_path_is_capped_too(self, recorder):
        provider = make_provider(1)

        async def run():
            await asyncio.gather(
                *[provider.chat([{"role": "user", "content": f"m{i}"}]) for i in range(4)]
            )

        # chat() parses a different response shape; give it one.
        InFlightRecorder.reset()
        original = _FakeResponse.json
        _FakeResponse.json = lambda self: {"message": {"content": "ok"}, "done": True}
        try:
            asyncio.run(run())
        finally:
            _FakeResponse.json = original
        assert recorder.peak == 1
