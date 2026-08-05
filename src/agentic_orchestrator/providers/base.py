"""
Base provider interface for LLM adapters.

Defines common interfaces, exceptions, and retry logic for all providers.

Spend governance lives here because there are two disjoint ways to reach a
paid model, and only one of them used to be governed:

    router path   HybridLLMRouter.route() -> provider.generate()
                  -> _make_request()            [gated + metered by the router]
    legacy path   stage/backlog @property -> provider.complete()
                  -> _complete_with_retry() -> _make_request()

The legacy path is the state-machine pipeline (``ao step`` / ``ao loop``) and
the GitHub backlog orchestrator (``ao backlog run`` / ``process``). It builds
Claude/OpenAI/Gemini providers straight from the ``create_*_provider``
factories, so it consulted neither ``MOSS_LOCAL_LLM_ONLY`` nor the budget:
no kill switch, no ``record_usage``, invisible to ``/usage``. No PM2 job
reaches it, but both API keys live in the server's ``.env``, so a manual
``ao`` invocation on the box could spend without limit or trace — on
``gpt-5.2-chat-latest`` ($2.50/$10.00 per M), 3.3x the debate tier's model.

Governing it at the factory (kill switch) and at ``_complete_with_retry``
(budget check + ledger write) covers all three paid providers, including
Gemini's overridden ``complete()``, and cannot double-count the router,
which never calls into this path.
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..utils.logging import get_logger

logger = get_logger(__name__)

LOCAL_ONLY_ENV = "MOSS_LOCAL_LLM_ONLY"

# Values that turn the kill switch OFF. Anything else — including the
# variable being unset — keeps the system local-only, so a forgotten or
# misspelled env var fails closed (no spend) rather than open.
_LOCAL_ONLY_DISABLED = ("0", "false", "no", "off")


def local_llm_only() -> bool:
    """Whether the ``MOSS_LOCAL_LLM_ONLY`` kill switch is engaged.

    Single source of truth for the flag: both the router and the paid
    provider factories read it through here, so the two entry points to a
    billed call can never disagree about whether spending is allowed.
    """
    return os.getenv(LOCAL_ONLY_ENV, "true").lower() not in _LOCAL_ONLY_DISABLED


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, provider: str = "", model: str = ""):
        super().__init__(message)
        self.provider = provider
        self.model = model


class RateLimitError(ProviderError):
    """
    Exception raised when rate limit is hit.

    Includes retry timing information when available.
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        model: str = "",
        retry_after: float | None = None,
        reset_time: float | None = None,
    ):
        super().__init__(message, provider, model)
        self.retry_after = retry_after  # Seconds to wait
        self.reset_time = reset_time  # Unix timestamp when limit resets


class QuotaExhaustedError(ProviderError):
    """
    Exception raised when API quota is exhausted.

    This typically requires user intervention (payment, key update).
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        model: str = "",
        quota_type: str = "unknown",
    ):
        super().__init__(message, provider, model)
        self.quota_type = quota_type  # e.g., "tokens", "requests", "billing"


class BudgetExhaustedError(QuotaExhaustedError):
    """
    Exception raised when the shared API budget has no headroom left.

    Deliberately a ``QuotaExhaustedError``: the legacy state machine already
    treats that as "pause and alert the operator" rather than "crash", and a
    spent budget wants exactly that handling. Unlike the router — which can
    silently degrade a task to local Ollama — the legacy path has no local
    alternative, so refusing is the only way to hold the cap.
    """

    def __init__(self, message: str, provider: str = "", model: str = ""):
        super().__init__(message, provider, model, quota_type="budget")


class PaidProviderBlockedError(ProviderError):
    """
    Exception raised when a paid provider is built under the kill switch.

    Raised at construction time by the ``create_*_provider`` factories so the
    refusal lands before any prompt is assembled, and so it cannot be
    mistaken for a transient API failure and retried.
    """

    pass


class ModelNotAvailableError(ProviderError):
    """Exception raised when a model is not available."""

    pass


def enforce_local_only(provider_name: str, dry_run: bool = False) -> None:
    """Refuse to build a paid provider while the kill switch is engaged.

    Args:
        provider_name: Provider being constructed, for the error message.
        dry_run: Dry-run providers return canned text and never reach the
            network, so they are exempt — blocking them would break
            ``--dry-run`` rehearsals of the legacy pipeline, which are the
            safe way to exercise it.

    Raises:
        PaidProviderBlockedError: If ``MOSS_LOCAL_LLM_ONLY`` is engaged.
    """
    if dry_run or not local_llm_only():
        return

    raise PaidProviderBlockedError(
        f"{LOCAL_ONLY_ENV} is engaged — refusing to construct the paid "
        f"{provider_name} provider. Set {LOCAL_ONLY_ENV}=false to allow "
        f"billed calls, or pass dry_run=True to rehearse without spending.",
        provider=provider_name,
    )


class AuthenticationError(ProviderError):
    """Exception raised for authentication failures."""

    pass


@dataclass
class Message:
    """A message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class CompletionResponse:
    """Response from a completion request."""

    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    raw_response: Any | None = None


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 5,
        max_wait_seconds: int = 3600,
        initial_backoff: float = 10.0,
        backoff_multiplier: float = 2.0,
    ):
        self.max_retries = max_retries
        self.max_wait_seconds = max_wait_seconds
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implements common retry logic and error handling.
    Subclasses must implement the actual API calls.
    """

    provider_name: str = "base"

    def __init__(
        self,
        model: str,
        fallback_model: str | None = None,
        retry_config: RetryConfig | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize provider.

        Args:
            model: Primary model to use.
            fallback_model: Fallback model if primary fails.
            retry_config: Retry configuration.
            dry_run: If True, don't make actual API calls.
        """
        self.model = model
        self.fallback_model = fallback_model
        self.retry_config = retry_config or RetryConfig()
        self.dry_run = dry_run
        self._current_model = model

    @abstractmethod
    def _make_request(
        self,
        messages: list[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """
        Make the actual API request.

        Subclasses must implement this method.

        Args:
            messages: List of messages.
            model: Model to use.
            **kwargs: Additional provider-specific arguments.

        Returns:
            CompletionResponse with the result.

        Raises:
            RateLimitError: When rate limited.
            QuotaExhaustedError: When quota is exhausted.
            ProviderError: For other errors.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available (API key set, etc.).

        Returns:
            True if provider can be used.
        """
        pass

    def complete(
        self,
        messages: list[Message],
        **kwargs,
    ) -> CompletionResponse:
        """
        Get a completion with retry logic and fallback.

        Args:
            messages: List of messages.
            **kwargs: Additional arguments.

        Returns:
            CompletionResponse with the result.

        Raises:
            RateLimitError: When rate limit exceeded and max retries hit.
            QuotaExhaustedError: When quota is exhausted.
            ProviderError: For other errors after retries.
        """
        if self.dry_run:
            return self._dry_run_response(messages)

        # Try primary model
        try:
            return self._complete_with_retry(messages, self.model, **kwargs)
        except (RateLimitError, ModelNotAvailableError) as e:
            if self.fallback_model:
                logger.warning(
                    f"{self.provider_name}: Primary model {self.model} failed, "
                    f"trying fallback {self.fallback_model}: {e}"
                )
                return self._complete_with_retry(messages, self.fallback_model, **kwargs)
            raise

    def _complete_with_retry(
        self,
        messages: list[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """
        Complete with retry logic for rate limits.

        Args:
            messages: List of messages.
            model: Model to use.
            **kwargs: Additional arguments.

        Returns:
            CompletionResponse with the result.
        """
        self._current_model = model
        last_error = None
        backoff = self.retry_config.initial_backoff

        # Before the first byte leaves: the ledger is the only thing standing
        # between a manual `ao` run and an unbounded bill. Checked here rather
        # than in complete() so each model in a fallback chain re-checks.
        self._check_budget(model)

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = self._make_request(messages, model, **kwargs)
                self._record_usage(model, response)
                return response

            except RateLimitError as e:
                last_error = e

                # Determine wait time
                wait_time = self._calculate_wait_time(e, backoff)

                if wait_time > self.retry_config.max_wait_seconds:
                    logger.error(
                        f"{self.provider_name}: Wait time {wait_time}s exceeds "
                        f"max {self.retry_config.max_wait_seconds}s, giving up"
                    )
                    raise

                if attempt < self.retry_config.max_retries:
                    logger.warning(
                        f"{self.provider_name}: Rate limited, waiting {wait_time:.1f}s "
                        f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1})"
                    )
                    time.sleep(wait_time)
                    backoff *= self.retry_config.backoff_multiplier
                else:
                    logger.error(f"{self.provider_name}: Max retries exceeded for rate limit")
                    raise

            except QuotaExhaustedError:
                # Don't retry quota errors - they need user intervention
                raise

            except ProviderError as e:
                # For other errors, retry with backoff
                last_error = e
                if attempt < self.retry_config.max_retries:
                    logger.warning(
                        f"{self.provider_name}: Request failed, retrying in {backoff}s: {e}"
                    )
                    time.sleep(backoff)
                    backoff *= self.retry_config.backoff_multiplier
                else:
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise ProviderError(f"Unknown error in {self.provider_name}")

    @staticmethod
    def _budget_controller():
        """Build a BudgetController, or None if the ledger is unreachable.

        Imported lazily: ``llm.budget`` pulls in the DB layer and
        ``llm/__init__`` imports the router, which imports this module —
        a module-level import would be circular.
        """
        try:
            from ..llm.budget import BudgetController

            return BudgetController()
        except Exception as e:  # DB down, migrations missing, import error
            logger.warning(f"Budget ledger unavailable: {e}")
            return None

    def _check_budget(self, model: str) -> None:
        """Refuse the call when the daily or monthly cap is already spent.

        Fails *open* when the ledger itself is unreachable: a broken DB
        should not take down the pipeline, and the kill switch plus the
        provider's own quota errors remain as backstops.

        Raises:
            BudgetExhaustedError: If the budget has no headroom.
        """
        controller = self._budget_controller()
        if controller is None:
            return

        try:
            status = controller.get_budget_status()
        except Exception as e:
            logger.warning(f"Could not read budget status, allowing call: {e}")
            return

        if status.get("can_use_api", True):
            return

        daily = status.get("daily", {})
        monthly = status.get("monthly", {})
        raise BudgetExhaustedError(
            f"API budget exhausted — refusing {self.provider_name}:{model}. "
            f"Today ${daily.get('total_cost', 0):.4f}/"
            f"${daily.get('daily_limit', 0):.2f}, this month "
            f"${monthly.get('total_cost', 0):.4f}/"
            f"${monthly.get('monthly_limit', 0):.2f}.",
            provider=self.provider_name,
            model=model,
        )

    def _record_usage(self, model: str, response: CompletionResponse) -> None:
        """Write a billed completion to the shared ``api_usage`` ledger.

        Only the legacy synchronous path lands here — the router reaches
        ``_make_request`` through ``generate()`` and records usage itself —
        so this cannot double-count.

        Metering must never be the reason a call fails, so every error is
        swallowed with a warning.
        """
        usage = response.usage or {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)

        # Claude's CLI mode reports no token usage (it bills against the
        # Claude Code subscription, not the API). Recording zero-token rows
        # would inflate the request count in /usage without adding cost.
        if not input_tokens and not output_tokens:
            return

        controller = self._budget_controller()
        if controller is None:
            return

        try:
            controller.record_usage(
                provider=self.provider_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except Exception as e:
            logger.warning(f"Could not record {self.provider_name}:{model} usage: {e}")

    def _calculate_wait_time(self, error: RateLimitError, default_backoff: float) -> float:
        """Calculate wait time from rate limit error or use default backoff."""
        if error.retry_after is not None:
            return error.retry_after
        if error.reset_time is not None:
            wait = error.reset_time - time.time()
            return max(0, wait)
        return default_backoff

    def _dry_run_response(self, messages: list[Message]) -> CompletionResponse:
        """Generate a dry-run response for testing."""
        return CompletionResponse(
            content=f"[DRY RUN] {self.provider_name} response for {len(messages)} messages",
            model=self.model,
            provider=self.provider_name,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="dry_run",
        )

    def chat(self, user_message: str, system_message: str | None = None) -> str:
        """
        Simple chat interface.

        Args:
            user_message: User's message.
            system_message: Optional system message.

        Returns:
            Assistant's response content.
        """
        messages = []
        if system_message:
            messages.append(Message(role="system", content=system_message))
        messages.append(Message(role="user", content=user_message))

        response = self.complete(messages)
        return response.content
