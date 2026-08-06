"""
Ollama Local LLM provider.

Provides interface to Ollama for running local LLMs.
Includes throttling and cooling support to prevent overheating.
"""

import asyncio
import contextlib as asynccontextlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
import yaml

from ..timeutil import utcnow
from .base import ProviderError

logger = logging.getLogger(__name__)


# Context window requested on every generate/chat call. Ollama's server-side
# default is 4096, and a model loaded at that size silently truncates: the
# trend-analysis prompt alone is ~3,300 tokens, so generation stopped at
# exactly prompt+output == 4096 with done_reason="length" (0 trends parsed,
# 2026-08-05). gemma3:4b supports 131k; 16k gives every pipeline prompt
# comfortable headroom while keeping the KV cache small (gemma3's sliding-
# window attention keeps per-token KV cost low). Override per deployment via
# `throttling.ollama.num_ctx` in config.yaml.
DEFAULT_NUM_CTX = 16384


def load_throttle_config() -> Dict[str, Any]:
    """Load throttling configuration from config.yaml."""
    config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
    default_config = {
        "min_request_interval": 5,
        "max_concurrent_requests": 1,
        "cooling_period_seconds": 30,
        "requests_before_cooling": 5,
        "request_timeout": 120,
        "batch_delay_seconds": 10,
        "num_ctx": DEFAULT_NUM_CTX,
    }

    try:
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
                throttle = config.get("throttling", {}).get("ollama", {})
                return {**default_config, **throttle}
    except Exception:
        pass

    return default_config


@dataclass
class ThrottleState:
    """State for request throttling."""

    request_count: int = 0
    last_request_time: float = 0.0
    is_cooling: bool = False
    cooling_until: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # Caps requests that are IN FLIGHT, which `_lock` never did — it only
    # guards state updates and is released before the HTTP call. Until
    # v0.6.21 `throttling.ollama.max_concurrent_requests` was therefore dead
    # config: a divergence round fans out 8 agents through asyncio.gather,
    # min_request_interval spaced their *starts* 5s apart, and all 8 then sat
    # on the single shared GPU at once. That is the load pattern behind the
    # KV-cache stalls that killed three debates on 2026-08-05.
    _slots: Optional[asyncio.Semaphore] = None


@dataclass
class OllamaConfig:
    """Ollama configuration."""

    base_url: str = "http://localhost:11434"
    default_model: str = "gemma3:4b"
    timeout: int = 300  # 5 minutes for large models
    max_retries: int = 3
    # Throttling settings (loaded from config.yaml)
    throttle: Dict[str, Any] = field(default_factory=load_throttle_config)


@dataclass
class OllamaResponse:
    """Response from Ollama."""

    content: str
    model: str
    total_duration: Optional[int] = None  # nanoseconds
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    done: bool = True
    # Ollama's reason for ending generation: "stop" is a natural finish,
    # "length" means the output was cut off (num_predict or context full).
    done_reason: Optional[str] = None

    @property
    def truncated(self) -> bool:
        """True when generation was cut off rather than finishing naturally."""
        return self.done_reason == "length" or not self.done

    @property
    def input_tokens(self) -> int:
        return self.prompt_eval_count or 0

    @property
    def output_tokens(self) -> int:
        return self.eval_count or 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def duration_seconds(self) -> float:
        if self.total_duration:
            return self.total_duration / 1e9
        return 0.0


class OllamaProvider:
    """
    Ollama Local LLM Provider.

    Features:
    - Completely free (runs locally)
    - Streaming support
    - Multiple model support
    - GPU memory management
    """

    # Available models on the remote Ollama server (host configured via OLLAMA_HOST).
    # Consolidated to a single chat model so the shared ~8GB GPU never has to
    # swap. qwen3-embedding:0.6b is a reserved slot with NO callers today and is
    # not pulled on the production host — see CLAUDE.md "작업별 LLM 모델".
    AVAILABLE_MODELS = {
        "gemma3:4b": {"size": "6.6GB", "context": 32768, "tier": "chat"},
        "qwen3-embedding:0.6b": {"size": "0.6GB", "context": 8192, "tier": "embedding"},
    }

    # Recommended models for different tasks. All chat/generation tasks resolve
    # to gemma3:4b; the "embedding" entry is aspirational (no call sites).
    TASK_MODELS = {
        "moderation": "gemma3:4b",
        "evaluation": "gemma3:4b",
        "generation": "gemma3:4b",
        "generation_alt": "gemma3:4b",
        "summary": "gemma3:4b",
        "classification": "gemma3:4b",
        "translation": "gemma3:4b",
        "planning": "gemma3:4b",
        "embedding": "qwen3-embedding:0.6b",
    }

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig(
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        self._available_models: List[str] = []
        self._last_health_check: Optional[datetime] = None
        self._throttle_state = ThrottleState()
        self._throttle_enabled = os.getenv("OLLAMA_THROTTLE", "true").lower() == "true"
        # 503 retry configuration. Tunable via env so the operator can
        # widen/narrow the patience window without a code change.
        self._max_503_retries = int(os.getenv("OLLAMA_503_RETRIES", "4"))
        self._503_backoff_base = float(os.getenv("OLLAMA_503_BACKOFF", "5"))

    def _concurrency_slots(self) -> Optional[asyncio.Semaphore]:
        """Lazily build the in-flight semaphore on the running loop.

        Created lazily (not in the dataclass default) because the provider is
        constructed outside any event loop by the schedulers, and binding a
        Semaphore to the wrong loop raises at await time.
        """
        if not self._throttle_enabled:
            return None
        # A malformed value in config.yaml must not raise from inside the
        # request path; fall back to the documented default instead.
        try:
            limit = int(self.config.throttle.get("max_concurrent_requests", 1) or 0)
        except (TypeError, ValueError):
            logger.warning(
                "throttling.ollama.max_concurrent_requests is not a number (%r); using 1",
                self.config.throttle.get("max_concurrent_requests"),
            )
            limit = 1
        if limit <= 0:
            return None
        state = self._throttle_state
        if state._slots is None or getattr(state._slots, "_moss_limit", None) != limit:
            state._slots = asyncio.Semaphore(limit)
            state._slots._moss_limit = limit  # type: ignore[attr-defined]
        return state._slots

    @asynccontextlib.asynccontextmanager
    async def _request_slot(self):
        """Hold one in-flight slot for the duration of an HTTP request.

        This is the piece `max_concurrent_requests` was missing: the throttle
        only spaced request *starts*, so 8 concurrent divergence agents all
        reached the GPU together regardless of the configured limit.
        """
        slots = self._concurrency_slots()
        if slots is None:
            yield
            return
        async with slots:
            yield

    async def _wait_for_throttle(self) -> None:
        """Wait for throttling conditions to be met.

        Releases the lock during sleep to avoid blocking other coroutines.
        """
        if not self._throttle_enabled:
            return

        throttle_config = self.config.throttle
        state = self._throttle_state

        # Phase 1: Check cooling period (release lock during sleep)
        cooling_wait = 0.0
        async with state._lock:
            now = time.time()
            if state.is_cooling and now < state.cooling_until:
                cooling_wait = state.cooling_until - now

        if cooling_wait > 0:
            logger.info(
                f"[Ollama] Cooling period: waiting {cooling_wait:.1f}s for GPU to cool down..."
            )
            await asyncio.sleep(cooling_wait)
            async with state._lock:
                state.is_cooling = False
                state.request_count = 0

        # Phase 2: Reserve a slot at least min_interval after the last one.
        #
        # The wait used to be computed under the lock but the slot claimed only
        # after sleeping, so every concurrent caller read the same
        # last_request_time, computed the same delay, and woke together -- the
        # interval throttled one caller and nothing else. Reserving and
        # computing in the same critical section is what makes it real;
        # sleeping still happens outside the lock so waiters do not serialize
        # on the mutex itself.
        async with state._lock:
            now = time.time()
            min_interval = throttle_config.get("min_request_interval", 5)
            scheduled_at = now
            if state.last_request_time > 0:
                scheduled_at = max(now, state.last_request_time + min_interval)

            state.last_request_time = scheduled_at
            state.request_count += 1

            # Check if cooling period is needed
            requests_before_cooling = throttle_config.get("requests_before_cooling", 5)
            if state.request_count >= requests_before_cooling:
                cooling_seconds = throttle_config.get("cooling_period_seconds", 30)
                state.is_cooling = True
                state.cooling_until = scheduled_at + cooling_seconds
                logger.info(
                    f"[Ollama] Scheduling cooling period after {requests_before_cooling} requests ({cooling_seconds}s)"
                )

        interval_wait = scheduled_at - time.time()
        if interval_wait > 0:
            logger.info(f"[Ollama] Throttling: waiting {interval_wait:.1f}s before next request...")
            await asyncio.sleep(interval_wait)

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        format_schema: Optional[Dict[str, Any]] = None,
        num_ctx: Optional[int] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> OllamaResponse:
        """
        Generate text using Ollama.

        Args:
            prompt: The prompt to send
            model: Model to use (default: config.default_model)
            system: System prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            format_schema: JSON schema for structured outputs. Passed as
                Ollama's ``format`` field, which enforces the schema with
                grammar-constrained decoding — invalid tokens (curly-quote
                delimiters, prose preambles, markdown fences) cannot be
                sampled at all. Supported since Ollama v0.5.0; only works on
                the native API, not the /v1 OpenAI-compatible endpoint.
            timeout: Per-call HTTP timeout in seconds, overriding
                `throttling.ollama.request_timeout`. That global value is
                sized for the longest task (a debate turn, 1800s), and a
                short task inheriting it turns "the GPU is wedged" into a
                30-minute hang per call. Covers only the HTTP request —
                throttle/cooling waits and the concurrency slot are acquired
                before the clock starts, so a short value here does not
                penalise a caller merely queued behind a debate.

        Returns:
            OllamaResponse with generated text
        """
        # Wait for throttle/cooling period
        await self._wait_for_throttle()

        model = model or self.config.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                # Always sent: without it Ollama loads the model at its own
                # default (4096), and long prompts silently truncate the
                # output at prompt+output == num_ctx. See DEFAULT_NUM_CTX.
                # A per-call num_ctx wins over the throttle-config default:
                # each distinct num_ctx is its own model instance on the
                # server, and a task whose prompt fits a small context must
                # be able to say so — a 16k KV-cache load can hang for
                # minutes on a congested shared GPU while the already-
                # resident small instance answers instantly (2026-08-05).
                "num_ctx": num_ctx or self.config.throttle.get("num_ctx", DEFAULT_NUM_CTX),
            },
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        if format_schema:
            payload["format"] = format_schema

        timeout = timeout or self.config.throttle.get("request_timeout", self.config.timeout)

        # Server-side 503 ("server busy, maximum pending requests exceeded")
        # is transient — Ollama returns it when its internal queue is full
        # because multiple PM2 workers (debate/trends/translator) hit it at
        # once. Retry with exponential backoff before giving up; the LLM
        # router's own fallback handles the give-up case.
        last_503_body = None
        for attempt in range(self._max_503_retries + 1):
            try:
                async with self._request_slot(), httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.config.base_url}/api/generate",
                        json=payload,
                    )
                    if response.status_code == 503:
                        last_503_body = response.text[:200]
                        if attempt < self._max_503_retries:
                            backoff = self._503_backoff_base * (2**attempt)
                            logger.warning(
                                f"[Ollama] 503 from server "
                                f"(attempt {attempt + 1}/{self._max_503_retries + 1}); "
                                f"sleeping {backoff:.1f}s before retry. body={last_503_body!r}"
                            )
                            await asyncio.sleep(backoff)
                            continue
                        raise ProviderError(
                            f"Ollama HTTP error: 503 (server busy after "
                            f"{self._max_503_retries + 1} retries) body={last_503_body!r}"
                        )

                    response.raise_for_status()
                    data = response.json()
                    result = OllamaResponse(
                        content=data.get("response", ""),
                        model=model,
                        total_duration=data.get("total_duration"),
                        load_duration=data.get("load_duration"),
                        prompt_eval_count=data.get("prompt_eval_count"),
                        eval_count=data.get("eval_count"),
                        done=data.get("done", True),
                        done_reason=data.get("done_reason"),
                    )
                    if result.truncated:
                        # Callers parse this content (JSON, plans, debate
                        # arguments); a silent cut-off produced 0-trend cycles
                        # for weeks. Make truncation impossible to miss.
                        logger.warning(
                            f"[Ollama] TRUNCATED generation from {model}: "
                            f"done={result.done} reason={result.done_reason!r} "
                            f"prompt_eval={result.prompt_eval_count} "
                            f"eval={result.eval_count} chars={len(result.content)}"
                        )
                    return result

            except httpx.TimeoutException as e:
                raise ProviderError(f"Ollama timeout after {timeout}s") from e
            except httpx.HTTPStatusError as e:
                raise ProviderError(f"Ollama HTTP error: {e.response.status_code}") from e
            except ProviderError:
                raise
            except Exception as e:
                raise ProviderError(f"Ollama error: {e}") from e

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream text generation.

        Yields:
            Text chunks as they are generated
        """
        model = model or self.config.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": self.config.throttle.get("num_ctx", DEFAULT_NUM_CTX),
            },
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST", f"{self.config.base_url}/api/generate", json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            raise ProviderError(f"Ollama stream error: {e}") from e

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        format_schema: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> OllamaResponse:
        """
        Chat completion using Ollama.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            model: Model to use
            system: System prompt
            temperature: Sampling temperature

        Returns:
            OllamaResponse with generated text
        """
        # Wait for throttle/cooling period
        await self._wait_for_throttle()

        model = model or self.config.default_model

        # Add system message if provided
        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend(messages)

        payload = {
            "model": model,
            "messages": chat_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": self.config.throttle.get("num_ctx", DEFAULT_NUM_CTX),
            },
        }

        if format_schema:
            payload["format"] = format_schema

        timeout = self.config.throttle.get("request_timeout", self.config.timeout)

        try:
            async with self._request_slot(), httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.config.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()

                return OllamaResponse(
                    content=data.get("message", {}).get("content", ""),
                    model=model,
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                    done=data.get("done", True),
                )

        except Exception as e:
            raise ProviderError(f"Ollama chat error: {e}") from e

    async def _fetch_available_models(self) -> List[str]:
        """Ask the server which models it has. Raises on failure."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.config.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

        self._available_models = [model["name"] for model in data.get("models", [])]
        return self._available_models

    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama, or [] when unreachable."""
        try:
            return await self._fetch_available_models()
        except Exception as e:
            logger.error(f"Error getting Ollama models: {e}")
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            async with httpx.AsyncClient(timeout=3600) as client:  # 1 hour timeout
                response = await client.post(
                    f"{self.config.base_url}/api/pull", json={"name": model}
                )
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Error pulling model {model}: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health and available models.

        This used to call ``get_available_models()``, which swallows every
        network, HTTP and JSON error into an empty list, and then report
        ``status="healthy"`` unconditionally -- so a completely unreachable
        Ollama looked healthy with no models, and the scheduler's health task
        never flagged it. The fetch now propagates its error, and a server
        that answers but is missing the model everything runs on is reported
        as degraded rather than healthy.
        """
        state = self._throttle_state
        throttle_status = {
            "enabled": self._throttle_enabled,
            "request_count": state.request_count,
            "is_cooling": state.is_cooling,
            "config": self.config.throttle,
        }

        try:
            models = await self._fetch_available_models()
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "base_url": self.config.base_url,
                "available_models": [],
                "default_model": self.config.default_model,
                "throttle": throttle_status,
            }

        self._last_health_check = utcnow()

        default_model = self.config.default_model
        if not models:
            status, detail = "degraded", "server reachable but reports no models"
        elif default_model not in models:
            status, detail = (
                "degraded",
                f"default model {default_model!r} is not installed on the server",
            )
        else:
            status, detail = "healthy", None

        result = {
            "status": status,
            "base_url": self.config.base_url,
            "available_models": models,
            "default_model": default_model,
            "last_check": self._last_health_check.isoformat(),
            "throttle": throttle_status,
        }
        if detail:
            result["detail"] = detail
            logger.warning(f"Ollama degraded: {detail}")
        return result

    def get_model_for_task(self, task: str) -> str:
        """Get recommended model for a task type."""
        return self.TASK_MODELS.get(task, self.config.default_model)

    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count."""
        # Rough estimate: ~4 characters per token for English
        return len(text) // 4

    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
