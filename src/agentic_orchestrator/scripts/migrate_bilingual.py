"""
Migration script to add bilingual translations to existing ideas and plans.

Detects the source language and:
- Korean content → translates to English for main field, keeps Korean in *_ko
- English content → keeps in main field, translates to Korean for *_ko

Usage:
    PYTHONPATH=./src python -m agentic_orchestrator.scripts.migrate_bilingual
"""

import asyncio
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def migrate_ideas():
    """Migrate all ideas to have bilingual content."""
    from ..db import get_database, IdeaRepository
    from ..translation import ContentTranslator

    db = get_database()
    session = db.get_session()
    idea_repo = IdeaRepository(session)
    translator = ContentTranslator()

    # Get all ideas
    ideas = session.query(idea_repo.model).all()
    total = len(ideas)
    logger.info(f"Found {total} ideas to process")

    migrated = 0
    skipped = 0
    failed = 0

    for idx, idea in enumerate(ideas, 1):
        try:
            # Skip if already has Korean translation
            if idea.title_ko and idea.summary_ko:
                logger.info(f"[{idx}/{total}] Skipping idea {idea.id} - already has translations")
                skipped += 1
                continue

            logger.info(f"[{idx}/{total}] Processing idea {idea.id}: {idea.title[:50]}...")

            # Process title
            if idea.title and not idea.title_ko:
                title_en, title_ko = await translator.ensure_bilingual(idea.title)
                idea.title = title_en or idea.title
                idea.title_ko = title_ko or idea.title

            # Process summary
            if idea.summary and not idea.summary_ko:
                summary_en, summary_ko = await translator.ensure_bilingual(idea.summary)
                idea.summary = summary_en or idea.summary
                idea.summary_ko = summary_ko or idea.summary

            # Process description
            if idea.description and not idea.description_ko:
                desc_en, desc_ko = await translator.ensure_bilingual(idea.description)
                idea.description = desc_en or idea.description
                idea.description_ko = desc_ko or idea.description

            session.add(idea)
            session.commit()

            migrated += 1
            logger.info(f"[{idx}/{total}] Migrated idea {idea.id}")

            # Small delay to avoid overwhelming the LLM
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"[{idx}/{total}] Failed to migrate idea {idea.id}: {e}")
            failed += 1
            session.rollback()
            continue

    logger.info(f"Ideas migration complete: {migrated} migrated, {skipped} skipped, {failed} failed")
    return migrated, skipped, failed


async def migrate_plans():
    """Migrate all plans to have bilingual content."""
    from ..db import get_database, PlanRepository
    from ..translation import ContentTranslator

    db = get_database()
    session = db.get_session()
    plan_repo = PlanRepository(session)
    translator = ContentTranslator()

    # Get all plans
    plans = session.query(plan_repo.model).all()
    total = len(plans)
    logger.info(f"Found {total} plans to process")

    migrated = 0
    skipped = 0
    failed = 0

    for idx, plan in enumerate(plans, 1):
        try:
            # Skip if already has Korean translation
            if plan.title_ko:
                logger.info(f"[{idx}/{total}] Skipping plan {plan.id} - already has translations")
                skipped += 1
                continue

            logger.info(f"[{idx}/{total}] Processing plan {plan.id}: {plan.title[:50]}...")

            # Process title
            if plan.title and not plan.title_ko:
                title_en, title_ko = await translator.ensure_bilingual(plan.title)
                plan.title = title_en or plan.title
                plan.title_ko = title_ko or plan.title

            # Process final_plan
            if plan.final_plan and not plan.final_plan_ko:
                final_en, final_ko = await translator.ensure_bilingual(plan.final_plan)
                plan.final_plan = final_en or plan.final_plan
                plan.final_plan_ko = final_ko or plan.final_plan

            session.add(plan)
            session.commit()

            migrated += 1
            logger.info(f"[{idx}/{total}] Migrated plan {plan.id}")

            # Small delay to avoid overwhelming the LLM
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"[{idx}/{total}] Failed to migrate plan {plan.id}: {e}")
            failed += 1
            session.rollback()
            continue

    logger.info(f"Plans migration complete: {migrated} migrated, {skipped} skipped, {failed} failed")
    return migrated, skipped, failed


async def migrate_trends():
    """Migrate all trends to have bilingual content."""
    from ..db import get_database, TrendRepository
    from ..translation import ContentTranslator

    db = get_database()
    session = db.get_session()
    trend_repo = TrendRepository(session)
    translator = ContentTranslator()

    # Get all trends
    from ..db.models import Trend
    trends = session.query(Trend).all()
    total = len(trends)
    logger.info(f"Found {total} trends to process")

    migrated = 0
    skipped = 0
    failed = 0

    for idx, trend in enumerate(trends, 1):
        try:
            # Skip if already has Korean translation
            if trend.name_ko and trend.description_ko:
                logger.info(f"[{idx}/{total}] Skipping trend {trend.id} - already has translations")
                skipped += 1
                continue

            logger.info(f"[{idx}/{total}] Processing trend {trend.id}: {trend.name[:50] if trend.name else 'N/A'}...")

            # Process name
            if trend.name and not trend.name_ko:
                name_en, name_ko = await translator.ensure_bilingual(trend.name)
                trend.name = name_en or trend.name
                trend.name_ko = name_ko or trend.name

            # Process description
            if trend.description and not trend.description_ko:
                desc_en, desc_ko = await translator.ensure_bilingual(trend.description)
                trend.description = desc_en or trend.description
                trend.description_ko = desc_ko or trend.description

            session.add(trend)
            session.commit()

            migrated += 1
            logger.info(f"[{idx}/{total}] Migrated trend {trend.id}")

            # Small delay to avoid overwhelming the LLM
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"[{idx}/{total}] Failed to migrate trend {trend.id}: {e}")
            failed += 1
            session.rollback()
            continue

    logger.info(f"Trends migration complete: {migrated} migrated, {skipped} skipped, {failed} failed")
    return migrated, skipped, failed


async def main():
    """Run the full migration."""
    logger.info("=" * 60)
    logger.info("Starting bilingual migration")
    logger.info("=" * 60)

    start_time = datetime.now()

    # Migrate in order
    logger.info("\n" + "=" * 40)
    logger.info("Phase 1: Migrating Trends")
    logger.info("=" * 40)
    trends_result = await migrate_trends()

    logger.info("\n" + "=" * 40)
    logger.info("Phase 2: Migrating Ideas")
    logger.info("=" * 40)
    ideas_result = await migrate_ideas()

    logger.info("\n" + "=" * 40)
    logger.info("Phase 3: Migrating Plans")
    logger.info("=" * 40)
    plans_result = await migrate_plans()

    duration = (datetime.now() - start_time).total_seconds()

    logger.info("\n" + "=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info(f"Trends:  {trends_result[0]} migrated, {trends_result[1]} skipped, {trends_result[2]} failed")
    logger.info(f"Ideas:   {ideas_result[0]} migrated, {ideas_result[1]} skipped, {ideas_result[2]} failed")
    logger.info(f"Plans:   {plans_result[0]} migrated, {plans_result[1]} skipped, {plans_result[2]} failed")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
