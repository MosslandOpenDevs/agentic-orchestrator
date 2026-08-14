"""
RSS Feed adapter for signal collection.

Collects signals from RSS feeds across multiple categories:
- AI/ML
- Crypto/Web3
- Finance
- Security
- Dev/Tech

The feed list is read from config.yaml's top-level `feeds` section, which is
the single source of truth shared with trend analysis (trends/feeds.py).
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import feedparser
import httpx

from ..timeutil import utcnow
from ..utils.config import load_config
from .base import AdapterConfig, AdapterResult, BaseAdapter, SignalData

logger = logging.getLogger(__name__)


@dataclass
class FeedConfig:
    """RSS feed configuration."""

    url: str
    category: str
    name: str
    enabled: bool = True


class RSSAdapter(BaseAdapter):
    """
    RSS Feed adapter.

    Fetches and parses RSS feeds from multiple sources.
    """

    # Emergency fallback only — used when config.yaml cannot be read (e.g. the
    # adapter is constructed from a working directory without one). The
    # canonical feed list lives in config.yaml's top-level `feeds` section; do
    # NOT grow this list, add feeds to config.yaml instead.
    FALLBACK_FEEDS: List[FeedConfig] = [
        FeedConfig("https://openai.com/news/rss.xml", "ai", "OpenAI News"),
        FeedConfig("https://news.ycombinator.com/rss", "ai", "Hacker News"),
        FeedConfig("https://www.coindesk.com/arc/outboundfeeds/rss/", "crypto", "CoinDesk"),
        FeedConfig("https://cointelegraph.com/rss", "crypto", "Cointelegraph"),
        FeedConfig("https://www.theverge.com/rss/index.xml", "dev", "The Verge"),
    ]

    # Some publishers (notably CNBC) reject httpx's library-default user agent.
    # A stable, honest application identity also makes our RSS traffic easier
    # for feed operators to distinguish from generic scraping.
    REQUEST_HEADERS = {
        "User-Agent": "Agentic-Orchestrator/1.0 (+https://ao.moss.land)",
        "Accept": (
            "application/rss+xml, application/atom+xml, application/xml;q=0.9, "
            "text/xml;q=0.8, */*;q=0.1"
        ),
    }

    @classmethod
    def load_configured_feeds(cls) -> List[FeedConfig]:
        """
        Load the canonical feed list from config.yaml's top-level `feeds`.

        Falls back to the legacy `trends.feeds` location, then to
        FALLBACK_FEEDS if neither is present. Disabled feeds are dropped here
        so they never reach the fetch loop. Config is re-read per construction,
        so an edited config.yaml takes effect on process restart.
        """
        try:
            config = load_config()
            feeds_config = config.get("feeds", default=None) or config.get(
                "trends", "feeds", default=None
            )
        except Exception as e:  # pragma: no cover - defensive, config is optional
            logger.warning(f"Could not read feed config, using fallback feeds: {e}")
            return list(cls.FALLBACK_FEEDS)

        if not feeds_config:
            logger.warning(
                f"No `feeds` section in config.yaml; using {len(cls.FALLBACK_FEEDS)} fallback feeds"
            )
            return list(cls.FALLBACK_FEEDS)

        # A hand-edited `feeds:` that is a flat list or a scalar would otherwise
        # raise AttributeError out of __init__ and take down SignalAggregator
        # construction — i.e. every adapter, not just this one.
        if not isinstance(feeds_config, dict):
            logger.warning(
                "`feeds` in config.yaml must be a mapping of category -> list of feeds, got "
                f"{type(feeds_config).__name__}; using {len(cls.FALLBACK_FEEDS)} fallback feeds"
            )
            return list(cls.FALLBACK_FEEDS)

        feeds: List[FeedConfig] = []
        disabled = 0
        for category, entries in feeds_config.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                try:
                    if not entry.get("enabled", True):
                        disabled += 1
                        continue
                    feeds.append(
                        FeedConfig(
                            url=entry["url"],
                            category=category,
                            name=entry.get("name", entry["url"]),
                        )
                    )
                except (AttributeError, KeyError, TypeError) as e:
                    logger.warning(f"Invalid feed config in category '{category}': {e}")

        if not feeds:
            logger.warning("Feed config contained no usable feeds; using fallback feeds")
            return list(cls.FALLBACK_FEEDS)

        logger.info(f"Loaded {len(feeds)} RSS feeds from config ({disabled} disabled)")
        return feeds

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        feeds: Optional[List[FeedConfig]] = None,
        custom_feeds: Optional[List[Dict[str, str]]] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        # list() so custom_feeds below can never mutate a caller's list or a
        # class-level default.
        self.feeds = list(feeds) if feeds else self.load_configured_feeds()

        # Add custom feeds if provided
        if custom_feeds:
            for feed in custom_feeds:
                self.feeds.append(
                    FeedConfig(
                        url=feed["url"],
                        category=feed.get("category", "other"),
                        name=feed.get("name", feed["url"]),
                        enabled=feed.get("enabled", True),
                    )
                )

    @property
    def name(self) -> str:
        return "rss"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from all RSS feeds."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch feeds concurrently. Keep the feed beside each task so failures
        # are attributable in AdapterResult instead of becoming anonymous
        # warnings in the helper.
        enabled_feeds = [feed for feed in self.feeds if feed.enabled]
        feed_errors: List[List[str]] = [[] for _ in enabled_feeds]
        tasks = [
            self._fetch_feed(feed, source_errors)
            for feed, source_errors in zip(enabled_feeds, feed_errors, strict=True)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        failed_feeds: List[str] = []
        for feed, source_errors, result in zip(enabled_feeds, feed_errors, results, strict=True):
            if isinstance(result, Exception):
                message = f"{feed.name}: {type(result).__name__}: {result}"
                errors.append(message)
            elif isinstance(result, list):
                signals.extend(result)
            errors.extend(source_errors)
            if isinstance(result, Exception) or source_errors:
                failed_feeds.append(feed.name)

        duration_ms = (time.time() - start_time) * 1000

        return AdapterResult(
            adapter_name=self.name,
            success=len(signals) > 0,
            signals=signals,
            error="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            metadata={
                "feeds_count": len(self.feeds),
                "enabled_feeds": len(enabled_feeds),
                "errors_count": len(errors),
                "failed_feeds": failed_feeds,
                "partial": bool(signals and errors),
            },
        )

    async def _fetch_feed(
        self,
        feed: FeedConfig,
        errors: Optional[List[str]] = None,
    ) -> List[SignalData]:
        """Fetch a single RSS feed."""
        signals: List[SignalData] = []

        # Let request and parsing failures reach fetch(), which can preserve
        # successful feeds while marking the adapter result as partial.
        async with httpx.AsyncClient(timeout=30, headers=self.REQUEST_HEADERS) as client:
            response = await client.get(feed.url, follow_redirects=True)
            response.raise_for_status()

            # Parse feed
            parsed = feedparser.parse(response.text)

            for index, entry in enumerate(parsed.entries[:20]):  # Limit to 20 per feed
                try:
                    # Extract published date
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])

                    # Extract summary
                    summary = None
                    if hasattr(entry, "summary"):
                        summary = self._clean_html(entry.summary)[:500]
                    elif hasattr(entry, "description"):
                        summary = self._clean_html(entry.description)[:500]

                    signal = SignalData(
                        source=self.name,
                        category=feed.category,
                        title=entry.get("title", "No title"),
                        summary=summary,
                        url=entry.get("link"),
                        raw_data={
                            "feed_name": feed.name,
                            "feed_url": feed.url,
                            "published": published.isoformat() if published else None,
                            "author": entry.get("author"),
                            "tags": (
                                [t.term for t in entry.get("tags", [])]
                                if hasattr(entry, "tags")
                                else []
                            ),
                        },
                        collected_at=utcnow(),
                        metadata={"feed_name": feed.name},
                    )
                    signals.append(signal)
                except Exception as e:
                    message = f"{feed.name} entry {index}: {type(e).__name__}: {e}"
                    if errors is None:
                        logger.warning(message)
                    else:
                        errors.append(message)

        return signals

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        import re

        clean = re.sub(r"<[^>]+>", "", html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def add_feed(self, url: str, category: str, name: str) -> None:
        """Add a new feed."""
        self.feeds.append(FeedConfig(url=url, category=category, name=name))

    def remove_feed(self, url: str) -> bool:
        """Remove a feed by URL."""
        for i, feed in enumerate(self.feeds):
            if feed.url == url:
                self.feeds.pop(i)
                return True
        return False

    def get_feeds_by_category(self, category: str) -> List[FeedConfig]:
        """Get feeds by category."""
        return [f for f in self.feeds if f.category == category]

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()
        base_health.update(
            {
                "feeds_count": len(self.feeds),
                "enabled_feeds": len([f for f in self.feeds if f.enabled]),
                "categories": list({f.category for f in self.feeds}),
            }
        )
        return base_health
