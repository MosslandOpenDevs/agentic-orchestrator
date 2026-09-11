"""
Trend analysis.

``TrendAnalyzer`` extracts trends from a batch of ``FeedItem``s with the LLM
router; the scheduled trend task builds that batch from recently collected
signals.
"""

from .analyzer import TrendAnalyzer
from .models import FeedItem, Trend, TrendAnalysis

__all__ = [
    "FeedItem",
    "Trend",
    "TrendAnalysis",
    "TrendAnalyzer",
]
