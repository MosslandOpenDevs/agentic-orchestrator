"""Regression coverage for RSS transport and partial-failure reporting."""

from pathlib import Path

import feedparser
import pytest
import yaml

from agentic_orchestrator.adapters.rss import FeedConfig, RSSAdapter

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example</title>
    <item>
      <title>Markets move after policy update</title>
      <link>https://example.com/story</link>
      <description><![CDATA[<p>Useful summary.</p>]]></description>
    </item>
  </channel>
</rss>
"""


class _Response:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class _RSSClient:
    routes = {}
    headers = []

    def __init__(self, *args, **kwargs):
        self.__class__.headers.append(kwargs.get("headers"))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kwargs):
        result = self.__class__.routes[url]
        if isinstance(result, Exception):
            raise result
        return _Response(result)


@pytest.fixture
def rss_client(monkeypatch):
    _RSSClient.routes = {}
    _RSSClient.headers = []
    monkeypatch.setattr("agentic_orchestrator.adapters.rss.httpx.AsyncClient", _RSSClient)
    return _RSSClient


@pytest.mark.asyncio
async def test_rss_requests_identify_the_application(rss_client):
    feed = FeedConfig("https://example.com/feed.xml", "finance", "Example")
    rss_client.routes[feed.url] = RSS_XML

    signals = await RSSAdapter(feeds=[feed])._fetch_feed(feed)

    assert len(signals) == 1
    assert signals[0].summary == "Useful summary."
    assert rss_client.headers == [RSSAdapter.REQUEST_HEADERS]
    assert rss_client.headers[0]["User-Agent"].startswith("Agentic-Orchestrator/")


@pytest.mark.asyncio
async def test_failed_feed_is_reported_without_discarding_good_feed(rss_client):
    good = FeedConfig("https://example.com/good.xml", "finance", "Good")
    blocked = FeedConfig("https://example.com/blocked.xml", "finance", "Blocked")
    rss_client.routes = {
        good.url: RSS_XML,
        blocked.url: RuntimeError("HTTP 403"),
    }

    result = await RSSAdapter(feeds=[good, blocked]).fetch()

    assert result.success is True
    assert len(result.signals) == 1
    assert result.metadata["partial"] is True
    assert result.metadata["errors_count"] == 1
    assert result.metadata["failed_feeds"] == ["Blocked"]
    assert "Blocked" in result.error
    assert "HTTP 403" in result.error


@pytest.mark.asyncio
async def test_malformed_entry_does_not_discard_other_feed_items(rss_client, monkeypatch):
    feed = FeedConfig("https://example.com/feed.xml", "finance", "Example")
    rss_client.routes[feed.url] = RSS_XML
    entries = [
        feedparser.FeedParserDict(
            title="First valid market story",
            link="https://example.com/first",
            summary="first",
        ),
        feedparser.FeedParserDict(
            title="Malformed story",
            link="https://example.com/bad",
            summary=123,
        ),
        feedparser.FeedParserDict(
            title="Last valid market story",
            link="https://example.com/last",
            summary="last",
        ),
    ]
    monkeypatch.setattr(
        "agentic_orchestrator.adapters.rss.feedparser.parse",
        lambda _: feedparser.FeedParserDict(entries=entries),
    )

    result = await RSSAdapter(feeds=[feed]).fetch()

    assert [signal.title for signal in result.signals] == [
        "First valid market story",
        "Last valid market story",
    ]
    assert result.success is True
    assert result.metadata["partial"] is True
    assert result.metadata["failed_feeds"] == ["Example"]
    assert "Example entry 1" in result.error


def test_shipped_cnbc_feeds_use_official_endpoints():
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with config_path.open() as config_file:
        config = yaml.safe_load(config_file)

    finance_feeds = {entry["name"]: entry["url"] for entry in config["feeds"]["finance"]}
    assert finance_feeds["CNBC Business News"] == (
        "https://search.cnbc.com/rs/search/combinedcms/view.xml" "?partnerId=wrss01&id=10001147"
    )
    assert finance_feeds["CNBC Finance"] == (
        "https://search.cnbc.com/rs/search/combinedcms/view.xml" "?partnerId=wrss01&id=10000664"
    )
