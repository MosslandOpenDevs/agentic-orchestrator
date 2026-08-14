"""
Base adapter class for signal collection.
"""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..timeutil import utcnow


def recurring_key(*parts: str) -> str:
    """Synthesized identity for a recurring status-report signal.

    Sources like GitHub trending or Coingecko movers have no publisher record
    id, and their titles embed values that move every poll (star counts,
    percentages, prices). Hashing such a title makes every 30-minute tick a
    "new" signal, so the cross-run dedup in ``_save_to_db`` never matches and
    the same subject lands dozens of times a day (measured 2026-08-14:
    coingecko 88%, onchain 95%, github 24% of a week's rows were repeats).

    The event these signals actually report is "subject X was in state S
    *today*" — so that is the identity: the caller's parts plus a UTC day
    bucket. One row per subject per state per day; the volatile numbers stay
    in the title and raw_data where they are information, not identity.

    Do NOT use this for one-time events (a release, a funding round, a
    transaction) — those already have stable natural keys without a date.
    """
    day = utcnow().strftime("%Y-%m-%d")
    return ":".join([*parts, day])


@dataclass
class AdapterConfig:
    """Configuration for adapters."""

    enabled: bool = True
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    rate_limit: Optional[float] = None  # requests per second
    batch_size: int = 50


@dataclass
class SignalData:
    """Raw signal data from adapters."""

    source: str
    category: str
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    collected_at: datetime = field(default_factory=utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Upstream's own stable identifier, when the source publishes one.
    #
    # The content hash below is the right identity for a feed that only ever
    # appends: RSS has no record id, so "same title + same link" is the best
    # available answer. It is the WRONG identity for a source that revises
    # records in place — SignalMap republishes a record with the same id and a
    # bumped `revision` when a canonical topic/entity is later attached, and an
    # upstream title edit would then land as a second, unrelated-looking row.
    # When this is set, identity follows the publisher instead of the bytes.
    external_id: Optional[str] = None

    @property
    def id(self) -> str:
        """Stable unique ID: publisher's id when known, else a content hash."""
        if self.external_id:
            return hashlib.sha256(f"{self.source}:{self.external_id}".encode()).hexdigest()[:16]
        content = f"{self.source}:{self.title}:{self.url or ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "raw_data": self.raw_data,
            "collected_at": self.collected_at.isoformat(),
            "metadata": self.metadata,
            "external_id": self.external_id,
        }


@dataclass
class AdapterResult:
    """Result from adapter fetch operation."""

    adapter_name: str
    success: bool
    signals: List[SignalData] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.signals)


class BaseAdapter(ABC):
    """
    Base class for all signal adapters.

    Subclasses must implement:
    - name: Adapter name
    - fetch(): Fetch signals from the source
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()
        self._last_fetch: Optional[datetime] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name."""
        pass

    @property
    def source_type(self) -> str:
        """Source type for signals."""
        return self.name.lower().replace(" ", "_")

    @abstractmethod
    async def fetch(self) -> AdapterResult:
        """
        Fetch signals from the source.

        Returns:
            AdapterResult with fetched signals
        """
        pass

    async def fetch_with_retry(self) -> AdapterResult:
        """Fetch with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                result = await asyncio.wait_for(self.fetch(), timeout=self.config.timeout)
                self._last_fetch = utcnow()
                return result

            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.timeout}s"
            except Exception as e:
                last_error = str(e)

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay)

        return AdapterResult(
            adapter_name=self.name,
            success=False,
            error=f"Failed after {self.config.max_retries} attempts: {last_error}",
        )

    def is_enabled(self) -> bool:
        """Check if adapter is enabled."""
        return self.config.enabled

    def get_last_fetch(self) -> Optional[datetime]:
        """Get last fetch time."""
        return self._last_fetch

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        return {
            "name": self.name,
            "enabled": self.config.enabled,
            "last_fetch": self._last_fetch.isoformat() if self._last_fetch else None,
        }
