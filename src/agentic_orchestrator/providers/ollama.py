"""
Ollama Local LLM provider.

Provides interface to Ollama for running local LLMs.
Includes throttling and cooling support to prevent overheating.
"""

import asyncio
import json
import os
import time
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, AsyncIterator

import logging

import httpx

from .base import ProviderError

logger = logging.getLogger(__name__)


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
    # Consolidated to a single chat model + a single embedding model so the shared
    # ~8GB GPU never has to swap. Any other model name will 404 against the server.
    AVAILABLE_MODELS = {
        "gemma3:4b": {"size": "6.6GB", "context": 32768, "tier": "chat"},
        "qwen3-embedding:0.6b": {"size": "0.6GB", "context": 8192, "tier": "embedding"},
    }

    # Recommended models for different tasks. All chat/generation tasks resolve
    # to gemma3:4b — embedding is the only task that uses qwen3-embedding:0.6b.
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
            logger.info(f"[Ollama] Cooling period: waiting {cooling_wait:.1f}s for GPU to cool down...")
            await asyncio.sleep(cooling_wait)
            async with state._lock:
                state.is_cooling = False
                state.request_count = 0

        # Phase 2: Enforce minimum interval (release lock during sleep)
        interval_wait = 0.0
        async with state._lock:
            now = time.time()
            min_interval = throttle_config.get("min_request_interval", 5)
            elapsed = now - state.last_request_time
            if elapsed < min_interval and state.last_request_time > 0:
                interval_wait = min_interval - elapsed

        if interval_wait > 0:
            logger.info(f"[Ollama] Throttling: waiting {interval_wait:.1f}s before next request...")
            await asyncio.sleep(interval_wait)

        # Phase 3: Update state (hold lock briefly)
        async with state._lock:
            state.last_request_time = time.time()
            state.request_count += 1

            # Check if cooling period is needed
            requests_before_cooling = throttle_config.get("requests_before_cooling", 5)
            if state.request_count >= requests_before_cooling:
                cooling_seconds = throttle_config.get("cooling_period_seconds", 30)
                state.is_cooling = True
                state.cooling_until = time.time() + cooling_seconds
                logger.info(f"[Ollama] Scheduling cooling period after {requests_before_cooling} requests ({cooling_seconds}s)")

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
        **kwargs
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
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        timeout = self.config.throttle.get("request_timeout", self.config.timeout)

        # Server-side 503 ("server busy, maximum pending requests exceeded")
        # is transient — Ollama returns it when its internal queue is full
        # because multiple PM2 workers (debate/trends/translator) hit it at
        # once. Retry with exponential backoff before giving up; the LLM
        # router's own fallback handles the give-up case.
        last_503_body = None
        for attempt in range(self._max_503_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.config.base_url}/api/generate",
                        json=payload,
                    )
                    if response.status_code == 503:
                        last_503_body = response.text[:200]
                        if attempt < self._max_503_retries:
                            backoff = self._503_backoff_base * (2 ** attempt)
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
                    return OllamaResponse(
                        content=data.get("response", ""),
                        model=model,
                        total_duration=data.get("total_duration"),
                        load_duration=data.get("load_duration"),
                        prompt_eval_count=data.get("prompt_eval_count"),
                        eval_count=data.get("eval_count"),
                        done=data.get("done", True),
                    )

            except httpx.TimeoutException:
                raise ProviderError(f"Ollama timeout after {timeout}s")
            except httpx.HTTPStatusError as e:
                raise ProviderError(f"Ollama HTTP error: {e.response.status_code}")
            except ProviderError:
                raise
            except Exception as e:
                raise ProviderError(f"Ollama error: {e}")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
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
            }
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.config.base_url}/api/generate",
                    json=payload
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
            raise ProviderError(f"Ollama stream error: {e}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
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
            }
        }

        timeout = self.config.throttle.get("request_timeout", self.config.timeout)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return OllamaResponse(
                    content=data.get("message", {}).get("content", ""),
                    model=model,
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                    done=data.get("done", True)
                )

        except Exception as e:
            raise ProviderError(f"Ollama chat error: {e}")

    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()

                self._available_models = [
                    model["name"] for model in data.get("models", [])
                ]
                return self._available_models

        except Exception as e:
            logger.error(f"Error getting Ollama models: {e}")
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            async with httpx.AsyncClient(timeout=3600) as client:  # 1 hour timeout
                response = await client.post(
                    f"{self.config.base_url}/api/pull",
                    json={"name": model}
                )
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Error pulling model {model}: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health and available models."""
        try:
            models = await self.get_available_models()
            self._last_health_check = datetime.utcnow()

            state = self._throttle_state
            throttle_status = {
                "enabled": self._throttle_enabled,
                "request_count": state.request_count,
                "is_cooling": state.is_cooling,
                "config": self.config.throttle,
            }

            return {
                "status": "healthy",
                "base_url": self.config.base_url,
                "available_models": models,
                "default_model": self.config.default_model,
                "last_check": self._last_health_check.isoformat(),
                "throttle": throttle_status,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "base_url": self.config.base_url,
            }

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
