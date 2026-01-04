"""
Trend analysis module for RSS feed-based idea generation.

This module provides functionality to:
- Fetch and parse RSS/Atom feeds from various news sources
- Analyze trends across different time periods (24h, 1 week, 1 month)
- Generate Web3 micro-service ideas based on trending topics
- Store trend analysis history for reference
"""

from .analyzer import TrendAnalyzer
from .feeds import FeedFetcher
from .models import FeedItem, Trend, TrendAnalysis, TrendIdeaLink
from .storage import TrendStorage

__all__ = [
    "FeedItem",
    "Trend",
    "TrendAnalysis",
    "TrendIdeaLink",
    "FeedFetcher",
    "TrendAnalyzer",
    "TrendStorage",
]
