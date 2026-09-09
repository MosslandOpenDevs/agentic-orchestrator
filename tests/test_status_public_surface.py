"""What ``/status`` may and may not publish.

``/status`` is listed in the links.moss.land registry as this service's status
endpoint, so it is read by anyone. Two properties have to hold together:

1. It must answer "is this pipeline actually running?" — the Q2 report's whole
   objection to cumulative counters was that they stay put when ingestion dies.
   That is what ``stats.last_signal_at`` is for.
2. It must not publish deployment detail that has nothing to do with that
   question — specifically which vendor and which exact model each paid tier
   buys. ``/usage`` keeps the full view; the public endpoint does not.

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
        view = _public_router_view(_report(active=False, reason="kill switch"))
        assert view["status"] == "healthy"
        assert view["local_only"] is False
        assert view["degraded_tiers"] == []
        debate = view["paid_tiers"]["debate"]
        # "could a paid tier bill anything at all, or are we silently all-local?"
        assert debate["enabled"] is True
        assert debate["active"] is False
        assert debate["reason"] == "kill switch"
        assert debate["name"] == "debate"

    def test_degraded_state_passes_through(self):
        report = _report(active=False)
        report["status"] = "degraded"
        report["degraded_tiers"] = ["debate"]
        view = _public_router_view(report)
        assert view["status"] == "degraded"
        assert view["degraded_tiers"] == ["debate"]

    def test_input_is_not_mutated(self):
        """The same report object also feeds /usage, which wants the full view."""
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
