#!/usr/bin/env python3
"""
Migration script: JSON/Markdown files → SQLite Database

Migrates existing trend analysis and idea data to the new database schema.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from agentic_orchestrator.db.connection import init_database, get_db
from agentic_orchestrator.db.models import Signal, Trend, Idea


def parse_trend_markdown(content: str, file_date: str) -> list[dict]:
    """Parse trend analysis markdown file and extract trends."""
    trends = []

    # Extract metadata
    metadata_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not metadata_match:
        return trends

    # Find all trend sections (### N. Title (Score: X.X))
    trend_pattern = r'### \d+\.\s+(.+?)\s+\(Score:\s+([\d.]+)\)\n\n(.*?)(?=\n### \d+\.|\n## |\Z)'
    matches = re.findall(trend_pattern, content, re.DOTALL)

    for title, score, body in matches:
        trend = {
            "name": title.strip(),
            "score": float(score),
            "date": file_date,
        }

        # Extract category
        cat_match = re.search(r'\*\*Category:\*\*\s*(\w+)', body)
        if cat_match:
            trend["category"] = cat_match.group(1).lower()

        # Extract articles count
        articles_match = re.search(r'\*\*Articles:\*\*\s*(\d+)', body)
        if articles_match:
            trend["signal_count"] = int(articles_match.group(1))

        # Extract keywords
        keywords_match = re.search(r'\*\*Keywords:\*\*\s*(.+)', body)
        if keywords_match:
            trend["keywords"] = [k.strip() for k in keywords_match.group(1).split(',')]

        # Extract summary
        summary_match = re.search(r'\*\*Summary:\*\*\s*(.+?)(?=\n\n|\*\*)', body, re.DOTALL)
        if summary_match:
            trend["description"] = summary_match.group(1).strip()

        # Extract idea seeds
        seeds_match = re.search(r'\*\*Idea Seeds:\*\*\n((?:- .+\n?)+)', body)
        if seeds_match:
            seeds = re.findall(r'- (.+)', seeds_match.group(1))
            trend["idea_seeds"] = seeds

        trends.append(trend)

    return trends


def migrate_trends(data_dir: Path, session) -> int:
    """Migrate trend markdown files to database."""
    trends_dir = data_dir / "trends"
    count = 0

    # Find all markdown files
    for md_file in trends_dir.rglob("*.md"):
        # Extract date from filename (e.g., 2026-01-21.md)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\.md$', str(md_file))
        if not date_match:
            continue

        file_date = date_match.group(1)
        print(f"  Processing {md_file.name}...")

        content = md_file.read_text(encoding='utf-8')
        trends = parse_trend_markdown(content, file_date)

        for trend_data in trends:
            # Check if trend already exists
            existing = session.query(Trend).filter(
                Trend.name == trend_data["name"],
                Trend.analyzed_at >= datetime.fromisoformat(f"{file_date}T00:00:00"),
                Trend.analyzed_at < datetime.fromisoformat(f"{file_date}T23:59:59"),
            ).first()

            if existing:
                continue

            trend = Trend(
                period="24h",
                name=trend_data["name"],
                description=trend_data.get("description"),
                score=trend_data["score"],
                signal_count=trend_data.get("signal_count", 0),
                category=trend_data.get("category", "other"),
                keywords=trend_data.get("keywords", []),
                analysis_data={"idea_seeds": trend_data.get("idea_seeds", [])},
                analyzed_at=datetime.fromisoformat(f"{file_date}T12:00:00"),
            )
            session.add(trend)
            count += 1

    session.commit()
    return count


def migrate_ideas(data_dir: Path, session) -> int:
    """Migrate idea links to database."""
    idea_links_file = data_dir / "trends" / "idea_links.json"

    if not idea_links_file.exists():
        print("  No idea_links.json found")
        return 0

    with open(idea_links_file, 'r') as f:
        idea_links = json.load(f)

    count = 0
    for link in idea_links:
        issue_number = link.get("idea_issue_number")

        # Check if idea already exists
        existing = session.query(Idea).filter(
            Idea.github_issue_id == issue_number
        ).first()

        if existing:
            continue

        idea = Idea(
            title=link.get("trend_topic", f"Idea #{issue_number}"),
            summary=f"Generated from trend: {link.get('trend_topic', 'Unknown')}",
            source_type="trend_based",
            status="pending",
            github_issue_id=issue_number,
            github_issue_url=f"https://github.com/mossland/agentic-orchestrator/issues/{issue_number}",
            score=0.0,
            created_at=datetime.fromisoformat(link.get("created_at", datetime.utcnow().isoformat()).replace('Z', '')),
        )
        session.add(idea)
        count += 1

    session.commit()
    return count


def create_sample_signals(session) -> int:
    """Create sample signals from trend data for demonstration."""
    # Get existing trends
    trends = session.query(Trend).limit(20).all()

    count = 0
    for trend in trends:
        # Create a signal for each trend
        signal = Signal(
            source="rss",
            category=trend.category or "other",
            title=trend.name,
            summary=trend.description,
            score=trend.score / 10.0,  # Normalize to 0-1
            topics=trend.keywords,
            collected_at=trend.analyzed_at,
        )
        session.add(signal)
        count += 1

    session.commit()
    return count


def main():
    print("=" * 50)
    print("MOSS.AO Data Migration: JSON → SQLite")
    print("=" * 50)
    print()

    # Initialize database
    print("[1/4] Initializing database...")
    db = init_database()

    data_dir = project_root / "data"

    with db.session() as session:
        # Migrate trends
        print("\n[2/4] Migrating trend analysis data...")
        trend_count = migrate_trends(data_dir, session)
        print(f"  ✓ Imported {trend_count} trends")

        # Migrate ideas
        print("\n[3/4] Migrating idea links...")
        idea_count = migrate_ideas(data_dir, session)
        print(f"  ✓ Imported {idea_count} ideas")

        # Create sample signals
        print("\n[4/4] Creating sample signals from trends...")
        signal_count = create_sample_signals(session)
        print(f"  ✓ Created {signal_count} signals")

    print("\n" + "=" * 50)
    print("Migration Complete!")
    print(f"  - Trends: {trend_count}")
    print(f"  - Ideas: {idea_count}")
    print(f"  - Signals: {signal_count}")
    print("=" * 50)


if __name__ == "__main__":
    main()
