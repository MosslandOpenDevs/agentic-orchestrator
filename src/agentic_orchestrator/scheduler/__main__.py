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
import logging
import sys

from .tasks import analyze_trends, health_check, process_backlog, run_debate, signal_collect

logger = logging.getLogger(__name__)


def _ensure_schema() -> None:
    """Idempotently create any missing tables before running a task.

    A fresh or emptied SQLite file would otherwise crash every scheduled task
    with "no such table" until an operator intervenes (2026-07 incident).
    ``create_tables()`` is CREATE TABLE IF NOT EXISTS, so this is a no-op on a
    healthy database. Failures are logged, not fatal: the task itself will
    surface a clearer error if the database is truly unusable.
    """
    from ..db.connection import get_db

    try:
        get_db().create_tables()
    except Exception:
        logger.exception("Could not ensure database schema; the task may fail")


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

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # backup-db is deliberately read-only: it must never mutate the database
    # it is about to snapshot. Every other command gets the schema guarantee.
    if args.command != "backup-db":
        _ensure_schema()

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
        from ..db.backup import backup_database

        dest = backup_database()
        if dest is None:
            print("No backup created (database missing, empty, dataless, or not SQLite).")
            sys.exit(1)
        print(f"Backup written: {dest}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
