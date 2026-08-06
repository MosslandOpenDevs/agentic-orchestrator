"""Regressions for the Ollama provider's throttle and health reporting.

Both defects made a shared, single-GPU dependency look better behaved than it
was: the interval throttle did nothing under concurrency, the declared
concurrency cap was never read, and health reported "healthy" for a server
that was unreachable or missing the only model the pipeline uses.
"""

import asyncio
import time

from agentic_orchestrator.providers.ollama import OllamaConfig, OllamaProvider

BASE_THROTTLE = {
    "min_request_interval": 0.1,
    "max_concurrent_requests": 1,
    "cooling_period_seconds": 30,
    "requests_before_cooling": 50,  # keep cooling out of these tests
    "request_timeout": 5,
    "batch_delay_seconds": 0,
    "num_ctx": 1024,
}


def _provider(**throttle_overrides) -> OllamaProvider:
    return OllamaProvider(
        config=OllamaConfig(
            base_url="http://127.0.0.1:1",
            throttle={**BASE_THROTTLE, **throttle_overrides},
        )
    )


class TestIntervalThrottle:
    async def test_concurrent_callers_are_spaced_not_released_together(self):
        """The wait used to be computed under the lock while the slot was only
        claimed after sleeping, so every waiter read the same timestamp,
        computed the same delay and woke at once."""
        provider = _provider(min_request_interval=0.1)
        # Seed a last-request time so the first caller also has to wait.
        await provider._wait_for_throttle()

        returned_at: list[float] = []

        async def call():
            await provider._wait_for_throttle()
            returned_at.append(time.monotonic())

        await asyncio.gather(*(call() for _ in range(3)))

        returned_at.sort()
        gaps = [b - a for a, b in zip(returned_at, returned_at[1:], strict=False)]
        assert all(gap >= 0.08 for gap in gaps), gaps

    async def test_throttle_can_be_disabled(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_THROTTLE", "false")
        provider = _provider(min_request_interval=5)

        started = time.monotonic()
        await provider._wait_for_throttle()
        assert time.monotonic() - started < 0.05


class TestConcurrencyCap:
    def test_cap_is_read_from_config(self):
        assert _provider(max_concurrent_requests=3)._concurrency_slots()._value == 3

    def test_invalid_cap_falls_back_to_one(self):
        """A typo in config.yaml must not raise from inside the request path."""
        assert _provider(max_concurrent_requests="nonsense")._concurrency_slots()._value == 1

    def test_zero_or_negative_disables_the_cap(self):
        assert _provider(max_concurrent_requests=0)._concurrency_slots() is None

    async def test_cap_actually_serializes_calls(self):
        """config.yaml documented `1 = sequential only` but nothing read the
        value, so every agent in a round could hit the GPU at once."""
        provider = _provider(max_concurrent_requests=1, min_request_interval=0)
        in_flight = 0
        peak = 0

        async def work():
            nonlocal in_flight, peak
            async with provider._request_slot():
                in_flight += 1
                peak = max(peak, in_flight)
                await asyncio.sleep(0.02)
                in_flight -= 1

        await asyncio.gather(*(work() for _ in range(4)))
        assert peak == 1


class TestTheGuardsAreActuallyApplied:
    """The tests above poke the throttle and the semaphore directly, which
    proves they work but not that anything uses them. These go through the
    public entry points, so removing the decorator fails them."""

    def test_generate_and_chat_hold_a_slot(self):
        import inspect

        for method in (OllamaProvider.generate, OllamaProvider.chat):
            source = inspect.getsource(method)
            assert "_request_slot()" in source, method.__name__
            assert "_wait_for_throttle()" in source, method.__name__

    async def test_generate_calls_are_serialized_by_the_cap(self, monkeypatch):
        provider = _provider(max_concurrent_requests=1, min_request_interval=0)

        in_flight = 0
        peak = 0

        class _FakeResponse:
            status_code = 200
            text = ""

            def raise_for_status(self):
                return None

            def json(self):
                return {"response": "ok", "model": "gemma3:4b", "done": True}

        class _FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def post(self, *args, **kwargs):
                nonlocal in_flight, peak
                in_flight += 1
                peak = max(peak, in_flight)
                await asyncio.sleep(0.03)
                in_flight -= 1
                return _FakeResponse()

        monkeypatch.setattr("agentic_orchestrator.providers.ollama.httpx.AsyncClient", _FakeClient)

        results = await asyncio.gather(*(provider.generate(f"prompt {i}") for i in range(4)))

        assert peak == 1, f"expected serialized calls, saw {peak} in flight"
        assert all(r.content == "ok" for r in results)

    async def test_generate_waits_out_the_interval(self, monkeypatch):
        provider = _provider(max_concurrent_requests=4, min_request_interval=0.1)

        class _FakeResponse:
            status_code = 200
            text = ""

            def raise_for_status(self):
                return None

            def json(self):
                return {"response": "ok", "model": "gemma3:4b", "done": True}

        class _FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def post(self, *args, **kwargs):
                return _FakeResponse()

        monkeypatch.setattr("agentic_orchestrator.providers.ollama.httpx.AsyncClient", _FakeClient)

        started = time.monotonic()
        await asyncio.gather(*(provider.generate(f"p{i}") for i in range(3)))
        elapsed = time.monotonic() - started

        # Three requests spaced 0.1s apart cannot finish instantly.
        assert elapsed >= 0.15, elapsed


class TestHealthReporting:
    async def test_unreachable_server_is_not_healthy(self, monkeypatch):
        provider = _provider()

        async def boom():
            raise ConnectionError("connection refused")

        monkeypatch.setattr(provider, "_fetch_available_models", boom)

        health = await provider.health_check()
        assert health["status"] == "error"
        assert "connection refused" in health["error"]

    async def test_server_with_no_models_is_degraded(self, monkeypatch):
        provider = _provider()

        async def empty():
            return []

        monkeypatch.setattr(provider, "_fetch_available_models", empty)

        health = await provider.health_check()
        assert health["status"] == "degraded"
        assert "no models" in health["detail"]

    async def test_missing_default_model_is_degraded(self, monkeypatch):
        provider = _provider()

        async def other_models():
            return ["llama3:8b"]

        monkeypatch.setattr(provider, "_fetch_available_models", other_models)

        health = await provider.health_check()
        assert health["status"] == "degraded"
        assert provider.config.default_model in health["detail"]

    async def test_healthy_server_reports_healthy(self, monkeypatch):
        provider = _provider()

        async def with_default():
            return [provider.config.default_model, "llama3:8b"]

        monkeypatch.setattr(provider, "_fetch_available_models", with_default)

        health = await provider.health_check()
        assert health["status"] == "healthy"
        assert provider.config.default_model in health["available_models"]
        assert "detail" not in health

    async def test_get_available_models_still_degrades_to_empty(self, monkeypatch):
        """Callers other than health_check keep the forgiving contract."""
        provider = _provider()

        async def boom():
            raise ConnectionError("nope")

        monkeypatch.setattr(provider, "_fetch_available_models", boom)

        assert await provider.get_available_models() == []

    async def test_model_list_lives_under_available_models(self, monkeypatch):
        """The scheduler's health task read `models`, a key health_check has
        never returned, so it logged "0 models" no matter the real state."""
        provider = _provider()

        async def with_default():
            return [provider.config.default_model]

        monkeypatch.setattr(provider, "_fetch_available_models", with_default)

        health = await provider.health_check()
        assert health["available_models"] == [provider.config.default_model]
        assert "models" not in health
