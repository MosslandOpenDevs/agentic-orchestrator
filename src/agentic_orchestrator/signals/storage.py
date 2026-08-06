"""
Signal storage utilities for persistence and retrieval.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..db.connection import db
from ..db.models import Signal
from ..db.repositories import SignalRepository
from ..timeutil import utcnow


class SignalStorage:
    """
    Signal storage manager.

    Provides:
    - Database operations wrapper
    - File-based backup
    - Cleanup and retention
    """

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path("data/signals")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # These read methods return plain dicts, not ORM rows.
    #
    # ``db.session()`` commits and closes on exit, and the session expires its
    # instances on commit, so a returned Signal was detached with no loaded
    # state: the caller got a DetachedInstanceError on the first attribute
    # access. Serialising inside the session is what makes the results usable
    # outside it -- and everything downstream (backup, export, the daily
    # summary) already wanted dicts.

    @staticmethod
    def _serialize(signal: Signal, include_raw: bool = False) -> Dict[str, Any]:
        """Signal.to_dict() deliberately omits raw_data (it is bulky provider
        payload). Callers that ask for it get it merged in here."""
        data = signal.to_dict()
        if include_raw:
            data["raw_data"] = signal.raw_data
        return data

    def get_recent(
        self,
        hours: int = 24,
        limit: int = 100,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_score: float = 0.0,
        include_raw: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get recent signals from database."""
        with db.session() as session:
            repo = SignalRepository(session)
            return [
                self._serialize(s, include_raw)
                for s in repo.get_recent(
                    hours=hours,
                    limit=limit,
                    source=source,
                    category=category,
                    min_score=min_score,
                )
            ]

    def get_by_source(self, source: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get signals by source."""
        with db.session() as session:
            repo = SignalRepository(session)
            return [s.to_dict() for s in repo.get_by_source(source, limit)]

    def get_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get signals by category."""
        with db.session() as session:
            repo = SignalRepository(session)
            return [s.to_dict() for s in repo.get_by_category(category, limit)]

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search signals."""
        with db.session() as session:
            repo = SignalRepository(session)
            return [s.to_dict() for s in repo.search(query, limit)]

    def get_stats(self) -> Dict[str, Any]:
        """Get signal statistics."""
        with db.session() as session:
            repo = SignalRepository(session)
            return {
                "by_source": repo.count_by_source(),
                "by_category": repo.count_by_category(),
            }

    def cleanup_old_signals(self, days: int = 90) -> int:
        """Delete signals older than specified days."""
        with db.session() as session:
            repo = SignalRepository(session)
            deleted = repo.delete_older_than(days)
            return deleted

    async def store_batch(self, signals_data: List[Dict[str, Any]]) -> int:
        """Store multiple signals in database.

        Args:
            signals_data: List of signal dictionaries

        Returns:
            Number of signals stored
        """
        stored = 0
        with db.session() as session:
            repo = SignalRepository(session)
            for data in signals_data:
                try:
                    # Ensure required fields
                    if not data.get("source") or not data.get("title"):
                        continue

                    repo.create(
                        {
                            "source": data.get("source", "unknown"),
                            "category": data.get("category", "other"),
                            "title": data.get("title", ""),
                            "summary": data.get("summary"),
                            "url": data.get("url"),
                            "score": data.get("score", 0.0),
                            "sentiment": data.get("sentiment"),
                            "topics": data.get("topics", []),
                            "entities": data.get("entities", []),
                            "raw_data": data.get("raw_data"),
                        }
                    )
                    stored += 1
                except Exception:
                    continue

        return stored

    def backup_signals(
        self,
        hours: int = 24,
        include_raw: bool = False,
    ) -> Path:
        """Backup recent signals to JSON file."""
        signals = self.get_recent(hours=hours, limit=10000, include_raw=include_raw)

        # Create backup filename
        timestamp = utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"signals_{timestamp}.json"

        # Convert to JSON-serializable format
        data = list(signals)

        with open(backup_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return backup_file

    def restore_from_backup(self, backup_file: Path) -> int:
        """Restore signals from backup file."""
        with open(backup_file, "r") as f:
            data = json.load(f)

        restored = 0
        with db.session() as session:
            repo = SignalRepository(session)

            for signal_data in data:
                # Check if already exists
                existing = session.query(Signal).filter(Signal.id == signal_data.get("id")).first()

                if not existing:
                    repo.create(signal_data)
                    restored += 1

        return restored

    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get summary of signals for a specific day."""
        if date is None:
            date = utcnow()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        with db.session() as session:
            # Query signals for the day
            signals = (
                session.query(Signal)
                .filter(Signal.collected_at >= start, Signal.collected_at < end)
                .all()
            )

            # Calculate statistics
            by_source = {}
            by_category = {}
            top_scored = []

            for signal in signals:
                # Count by source
                by_source[signal.source] = by_source.get(signal.source, 0) + 1
                # Count by category
                by_category[signal.category] = by_category.get(signal.category, 0) + 1
                # Track top scored
                if signal.score and signal.score > 0.5:
                    top_scored.append(signal.to_dict())

            # Sort top scored
            top_scored.sort(key=lambda x: x.get("score", 0), reverse=True)

            return {
                "date": start.strftime("%Y-%m-%d"),
                "total_signals": len(signals),
                "by_source": by_source,
                "by_category": by_category,
                "top_scored": top_scored[:10],
            }

    def export_for_analysis(
        self,
        hours: int = 168,  # 1 week
        format: str = "json",
    ) -> Path:
        """Export signals for external analysis."""
        signals = self.get_recent(hours=hours, limit=10000)

        timestamp = utcnow().strftime("%Y%m%d")
        export_file = self.backup_dir / f"export_{timestamp}.{format}"

        if format == "json":
            data = list(signals)
            with open(export_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

        elif format == "csv":
            import csv

            with open(export_file, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "id",
                        "source",
                        "category",
                        "title",
                        "url",
                        "score",
                        "collected_at",
                    ],
                )
                writer.writeheader()
                for signal in signals:
                    writer.writerow(
                        {
                            key: signal.get(key)
                            for key in (
                                "id",
                                "source",
                                "category",
                                "title",
                                "url",
                                "score",
                                "collected_at",
                            )
                        }
                    )

        return export_file
