"""Restoring the SQLite database from a rolling snapshot.

Restoring used to be a documented four-step procedure a human performed by
hand, during an incident, from memory. One of those steps -- deleting the
``-wal``/``-shm`` sidecars before copying a snapshot over the database -- is
both easy to forget and silently destructive when forgotten: the database runs
in WAL mode, so SQLite replays the *old* database's write-ahead log on top of
the file you just restored. The result looks like a successful restore and is
not one.

Anything a runbook can get wrong under pressure belongs in a command, so this
module performs the whole sequence, refuses when it is unsafe, and leaves a
way back:

1. validate the snapshot before touching anything (integrity + has real rows)
2. refuse while another process holds a write lock, unless forced
3. copy the current database aside first, so the restore itself is reversible
4. build the replacement file, *then* remove the sidecars, then swap it in
5. verify the result and report what is in it
"""

import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..timeutil import utcnow
from .backup import (
    BACKUP_DIR_NAME,
    _has_meaningful_data,
    _quick_check_ok,
    _sqlite_path,
    list_backups,
)
from .connection import get_db

logger = logging.getLogger(__name__)

# Everything SQLite may leave beside the database file. All of it belongs to
# the database being replaced, so all of it has to go with it.
SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")

PRE_RESTORE_PREFIX = ".pre-restore-"
_RESTORE_TMP_SUFFIX = ".restore-tmp"

# Tables whose row counts are worth reporting back to the operator: they are
# what someone restoring after data loss actually wants to see.
REPORTED_TABLES = ("signals", "trends", "ideas", "plans", "debate_sessions", "projects")


class RestoreError(RuntimeError):
    """A restore was refused or failed. The message is operator-facing."""


@dataclass
class RestoreResult:
    restored_from: Path
    target: Path
    pre_restore_copy: Optional[Path]
    removed_sidecars: List[Path] = field(default_factory=list)
    row_counts: Dict[str, int] = field(default_factory=dict)


def _sidecars(target: Path) -> List[Path]:
    return [target.with_name(target.name + suffix) for suffix in SIDECAR_SUFFIXES]


def _row_counts(path: Path) -> Dict[str, int]:
    """Row counts for the reported tables; missing tables are simply absent."""
    counts: Dict[str, int] = {}
    try:
        conn = sqlite3.connect(str(path))
    except sqlite3.Error:
        return counts
    try:
        for table in REPORTED_TABLES:
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
            except sqlite3.Error:
                continue
            counts[table] = row[0] if row else 0
    finally:
        conn.close()
    return counts


def _writer_active(target: Path) -> bool:
    """True when another connection currently holds the write lock.

    A best-effort check, not a guarantee: it catches the scheduler mid-write
    (the realistic case -- signals every 30 min, a debate for ~30 min) but not
    a process that is merely idle with the database open. It is a guard against
    the common mistake, which is why ``--force`` exists.
    """
    if not target.exists():
        return False
    try:
        conn = sqlite3.connect(str(target), timeout=0)
    except sqlite3.Error:
        return False
    try:
        conn.execute("PRAGMA busy_timeout = 0")
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("ROLLBACK")
        return False
    except sqlite3.OperationalError:
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def list_snapshots(url: Optional[str] = None) -> List[Path]:
    """Available snapshots, newest first."""
    target = _sqlite_path(url or get_db().url)
    if target is None:
        return []
    return list(reversed(list_backups(target.parent / BACKUP_DIR_NAME)))


def describe_snapshots(url: Optional[str] = None) -> List[Dict[str, object]]:
    """Snapshots with the detail an operator needs to choose one."""
    described = []
    for path in list_snapshots(url):
        stat = path.stat()
        described.append(
            {
                "path": path,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "healthy": _quick_check_ok(path),
                "row_counts": _row_counts(path),
            }
        )
    return described


def _validate_snapshot(source: Path) -> None:
    if not source.is_file():
        raise RestoreError(f"Snapshot not found: {source}")
    if source.stat().st_size == 0:
        raise RestoreError(f"Snapshot is empty: {source}")
    if not _quick_check_ok(source):
        raise RestoreError(f"Snapshot failed PRAGMA quick_check and will not be restored: {source}")


def _snapshot_has_data(source: Path) -> bool:
    conn = sqlite3.connect(str(source))
    try:
        return _has_meaningful_data(conn)
    finally:
        conn.close()


def _unique_aside_path(target: Path) -> Path:
    """A pre-restore filename that cannot already exist.

    Second-resolution names collide when a restore is immediately reverted --
    and because the copy is written *before* the source is read, a collision
    with the file being restored FROM would overwrite it with the database
    being replaced. The restore would then silently "succeed" by restoring the
    state it was meant to undo.
    """
    stamp = utcnow().strftime("%Y%m%d-%H%M%S")
    candidate = target.with_name(target.name + PRE_RESTORE_PREFIX + stamp)
    suffix = 1
    while candidate.exists():
        candidate = target.with_name(f"{target.name}{PRE_RESTORE_PREFIX}{stamp}-{suffix}")
        suffix += 1
    return candidate


def _copy_aside(target: Path) -> Optional[Path]:
    """Snapshot the current database (WAL and all) before replacing it.

    Uses the online backup API rather than a file copy: the live database may
    have committed data sitting in ``-wal`` that a plain ``cp`` of the main
    file would not capture.
    """
    if not target.is_file() or target.stat().st_size == 0:
        return None

    aside = _unique_aside_path(target)
    try:
        src = sqlite3.connect(str(target))
        try:
            dest = sqlite3.connect(str(aside))
            try:
                src.backup(dest)
            finally:
                dest.close()
        finally:
            src.close()
    except sqlite3.Error as exc:
        aside.unlink(missing_ok=True)
        logger.warning("Could not copy the current database aside: %s", exc)
        return None
    return aside


def restore_database(
    source: Optional[Path] = None,
    url: Optional[str] = None,
    force: bool = False,
) -> RestoreResult:
    """Replace the live database with a snapshot.

    Args:
        source: snapshot to restore; defaults to the newest in ``data/backup/``.
        url: database URL; defaults to the configured one.
        force: proceed even when another process appears to be writing.

    Raises:
        RestoreError: with an operator-facing message, having changed nothing.
    """
    db_url = url or get_db().url
    target = _sqlite_path(db_url)
    if target is None:
        raise RestoreError(
            f"{db_url!r} is not a file-backed SQLite database; there is nothing to restore."
        )

    if source is None:
        snapshots = list_snapshots(db_url)
        if not snapshots:
            raise RestoreError(
                f"No snapshots found in {target.parent / BACKUP_DIR_NAME}. "
                "Nothing to restore from."
            )
        source = snapshots[0]
    source = Path(source)

    _validate_snapshot(source)
    if not _snapshot_has_data(source):
        raise RestoreError(
            f"Snapshot {source} has no rows in any core table. Restoring it would "
            "replace the database with an empty one; pick another snapshot."
        )

    if source.resolve() == target.resolve():
        raise RestoreError("Source and target are the same file.")

    if not force and _writer_active(target):
        raise RestoreError(
            "Another process is writing to the database. Stop the writers first:\n"
            "  pm2 stop moss-ao-api moss-ao-signals moss-ao-trends "
            "moss-ao-debate moss-ao-backlog moss-ao-health\n"
            "then re-run this command (or pass --force to override)."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    pre_restore = _copy_aside(target)

    # Build the replacement beside the target first, so a failure here leaves
    # the live database untouched.
    tmp = target.with_name(target.name + _RESTORE_TMP_SUFFIX)
    tmp.unlink(missing_ok=True)
    try:
        src_conn = sqlite3.connect(str(source))
        try:
            dest_conn = sqlite3.connect(str(tmp))
            try:
                src_conn.backup(dest_conn)
            finally:
                dest_conn.close()
        finally:
            src_conn.close()
    except (sqlite3.Error, OSError) as exc:
        tmp.unlink(missing_ok=True)
        raise RestoreError(f"Could not build the restored database: {exc}") from exc

    if not _quick_check_ok(tmp):
        tmp.unlink(missing_ok=True)
        raise RestoreError(
            "The rebuilt database failed its integrity check; the live database "
            "was left untouched."
        )

    # Sidecars belong to the database being replaced. Left in place, SQLite
    # replays the old WAL over the restored file -- the exact failure this
    # command exists to prevent (tests/test_restore.py demonstrates a naive
    # copy losing the restore entirely and still passing integrity_check).
    #
    # In practice the steps above have usually made SQLite clean these up
    # already, since reading the database checkpoints it. This sweep is the
    # guarantee rather than the mechanism: it must not depend on a side effect
    # of a probe that a later refactor could remove.
    removed = []
    for sidecar in _sidecars(target):
        if sidecar.exists():
            sidecar.unlink()
            removed.append(sidecar)

    os.replace(tmp, target)
    # A stale sidecar can also be created between the two steps above by a
    # reader; sweep once more now that the file is in place.
    for sidecar in _sidecars(target):
        if sidecar.exists():
            sidecar.unlink()
            if sidecar not in removed:
                removed.append(sidecar)

    counts = _row_counts(target)
    logger.info(
        "Restored %s from %s (%s)",
        target,
        source,
        ", ".join(f"{k}={v}" for k, v in counts.items()) or "no tables read",
    )
    return RestoreResult(
        restored_from=source,
        target=target,
        pre_restore_copy=pre_restore,
        removed_sidecars=removed,
        row_counts=counts,
    )


def revert_restore(pre_restore_copy: Path, url: Optional[str] = None) -> RestoreResult:
    """Put back the database that ``restore_database`` copied aside."""
    return restore_database(source=Path(pre_restore_copy), url=url, force=True)


__all__ = [
    "RestoreError",
    "RestoreResult",
    "describe_snapshots",
    "list_snapshots",
    "restore_database",
    "revert_restore",
]
