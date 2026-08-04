"""Small time helpers.

Kept dependency-free (stdlib only) so it is safe to import from anywhere,
including the low-level ``db.models`` module, without risking import cycles.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a *naive* datetime.

    Drop-in replacement for the deprecated ``datetime.utcnow()``. It preserves
    the original naive-UTC semantics on purpose: the SQLAlchemy ``DateTime``
    columns store naive datetimes, so returning an aware datetime here (e.g.
    ``datetime.now(timezone.utc)``) would raise "can't compare offset-naive and
    offset-aware datetimes" wherever stored values are compared.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
