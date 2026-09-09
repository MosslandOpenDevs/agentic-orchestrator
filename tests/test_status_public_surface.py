"""What the unauthenticated endpoints may and may not publish.

``/status`` is listed in the links.moss.land registry as this service's status
endpoint and ``/usage`` is called by the public web client; neither takes a
credential, so both are read by anyone. Two properties have to hold together:

1. It must answer "is this pipeline actually running?" — the Q2 report's whole
   objection to cumulative counters was that they stay put when ingestion dies.
   That is what ``stats.last_signal_at`` is for.
2. Neither may publish deployment detail that has nothing to do with that
   question — specifically which vendor and which exact model each paid tier
   buys. Both route the router report through ``_public_router_view``.

Both are easy to lose in a refactor and neither fails loudly, so they are
pinned here.
"""

from agentic_orchestrator.api.main import _public_router_view


def _report(**tier_overrides):
    tier = {
        "name": "debate",
        "enabled": True,
        "provider": "openai",
        "model": "gpt-5.4-mini",
        "active": True,
        "reason": None,
        "reason_code": None,
    }
    tier.update(tier_overrides)
    return {
        "status": "healthy",
        "local_only": False,
        "degraded_tiers": [],
        "paid_tiers": {"debate": tier},
    }


class TestPublicRouterView:
    def test_vendor_and_model_are_not_published(self):
        view = _public_router_view(_report())
        debate = view["paid_tiers"]["debate"]
        assert "provider" not in debate
        assert "model" not in debate

    def test_the_operational_answer_survives(self):
        """Redaction must not cost the signal the endpoint exists to give."""
        view = _public_router_view(
            _report(
                active=False,
                reason="tier 'debate' is disabled (llm.paid_tiers.debate.enabled)",
                reason_code="disabled",
            )
        )
        assert view["status"] == "healthy"
        assert view["local_only"] is False
        assert view["degraded_tiers"] == []
        debate = view["paid_tiers"]["debate"]
        # "could a paid tier bill anything at all, or are we silently all-local?"
        assert debate["enabled"] is True
        assert debate["active"] is False
        assert debate["name"] == "debate"
        # The verdict survives; the config path that produced it does not.
        assert debate["reason_code"] == "disabled"
        assert debate["reason"] == "tier is disabled"
        assert "llm.paid_tiers" not in debate["reason"]

    def test_degraded_state_passes_through(self):
        report = _report(active=False)
        report["status"] = "degraded"
        report["degraded_tiers"] = ["debate"]
        view = _public_router_view(report)
        assert view["status"] == "degraded"
        assert view["degraded_tiers"] == ["debate"]

    def test_input_is_not_mutated(self):
        """Redaction must not corrupt the caller's own copy of the report."""
        report = _report()
        _public_router_view(report)
        assert report["paid_tiers"]["debate"]["model"] == "gpt-5.4-mini"
        assert report["paid_tiers"]["debate"]["provider"] == "openai"

    def test_degenerate_reports_pass_through_untouched(self):
        """A router that failed to report must not turn into a crash here."""
        assert _public_router_view({"status": "unknown"}) == {"status": "unknown"}
        assert _public_router_view({"paid_tiers": None}) == {"paid_tiers": None}

    def test_non_dict_tier_is_left_alone(self):
        report = {"status": "healthy", "paid_tiers": {"debate": "unavailable"}}
        assert _public_router_view(report)["paid_tiers"]["debate"] == "unavailable"


class TestNoPublicRouteLeaksTheModelPin:
    """The two guarantees the redactor exists for, checked on real output.

    An earlier version of this class scanned source text for unredacted call
    sites and got the exclusion condition wrong -- it skipped every line
    containing ``paid_tier_report()``, which is every line it was supposed to
    inspect, so reverting /status to the leaking call still passed. Both
    checks below run against actual values instead.
    """

    def test_call_sites_are_wrapped(self):
        """Every paid_tier_report() call that feeds a response is wrapped.

        Parsed, not grepped: a docstring mentioning the function is not a call,
        and a call is not excused by the words around it.
        """
        import ast
        import inspect

        from agentic_orchestrator.api import main

        tree = ast.parse(inspect.getsource(main))
        wrapped, bare = set(), []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "_public_router_view":
                for arg in node.args:
                    if (
                        isinstance(arg, ast.Call)
                        and getattr(arg.func, "id", None) == "paid_tier_report"
                    ):
                        wrapped.add(arg.lineno)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "paid_tier_report"
                and node.lineno not in wrapped
            ):
                bare.append(node.lineno)
        assert bare == [], f"paid_tier_report() called unwrapped at line(s) {bare}"

    def test_no_deployment_detail_survives_in_the_payload(self, monkeypatch):
        """Seed a distinctive vendor and model, then look for them in the output.

        Key-level redaction alone is not enough: the private `reason` string
        interpolates the provider name and its API-key environment variable,
        so a tier that is merely missing its key used to put both back.
        """
        import json

        from agentic_orchestrator.api.main import _public_router_view
        from agentic_orchestrator.llm import router as router_mod

        monkeypatch.setattr(
            router_mod,
            "_cached_paid_tiers",
            lambda: {
                "debate": {
                    "enabled": True,
                    "provider": "acmevendor",
                    "model": "acme-supermodel-9",
                }
            },
        )
        monkeypatch.setattr(router_mod, "local_llm_only", lambda: False)
        # No API key for this provider -> the "provider unavailable" branch,
        # which is exactly the reason string that used to leak.
        monkeypatch.setitem(router_mod._PROVIDER_KEY_ENV, "acmevendor", "ACME_API_KEY")
        monkeypatch.delenv("ACME_API_KEY", raising=False)

        report = router_mod.paid_tier_report()
        private = json.dumps(report)
        assert (
            "acmevendor" in private and "acme-supermodel-9" in private
        ), "the fixture is not exercising the path it claims to"
        assert "ACME_API_KEY" in private, "expected the leaky reason branch"

        public = json.dumps(_public_router_view(report))
        for secret in ("acmevendor", "acme-supermodel-9", "ACME_API_KEY"):
            assert secret not in public, f"{secret} survived redaction: {public}"

        # The operational answer must still be there.
        tier = _public_router_view(report)["paid_tiers"]["debate"]
        assert tier["enabled"] is True
        assert tier["active"] is False
        assert tier["reason_code"] == "provider_unavailable"
        assert tier["reason"] == "provider credentials are unavailable"
