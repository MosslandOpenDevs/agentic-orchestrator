"""A switched-off adapter must be off everywhere, and still be visible.

The twitter adapter reached every Nitter mirror it knows and stored zero rows
for the entire 30 days the signals table retains, while emitting roughly 1,440
"Error fetching" lines a day. It could not be stopped without editing code
because ``AdapterConfig.enabled`` defaulted to True and no adapter ever passed
anything else.

Two properties have to hold together, and they are easy to get half-right:

1. **Off means off before the network.** The aggregator has to skip it, not
   call it and discard the result.
2. **Off is reported as off.** ``GET /adapters`` builds its own instances from
   its own hardcoded list, separately from ``_default_adapters()``, so a
   disable that lived in the aggregator would have left the endpoint saying
   ``enabled: true`` about an adapter that never runs. That is why the switch
   is the class's own default config -- ``BaseAdapter.is_enabled()`` is the one
   place either side can read.

A third property is negative: the adapter stays *registered*. Deleting it would
make the system silent about a source it used to have, and ``/adapters`` is
where an operator goes to find out what happened to it.
"""

import pytest

from agentic_orchestrator.adapters import SocialMediaAdapter, TwitterAdapter
from agentic_orchestrator.adapters.base import AdapterConfig
from agentic_orchestrator.signals.aggregator import SignalAggregator

pytest_plugins = ["tests.test_api"]


class TestTheDeadAdapterIsOff:
    def test_twitter_is_disabled_by_default(self):
        assert TwitterAdapter().is_enabled() is False

    def test_it_is_still_registered(self):
        """The fleet is still twelve; one of them says no."""
        adapters = SignalAggregator()._default_adapters()
        names = [a.name for a in adapters]

        assert "twitter" in names
        assert len(names) == 12
        assert [a.name for a in adapters if not a.is_enabled()] == ["twitter"]

    @pytest.mark.asyncio
    async def test_the_aggregator_never_calls_it(self, monkeypatch):
        """Skipped before the network, not called and discarded.

        Every other adapter is stubbed to return nothing so the test makes no
        outbound requests; twitter's fetch is stubbed to fail loudly, so if the
        skip regresses this test errors rather than quietly passing.
        """
        from agentic_orchestrator.adapters.base import AdapterResult

        called = []

        async def _explode(self):
            called.append(self.name)
            raise AssertionError(f"{self.name} was fetched while disabled")

        async def _empty(self):
            return AdapterResult(adapter_name=self.name, success=True, signals=[])

        aggregator = SignalAggregator()
        for adapter in aggregator.adapters:
            target = _explode if adapter.name == "twitter" else _empty
            monkeypatch.setattr(type(adapter), "fetch_with_retry", target, raising=False)

        await aggregator.collect_all(save_to_db=False)
        assert called == []

    def test_an_explicit_config_still_wins(self):
        """The default is a default, not a lock -- re-enabling is one deletion."""
        assert TwitterAdapter(AdapterConfig(timeout=60)).is_enabled() is True


class TestTheEndpointAndTheLoopAgree:
    """The anti-lie property: one switch, one answer, two code paths."""

    def test_adapters_reports_twitter_disabled(self, client, stub_adapter_health):
        body = client.get("/adapters").json()
        by_name = {a["name"]: a for a in body["adapters"]}

        assert by_name["twitter"]["enabled"] is False
        assert body["enabled_count"] == body["total"] - 1

    def test_every_other_adapter_is_still_enabled(self, client, stub_adapter_health):
        """A blunt guard against a future edit switching something off quietly."""
        body = client.get("/adapters").json()
        disabled = sorted(a["name"] for a in body["adapters"] if not a["enabled"])

        assert disabled == ["twitter"]

    @pytest.mark.asyncio
    async def test_the_health_dict_carries_the_same_answer(self):
        """The modal renders health key by key, so it must not disagree."""
        health = await TwitterAdapter().health_check()
        assert health["enabled"] is False


class TestTheSignalMapSwitchIsWholeNow:
    """``signalmap.enabled: false`` stopped the fetch but not the report.

    The guard lived inside ``fetch()``, so a disabled feed was still dispatched
    every cycle to return an empty result, and ``is_enabled()`` -- which is what
    ``/adapters`` publishes -- still said True. Currently latent: the shipped
    config has it on.
    """

    def test_config_disabled_means_adapter_disabled(self):
        import dataclasses

        from agentic_orchestrator.adapters.signalmap import SignalMapAdapter, SignalMapConfig

        off = dataclasses.replace(SignalMapConfig.load(), enabled=False)
        assert SignalMapAdapter(signalmap_config=off).is_enabled() is False

    def test_the_shipped_config_is_on(self):
        from agentic_orchestrator.adapters.signalmap import SignalMapAdapter

        assert SignalMapAdapter().is_enabled() is True


class TestTheSecondNitterPathIsGone:
    """Disabling twitter removes only half the noise if this one survives.

    ``SocialMediaAdapter`` carried its own copy of the same three dead mirrors,
    five accounts deep, on every cycle. It could not be switched off with the
    adapter -- that would have taken Reddit down too -- so the path is deleted.
    """

    def test_no_nitter_state_remains_on_the_adapter(self):
        for attribute in ("NITTER_INSTANCES", "TWITTER_ACCOUNTS", "_fetch_twitter_nitter"):
            assert not hasattr(SocialMediaAdapter, attribute), attribute

    def test_reddit_still_works_and_is_still_enabled(self):
        adapter = SocialMediaAdapter()
        assert adapter.is_enabled() is True
        assert len(adapter.SUBREDDITS) > 0

    def test_no_mention_of_nitter_survives_in_a_code_path(self):
        """Source invariant, in the style of tests/test_paid_provider_gating.py.

        The prose above the class deliberately explains what was removed and why,
        so this checks the code rather than the file: any `nitter` outside a
        comment or docstring line means the path grew back.
        """
        import ast
        import inspect

        from agentic_orchestrator.adapters import social

        source = inspect.getsource(social)
        tree = ast.parse(source)
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    docstrings.add(doc)

        offending = []
        for lineno, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if "nitter" not in stripped.lower():
                continue
            if stripped.startswith("#"):
                continue
            if any(stripped in doc for doc in docstrings):
                continue
            offending.append((lineno, stripped))

        assert offending == [], offending
