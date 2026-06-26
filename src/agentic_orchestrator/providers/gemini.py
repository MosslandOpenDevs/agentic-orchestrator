"""
Google Gemini provider adapter.

Handles API calls to Google's Gemini models with proper error handling.
"""

import os

from ..utils.logging import get_logger
from .base import (
    AuthenticationError,
    BaseProvider,
    CompletionResponse,
    Message,
    ModelNotAvailableError,
    ProviderError,
    QuotaExhaustedError,
    RateLimitError,
    RetryConfig,
)

logger = get_logger(__name__)

# Use the current google-genai SDK (the legacy google-generativeai SDK is EOL).
try:
    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types as genai_types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    genai_errors = None
    genai_types = None


class GeminiProvider(BaseProvider):
    """
    Google Gemini provider.

    Used for fast agentic tasks and secondary review.
    Supports latest preview models and fallback configuration.
    """

    provider_name = "gemini"

    # Default models
    DEFAULT_MODEL = "gemini-3-flash-preview"
    DEFAULT_FALLBACK = "gemini-3-pro-preview"
    SECONDARY_FALLBACK = "gemini-2.5-pro"

    def __init__(
        self,
        model: str | None = None,
        fallback_model: str | None = None,
        api_key: str | None = None,
        retry_config: RetryConfig | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize Gemini provider.

        Args:
            model: Model to use. Defaults to gemini-3-flash-preview.
            fallback_model: Fallback model. Defaults to gemini-3-pro-preview.
            api_key: Gemini API key. Defaults to GEMINI_API_KEY env var.
            retry_config: Retry configuration.
            dry_run: If True, don't make actual API calls.
        """
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            fallback_model=fallback_model or self.DEFAULT_FALLBACK,
            retry_config=retry_config,
            dry_run=dry_run,
        )
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.secondary_fallback = self.SECONDARY_FALLBACK
        self._client = None

    def _ensure_configured(self) -> None:
        """Ensure the Gemini client is created."""
        if self._client is not None:
            return

        if not GEMINI_AVAILABLE:
            raise ProviderError(
                "google-genai package not installed. Run: pip install google-genai",
                provider=self.provider_name,
            )

        if not self.api_key:
            raise AuthenticationError(
                "Gemini API key not set. Set GEMINI_API_KEY environment variable.",
                provider=self.provider_name,
            )

        self._client = genai.Client(api_key=self.api_key)

    def is_available(self) -> bool:
        """Check if Gemini provider is available."""
        return GEMINI_AVAILABLE and bool(self.api_key)

    def _make_request(
        self,
        messages: list[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """Make request to Gemini API."""
        self._ensure_configured()

        try:
            # Convert messages to the google-genai format: a list of Content
            # objects (role "user"/"model") plus an optional system_instruction.
            system_parts: list[str] = []
            contents = []

            for msg in messages:
                if msg.role == "system":
                    system_parts.append(msg.content)
                elif msg.role == "user":
                    contents.append(
                        genai_types.Content(role="user", parts=[genai_types.Part(text=msg.content)])
                    )
                elif msg.role == "assistant":
                    contents.append(
                        genai_types.Content(
                            role="model", parts=[genai_types.Part(text=msg.content)]
                        )
                    )

            config = None
            if system_parts:
                config = genai_types.GenerateContentConfig(
                    system_instruction="\n\n".join(system_parts)
                )

            response = self._client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            # Extract response text
            response_text = response.text or ""

            # Get usage if available
            usage = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(
                        response.usage_metadata, "candidates_token_count", 0
                    ),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            return CompletionResponse(
                content=response_text,
                model=model,
                provider=self.provider_name,
                usage=usage,
                finish_reason="stop",
                raw_response=response,
            )

        except Exception as e:
            self._handle_error(e, model)
            raise  # Should not reach here

    def _handle_error(self, error: Exception, model: str) -> None:
        """Convert Gemini exceptions to our exception types."""
        error_str = str(error).lower()

        # Check for specific google-genai API errors (APIError carries an HTTP code)
        if GEMINI_AVAILABLE and genai_errors and isinstance(error, genai_errors.APIError):
            code = getattr(error, "code", None)

            if code == 429 or "resource exhausted" in error_str:
                raise RateLimitError(
                    str(error),
                    provider=self.provider_name,
                    model=model,
                )

            if code == 403:
                if "quota" in error_str:
                    raise QuotaExhaustedError(
                        str(error),
                        provider=self.provider_name,
                        model=model,
                        quota_type="quota",
                    )
                raise AuthenticationError(
                    str(error),
                    provider=self.provider_name,
                    model=model,
                )

            if code == 404:
                raise ModelNotAvailableError(
                    str(error),
                    provider=self.provider_name,
                    model=model,
                )

        # String-based error detection
        if "rate limit" in error_str or "resource exhausted" in error_str:
            raise RateLimitError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        if "quota" in error_str or "billing" in error_str:
            raise QuotaExhaustedError(
                str(error),
                provider=self.provider_name,
                model=model,
                quota_type="quota",
            )

        if "api key" in error_str or "authentication" in error_str:
            raise AuthenticationError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        if "model" in error_str and "not found" in error_str:
            raise ModelNotAvailableError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        # Generic error
        raise ProviderError(
            str(error),
            provider=self.provider_name,
            model=model,
        )

    def complete(
        self,
        messages: list[Message],
        **kwargs,
    ) -> CompletionResponse:
        """
        Get a completion with retry logic and multi-level fallback.

        Gemini supports a secondary fallback (gemini-2.5-pro) in addition
        to the primary fallback.
        """
        if self.dry_run:
            return self._dry_run_response(messages)

        # Try primary model
        try:
            return self._complete_with_retry(messages, self.model, **kwargs)
        except (RateLimitError, ModelNotAvailableError) as e:
            logger.warning(f"{self.provider_name}: Primary model {self.model} failed: {e}")

            # Try primary fallback
            if self.fallback_model:
                try:
                    logger.info(f"Trying fallback model: {self.fallback_model}")
                    return self._complete_with_retry(messages, self.fallback_model, **kwargs)
                except (RateLimitError, ModelNotAvailableError) as e2:
                    logger.warning(
                        f"{self.provider_name}: Fallback {self.fallback_model} failed: {e2}"
                    )

                    # Try secondary fallback
                    if self.secondary_fallback:
                        logger.info(f"Trying secondary fallback: {self.secondary_fallback}")
                        return self._complete_with_retry(
                            messages, self.secondary_fallback, **kwargs
                        )
                    raise
            raise


def create_gemini_provider(
    model: str | None = None,
    fallback_model: str | None = None,
    dry_run: bool = False,
) -> GeminiProvider:
    """
    Factory function to create Gemini provider with config defaults.

    Args:
        model: Override model.
        fallback_model: Override fallback model.
        dry_run: Enable dry run mode.

    Returns:
        Configured GeminiProvider instance.
    """
    from ..utils.config import load_config

    config = load_config()

    return GeminiProvider(
        model=model or config.gemini_model,
        fallback_model=fallback_model or config.gemini_model_fallback,
        retry_config=RetryConfig(
            max_retries=config.rate_limit_max_retries,
            max_wait_seconds=config.rate_limit_max_wait,
        ),
        dry_run=dry_run or config.dry_run,
    )
