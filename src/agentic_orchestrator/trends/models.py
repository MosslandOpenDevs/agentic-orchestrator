"""
Data models for trend analysis.

Defines dataclasses for feed items, trends, and analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime

from ..timeutil import utcnow


@dataclass
class FeedItem:
    """
    One item for TrendAnalyzer; the scheduled trend task builds these from
    collected signals.
    """

    title: str
    link: str
    published: datetime
    summary: str
    source: str  # Signal source (adapter name)
    category: str  # Category (ai, crypto, finance, dev, security)

    def __post_init__(self):
        """Validate and clean data after initialization."""
        self.title = self.title.strip()
        self.summary = self.summary.strip() if self.summary else ""

    @property
    def age_hours(self) -> float:
        """Get the age of this item in hours."""
        delta = utcnow() - self.published
        return delta.total_seconds() / 3600


@dataclass
class Trend:
    """
    Identified trend from feed analysis.

    Represents a hot topic identified from analyzing multiple news articles.
    """

    topic: str  # Main topic/theme (3-5 words)
    keywords: list[str]  # Related keywords
    score: float  # Relevance/heat score (0-10)
    time_period: str  # Analysis period label, e.g. 24h
    sources: list[str]  # Signal sources the model cited for this trend
    article_count: int  # Number of articles about this trend
    sample_headlines: list[str]  # Sample headlines for context
    category: str  # Primary category (ai, crypto, etc.)
    summary: str  # Why this is trending
    web3_relevance: str = ""  # How it relates to Web3/blockchain
    idea_seeds: list[str] = field(default_factory=list)  # Potential project ideas

    def __post_init__(self):
        """Ensure lists are properly initialized."""
        if self.keywords is None:
            self.keywords = []
        if self.sources is None:
            self.sources = []
        if self.sample_headlines is None:
            self.sample_headlines = []
        if self.idea_seeds is None:
            self.idea_seeds = []


@dataclass
class TrendAnalysis:
    """
    Complete trend analysis for a time period.

    Contains all trends identified from a batch of feed items.
    """

    date: datetime  # When analysis was performed
    period: str  # Analysis period label, e.g. 24h
    trends: list[Trend]  # Identified trends, sorted by score
    raw_article_count: int  # Total articles analyzed
    sources_analyzed: list[str]  # Signal sources (adapter names) in the batch
    categories_analyzed: list[str] = field(default_factory=list)  # Categories covered

    def __post_init__(self):
        """Sort trends by score and ensure lists are initialized."""
        if self.trends:
            self.trends = sorted(self.trends, key=lambda t: t.score, reverse=True)
        if self.categories_analyzed is None:
            self.categories_analyzed = []

    @property
    def top_trends(self) -> list[Trend]:
        """Get top 5 trends by score."""
        return self.trends[:5] if self.trends else []

    def get_trends_by_category(self, category: str) -> list[Trend]:
        """Filter trends by category."""
        return [t for t in self.trends if t.category == category]
