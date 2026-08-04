"""
Rolling local backups for the SQLite database.

Production stores everything in a single SQLite file (``data/orchestrator.db``)
that is intentionally never tracked in git. Losing or emptying that file takes
down every DB-backed API endpoint at once (the 2026-07 ``/status`` 500
incident), so we keep rolling snapshots in ``data/backup/`` (gitignored).

Safety properties (each closes a reviewed failure mode):

- Snapshots are written to a ``.tmp`` name and renamed into place only after
  an integrity ``quick_check`` passes — an unclean death mid-copy or a
  corrupt source can never leave a garbage file that gates the backup
  interval or occupies a retention slot.
- Copies are incremental (``pages``/``sleep``) so writers are not starved
  while a large database is snapshotted; the production DB does not run WAL.
- Pruning is regression-aware: if the history tables (ideas / plans /
  debate_sessions) shrank drastically versus the newest existing snapshot,
  the new snapshot is still written but nothing is pruned — a wiped-and-
  auto-refilled database can never rotate out the last pre-incident backups.
- Missing / empty / dataless / corrupt databases are never snapshotted.
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
TMP_SUFFIX = ".tmp"

# Keep one week of daily snapshots by default.
DEFAULT_KEEP = 7
DEFAULT_MIN_INTERVAL_HOURS = 24.0

# A snapshot is only worth taking when at least one of these tables has rows.
_MEANINGFUL_TABLES = ("signals", "ideas", "plans", "debate_sessions")

# Regression guard: these tables hold history the pipeline cannot regenerate
# (signals are excluded — they refill automatically within 30 minutes, which
# would mask a wipe). If their combined row count collapses versus the newest
# existing snapshot, pruning is suspended.
_HISTORY_TABLES = ("ideas", "plans", "debate_sessions")
REGRESSION_MIN_BASELINE = 20
REGRESSION_RATIO = 0.5

# Incremental-copy tuning: copy N pages per step, sleeping between steps so
# concurrent writers can grab the lock (production journal mode is not WAL).
_COPY_PAGES_PER_STEP = 1024
_COPY_SLEEP_SECONDS = 0.1
_BUSY_TIMEOUT_MS = 30_000


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


def _history_count(path: Path) -> Optional[int]:
    """Combined row count of the non-regenerating history tables.

    Returns None when the file cannot be read as a database (garbage or
    partial snapshots must not poison the regression comparison).
    """
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    except (sqlite3.Error, OSError, ValueError):
        return None
    try:
        total = 0
        for table in _HISTORY_TABLES:
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
            except sqlite3.Error:
                continue
            total += row[0] if row else 0
        return total
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def _quick_check_ok(path: Path) -> bool:
    """PRAGMA quick_check on a snapshot; any failure means 'discard it'."""
    try:
        conn = sqlite3.connect(str(path))
        try:
            row = conn.execute("PRAGMA quick_check").fetchone()
            return bool(row) and row[0] == "ok"
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def _copy_database(src_conn: sqlite3.Connection, dest_conn: sqlite3.Connection) -> None:
    """Incremental online backup: release the source lock between steps."""
    src_conn.backup(dest_conn, pages=_COPY_PAGES_PER_STEP, sleep=_COPY_SLEEP_SECONDS)


def _history_regressed(new_snapshot: Path, previous_newest: Optional[Path]) -> bool:
    """True when history rows collapsed versus the newest existing snapshot."""
    if previous_newest is None:
        return False
    prev_count = _history_count(previous_newest)
    if prev_count is None or prev_count < REGRESSION_MIN_BASELINE:
        return False
    new_count = _history_count(new_snapshot)
    if new_count is None:
        return False
    return new_count < prev_count * REGRESSION_RATIO


def list_backups(backup_dir: Path) -> List[Path]:
    """Finalized snapshots, oldest first (names embed a UTC timestamp).

    In-flight ``.tmp`` files never match, so partial copies cannot gate the
    backup interval or occupy retention slots.
    """
    if not backup_dir.is_dir():
        return []
    return sorted(backup_dir.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"))


def _cleanup_stale_tmp(backup_dir: Path) -> None:
    """Remove leftovers from previous crashed copy attempts."""
    for leftover in backup_dir.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}{TMP_SUFFIX}"):
        try:
            leftover.unlink()
            logger.info("Removed stale partial snapshot %s", leftover)
        except OSError as e:
            logger.warning("Could not remove stale partial snapshot %s: %s", leftover, e)


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
    up (non-SQLite backend, missing/empty/dataless file) or the snapshot
    failed its integrity check. Raises on an actual copy failure so callers
    can surface it; no partial snapshot is ever left behind.
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
        src_conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
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
        _cleanup_stale_tmp(backup_dir)
        previous = list_backups(backup_dir)

        dest = backup_dir / f"{BACKUP_PREFIX}{utcnow().strftime('%Y%m%d-%H%M%S')}{BACKUP_SUFFIX}"
        tmp = dest.with_name(dest.name + TMP_SUFFIX)

        dest_conn = sqlite3.connect(str(tmp))
        try:
            _copy_database(src_conn, dest_conn)
        except BaseException:
            dest_conn.close()
            tmp.unlink(missing_ok=True)
            raise
        dest_conn.close()
    finally:
        src_conn.close()

    if not _quick_check_ok(tmp):
        tmp.unlink(missing_ok=True)
        logger.error(
            "Snapshot of %s failed PRAGMA quick_check (source likely corrupt); "
            "discarded it and kept the existing backups",
            src,
        )
        return None

    tmp.rename(dest)  # atomic finalize: only verified snapshots become visible
    logger.info("Database backed up to %s", dest)

    if _history_regressed(dest, previous[-1] if previous else None):
        logger.error(
            "History tables (%s) collapsed versus newest snapshot %s — data-loss "
            "suspected; SKIPPING prune so pre-incident backups are retained until "
            "an operator investigates",
            "/".join(_HISTORY_TABLES),
            previous[-1].name,
        )
        return dest

    _prune_backups(backup_dir, keep)
    return dest


def maybe_backup_database(
    url: Optional[str] = None,
    keep: int = DEFAULT_KEEP,
    min_interval_hours: float = DEFAULT_MIN_INTERVAL_HOURS,
) -> Optional[Path]:
    """Take a snapshot only when the newest one is older than the interval.

    Designed to piggyback on a frequent scheduler task (the 5-minute health
    check) while still producing roughly daily backups. Because the interval
    is gated on the newest *finalized* snapshot, a failed attempt is retried
    on the next tick instead of silently skipping a day.
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
