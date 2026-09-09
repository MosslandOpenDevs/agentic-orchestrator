"""Small time helpers.

Kept dependency-free (stdlib only) so it is safe to import from anywhere,
including the low-level ``db.models`` module, without risking import cycles.
"""

from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Return the current UTC time as a *naive* datetime.

    Drop-in replacement for the deprecated ``datetime.utcnow()``. It preserves
    the original naive-UTC semantics on purpose: the SQLAlchemy ``DateTime``
    columns store naive datetimes, so returning an aware datetime here (e.g.
    ``datetime.now(timezone.utc)``) would raise "can't compare offset-naive and
    offset-aware datetimes" wherever stored values are compared.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_iso(value: Optional[datetime]) -> Optional[str]:
    """Serialise a timestamp with an explicit UTC marker.

    A naive ISO string is read as *local time* by browsers, which silently
    shifts the age by the viewer's offset -- in KST a nine-hour-old feed reads
    as current. ``None`` stays ``None``: when the answer is unknown, say so
    rather than inventing a "now".

    The counterpart to ``utcnow()`` and the reason it can stay naive: the naive
    value is what comparisons and the DateTime columns need, and this is what
    anything leaving the process as a string needs. Write ``utc_iso(utcnow())``
    rather than ``utcnow().isoformat()`` wherever the value goes out over HTTP.

    Lives here rather than beside its first caller in ``api.main``: the
    adapters publish stored timestamps on the same public endpoints, and a
    module below the API layer must not import it to get the rule right.
    """
    if value is None:
        return None
    return value.isoformat() + ("" if value.tzinfo else "Z")
