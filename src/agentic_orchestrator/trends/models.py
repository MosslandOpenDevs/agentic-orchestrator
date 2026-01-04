"""
Data models for trend analysis.

Defines dataclasses for feed items, trends, and analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FeedItem:
    """
    Single RSS/Atom feed item.

    Represents a news article or blog post from an RSS feed.
    """

    title: str
    link: str
    published: datetime
    summary: str
    source: str  # Feed source name (e.g., "OpenAI News")
    category: str  # Category (ai, crypto, finance, dev, security)

    def __post_init__(self):
        """Validate and clean data after initialization."""
        self.title = self.title.strip()
        self.summary = self.summary.strip() if self.summary else ""

    @property
    def age_hours(self) -> float:
        """Get the age of this item in hours."""
        delta = datetime.utcnow() - self.published
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
    time_period: str  # Analysis period: 24h, 1w, 1m
    sources: list[str]  # Which feeds mentioned this trend
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
    period: str  # Time period analyzed: 24h, 1w, 1m
    trends: list[Trend]  # Identified trends, sorted by score
    raw_article_count: int  # Total articles analyzed
    sources_analyzed: list[str]  # List of feed sources used
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


@dataclass
class TrendIdeaLink:
    """
    Links a generated idea to its source trend.

    Maintains traceability between trends and the ideas they inspired.
    """

    idea_issue_number: int  # GitHub Issue number of the generated idea
    trend_topic: str  # Topic of the trend that inspired this idea
    trend_category: str  # Category of the source trend
    analysis_date: datetime  # When the trend was analyzed
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "idea_issue_number": self.idea_issue_number,
            "trend_topic": self.trend_topic,
            "trend_category": self.trend_category,
            "analysis_date": self.analysis_date.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrendIdeaLink":
        """Create from dictionary."""
        return cls(
            idea_issue_number=data["idea_issue_number"],
            trend_topic=data["trend_topic"],
            trend_category=data["trend_category"],
            analysis_date=datetime.fromisoformat(data["analysis_date"]),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.utcnow().isoformat())
            ),
        )


@dataclass
class FeedConfig:
    """
    Configuration for a single RSS feed.

    Loaded from config.yaml trends.feeds section.
    """

    name: str
    url: str
    category: str
    weight: float = 1.0  # Optional weight for trend scoring

    @classmethod
    def from_dict(cls, data: dict, category: str) -> "FeedConfig":
        """Create from config dictionary."""
        return cls(
            name=data["name"],
            url=data["url"],
            category=category,
            weight=data.get("weight", 1.0),
        )
