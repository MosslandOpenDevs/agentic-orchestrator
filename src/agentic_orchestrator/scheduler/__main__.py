"""
CLI entry point for scheduler tasks.

Usage:
    python -m agentic_orchestrator.scheduler signal-collect
    python -m agentic_orchestrator.scheduler analyze-trends
    python -m agentic_orchestrator.scheduler run-debate
    python -m agentic_orchestrator.scheduler process-backlog
    python -m agentic_orchestrator.scheduler health-check
    python -m agentic_orchestrator.scheduler backup-db
"""

import argparse
import sys

from ..db.connection import ensure_schema
from .tasks import analyze_trends, health_check, process_backlog, run_debate, signal_collect


def main():
    parser = argparse.ArgumentParser(
        description="Mossland Agentic Orchestrator Scheduler",
        prog="python -m agentic_orchestrator.scheduler",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # signal-collect command
    subparsers.add_parser(
        "signal-collect",
        help="Collect signals from all adapters",
    )

    # analyze-trends command
    subparsers.add_parser(
        "analyze-trends",
        help="Analyze trends from recent signals using local LLM",
    )

    # run-debate command
    debate_parser = subparsers.add_parser(
        "run-debate",
        help="Run multi-stage debate",
    )
    debate_parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Optional debate topic (auto-selected from signals if not provided)",
    )

    # process-backlog command
    subparsers.add_parser(
        "process-backlog",
        help="Process pending backlog items",
    )

    # health-check command
    subparsers.add_parser(
        "health-check",
        help="Check system health",
    )

    # backup-db command
    subparsers.add_parser(
        "backup-db",
        help="Snapshot the SQLite database into data/backup/ (manual/on-demand)",
    )

    # restore-db command
    restore_parser = subparsers.add_parser(
        "restore-db",
        help="Restore the SQLite database from a snapshot in data/backup/",
        description=(
            "Restores safely: validates the snapshot, refuses while another process "
            "is writing, copies the current database aside first, and removes the "
            "WAL sidecars that would otherwise be replayed over the restored file."
        ),
    )
    restore_parser.add_argument(
        "--list",
        action="store_true",
        help="list available snapshots and exit, without restoring anything",
    )
    restore_parser.add_argument(
        "--from",
        dest="source",
        metavar="SNAPSHOT",
        help="snapshot to restore (default: the newest one)",
    )
    restore_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="skip the confirmation prompt (required when not attached to a terminal)",
    )
    restore_parser.add_argument(
        "--force",
        action="store_true",
        help="restore even though another process appears to be writing",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # backup-db and restore-db must not touch the schema of the database they
    # are about to snapshot or replace. Every other command gets the schema
    # guarantee (idempotent create_tables with a boot-race retry; never raises).
    if args.command not in ("backup-db", "restore-db"):
        ensure_schema()

    if args.command == "signal-collect":
        signal_collect()
    elif args.command == "analyze-trends":
        analyze_trends()
    elif args.command == "run-debate":
        run_debate(topic=args.topic if hasattr(args, "topic") else None)
    elif args.command == "process-backlog":
        process_backlog()
    elif args.command == "health-check":
        health_check()
    elif args.command == "backup-db":
        # Exit codes are a contract with scripts/deploy.sh, which refuses to
        # deploy without a restore point:
        #   0 - snapshot written
        #   2 - nothing worth snapshotting (no/empty/dataless database)
        #   1 - the snapshot failed, including a corrupt source (an uncaught
        #       exception also exits 1)
        from ..db.backup import BackupIntegrityError, backup_database

        try:
            dest = backup_database()
        except BackupIntegrityError as exc:
            # The one state where a restore point matters most. Exiting 2 here
            # would have told deploy.sh "nothing to snapshot -- carry on".
            print(f"Backup failed: {exc}", file=sys.stderr)
            sys.exit(1)
        if dest is None:
            print("No backup created (database missing, empty, dataless, or not SQLite).")
            sys.exit(2)
        print(f"Backup written: {dest}")
    elif args.command == "restore-db":
        sys.exit(_restore_db(args))
    else:
        parser.print_help()
        sys.exit(1)


def _restore_db(args) -> int:
    """Exit codes mirror backup-db: 0 done, 2 nothing to do, 1 refused/failed."""
    from ..db.restore import RestoreError, describe_snapshots, restore_database

    if args.list:
        snapshots = describe_snapshots()
        if not snapshots:
            print("No snapshots found.")
            return 2
        print(f"{'SNAPSHOT':<44} {'MODIFIED':<26} {'SIZE':>10}  CONTENTS")
        for snap in snapshots:
            counts = snap["row_counts"]
            summary = ", ".join(f"{k}={v}" for k, v in counts.items()) or "unreadable"
            health = "" if snap["healthy"] else "  [FAILS INTEGRITY CHECK]"
            print(
                f"{snap['path'].name:<44} {snap['modified']:<26} "
                f"{snap['size_bytes'] / 1024:>9.0f}K  {summary}{health}"
            )
        return 0

    if not args.yes:
        if not sys.stdin.isatty():
            print(
                "restore-db replaces the live database. Re-run with --yes to confirm "
                "(no terminal attached, so there is nobody to prompt).",
                file=sys.stderr,
            )
            return 1
        target = args.source or "the newest snapshot"
        answer = input(f"Replace the live database with {target}? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted; nothing was changed.")
            return 1

    try:
        result = restore_database(source=args.source, force=args.force)
    except RestoreError as exc:
        print(f"Restore refused: {exc}", file=sys.stderr)
        return 1

    print(f"Restored {result.target} from {result.restored_from}")
    if result.removed_sidecars:
        print(f"  removed stale WAL sidecars: {', '.join(p.name for p in result.removed_sidecars)}")
    if result.pre_restore_copy:
        print(f"  previous database kept at: {result.pre_restore_copy}")
    counts = ", ".join(f"{k}={v}" for k, v in result.row_counts.items())
    print(f"  contents: {counts or 'no tables read'}")
    print("Restart the writers when ready:  pm2 restart all")
    return 0


if __name__ == "__main__":
    main()
