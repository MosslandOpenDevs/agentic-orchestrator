"""Tests for the transitional issue-mirror retirement.

Two jobs run from the backlog tick until the follow-up PR deletes this file
with its module: draft plan rows that are not plan documents become
``placeholder``, and open bot issues are closed once with a link to their live
record. Most of the issue pins are about NOT closing: a curated or discussed
issue must survive, and one a person reopened must not be fought.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.db.models import Base, Idea, Plan, Project
from agentic_orchestrator.github_client import GitHubIssue, Labels
from agentic_orchestrator.scheduler import mirror_retirement as mod
from agentic_orchestrator.scheduler.mirror_retirement import (
    LIFECYCLE_SIGNATURE,
    RETIREMENT_MARKER,
    SEED_NOTICE_PREFIX,
    SITE_URL,
    _already_retired,
    _retirement_comment,
    has_human_engagement,
    reclassify_placeholder_plans,
    retire_open_issues,
    run_mirror_retirement,
)


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
        self.close_attempts = []  # numbers, in order, including failures
        self.closed = {}  # number -> state_reason
        self.comments = {}  # number -> [bodies]
        self.label_updates = {}  # number -> labels
        # number -> [{"author_association": ..., "body": ...}]. Defaults to a
        # maintainer comment so an issue carrying `comments=N` is engaged,
        # therefore spared, unless a test says otherwise.
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
        if state == "closed":
            self.close_attempts.append(number)
        if number in self.fail_numbers or number in self.fail_close_numbers:
            raise RuntimeError("boom")
        if state == "closed":
            self.closed[number] = state_reason
        if labels is not None:
            self.label_updates[number] = labels
        return self.open_issues.get(number) or make_issue(number, state="closed")


class Blind(FakeClient):
    def list_comments(self, number, per_page=30):
        raise RuntimeError("403 from GitHub")


def no_pause(_seconds):
    pass


@pytest.fixture()
def factory():
    # StaticPool: an in-memory database lives inside its one connection, so
    # every session from this factory has to share it to see the others' rows.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture()
def session(factory):
    db = factory()
    yield db
    db.close()


def add_idea(session, idea_id, description=None, github_issue_id=None):
    session.add(
        Idea(
            id=idea_id,
            title="t",
            summary="s",
            source_type="debate",
            status="promoted",
            description=description,
            github_issue_id=github_issue_id,
        )
    )
    session.flush()


def add_plan(
    session,
    plan_id,
    idea_id,
    status="draft",
    final_plan=None,
    github_issue_id=None,
    extra_metadata=None,
):
    session.add(
        Plan(
            id=plan_id,
            idea_id=idea_id,
            title="Plan: t",
            status=status,
            final_plan=final_plan,
            github_issue_id=github_issue_id,
            extra_metadata=extra_metadata,
        )
    )
    session.flush()


class TestRetireOpenIssues:
    def test_a_bot_issue_is_closed_not_planned_with_the_exact_comment(self, session):
        """The signature and the marker are literals here on purpose: comments
        already on GitHub carry them, so changing either constant must fail."""
        add_idea(session, "i10", github_issue_id=10)
        client = FakeClient([make_issue(10)])

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["retired"] == 1
        assert client.closed == {10: "not_planned"}
        assert client.comments[10] == [
            "The per-item GitHub issue mirror has been retired, so this issue is closed. "
            "This is not a decision about the idea or plan itself: its live record and "
            "current status are at https://ao.moss.land/ideas/i10\n"
            "\n"
            "<!-- ao:issue-mirror-retired -->\n"
            "_(automated issue lifecycle)_"
        ]

    def test_links_point_at_the_idea_page_or_the_site(self, session):
        """A [Plan] issue links its idea, not its plan: the plan may be a
        placeholder with nothing on its page, which is also why the lookup
        cannot go through PlanRepository."""
        add_idea(session, "idea-a", github_issue_id=10)
        add_idea(session, "idea-b")
        add_plan(session, "plan-b", "idea-b", status="placeholder", github_issue_id=11)
        client = FakeClient([make_issue(10), make_issue(11), make_issue(12)])

        retire_open_issues(client, session, pause=no_pause)

        assert f"are at {SITE_URL}/ideas/idea-a\n" in client.comments[10][0]
        assert f"are at {SITE_URL}/ideas/idea-b\n" in client.comments[11][0]
        assert f"are at {SITE_URL}\n" in client.comments[12][0]

    def test_labels_are_never_sent(self, session):
        """An empty label list would strip curated markers on the way out."""
        client = FakeClient([make_issue(1, labels=[Labels.GENERATED_BY_ORCHESTRATOR, "type:idea"])])

        retire_open_issues(client, session, pause=no_pause)

        assert client.closed == {1: "not_planned"}  # the close happened
        assert client.label_updates == {}

    def test_curated_keep_is_untouchable(self, session):
        issue = make_issue(1, labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.CURATED_KEEP])
        client = FakeClient([issue])

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["spared_curated"] == 1
        assert client.closed == {}

    def test_source_trend_is_untouchable(self, session):
        issue = make_issue(1, labels=[Labels.GENERATED_BY_ORCHESTRATOR, Labels.SOURCE_TREND])
        client = FakeClient([issue])

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["spared_curated"] == 1
        assert client.closed == {}

    def test_non_bot_issue_is_never_touched(self, session):
        client = FakeClient([make_issue(1, labels=["bug"])])

        stats = retire_open_issues(client, session, pause=no_pause)

        assert client.close_attempts == []
        assert sum(stats.values()) == 0

    def test_closed_issue_is_skipped(self, session):
        client = FakeClient([make_issue(1, state="closed")])

        retire_open_issues(client, session, pause=no_pause)

        assert client.close_attempts == []

    def test_a_strangers_comment_does_not_spare_the_issue(self, session):
        """The exemption protects a maintainer's discussion, not any comment.

        Four archived ideas (#3309, #3311, #3312, #3529) were held open because
        a passer-by dropped sales spam or a `/claim` bot reply on them — two of
        those comments byte-identical, 32 seconds apart, same account.
        """
        spammed = make_issue(20, comments=2)
        client = FakeClient(
            [spammed],
            existing_comments={
                20: [
                    {"author_association": "NONE", "body": "Great project! DM me for growth."},
                    {"author_association": "NONE", "body": "Great project! DM me for growth."},
                ]
            },
        )

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["retired"] == 1
        assert client.closed == {20: "not_planned"}

    def test_a_maintainers_comment_spares_the_issue(self, session):
        discussed = make_issue(21, comments=1)
        client = FakeClient(
            [discussed],
            existing_comments={
                21: [{"author_association": "COLLABORATOR", "body": "Worth keeping, see #12."}]
            },
        )

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["spared_engaged"] == 1
        assert client.closed == {}

    def test_the_bots_own_comment_is_not_human_engagement(self, session):
        """The bot comments as an account with standing in this repo, so
        without this check every issue it ever commented on would exempt
        itself."""
        touched = make_issue(22, comments=1)
        client = FakeClient(
            [touched],
            existing_comments={
                22: [{"author_association": "OWNER", "body": f"Closing. {LIFECYCLE_SIGNATURE}"}]
            },
        )

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["retired"] == 1

    def test_a_quote_reply_is_the_person_talking_not_the_bot(self, session):
        """GitHub's "Quote reply" copies the quoted comment verbatim, so a
        maintainer answering the bot carries the lifecycle signature inside
        their own body. A substring test read that as the bot talking to
        itself and closed the issue."""
        issue = make_issue(30, comments=1)
        client = FakeClient(
            [issue],
            existing_comments={
                30: [
                    {
                        "author_association": "OWNER",
                        "body": (
                            f"> Backlog triage re-scored this idea at 8.0/10 — archived. "
                            f"{LIFECYCLE_SIGNATURE}\n\n"
                            "No — keep this open, we are shipping it next sprint."
                        ),
                    }
                ]
            },
        )

        retire_open_issues(client, session, pause=no_pause)

        assert client.closed == {}, "a maintainer's reply was mistaken for the bot's own comment"

    def test_unreadable_comments_spare_the_issue(self, session):
        """A missed close costs one stale issue; a wrong close buries a real
        conversation under a bot's verdict. Fail toward leaving it open."""
        client = Blind([make_issue(23, comments=1)])

        retire_open_issues(client, session, pause=no_pause)

        assert client.close_attempts == []

    def test_an_issue_already_carrying_the_marker_is_left_alone(self, session):
        """Open with the marker means a person reopened it after retirement.
        The bot's comment carries the signature, so engagement alone would
        read it as nobody and close it again every cycle."""
        reopened = make_issue(40, comments=1)
        client = FakeClient(
            [reopened],
            existing_comments={
                40: [{"author_association": "MEMBER", "body": _retirement_comment(SITE_URL)}]
            },
        )

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["already_retired"] == 1
        assert client.close_attempts == []
        assert client.comments == {}

    def test_failed_close_posts_no_comment_and_stays_retryable(self, session):
        # If the comment landed while the close failed, the still-open issue
        # would carry the marker and never be retried. Close-first prevents it.
        client = FakeClient([make_issue(10)], fail_close_numbers={10})

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["errors"] == 1
        assert client.comments == {}
        assert client.closed == {}

        client.fail_close_numbers.clear()
        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["retired"] == 1
        assert client.closed[10] == "not_planned"
        assert RETIREMENT_MARKER in client.comments[10][0]

    def test_github_errors_are_counted_not_raised(self, session):
        client = FakeClient([make_issue(1)], fail_numbers={1})

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["errors"] == 1
        assert stats["retired"] == 0

    def test_the_budget_is_respected_oldest_first(self, session):
        client = FakeClient([make_issue(n) for n in range(10, 0, -1)])

        stats = retire_open_issues(client, session, max_closes_per_run=3, pause=no_pause)

        assert stats["retired"] == 3
        assert sorted(client.closed) == [1, 2, 3]

    def test_three_consecutive_failures_stop_the_pass(self, session):
        client = FakeClient([make_issue(n) for n in range(1, 7)], fail_close_numbers=range(1, 7))

        stats = retire_open_issues(client, session, pause=no_pause)

        assert client.close_attempts == [1, 2, 3]
        assert stats["errors"] == 3

    def test_a_success_resets_the_failure_run(self, session):
        client = FakeClient([make_issue(n) for n in range(1, 7)], fail_close_numbers={1, 2, 4, 5})

        stats = retire_open_issues(client, session, pause=no_pause)

        assert client.close_attempts == [1, 2, 3, 4, 5, 6]
        assert (stats["retired"], stats["errors"]) == (2, 4)

    def test_pause_follows_every_close_attempt(self, session):
        pauses = []
        client = FakeClient(
            [make_issue(1), make_issue(2), make_issue(3, comments=1)], fail_close_numbers={2}
        )

        retire_open_issues(client, session, pause=pauses.append, pause_seconds=1.5)

        assert client.close_attempts == [1, 2]  # 3 is spared: no attempt, no pause
        assert pauses == [1.5, 1.5]


class TestCannotTellMeansLeaveIt:
    """Each guard fails toward leaving the issue open on its own; the sweep
    test above cannot tell which of the two spared the issue."""

    @pytest.mark.parametrize("guard", [has_human_engagement, _already_retired])
    def test_comments_that_raise(self, guard):
        assert guard(Blind(), make_issue(1, comments=1)) is True

    @pytest.mark.parametrize("guard", [has_human_engagement, _already_retired])
    def test_a_blank_answer_despite_a_comment_count(self, guard):
        client = FakeClient(existing_comments={1: []})

        assert guard(client, make_issue(1, comments=1)) is True

    @pytest.mark.parametrize("guard", [has_human_engagement, _already_retired])
    def test_no_comments_needs_no_read(self, guard):
        assert guard(Blind(), make_issue(1, comments=0)) is False


class TestReclassifyPlaceholderPlans:
    def test_each_class_becomes_a_placeholder(self, session):
        add_idea(session, "i1", description="The idea, in full.")
        add_plan(session, "empty-none", "i1", final_plan=None)
        add_plan(session, "empty-blank", "i1", final_plan="  \n")
        add_plan(session, "seed", "i1", final_plan=f"{SEED_NOTICE_PREFIX} Seeded.\n\n## Source")
        add_plan(session, "copy", "i1", final_plan="The idea, in full.")

        counts = reclassify_placeholder_plans(session)

        assert counts == {"empty": 2, "seed": 1, "idea_copy": 1}
        reasons = {
            plan.id: (plan.status, plan.extra_metadata["reclassified_reason"])
            for plan in session.query(Plan)
        }
        assert reasons == {
            "empty-none": ("placeholder", "empty"),
            "empty-blank": ("placeholder", "empty"),
            "seed": ("placeholder", "seed"),
            "copy": ("placeholder", "idea_copy"),
        }

    def test_an_authored_draft_is_untouched(self, session):
        add_idea(session, "i1", description="The idea, in full.")
        add_plan(session, "p1", "i1", final_plan="# Project overview\n\nA real plan.")

        counts = reclassify_placeholder_plans(session)

        assert counts == {"empty": 0, "seed": 0, "idea_copy": 0}
        assert session.query(Plan).one().status == "draft"

    def test_an_approved_plan_is_untouched_even_when_empty(self, session):
        add_idea(session, "i1")
        add_plan(session, "p1", "i1", status="approved", final_plan=None)

        reclassify_placeholder_plans(session)

        assert session.query(Plan).one().status == "approved"

    def test_a_draft_with_a_project_is_untouched(self, session):
        add_idea(session, "i1")
        add_plan(session, "built", "i1", final_plan=None)
        add_plan(session, "unbuilt", "i1", final_plan=None)
        session.add(Project(id="prj", plan_id="built", name="app", status="ready"))
        session.flush()

        counts = reclassify_placeholder_plans(session)

        assert counts["empty"] == 1  # the same fixture without a project does move
        statuses = {plan.id: plan.status for plan in session.query(Plan)}
        assert statuses == {"built": "draft", "unbuilt": "placeholder"}

    def test_an_idea_copy_needs_a_byte_identical_non_blank_description(self, session):
        add_idea(session, "blank", description="")
        add_plan(session, "p-blank", "blank", final_plan="")
        add_idea(session, "near", description="The idea, in full.")
        add_plan(session, "p-near", "near", final_plan="The idea, in full.\n")

        counts = reclassify_placeholder_plans(session)

        assert counts == {"empty": 1, "seed": 0, "idea_copy": 0}
        assert session.query(Plan).filter_by(id="p-near").one().status == "draft"

    def test_a_second_run_finds_nothing(self, session):
        add_idea(session, "i1")
        add_plan(session, "p1", "i1", final_plan=None)
        assert reclassify_placeholder_plans(session)["empty"] == 1

        assert reclassify_placeholder_plans(session) == {"empty": 0, "seed": 0, "idea_copy": 0}

    def test_metadata_is_persisted_next_to_the_old_keys(self, session):
        add_idea(session, "i1")
        add_plan(
            session,
            "p1",
            "i1",
            final_plan=f"{SEED_NOTICE_PREFIX} Seeded.",
            extra_metadata={"promoted_by": "backlog_triage"},
        )
        session.commit()

        reclassify_placeholder_plans(session)
        session.expire_all()

        plan = session.query(Plan).one()
        assert plan.status == "placeholder"
        assert plan.extra_metadata == {
            "promoted_by": "backlog_triage",
            "reclassified_from": "draft",
            "reclassified_reason": "seed",
        }


def _without_pauses(monkeypatch):
    real = mod.retire_open_issues
    monkeypatch.setattr(
        mod,
        "retire_open_issues",
        lambda client, session, **kw: real(client, session, pause=no_pause, **kw),
    )


class TestRunMirrorRetirement:
    def test_disabled_touches_nothing(self, monkeypatch):
        calls = []
        monkeypatch.setattr(mod, "reclassify_placeholder_plans", lambda s: calls.append("db"))
        monkeypatch.setattr(mod, "GitHubClient", lambda: calls.append("github"))

        result = run_mirror_retirement(lambda: calls.append("session"), {"enabled": False})

        assert result == {"skipped": True}
        assert calls == []

    def test_github_being_unavailable_still_commits_the_reclassification(
        self, factory, monkeypatch
    ):
        setup = factory()
        add_idea(setup, "i1")
        add_plan(setup, "p1", "i1", final_plan=None)
        setup.commit()
        setup.close()

        def no_token():
            raise RuntimeError("GITHUB_TOKEN not set")

        monkeypatch.setattr(mod, "GitHubClient", no_token)

        result = run_mirror_retirement(factory, {})

        assert result["plans_reclassified"] == {"empty": 1, "seed": 0, "idea_copy": 0}
        assert "GITHUB_TOKEN" in result["issues"]["error"]
        check = factory()
        assert check.query(Plan).filter_by(id="p1").one().status == "placeholder"
        check.close()

    def test_a_failed_reclassification_still_retires_issues(self, factory, monkeypatch):
        def broken(session):
            raise RuntimeError("no such table: plans")

        client = FakeClient([make_issue(7), make_issue(8)])
        monkeypatch.setattr(mod, "reclassify_placeholder_plans", broken)
        monkeypatch.setattr(mod, "GitHubClient", lambda: client)
        _without_pauses(monkeypatch)

        result = run_mirror_retirement(factory, {"max_closes_per_run": 1})

        assert "no such table" in result["plans_reclassified"]["error"]
        assert result["issues"]["retired"] == 1
        assert client.closed == {7: "not_planned"}


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
