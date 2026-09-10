"""One-off backfill: strip leaked markdown out of titles already in the database.

The write-side fix stops new rows from being written dirty. It does nothing for
what is already stored — 240 of 1,264 ideas carry markup in at least one
language, 8 of 44 plans do, and 29 trend names start with a heading marker.

Design notes, because a backfill that rewrites rows deserves them:

- **Dry run by default.** ``--apply`` is required to write anything, and the
  report it prints first is the same computation the write pass performs.
- **Idempotent.** ``clean_title`` is a fixed point on already-clean text, so a
  second run finds nothing and a half-finished run resumes safely.
- **Never blanks a field.** If cleaning would empty a title — a title that was
  *only* markup — the row is left alone and counted as skipped. A visible
  ``## Idea:`` is worse than a clean title and better than no title at all.

Usage::

    python -m agentic_orchestrator.scheduler clean-titles            # report
    python -m agentic_orchestrator.scheduler clean-titles --apply
"""

from typing import Dict, List, Optional, Tuple

from ..textutil import clean_name, clean_title
from ..utils.logging import get_logger

logger = get_logger(__name__)

# (model attribute, cleaner). Trend names get `clean_name`, which also cuts the
# serialized tail that leaked into a few of them; everything else gets
# `clean_title`, which leaves an ordinary title untouched.
IDEA_FIELDS = (("title", clean_title), ("title_ko", clean_title))
PLAN_FIELDS = (("title", clean_title), ("title_ko", clean_title))
TREND_FIELDS = (("name", clean_name), ("name_ko", clean_name))


def _plan_row_changes(row, fields) -> Dict[str, str]:
    """Field -> cleaned value, for fields the cleaner would actually change."""
    changes: Dict[str, str] = {}
    for attribute, cleaner in fields:
        current = getattr(row, attribute, None)
        if not current:
            continue
        cleaned = cleaner(current)
        # Never trade a dirty title for an empty one.
        if cleaned and cleaned != current:
            changes[attribute] = cleaned
    return changes


def _sweep(session, model, fields, limit: Optional[int]) -> Tuple[List[Tuple], int]:
    """Return ``([(row, {field: cleaned}), ...], skipped_count)`` for one table."""
    query = session.query(model)
    if limit is not None:
        # `if limit:` made `--limit 0` mean NO limit -- the most cautious-looking
        # input a person could type would have swept the whole table.
        query = query.limit(max(limit, 0))

    planned: List[Tuple] = []
    skipped = 0
    for row in query.all():
        changes = _plan_row_changes(row, fields)
        if not changes:
            # Distinguish "already clean" from "cleaning would blank it": only
            # the latter is a row we are deliberately declining to fix.
            for attribute, cleaner in fields:
                current = getattr(row, attribute, None)
                if current and not cleaner(current):
                    skipped += 1
                    logger.warning(f"{model.__name__} {row.id}: {attribute} is only markup, left")
                    break
            continue
        planned.append((row, changes))
    return planned, skipped


def clean_titles(apply: bool = False, limit: Optional[int] = None) -> Dict[str, int]:
    """Clean stored titles. Reports without writing unless ``apply`` is set."""
    from ..db import get_db
    from ..db.models import Idea, Plan, Trend

    stats = {"ideas": 0, "plans": 0, "trends": 0, "skipped": 0}

    db = get_db()
    with db.session() as session:
        for key, model, fields in (
            ("ideas", Idea, IDEA_FIELDS),
            ("plans", Plan, PLAN_FIELDS),
            ("trends", Trend, TREND_FIELDS),
        ):
            planned, skipped = _sweep(session, model, fields, limit)
            stats["skipped"] += skipped
            stats[key] = len(planned)

            for row, changes in planned:
                for attribute, cleaned in changes.items():
                    logger.info(
                        f"{model.__name__} {row.id}.{attribute}: "
                        f"{getattr(row, attribute)!r} -> {cleaned!r}"
                    )
                    if apply:
                        setattr(row, attribute, cleaned)

        if apply:
            session.commit()
            logger.info("Database titles cleaned")
        else:
            # Nothing was assigned above, so the session is not dirty and the
            # context manager's commit-on-exit is a no-op. Stating it because
            # the alternative -- a rollback here -- would read as the thing
            # keeping a dry run dry, and it would not be.
            logger.info("Dry run — nothing written. Re-run with --apply to write.")

    return stats
