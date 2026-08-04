"""
Signal adapters for Agentic Orchestrator.

Provides adapters for collecting signals from various sources:
- RSS feeds
- GitHub events
- OnChain data (Ethereum, MOC, DEX volume, Whale alerts)
- Social media (Twitter/X, Reddit, Discord)
- Web3 social (Lens Protocol, Farcaster)
- News APIs
"""

from .base import AdapterConfig, AdapterResult, BaseAdapter, SignalData
from .coingecko import CoingeckoAdapter
from .discord import DiscordAdapter
from .farcaster import FarcasterAdapter
from .github_events import GitHubEventsAdapter
from .lens import LensAdapter
from .news import NewsAPIAdapter
from .onchain import OnChainAdapter
from .rss import RSSAdapter
from .social import SocialMediaAdapter
from .threads import ThreadsAdapter
from .twitter import TwitterAdapter

__all__ = [
    # Base
    "BaseAdapter",
    "AdapterConfig",
    "AdapterResult",
    "SignalData",
    # Core Adapters
    "RSSAdapter",
    "GitHubEventsAdapter",
    "OnChainAdapter",
    "SocialMediaAdapter",
    "NewsAPIAdapter",
    # New Adapters (v0.5.0)
    "TwitterAdapter",
    "DiscordAdapter",
    "LensAdapter",
    "FarcasterAdapter",
    "CoingeckoAdapter",
    # New Adapters (v0.6.6)
    "ThreadsAdapter",
]
