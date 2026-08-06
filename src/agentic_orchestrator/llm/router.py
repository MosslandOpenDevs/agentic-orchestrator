"""
Hybrid LLM router for intelligent model selection.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..providers.base import local_llm_only
from ..providers.claude import ClaudeProvider
from ..providers.ollama import OllamaProvider, OllamaResponse
from ..providers.openai import OpenAIProvider
from ..timeutil import utcnow
from .budget import BudgetController
from .hierarchy import LLMHierarchy

logger = logging.getLogger(__name__)

# Env var that must hold an API key for a paid tier's provider to be usable.
# Used by describe_paid_tier() to answer "could this tier bill anything?"
# without constructing a provider or touching the network.
_PROVIDER_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}


def describe_paid_tier(
    name: str,
    tier: Optional[dict],
    *,
    local_only: bool,
    provider_ready: Optional[bool] = None,
    budget_ok: Optional[bool] = None,
) -> Dict[str, Any]:
    """Effective state of one paid tier: active, or *why* it is not.

    A paid tier that cannot reach its provider degrades to local Ollama by
    design — an API outage must not kill the debate. The failure mode that
    design creates is that a tier which was never enabled is indistinguishable
    from one working perfectly: no error, no alert, `/status` healthy, and the
    only evidence is an empty `api_usage` ledger nobody watches. That is
    exactly what happened between 2026-08-05 and 2026-08-06, when PM2 served
    the debate a stale ``MOSS_LOCAL_LLM_ONLY=true`` and every debate quietly
    ran on gemma3:4b — the quality ceiling v0.6.19 shipped to remove.

    So the degradation stays, but it is never silent: route() logs the reason
    at WARNING, and the API reports it on /status and /usage. This function is
    the single place the reason is derived, so the runtime path and the
    endpoints can never disagree about whether spending is possible.

    ``provider_ready``/``budget_ok`` default to None meaning "not checked" —
    a caller that cannot cheaply determine them (e.g. the DB-free /status
    handler) gets a verdict from the preconditions it *can* see rather than a
    false negative.
    """
    tier = tier if isinstance(tier, dict) else None
    provider = str((tier or {}).get("provider") or "") or None
    model = (tier or {}).get("model") or None
    enabled = bool((tier or {}).get("enabled"))

    if provider_ready is None and provider:
        key_env = _PROVIDER_KEY_ENV.get(provider)
        # Unknown provider name: no key to look for, so leave it unchecked
        # rather than declaring it broken.
        provider_ready = bool(os.getenv(key_env)) if key_env else None

    # Precedence matters: report the switch an operator must flip *first*.
    if tier is None:
        reason = f"tier '{name}' is not configured in config.yaml llm.paid_tiers"
    elif local_only:
        reason = "MOSS_LOCAL_LLM_ONLY is engaged — paid providers disabled"
    elif not enabled:
        reason = f"tier '{name}' is disabled (llm.paid_tiers.{name}.enabled)"
    elif not model:
        reason = f"tier '{name}' has no model configured"
    elif not provider:
        reason = f"tier '{name}' has no provider configured"
    elif provider_ready is False:
        reason = (
            f"provider '{provider}' unavailable (no {_PROVIDER_KEY_ENV.get(provider, 'API key')})"
        )
    elif budget_ok is False:
        reason = "API budget exhausted (see config.yaml budget.*)"
    else:
        reason = None

    return {
        "name": name,
        "enabled": enabled,
        "provider": provider,
        "model": model,
        "active": reason is None,
        "reason": reason,
    }


_PAID_TIERS_CACHE: Optional[dict] = None


def _cached_paid_tiers() -> dict:
    """Parsed `llm.paid_tiers`, read from config.yaml once per process.

    Same contract as RSSAdapter's feed list: editing config.yaml takes effect
    on restart. `/status` is public, unauthenticated and uncached, and its
    handler is `async def` on a single-instance app — re-parsing 22 KB of YAML
    there costs ~8 ms of blocking CPU on the event loop per request, several
    times the endpoint's entire remaining cost. The verdict is NOT cached,
    only the file parse: `local_only`, the API-key env and the budget are all
    still evaluated per call, so a kill switch flip shows up immediately.

    Deliberately not `@lru_cache` on `_load_paid_tiers` itself — the malformed
    config tests monkeypatch `yaml.safe_load` and call that method directly,
    and would poison or read a stale cache.
    """
    global _PAID_TIERS_CACHE
    if _PAID_TIERS_CACHE is None:
        _PAID_TIERS_CACHE = HybridLLMRouter._load_paid_tiers()
    return _PAID_TIERS_CACHE


def paid_tier_report(budget_ok: Optional[bool] = None) -> Dict[str, Any]:
    """Config-level view of every paid tier, for /status and /usage.

    Derived from the same preconditions route() uses, but without building a
    provider, making a network call, or re-reading config.yaml, so it is safe
    on hot public endpoints.

    Caveat worth knowing when reading the output: this reflects *this*
    process's environment. The API and the debate scheduler are separate PM2
    apps, so in principle they could disagree — in practice both take their
    env from one `pm2 start ecosystem.config.js`, which is why they were
    wrong together in the 2026-08-06 incident and why this reading would have
    caught it.
    """
    local_only = local_llm_only()
    tiers = {
        name: describe_paid_tier(name, tier, local_only=local_only, budget_ok=budget_ok)
        for name, tier in _cached_paid_tiers().items()
    }
    degraded = sorted(n for n, t in tiers.items() if t["enabled"] and not t["active"])
    return {
        # "degraded" means a tier that config says should be spending is not.
        # An all-local deployment (no tiers, or all disabled) is "healthy".
        "status": "degraded" if degraded else "healthy",
        "local_only": local_only,
        "degraded_tiers": degraded,
        "paid_tiers": tiers,
    }


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
        # Ollama-only mode: when MOSS_LOCAL_LLM_ONLY is unset or truthy
        # (default), the router refuses to instantiate paid providers and
        # forces every request to local models, regardless of what
        # `quality` or `force_api` the caller asks for. Set to "false" to
        # re-enable the hybrid behavior.
        #
        # Shared with the paid provider factories via local_llm_only() so
        # the router and the legacy `ao` CLI path read one flag one way.
        self.local_only = local_llm_only()

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
        # A pinned paid tier retries ITSELF rather than degrading to local.
        # Short and few: the debate's own cron tick is the real retry, and a
        # long wait here just holds a debate round open.
        self._paid_tier_retries = int(os.getenv("MOSS_PAID_TIER_RETRIES", "2"))
        self._paid_tier_backoff = float(os.getenv("MOSS_PAID_TIER_BACKOFF", "2.0"))
        # Tiers already reported as degraded. One debate makes ~38 routed
        # calls; the operator needs the fact once, not 38 times. Each cron
        # tick is a fresh process, so this still warns once per debate run.
        self._degraded_tiers_warned: set = set()

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

    def _warn_tier_degraded(
        self,
        name: str,
        *,
        caller_model: Optional[str],
        caller_forced_local: bool,
    ) -> None:
        """Report, once per process, that a requested paid tier is not active.

        Never raises: this is diagnostics on the hot path, and a broken
        ledger must not take down a debate that is otherwise fine.
        """
        if caller_model or caller_forced_local:
            # Documented per-call opt-out, not a failure. Keep it at DEBUG so
            # the WARNING channel stays a reliable signal of real degradation.
            logger.debug(f"Paid tier '{name}' skipped: caller passed model/force_local")
            return
        # Lazily materialized: a router built without __init__ (tests do this,
        # and paid_tiers is already documented as caller-settable) must still
        # route rather than die on a missing diagnostics attribute.
        warned = getattr(self, "_degraded_tiers_warned", None)
        if warned is None:
            warned = self._degraded_tiers_warned = set()
        if name in warned:
            return
        warned.add(name)

        try:
            tier = self.paid_tiers.get(name)
            provider_name = str((tier or {}).get("provider") or "")
            try:
                budget_ok = bool(self.budget.get_budget_status().get("can_use_api"))
            except Exception:
                # Ledger unreadable: report the preconditions we can see
                # rather than blaming the budget.
                budget_ok = None
            state = describe_paid_tier(
                name,
                tier,
                local_only=self.local_only,
                provider_ready=(
                    getattr(self, provider_name, None) is not None if provider_name else None
                ),
                budget_ok=budget_ok,
            )
            logger.warning(
                f"Paid tier '{name}' requested but NOT active — this run is "
                f"degrading to local Ollama. Reason: {state['reason']}"
            )
        except Exception:  # pragma: no cover - diagnostics must never break routing
            logger.warning(f"Paid tier '{name}' requested but NOT active — degrading to local")

    def _init_api_providers(self):
        """Initialize API providers if not provided. No-op in local-only mode."""
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

        # Captured before local-only mode rewrites them below: a tier that
        # loses to the operator's kill switch is an infrastructure problem
        # worth a WARNING, while one the *caller* opted out of via an
        # explicit model / force_local is ordinary and must stay quiet.
        caller_model = model
        caller_forced_local = force_local

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
        tier_pinned = False
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
                    tier_pinned = True
                    logger.info(
                        f"Paid tier '{paid_tier}' active: routing to "
                        f"{tier_provider_name}:{tier_model}"
                    )

        # The tier was asked for and did not engage, so this call is about to
        # run on local Ollama. Say so out loud — a capability that silently
        # no-ops is indistinguishable from one that was never deployed.
        if paid_tier and not tier_pinned:
            self._warn_tier_degraded(
                paid_tier,
                caller_model=caller_model,
                caller_forced_local=caller_forced_local,
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
            logger.error(f"Error with {selected_model}: {e}")

            # A pinned paid tier must NOT silently become a local call.
            # Degrading a debate turn to gemma3:4b mid-round is worse than
            # losing the turn (and the same holds for the second-pass
            # promotion reviewer, the other tier): the
            # round would mix two models' output quality invisibly, and it
            # would push load onto the very Ollama path whose congestion the
            # tier exists to escape (2026-08-05: three debates died there).
            # Retry the same API briefly, then raise and let the scheduler's
            # next cron tick be the retry.
            if tier_pinned:
                for attempt in range(1, self._paid_tier_retries + 1):
                    delay = self._paid_tier_backoff * attempt
                    logger.warning(
                        f"Paid tier '{paid_tier}' call failed ({e}); retry "
                        f"{attempt}/{self._paid_tier_retries} in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    try:
                        response = await self._call_openai(
                            model=selected_model,
                            prompt=prompt,
                            system=system,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        provider_name = "openai"
                        break
                    except Exception as retry_error:  # noqa: PERF203
                        e = retry_error
                else:
                    logger.error(
                        f"Paid tier '{paid_tier}' exhausted its retries; failing the "
                        f"call instead of degrading to local"
                    )
                    raise
            else:
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
