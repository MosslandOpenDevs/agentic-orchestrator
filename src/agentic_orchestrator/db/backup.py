"""
Rolling local backups for the SQLite database.

Production stores everything in a single SQLite file (``data/orchestrator.db``)
that is intentionally never tracked in git. Losing or emptying that file takes
down every DB-backed API endpoint at once (the 2026-07 ``/status`` 500
incident), so we keep rolling snapshots in ``data/backup/`` (gitignored).

Snapshots use the sqlite3 online-backup API, which produces a consistent copy
even while other processes are writing (WAL-safe). Backups are deliberately
skipped when the database is missing, empty, or contains no meaningful rows —
a freshly self-healed (schema-only) database must never rotate out the last
good snapshots of real data.
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from ..timeutil import utcnow
from .connection import get_db

logger = logging.getLogger(__name__)

BACKUP_DIR_NAME = "backup"
BACKUP_PREFIX = "orchestrator-"
BACKUP_SUFFIX = ".db"

# Keep one week of daily snapshots by default.
DEFAULT_KEEP = 7
DEFAULT_MIN_INTERVAL_HOURS = 24.0

# A snapshot is only worth taking when at least one of these tables has rows.
_MEANINGFUL_TABLES = ("signals", "ideas", "plans", "debate_sessions")


def _sqlite_path(url: str) -> Optional[Path]:
    """Return the filesystem path behind a SQLite URL, or None otherwise.

    Non-SQLite backends (PostgreSQL) and in-memory databases have nothing to
    snapshot at the file level.
    """
    if not url.startswith("sqlite:///"):
        return None
    path = url.replace("sqlite:///", "", 1)
    if not path or path == ":memory:":
        return None
    return Path(path)


def _has_meaningful_data(conn: sqlite3.Connection) -> bool:
    """True when at least one core table contains rows.

    Missing tables count as empty — never raises for a schema-only or
    partially created database.
    """
    for table in _MEANINGFUL_TABLES:
        try:
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
        except sqlite3.Error:
            continue
        if row and row[0] > 0:
            return True
    return False


def list_backups(backup_dir: Path) -> List[Path]:
    """Existing snapshots, oldest first (names embed a UTC timestamp)."""
    if not backup_dir.is_dir():
        return []
    return sorted(backup_dir.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"))


def _prune_backups(backup_dir: Path, keep: int) -> None:
    """Delete the oldest snapshots beyond ``keep`` (0 disables pruning)."""
    if keep <= 0:
        return
    for stale in list_backups(backup_dir)[:-keep]:
        try:
            stale.unlink()
            logger.info("Pruned old database backup %s", stale)
        except OSError as e:
            logger.warning("Could not prune old database backup %s: %s", stale, e)


def backup_database(url: Optional[str] = None, keep: int = DEFAULT_KEEP) -> Optional[Path]:
    """Snapshot the SQLite database into ``<db-dir>/backup/``, pruning old copies.

    Returns the snapshot path, or ``None`` when there is nothing worth backing
    up (non-SQLite backend, missing/empty file, or no meaningful rows).
    Raises on an actual copy failure (e.g. corrupted source) so callers can
    surface it; no partial snapshot is left behind.
    """
    db_url = url or get_db().url
    src = _sqlite_path(db_url)
    if src is None:
        logger.info("Database %r is not a file-backed SQLite DB; skipping backup", db_url)
        return None
    if not src.is_file() or src.stat().st_size == 0:
        logger.warning("Database file %s is missing or empty; skipping backup", src)
        return None

    src_conn = sqlite3.connect(str(src))
    try:
        if not _has_meaningful_data(src_conn):
            logger.warning(
                "Database %s has no rows in %s; skipping backup so real snapshots "
                "are never rotated out by schema-only ones",
                src,
                "/".join(_MEANINGFUL_TABLES),
            )
            return None

        backup_dir = src.parent / BACKUP_DIR_NAME
        backup_dir.mkdir(parents=True, exist_ok=True)
        dest = backup_dir / f"{BACKUP_PREFIX}{utcnow().strftime('%Y%m%d-%H%M%S')}{BACKUP_SUFFIX}"

        dest_conn = sqlite3.connect(str(dest))
        try:
            src_conn.backup(dest_conn)
        except BaseException:
            dest_conn.close()
            dest.unlink(missing_ok=True)
            raise
        dest_conn.close()
    finally:
        src_conn.close()

    logger.info("Database backed up to %s", dest)
    _prune_backups(backup_dir, keep)
    return dest


def maybe_backup_database(
    url: Optional[str] = None,
    keep: int = DEFAULT_KEEP,
    min_interval_hours: float = DEFAULT_MIN_INTERVAL_HOURS,
) -> Optional[Path]:
    """Take a snapshot only when the newest one is older than the interval.

    Designed to piggyback on a frequent scheduler task (the 5-minute health
    check) while still producing roughly daily backups.
    """
    db_url = url or get_db().url
    src = _sqlite_path(db_url)
    if src is None:
        return None

    backups = list_backups(src.parent / BACKUP_DIR_NAME)
    if backups:
        newest_age_seconds = time.time() - backups[-1].stat().st_mtime
        if newest_age_seconds < min_interval_hours * 3600:
            return None

    return backup_database(url=db_url, keep=keep)
