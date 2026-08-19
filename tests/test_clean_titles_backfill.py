"""The backfill that cleans titles already stored.

A migration that rewrites rows in place has to be safe to run twice, safe to
interrupt, and unable to make a row worse than it found it. These pin all three,
plus the one judgement call: a title that is *only* markup is left alone rather
than blanked.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_orchestrator.db.models import Base, Idea, Plan, Trend
from agentic_orchestrator.scheduler.clean_titles import (
    IDEA_FIELDS,
    TREND_FIELDS,
    _plan_row_changes,
    _sweep,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    yield db
    db.close()


def add_idea(session, idea_id, title, title_ko=None):
    session.add(
        Idea(
            id=idea_id,
            title=title,
            title_ko=title_ko,
            summary="s",
            source_type="debate",
            status="scored",
        )
    )
    session.flush()


class TestPlanningTheChanges:
    def test_a_dirty_title_is_planned_for_cleaning(self, session):
        add_idea(session, "a", "## Idea: ERC-6551 Token-Bound Spend Passport")

        planned, skipped = _sweep(session, Idea, IDEA_FIELDS, limit=None)

        assert len(planned) == 1
        _, changes = planned[0]
        assert changes == {"title": "ERC-6551 Token-Bound Spend Passport"}
        assert skipped == 0

    def test_both_languages_are_cleaned_independently(self, session):
        # 57 ideas in production had a clean English title and a dirty Korean
        # one, because the translator is a separate source of the markup.
        add_idea(session, "b", "Gas-Guard Copilot", "## 아이디어: 가스 가드 코파일럿")

        planned, _ = _sweep(session, Idea, IDEA_FIELDS, limit=None)
        _, changes = planned[0]

        assert changes == {"title_ko": "가스 가드 코파일럿"}

    def test_a_clean_row_is_not_touched(self, session):
        add_idea(session, "c", "EIP-7702 Intent Vault for Wallet Power Users")

        planned, skipped = _sweep(session, Idea, IDEA_FIELDS, limit=None)

        assert planned == []
        assert skipped == 0

    def test_a_title_that_is_only_markup_is_left_alone(self, session):
        """A visible ``## Idea:`` is worse than a clean title and better than
        no title at all — the row would become unidentifiable in every list."""
        add_idea(session, "d", "## Idea:")

        planned, skipped = _sweep(session, Idea, IDEA_FIELDS, limit=None)

        assert planned == []
        assert skipped == 1

    def test_trend_names_also_lose_a_serialized_tail(self, session):
        # Length matters here: `clean_name` refuses a cut that would leave less
        # than a usable title, so the fixture has to be as long as the real
        # leaked names (~100 chars before the tail), not a toy.
        session.add(
            Trend(
                id="t1",
                period="24h",
                score=8.7,
                name=(
                    "Provenance Blockchain Token Surge Signals Growing Demand for "
                    'Supply Chain Tracking in Web3", "keywords": ["Provenance"], "score": 8.7'
                ),
            )
        )
        session.flush()

        planned, _ = _sweep(session, Trend, TREND_FIELDS, limit=None)
        _, changes = planned[0]

        assert changes["name"] == (
            "Provenance Blockchain Token Surge Signals Growing Demand for "
            "Supply Chain Tracking in Web3"
        )

    def test_limit_bounds_a_trial_run(self, session):
        for n in range(5):
            add_idea(session, f"L{n}", f"## Idea: Candidate number {n}")

        planned, _ = _sweep(session, Idea, IDEA_FIELDS, limit=2)

        assert len(planned) == 2


class TestIdempotence:
    def test_running_twice_finds_nothing_the_second_time(self, session):
        add_idea(session, "e", "## Idea: Session-Key Budget Vault")

        planned, _ = _sweep(session, Idea, IDEA_FIELDS, limit=None)
        for row, changes in planned:
            for attribute, cleaned in changes.items():
                setattr(row, attribute, cleaned)
        session.flush()

        again, skipped = _sweep(session, Idea, IDEA_FIELDS, limit=None)

        assert again == []
        assert skipped == 0

    def test_cleaning_is_a_fixed_point(self):
        """What makes an interrupted run safe to resume: every row is either
        already done or untouched, never half-converted."""
        from agentic_orchestrator.textutil import clean_title

        once = clean_title("> ## **Idea: Chrome MV3 Intent-Caching Relayer**")

        assert clean_title(once) == once


class TestNeverMakesARowWorse:
    def test_an_empty_result_is_never_written(self):
        row = Plan(id="p", idea_id="i", title="**", title_ko=None, version=1, status="draft")

        assert _plan_row_changes(row, (("title", lambda v: ""),)) == {}

    def test_a_missing_field_is_skipped_rather_than_set(self):
        row = Plan(
            id="p", idea_id="i", title="Plan: Clean", title_ko=None, version=1, status="draft"
        )

        changes = _plan_row_changes(row, IDEA_FIELDS)

        assert "title_ko" not in changes


class TestLimitZeroMeansZero:
    """`if limit:` made `--limit 0` mean NO limit — the most cautious-looking
    input a person could type would have swept the whole table and, with
    `--issues`, renamed every open bot issue on a public repository."""

    def test_limit_zero_selects_nothing(self, session):
        for n in range(5):
            add_idea(session, f"z{n}", f"## Idea: Candidate number {n}")

        planned, _ = _sweep(session, Idea, IDEA_FIELDS, limit=0)

        assert planned == []

    def test_a_negative_limit_selects_nothing_rather_than_everything(self, session):
        for n in range(5):
            add_idea(session, f"n{n}", f"## Idea: Candidate number {n}")

        planned, _ = _sweep(session, Idea, IDEA_FIELDS, limit=-1)

        assert planned == []

    def test_none_still_means_no_limit(self, session):
        for n in range(5):
            add_idea(session, f"a{n}", f"## Idea: Candidate number {n}")

        planned, _ = _sweep(session, Idea, IDEA_FIELDS, limit=None)

        assert len(planned) == 5
