"""
Hybrid LLM router for intelligent model selection.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..providers.claude import ClaudeProvider
from ..providers.ollama import OllamaProvider, OllamaResponse
from ..providers.openai import OpenAIProvider
from ..timeutil import utcnow
from .budget import BudgetController
from .hierarchy import LLMHierarchy

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""

    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost: float
    duration_seconds: float
    cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": self.cost,
            "duration_seconds": self.duration_seconds,
            "cached": self.cached,
        }


class HybridLLMRouter:
    """
    Routes LLM requests between local (Ollama) and API providers.

    Routing strategy:
    1. Default to local models (free)
    2. Use API for critical/final outputs
    3. Automatic fallback when API budget exceeded
    4. Task-based model selection
    """

    def __init__(
        self,
        ollama: Optional[OllamaProvider] = None,
        claude: Optional[ClaudeProvider] = None,
        openai: Optional[OpenAIProvider] = None,
        budget: Optional[BudgetController] = None,
        hierarchy: Optional[LLMHierarchy] = None,
    ):
        import os

        # Ollama-only mode: when MOSS_LOCAL_LLM_ONLY is unset or truthy
        # (default), the router refuses to instantiate paid providers and
        # forces every request to local models, regardless of what
        # `quality` or `force_api` the caller asks for. Set to "false" to
        # re-enable the hybrid behavior.
        self.local_only = os.getenv("MOSS_LOCAL_LLM_ONLY", "true").lower() not in (
            "0",
            "false",
            "no",
            "off",
        )

        self.ollama = ollama or OllamaProvider()
        self.claude = None if self.local_only else claude
        self.openai = None if self.local_only else openai
        self.budget = budget or BudgetController()
        self.hierarchy = hierarchy or LLMHierarchy()

        # Paid-tier allowlist (config.yaml `llm.paid_tiers`): call sites may
        # name a tier ("debate"); only enabled tiers whose provider is
        # actually initialized can reach a paid model. Two independent
        # switches must both be on before a single cent is spent: the env
        # flag (MOSS_LOCAL_LLM_ONLY=false) and the tier's `enabled` in
        # config — everything not listed stays on local Ollama either way.
        self.paid_tiers = self._load_paid_tiers()

        if not self.local_only:
            self._init_api_providers()
        else:
            logger.info("HybridLLMRouter: MOSS_LOCAL_LLM_ONLY active — paid providers disabled")

    @staticmethod
    def _load_paid_tiers() -> dict:
        """Read `llm.paid_tiers` from config.yaml; {} on any failure."""
        from pathlib import Path

        import yaml

        config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            tiers = (config.get("llm") or {}).get("paid_tiers") or {}
            if not isinstance(tiers, dict):
                return {}
            # Drop malformed entries here rather than at the call site: a
            # one-line YAML typo (`debate: true`) would otherwise reach
            # `tier.get(...)` in route() as a bool and raise AttributeError
            # on every debate call — outside the try/fallback block, so it
            # would kill the debate instead of degrading it to local.
            clean = {}
            for name, tier in tiers.items():
                if isinstance(tier, dict):
                    clean[name] = tier
                else:
                    logger.warning(f"Ignoring malformed paid tier '{name}': expected a mapping")
            return clean
        except Exception as e:
            logger.warning(f"Could not load paid-tier config, staying fully local: {e}")
            return {}

    def _init_api_providers(self):
        """Initialize API providers if not provided. No-op in local-only mode."""
        import os

        if self.local_only:
            return

        if self.claude is None and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.claude = ClaudeProvider()
            except Exception:
                pass

        if self.openai is None and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai = OpenAIProvider()
            except Exception:
                pass

    async def route(
        self,
        prompt: str,
        task_type: str = "generation",
        system: Optional[str] = None,
        quality: str = "normal",  # low, normal, high, critical
        force_local: bool = False,
        force_api: bool = False,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_schema: Optional[dict] = None,
        num_ctx: Optional[int] = None,
        paid_tier: Optional[str] = None,
    ) -> LLMResponse:
        """
        Route a request to the appropriate LLM.

        Args:
            prompt: The prompt to send
            task_type: Type of task (for model selection)
            system: System prompt
            quality: Required quality level
            force_local: Force use of local models
            force_api: Force use of API models
            model: Specific model to use (overrides routing)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_schema: JSON schema for structured outputs. On Ollama
                this becomes the ``format`` field (grammar-constrained
                decoding, supported since v0.5.0) — the model physically
                cannot emit smart-quote delimiters, prose preambles, or
                markdown fences. Ignored on the Claude/OpenAI paths, which
                are unused in local-only production.
            num_ctx: Per-call Ollama context override. Each distinct value
                is its own model instance server-side; tasks whose prompt
                fits a small context should pass one so they use the
                already-resident instance instead of forcing a large
                KV-cache load (which can hang on a congested shared GPU).
                None keeps the throttle-config default. Forwarded on every
                Ollama path, including both fallbacks — a dropped override
                would silently reintroduce the hang.
            paid_tier: Name of a paid-API tier from config.yaml
                `llm.paid_tiers` (e.g. "debate"). Honored only when the tier
                is enabled, its provider is initialized (needs
                MOSS_LOCAL_LLM_ONLY=false plus an API key), the caller did
                not pass an explicit `model` or `force_local`, and the
                budget has headroom. Any missing precondition silently
                falls back to the normal local selection — an API outage or
                an exhausted budget must degrade the tier's task to local,
                never kill it.

        Returns:
            LLMResponse with generated content
        """
        start_time = utcnow()

        # In local-only mode any caller-supplied force_api / paid model
        # selection is silently overridden — we never make billed calls.
        if self.local_only:
            force_api = False
            force_local = True
            if model:
                model_config = self.hierarchy.get_model_config(model)
                if model_config and model_config.provider != "ollama":
                    logger.warning(
                        f"local-only: ignoring requested paid model '{model}', "
                        f"falling back to task-based local selection for '{task_type}'"
                    )
                    model = None

        # Determine model to use
        if model:
            selected_model = model
        else:
            selected_model = self._select_model(
                task_type=task_type,
                quality=quality,
                force_local=force_local,
                force_api=force_api,
            )
            # Paid-tier override — the ONLY doorway to paid models besides
            # an explicit force_api/model. Note force_local has already
            # absorbed local-only mode above, so the env kill-switch also
            # kills tiers. If the provider object is missing (no key /
            # local-only) the provider branch below falls back to local by
            # itself, but checking here keeps the budget math honest.
            if paid_tier and not force_local:
                # _load_paid_tiers guarantees dict values; be defensive
                # anyway since paid_tiers is a public attribute callers and
                # tests may set directly, and this runs outside the try.
                tier = self.paid_tiers.get(paid_tier)
                tier = tier if isinstance(tier, dict) else {}
                tier_model = tier.get("model")
                tier_provider_name = str(tier.get("provider") or "")
                tier_provider = getattr(self, tier_provider_name, None)
                if (
                    tier.get("enabled")
                    and tier_model
                    and tier_provider is not None
                    and self.budget.get_budget_status()["can_use_api"]
                ):
                    selected_model = tier_model
                    logger.info(
                        f"Paid tier '{paid_tier}' active: routing to "
                        f"{tier_provider_name}:{tier_model}"
                    )

        # Get model config
        model_config = self.hierarchy.get_model_config(selected_model)
        provider_name = model_config.provider if model_config else "ollama"

        # Route to appropriate provider
        try:
            if provider_name == "ollama":
                response = await self._call_ollama(
                    model=selected_model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    format_schema=response_schema,
                    num_ctx=num_ctx,
                )
            elif provider_name == "claude" and self.claude:
                response = await self._call_claude(
                    model=selected_model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            elif provider_name == "openai" and self.openai:
                response = await self._call_openai(
                    model=selected_model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                # Fallback to local
                fallback = self.hierarchy.get_fallback_model(selected_model)
                response = await self._call_ollama(
                    model=fallback,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    format_schema=response_schema,
                    num_ctx=num_ctx,
                )
                selected_model = fallback
                provider_name = "ollama"

        except Exception as e:
            # On error, try fallback (once only to prevent infinite loops)
            logger.error(f"Error with {selected_model}: {e}")
            fallback = self.hierarchy.get_fallback_model(selected_model)

            if fallback and fallback != selected_model:
                try:
                    response = await self._call_ollama(
                        model=fallback,
                        prompt=prompt,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        format_schema=response_schema,
                        num_ctx=num_ctx,
                    )
                    selected_model = fallback
                    provider_name = "ollama"
                except Exception as fallback_error:
                    logger.error(f"Fallback model {fallback} also failed: {fallback_error}")
                    raise fallback_error
            else:
                raise

        # Calculate duration
        duration = (utcnow() - start_time).total_seconds()

        # Record usage for API calls
        if provider_name != "ollama":
            self.budget.record_usage(
                provider=provider_name,
                model=selected_model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )

        return LLMResponse(
            content=response.content,
            model=selected_model,
            provider=provider_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=self.budget.estimate_cost(
                selected_model, response.input_tokens, response.output_tokens
            ),
            duration_seconds=duration,
        )

    def _select_model(
        self,
        task_type: str,
        quality: str,
        force_local: bool,
        force_api: bool,
    ) -> str:
        """Select the best model for the request."""
        # Check budget status
        budget_status = self.budget.get_budget_status()
        budget_available = budget_status["can_use_api"]
        self.budget.should_use_local()

        # Force local if requested or no budget
        if force_local or not budget_available:
            return self.hierarchy.get_model_for_task(
                task_type,
                prefer_local=True,
                budget_available=False,
            )

        # Force API if requested and available
        if force_api and budget_available:
            return self.hierarchy.get_model_for_task(
                task_type,
                prefer_local=False,
                budget_available=True,
            )

        # Quality-based selection - always prefer local to save costs
        if quality == "critical":
            # Use best local model for critical tasks
            return "gemma3:4b"

        elif quality == "high":
            return "gemma3:4b"

        else:
            # Normal/low quality - use local
            return self.hierarchy.get_model_for_task(
                task_type,
                prefer_local=True,
                budget_available=budget_available,
            )

    async def _call_ollama(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        format_schema: Optional[dict] = None,
        num_ctx: Optional[int] = None,
    ) -> OllamaResponse:
        """Call Ollama provider."""
        return await self.ollama.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            format_schema=format_schema,
            num_ctx=num_ctx,
        )

    async def _call_claude(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ):
        """Call Claude provider."""
        if not self.claude:
            raise Exception("Claude provider not configured")

        response = await self.claude.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )

        # Convert to OllamaResponse-like object
        class APIResponse:
            def __init__(self, content, input_tokens, output_tokens):
                self.content = content
                self.input_tokens = input_tokens
                self.output_tokens = output_tokens

        return APIResponse(
            content=response.get("content", ""),
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
        )

    async def _call_openai(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ):
        """Call OpenAI provider."""
        if not self.openai:
            raise Exception("OpenAI provider not configured")

        response = await self.openai.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )

        class APIResponse:
            def __init__(self, content, input_tokens, output_tokens):
                self.content = content
                self.input_tokens = input_tokens
                self.output_tokens = output_tokens

        return APIResponse(
            content=response.get("content", ""),
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        health = {
            "status": "healthy",
            "providers": {},
            "budget": self.budget.get_budget_status(),
        }

        # Check Ollama
        ollama_health = await self.ollama.health_check()
        health["providers"]["ollama"] = ollama_health

        if ollama_health.get("status") != "healthy":
            health["status"] = "degraded"

        # Check Claude
        if self.claude:
            try:
                health["providers"]["claude"] = {"status": "configured"}
            except Exception as e:
                health["providers"]["claude"] = {"status": "error", "error": str(e)}

        # Check OpenAI
        if self.openai:
            try:
                health["providers"]["openai"] = {"status": "configured"}
            except Exception as e:
                health["providers"]["openai"] = {"status": "error", "error": str(e)}

        return health

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models by provider."""
        return {
            "local": self.hierarchy.get_local_models(),
            "api": self.hierarchy.get_api_models(),
        }
