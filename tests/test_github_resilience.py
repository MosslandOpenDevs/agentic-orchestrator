"""GitHub item isolation and partial-result reporting regressions."""

import logging

import pytest

from agentic_orchestrator.adapters.base import AdapterResult, SignalData
from agentic_orchestrator.adapters.github_events import GitHubEventsAdapter
from agentic_orchestrator.signals.aggregator import SignalAggregator


class _Response:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _Client:
    payload = None
    init_kwargs = []

    def __init__(self, *args, **kwargs):
        self.__class__.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kwargs):
        return _Response(self.__class__.payload)


def _repo(name, description="description"):
    return {
        "full_name": name,
        "stargazers_count": 100,
        "forks_count": 10,
        "html_url": f"https://github.com/{name}",
        "description": description,
        "language": "Python",
        "topics": [],
        "created_at": "2026-08-10T00:00:00Z",
        "updated_at": "2026-08-14T00:00:00Z",
    }


@pytest.fixture
def github_client(monkeypatch):
    _Client.init_kwargs = []
    monkeypatch.setattr("agentic_orchestrator.adapters.github_events.httpx.AsyncClient", _Client)
    return _Client


@pytest.mark.asyncio
async def test_null_description_does_not_truncate_trending_results(github_client):
    github_client.payload = {
        "items": [
            _repo("org/first"),
            _repo("org/no-description", None),
            _repo("org/last"),
        ]
    }

    signals = await GitHubEventsAdapter(github_token="token")._fetch_trending_repos()

    assert [signal.raw_data["repo"] for signal in signals] == [
        "org/first",
        "org/no-description",
        "org/last",
    ]
    assert signals[1].summary is None


@pytest.mark.asyncio
async def test_malformed_trending_item_does_not_drop_later_items(github_client):
    github_client.payload = {
        "items": [_repo("org/first"), {"description": "missing fields"}, _repo("org/last")]
    }
    errors = []

    signals = await GitHubEventsAdapter(github_token="token")._fetch_trending_repos(errors)

    assert [signal.raw_data["repo"] for signal in signals] == ["org/first", "org/last"]
    assert len(errors) == 1
    assert "trending item" in errors[0]


@pytest.mark.asyncio
async def test_null_description_is_safe_for_topic_results(github_client):
    github_client.payload = {"items": [_repo("org/topic", None), _repo("org/after")]}
    adapter = GitHubEventsAdapter(github_token="token")
    adapter.TRENDING_TOPICS = ["web3"]

    signals = await adapter._fetch_topic_repos()

    assert len(signals) == 2
    assert signals[0].summary is None


@pytest.mark.asyncio
async def test_release_requests_follow_repository_renames(github_client):
    github_client.payload = []
    adapter = GitHubEventsAdapter(github_token="token", watched_repos=["org/repo"])

    assert "ggerganov/llama.cpp" not in adapter.WATCHED_REPOS
    assert "wagmi-dev/wagmi" not in adapter.WATCHED_REPOS
    assert {"ggml-org/llama.cpp", "wevm/wagmi"} <= set(adapter.WATCHED_REPOS)

    assert await adapter._fetch_releases() == []
    assert github_client.init_kwargs[-1]["follow_redirects"] is True


@pytest.mark.asyncio
async def test_fetch_reports_partial_github_failure(monkeypatch):
    adapter = GitHubEventsAdapter(github_token="token")
    good = SignalData(source="github", category="dev", title="A valid GitHub signal")

    async def trending(errors=None):
        errors.append("trending item malformed")
        return [good]

    async def empty(errors=None):
        return []

    monkeypatch.setattr(adapter, "_fetch_trending_repos", trending)
    monkeypatch.setattr(adapter, "_fetch_releases", empty)
    monkeypatch.setattr(adapter, "_fetch_topic_repos", empty)

    result = await adapter.fetch()

    assert result.success is True
    assert result.signals == [good]
    assert result.metadata["partial"] is True
    assert result.metadata["failed_subsources"] == ["trending"]
    assert result.error == "trending item malformed"


class _PartialAdapter:
    name = "partial"

    def is_enabled(self):
        return True

    async def fetch_with_retry(self):
        signal = SignalData(source=self.name, category="dev", title="A partial source signal")
        return AdapterResult(
            adapter_name=self.name,
            success=True,
            signals=[signal],
            error="one subsource failed",
            metadata={"partial": True},
        )

    async def health_check(self):
        return {"name": self.name, "enabled": True}


class _NoopScorer:
    def score_batch(self, signals):
        return signals


@pytest.mark.asyncio
async def test_aggregator_preserves_signals_and_logs_partial_result(caplog):
    aggregator = SignalAggregator(adapters=[_PartialAdapter()], scorer=_NoopScorer())

    with caplog.at_level(logging.WARNING):
        signals = await aggregator.collect_all(save_to_db=False, deduplicate=False)

    assert len(signals) == 1
    assert "Adapter partial partially failed" in caplog.text
