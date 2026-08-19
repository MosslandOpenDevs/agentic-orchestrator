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


class TestRenamingPublicIssues:
    """The only code in this repo that renames issues on a public tracker.

    It had no test at all. Every assertion here is about not doing damage: the
    rename is outward-facing, it hits a repository anyone can read, and a bad
    title cannot be un-published.
    """

    class FakeClient:
        def __init__(self, issues):
            self._issues = issues
            self.renamed = {}

        def list_issues(self, labels=None, state="open", **kw):
            return self._issues

        def update_issue(self, number, title=None, **kw):
            self.renamed[number] = title

    @staticmethod
    def _issue(number, title):
        from agentic_orchestrator.github_client import GitHubIssue, Labels

        return GitHubIssue(
            number=number,
            title=title,
            body="",
            state="open",
            labels=[Labels.GENERATED_BY_ORCHESTRATOR],
            created_at="2026-08-01T00:00:00Z",
            updated_at="2026-08-01T00:00:00Z",
            html_url="",
            comments=0,
        )

    def _run(self, monkeypatch, titles, apply=True, limit=None):
        from agentic_orchestrator.scheduler import clean_titles as mod

        client = self.FakeClient([self._issue(n, t) for n, t in titles.items()])
        monkeypatch.setattr(mod, "GitHubClient", lambda: client, raising=False)
        import agentic_orchestrator.github_client as gh

        monkeypatch.setattr(gh, "GitHubClient", lambda: client)
        changed, errors = mod._clean_issue_titles(apply=apply, limit=limit)
        return client, changed, errors

    def test_the_tracker_prefix_is_preserved(self, monkeypatch):
        """`[Idea] ` is the tracker's own marker, not model output — losing it
        would break every label-and-prefix convention the repo reads by."""
        client, changed, _ = self._run(monkeypatch, {1: "[Idea] Idea: Gas-Guard Copilot"})

        assert client.renamed == {1: "[Idea] Gas-Guard Copilot"}
        assert changed == 1

    def test_a_dry_run_writes_nothing(self, monkeypatch):
        client, changed, _ = self._run(
            monkeypatch, {1: "[Idea] Idea: Gas-Guard Copilot"}, apply=False
        )

        assert client.renamed == {}
        assert changed == 1, "a dry run still has to report what it would do"

    def test_a_clean_title_is_not_rewritten(self, monkeypatch):
        client, changed, _ = self._run(
            monkeypatch, {1: "[Idea] ERC-6551 Token-Bound Spend Passport"}
        )

        assert client.renamed == {}
        assert changed == 0

    def test_a_title_without_the_prefix_is_still_handled(self, monkeypatch):
        client, _, _ = self._run(monkeypatch, {1: "Idea: Bare title with no prefix"})

        assert client.renamed == {1: "Bare title with no prefix"}

    def test_a_bracket_later_in_the_title_does_not_confuse_the_split(self, monkeypatch):
        client, _, _ = self._run(monkeypatch, {1: "[Idea] Idea: Fix [bug] parsing in the relayer"})

        assert client.renamed == {1: "[Idea] Fix [bug] parsing in the relayer"}

    def test_a_title_that_would_clean_to_nothing_is_left_alone(self, monkeypatch):
        client, changed, _ = self._run(monkeypatch, {1: "[Idea] **"})

        assert client.renamed == {}
        assert changed == 0

    def test_renaming_is_idempotent(self, monkeypatch):
        """A second run must be a no-op. Otherwise the command churns the public
        tracker every time an operator repeats it."""
        client, _, _ = self._run(monkeypatch, {1: "[Idea] **Idea:** Session-Key Budget Vault"})
        once = client.renamed[1]

        client2, changed2, _ = self._run(monkeypatch, {1: once})

        assert changed2 == 0, f"{once!r} was renamed twice"

    def test_limit_bounds_how_many_public_issues_are_touched(self, monkeypatch):
        client, changed, _ = self._run(
            monkeypatch, {n: f"[Idea] Idea: Candidate {n}" for n in range(1, 6)}, limit=2
        )

        assert len(client.renamed) == 2

    def test_limit_zero_touches_nothing(self, monkeypatch):
        client, changed, _ = self._run(
            monkeypatch, {n: f"[Idea] Idea: Candidate {n}" for n in range(1, 6)}, limit=0
        )

        assert client.renamed == {}
        assert changed == 0

    def test_a_failed_rename_is_counted_not_raised(self, monkeypatch):
        import agentic_orchestrator.github_client as gh
        from agentic_orchestrator.scheduler import clean_titles as mod

        class Failing(self.FakeClient):
            def update_issue(self, number, title=None, **kw):
                raise RuntimeError("422 from GitHub")

        client = Failing([self._issue(1, "[Idea] Idea: X marks a specific spot")])
        monkeypatch.setattr(gh, "GitHubClient", lambda: client)
        monkeypatch.setattr(mod, "GitHubClient", lambda: client, raising=False)

        changed, errors = mod._clean_issue_titles(apply=True, limit=None)

        assert errors == 1

    def test_github_being_unavailable_is_an_error_not_a_crash(self, monkeypatch):
        import agentic_orchestrator.github_client as gh
        from agentic_orchestrator.scheduler import clean_titles as mod

        def boom():
            raise RuntimeError("GITHUB_TOKEN not set")

        monkeypatch.setattr(gh, "GitHubClient", boom)
        monkeypatch.setattr(mod, "GitHubClient", boom, raising=False)

        changed, errors = mod._clean_issue_titles(apply=True, limit=None)

        assert (changed, errors) == (0, 1)
