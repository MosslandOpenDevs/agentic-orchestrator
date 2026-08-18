"""Tests for the GitHub issue lifecycle (pipeline-linked closes + aging sweep).

The tracker was write-only: the orchestrator created an issue per idea and per
plan and nothing ever closed one (2,866 open issues by 2026-06). These tests
pin the circulation added in v0.6.15: issues follow the DB pipeline and stale
untouched backlog issues age out — while the curated keep-set is untouchable.
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_orchestrator.db.models import Base
from agentic_orchestrator.db.repositories import (
    IdeaRepository,
    PlanRepository,
    ProjectRepository,
)
from agentic_orchestrator.github_client import GitHubIssue, Labels
from agentic_orchestrator.scheduler.issue_lifecycle import (
    close_idea_issue_for_plan,
    run_issue_lifecycle,
    should_age_out,
)

NOW = datetime(2026, 8, 5, 12, 0, 0)


def make_issue(
    number: int,
    labels: list = None,
    created_at: str = "2026-01-01T00:00:00Z",
    comments: int = 0,
    state: str = "open",
) -> GitHubIssue:
    return GitHubIssue(
        number=number,
        title=f"[Idea] Issue {number}",
        body="",
        state=state,
        labels=labels if labels is not None else [Labels.GENERATED_BY_ORCHESTRATOR],
        created_at=created_at,
        updated_at=created_at,
        html_url=f"https://github.com/x/y/issues/{number}",
        comments=comments,
    )


class FakeClient:
    """Duck-typed GitHubClient recording every mutation.

    ``fail_numbers`` fails every call for an issue; ``fail_close_numbers``
    fails only ``update_issue`` — the partial-failure window where a comment
    could land on an issue that then stays open.
    """

    def __init__(
        self,
        open_issues=None,
        fail_numbers=(),
        fail_close_numbers=(),
        existing_comments=None,
    ):
        self.open_issues = {i.number: i for i in (open_issues or [])}
        self.fail_numbers = set(fail_numbers)
        self.fail_close_numbers = set(fail_close_numbers)
        self.closed = {}  # number -> state_reason
        self.comments = {}  # number -> [bodies]
        self.label_updates = {}  # number -> labels
        self.marked_planned = []
        # number -> [{"author_association": ..., "body": ...}]. Defaults to a
        # maintainer comment so an issue carrying `comments=N` behaves the way
        # every pre-existing test means it to: engaged, therefore spared.
        self.existing_comments = existing_comments or {}

    def list_comments(self, number, per_page=30):
        if number in self.existing_comments:
            return self.existing_comments[number]
        count = self.open_issues[number].comments if number in self.open_issues else 0
        return [{"author_association": "OWNER", "body": "looks useful"} for _ in range(count)]

    def list_issues(self, labels=None, state="open", per_page=100, max_pages=10):
        return list(self.open_issues.values())

    def add_comment(self, number, body):
        if number in self.fail_numbers:
            raise RuntimeError("boom")
        self.comments.setdefault(number, []).append(body)
        return {}

    def update_issue(self, number, state=None, state_reason=None, labels=None, **kw):
        if number in self.fail_numbers or number in self.fail_close_numbers:
            raise RuntimeError("boom")
        if state == "closed":
            self.closed[number] = state_reason
        if labels is not None:
            self.label_updates[number] = labels
        return self.open_issues.get(number) or make_issue(number, state="closed")

    def mark_idea_as_planned(self, number):
        if number in self.fail_numbers:
            raise RuntimeError("boom")
        self.marked_planned.append(number)
        return make_issue(number)


@pytest.fixture()
def repos():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield (
        IdeaRepository(session),
        PlanRepository(session),
        ProjectRepository(session),
        session,
    )
    session.close()


class TestShouldAgeOut:
    def test_old_untouched_bot_issue_ages_out(self):
        issue = make_issue(1, created_at="2026-01-01T00:00:00Z", comments=0)
        decision, reason = should_age_out(issue, NOW, max_age_days=30)
        assert decision
        assert "without engagement" in reason

    def test_young_issue_survives(self):
        issue = make_issue(1, created_at="2026-08-01T00:00:00Z")
        assert not should_age_out(issue, NOW, max_age_days=30)[0]

    def test_human_comment_exempts(self):
        issue = make_issue(1, comments=2)
        decision, reason = should_age_out(issue, NOW, max_age_days=30)
        assert not decision
        assert reason == "has discussion"

    def test_curated_keep_is_untouchable(self):
        issue = make_issue(1, labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.CURATED_KEEP])
        assert not should_age_out(issue, NOW, max_age_days=30)[0]

    def test_source_trend_is_untouchable(self):
        issue = make_issue(1, labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.SOURCE_TREND])
        assert not should_age_out(issue, NOW, max_age_days=30)[0]

    def test_non_bot_issue_is_never_touched(self):
        issue = make_issue(1, labels=["bug"])
        decision, reason = should_age_out(issue, NOW, max_age_days=30)
        assert not decision
        assert reason == "not bot-generated"

    def test_closed_issue_is_skipped(self):
        issue = make_issue(1, state="closed")
        assert not should_age_out(issue, NOW, max_age_days=30)[0]


class TestCloseIdeaIssueForPlan:
    def test_comments_marks_and_closes_completed(self):
        client = FakeClient([make_issue(7)])
        assert close_idea_issue_for_plan(client, 7, plan_issue_number=8, plan_id="p1")
        assert client.closed[7] == "completed"
        assert 7 in client.marked_planned
        assert "#8" in client.comments[7][0]

    def test_missing_plan_issue_links_plan_id(self):
        client = FakeClient([make_issue(7)])
        assert close_idea_issue_for_plan(client, 7, plan_issue_number=None, plan_id="p1")
        assert "p1" in client.comments[7][0]

    def test_github_failure_never_raises(self):
        client = FakeClient([make_issue(7)], fail_numbers={7})
        assert close_idea_issue_for_plan(client, 7, 8, "p1") is False


class TestRunIssueLifecycle:
    def test_promoted_idea_with_plan_closes_completed(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        idea_repo.create(
            {
                "id": "i1",
                "title": "t",
                "summary": "s",
                "source_type": "debate",
                "status": "promoted",
                "github_issue_id": 10,
            }
        )
        plan_repo.create({"id": "p1", "idea_id": "i1", "title": "t", "github_issue_id": 11})
        issue = make_issue(10, labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.PROMOTE_TO_PLAN])
        client = FakeClient([issue, make_issue(11, created_at="2026-08-05T00:00:00Z")])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_ideas"] == 1
        assert client.closed[10] == "completed"
        assert "#11" in client.comments[10][0]
        assert Labels.PROCESSED_TO_PLAN in client.label_updates[10]
        assert Labels.PROMOTE_TO_PLAN not in client.label_updates[10]

    def test_plan_with_project_closes_completed(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        idea_repo.create({"id": "i1", "title": "t", "summary": "s", "source_type": "debate"})
        plan_repo.create({"id": "p1", "idea_id": "i1", "title": "t", "github_issue_id": 20})
        project_repo.create(
            {
                "id": "prj1",
                "plan_id": "p1",
                "name": "cool-app",
                "directory_path": "/x",
                "status": "ready",
            }
        )
        issue = make_issue(20, labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.STATUS_BACKLOG])
        client = FakeClient([issue])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_plans"] == 1
        assert client.closed[20] == "completed"
        assert "cool-app" in client.comments[20][0]
        assert Labels.STATUS_DONE in client.label_updates[20]

    @pytest.mark.parametrize("project_status", ["pending", "generating", "error"])
    def test_plan_with_unfinished_project_stays_open(self, repos, project_status):
        idea_repo, plan_repo, project_repo, session = repos
        idea_repo.create({"id": "i1", "title": "t", "summary": "s", "source_type": "debate"})
        plan_repo.create({"id": "p1", "idea_id": "i1", "title": "t", "github_issue_id": 20})
        project_repo.create(
            {
                "id": "prj1",
                "plan_id": "p1",
                "name": "cool-app",
                "directory_path": "/x",
                "status": project_status,
            }
        )
        issue = make_issue(
            20,
            labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.STATUS_BACKLOG],
            created_at="2026-08-05T00:00:00Z",
        )
        client = FakeClient([issue])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_plans"] == 0
        assert client.closed == {}

    def test_aging_closes_stale_and_spares_protected(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        stale = make_issue(1, created_at="2026-01-01T00:00:00Z")
        fresh = make_issue(2, created_at="2026-08-01T00:00:00Z")
        curated = make_issue(
            3,
            labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.CURATED_KEEP],
            created_at="2026-01-01T00:00:00Z",
        )
        discussed = make_issue(4, created_at="2026-01-01T00:00:00Z", comments=3)
        client = FakeClient([stale, fresh, curated, discussed])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["aged_out"] == 1
        assert client.closed == {1: "not_planned"}

    def test_close_budget_is_respected(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        issues = [make_issue(n, created_at="2026-01-01T00:00:00Z") for n in range(1, 11)]
        client = FakeClient(issues)

        stats = run_issue_lifecycle(
            client,
            idea_repo,
            plan_repo,
            project_repo,
            config={"max_closes_per_run": 3},
            now=NOW,
        )

        assert stats["aged_out"] == 3
        assert len(client.closed) == 3

    def test_idea_without_plan_stays_open(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        idea_repo.create(
            {
                "id": "i1",
                "title": "t",
                "summary": "s",
                "source_type": "debate",
                "status": "promoted",
                "github_issue_id": 10,
            }
        )
        issue = make_issue(10, created_at="2026-08-05T00:00:00Z")
        client = FakeClient([issue])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_ideas"] == 0
        assert client.closed == {}

    def test_github_errors_are_counted_not_raised(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        stale = make_issue(1, created_at="2026-01-01T00:00:00Z")
        client = FakeClient([stale], fail_numbers={1})

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["errors"] == 1
        assert stats["aged_out"] == 0


class TestArchivedReconciliation:
    """DB-archived ideas (backlog triage rejects) close their mirror issue.

    Issues here are FRESH — well under max_age_days — so any close observed
    comes from the archived reconciliation, never from the aging sweep.
    """

    def _archived_idea(self, idea_repo, issue_number, triage=None):
        extra = {"triage": triage} if triage else None
        idea_repo.create(
            {
                "id": f"i{issue_number}",
                "title": "t",
                "summary": "s",
                "source_type": "debate",
                "status": "archived",
                "github_issue_id": issue_number,
                "extra_metadata": extra,
            }
        )

    def test_archived_idea_closes_not_planned_with_verdict(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(
            idea_repo,
            10,
            triage={
                "last_score": 3.1,
                "last_at": "2026-08-05T08:00:00",
                "reason": "re-scored below archive threshold",
            },
        )
        issue = make_issue(
            10,
            labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.STATUS_BACKLOG],
            created_at="2026-08-05T00:00:00Z",
        )
        client = FakeClient([issue])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_archived"] == 1
        assert client.closed[10] == "not_planned"
        assert "3.1/10" in client.comments[10][0]
        assert "re-scored below archive threshold" in client.comments[10][0]
        assert Labels.STATUS_ARCHIVED in client.label_updates[10]
        assert Labels.STATUS_BACKLOG not in client.label_updates[10]

    def test_archived_idea_without_triage_record_still_closes(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 10)
        issue = make_issue(10, created_at="2026-08-05T00:00:00Z")
        client = FakeClient([issue])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_archived"] == 1
        assert client.closed[10] == "not_planned"

    def test_human_engagement_overrides_the_archive_close(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 10)
        self._archived_idea(idea_repo, 11)
        curated = make_issue(
            10,
            labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.CURATED_KEEP],
            created_at="2026-08-05T00:00:00Z",
        )
        discussed = make_issue(11, created_at="2026-08-05T00:00:00Z", comments=2)
        client = FakeClient([curated, discussed])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_archived"] == 0
        assert client.closed == {}

    def test_a_strangers_comment_does_not_pin_the_issue_open(self, repos):
        """The exemption protects a maintainer's discussion, not any comment.

        Four archived ideas (#3309, #3311, #3312, #3529) are open on GitHub
        permanently because a passer-by dropped sales spam or a `/claim` bot
        reply on them — two of those comments byte-identical, 32 seconds apart,
        same account. A bare comment count handed the veto to the internet.
        """
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 20)
        spammed = make_issue(20, created_at="2026-08-05T00:00:00Z", comments=2)
        client = FakeClient(
            [spammed],
            existing_comments={
                20: [
                    {"author_association": "NONE", "body": "Great project! DM me for growth."},
                    {"author_association": "NONE", "body": "Great project! DM me for growth."},
                ]
            },
        )

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_archived"] == 1
        assert client.closed == {20: "not_planned"}

    def test_a_maintainers_comment_still_spares_the_issue(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 21)
        discussed = make_issue(21, created_at="2026-08-05T00:00:00Z", comments=1)
        client = FakeClient(
            [discussed],
            existing_comments={
                21: [{"author_association": "COLLABORATOR", "body": "Worth keeping, see #12."}]
            },
        )

        run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert client.closed == {}

    def test_the_bots_own_comment_is_not_human_engagement(self, repos):
        """The lifecycle comments as an account with standing in this repo, so
        without this check every issue it ever touched would exempt itself —
        which is the deadlock the close-before-comment ordering exists to
        avoid, arriving by a different road."""
        from agentic_orchestrator.scheduler.issue_lifecycle import LIFECYCLE_SIGNATURE

        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 22)
        touched = make_issue(22, created_at="2026-08-05T00:00:00Z", comments=1)
        client = FakeClient(
            [touched],
            existing_comments={
                22: [{"author_association": "OWNER", "body": f"Closing. {LIFECYCLE_SIGNATURE}"}]
            },
        )

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_archived"] == 1

    def test_unreadable_comments_spare_the_issue(self, repos):
        """A missed close costs one stale issue; a wrong close buries a real
        conversation under a bot's verdict. Fail toward leaving it open."""
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 23)
        issue = make_issue(23, created_at="2026-08-05T00:00:00Z", comments=1)

        class Blind(FakeClient):
            def list_comments(self, number, per_page=30):
                raise RuntimeError("403 from GitHub")

        client = Blind([issue])

        run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert client.closed == {}

    def test_archived_idea_with_closed_or_missing_issue_is_skipped(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 99)  # issue not in the open list
        client = FakeClient([])

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_archived"] == 0
        assert client.closed == {}

    def test_failed_close_posts_no_comment_and_stays_retryable(self, repos):
        # The poison scenario: if the verdict comment landed while the close
        # failed, the bot's own comment would read as human engagement and
        # block every future auto-close. Close-first ordering prevents it.
        idea_repo, plan_repo, project_repo, session = repos
        self._archived_idea(idea_repo, 10, triage={"last_score": 3.0})
        issue = make_issue(10, created_at="2026-08-05T00:00:00Z")
        client = FakeClient([issue], fail_close_numbers={10})

        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["errors"] == 1
        assert client.comments == {}  # nothing posted — the issue is clean
        assert client.closed == {}

        # Next cycle, GitHub recovered: the same issue closes normally.
        client.fail_close_numbers.clear()
        stats = run_issue_lifecycle(client, idea_repo, plan_repo, project_repo, now=NOW)

        assert stats["reconciled_archived"] == 1
        assert client.closed[10] == "not_planned"
        assert "3.0/10" in client.comments[10][0]

    def test_archived_loop_respects_the_close_budget(self, repos):
        idea_repo, plan_repo, project_repo, session = repos
        for number in (10, 11, 12):
            self._archived_idea(idea_repo, number)
        issues = [make_issue(n, created_at="2026-08-05T00:00:00Z") for n in (10, 11, 12)]
        client = FakeClient(issues)

        stats = run_issue_lifecycle(
            client,
            idea_repo,
            plan_repo,
            project_repo,
            config={"max_closes_per_run": 2},
            now=NOW,
        )

        assert stats["reconciled_archived"] == 2
        assert len(client.closed) == 2


class TestGitHubIssueParsing:
    def test_comments_count_is_parsed(self):
        issue = GitHubIssue.from_api_response(
            {
                "number": 1,
                "title": "t",
                "state": "open",
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": "https://github.com/x/y/issues/1",
                "comments": 5,
            }
        )
        assert issue.comments == 5

    def test_comments_default_zero(self):
        issue = GitHubIssue.from_api_response(
            {
                "number": 1,
                "title": "t",
                "state": "open",
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": "https://github.com/x/y/issues/1",
            }
        )
        assert issue.comments == 0


class TestClientEndpoints:
    """list_issues must use the list API (search silently omits issues) and
    filter out pull requests; update_issue must send state_reason."""

    def _client(self, monkeypatch):
        from agentic_orchestrator.github_client import GitHubClient

        monkeypatch.setenv("GITHUB_TOKEN", "t")
        monkeypatch.setenv("GITHUB_OWNER", "o")
        monkeypatch.setenv("GITHUB_REPO", "r")
        return GitHubClient()

    def test_list_issues_filters_pull_requests(self, monkeypatch):
        client = self._client(monkeypatch)
        raw = [
            {
                "number": 1,
                "title": "issue",
                "state": "open",
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": "u",
            },
            {
                "number": 2,
                "title": "pr",
                "state": "open",
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": "u",
                "pull_request": {"url": "x"},
            },
        ]
        calls = []

        def fake_request(method, endpoint, **kwargs):
            calls.append((method, endpoint, kwargs))
            return raw if len(calls) == 1 else []

        monkeypatch.setattr(client, "_request", fake_request)
        issues = client.list_issues(labels=["generated:by-orchestrator"])

        assert [i.number for i in issues] == [1]
        assert calls[0][1] == "/repos/o/r/issues"
        assert calls[0][2]["params"]["labels"] == "generated:by-orchestrator"

    def test_update_issue_sends_state_reason(self, monkeypatch):
        client = self._client(monkeypatch)
        captured = {}

        def fake_request(method, endpoint, **kwargs):
            captured["method"] = method
            captured["json"] = kwargs.get("json")
            return {
                "number": 1,
                "title": "t",
                "state": "closed",
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": "u",
            }

        monkeypatch.setattr(client, "_request", fake_request)
        client.update_issue(1, state="closed", state_reason="not_planned")

        assert captured["method"] == "PATCH"
        assert captured["json"] == {"state": "closed", "state_reason": "not_planned"}
