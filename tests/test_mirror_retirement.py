"""Tests for the transitional issue-mirror retirement.

Two jobs run from the backlog tick until the follow-up PR deletes this file
with its module: draft plan rows that are not plan documents become
``placeholder``, and open bot issues are closed once with a link to their live
record. Most of the issue pins are about NOT closing: a curated or discussed
issue must survive, and one a person reopened must not be fought.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.db.models import Base, Idea, Plan, Project
from agentic_orchestrator.github_client import GitHubIssue, Labels
from agentic_orchestrator.scheduler import mirror_retirement as mod
from agentic_orchestrator.scheduler import tasks as tasks_mod
from agentic_orchestrator.scheduler.mirror_retirement import (
    LIFECYCLE_SIGNATURE,
    RETIREMENT_MARKER,
    SITE_URL,
    _retirement_comment,
    reclassify_placeholder_plans,
    retire_open_issues,
    run_mirror_retirement,
)

# A seed draft as backlog triage wrote it into production rows. A literal, so a
# SEED_NOTICE_PREFIX that stops matching those rows fails here.
SEED_BODY = (
    "> **Not an authored plan yet.** Backlog triage promoted the idea below on a "
    "re-score and seeded this draft from it. The six required sections still have "
    "to be written before there is anything here to approve.\n\n## Source idea\n\n"
    "The idea, rendered."
)


def make_issue(
    number: int,
    labels: list = None,
    comments: int = 0,
    state: str = "open",
) -> GitHubIssue:
    return GitHubIssue(
        number=number,
        title=f"[Idea] Issue {number}",
        body="",
        state=state,
        labels=labels if labels is not None else [Labels.GENERATED_BY_ORCHESTRATOR],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        html_url=f"https://github.com/x/y/issues/{number}",
        comments=comments,
    )


class FakeClient:
    """Duck-typed GitHubClient recording every write request.

    ``fail_close_numbers`` fails ``update_issue`` for those issues — the window
    where a comment could land on an issue that then stays open.
    ``fail_comment_numbers`` fails only ``add_comment``.
    """

    def __init__(
        self,
        open_issues=None,
        fail_close_numbers=(),
        fail_comment_numbers=(),
        existing_comments=None,
    ):
        self.open_issues = {i.number: i for i in (open_issues or [])}
        self.fail_close_numbers = set(fail_close_numbers)
        self.fail_comment_numbers = set(fail_comment_numbers)
        self.close_attempts = []  # numbers, in order, including failures
        self.closed = {}  # number -> state_reason
        self.comments = {}  # number -> [bodies]
        self.label_updates = {}  # number -> labels
        self.events = []  # ("close" | "comment", number) per write, including failures
        self.client_closed = False
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
        self.events.append(("comment", number))
        if number in self.fail_comment_numbers:
            raise RuntimeError("boom")
        self.comments.setdefault(number, []).append(body)
        return {}

    def update_issue(self, number, state=None, state_reason=None, labels=None, **kw):
        if state == "closed":
            self.close_attempts.append(number)
            self.events.append(("close", number))
        if number in self.fail_close_numbers:
            raise RuntimeError("boom")
        if state == "closed":
            self.closed[number] = state_reason
        if labels is not None:
            self.label_updates[number] = labels
        return self.open_issues.get(number) or make_issue(number, state="closed")

    def close(self):
        self.client_closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()


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
        """An empty label list would strip the issue's labels on the way out."""
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

    @pytest.mark.parametrize(
        "client",
        [
            Blind([make_issue(23, comments=1)]),
            FakeClient([make_issue(23, comments=1)], existing_comments={23: []}),
        ],
        ids=["the-read-raises", "a-blank-answer-to-a-comment-count"],
    )
    def test_unreadable_comments_spare_the_issue(self, session, client):
        """A missed close costs one stale issue; a wrong close buries a real
        conversation under a bot's verdict. GitHubClient.list_comments answers
        a failed request with [], so a blank answer despite a count is one."""
        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["spared_unreadable"] == 1
        assert stats["already_retired"] == 0
        assert client.close_attempts == []

    def test_an_issue_without_comments_needs_no_read(self, session):
        client = Blind([make_issue(24, comments=0)])

        stats = retire_open_issues(client, session, pause=no_pause)

        assert stats["retired"] == 1

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

    def test_three_comment_failures_in_a_row_stop_the_pass(self, session):
        """A limit that rejects only comments must not close every remaining
        issue without its link: a closed issue is never listed again, so its
        comment is never retried."""
        client = FakeClient([make_issue(n) for n in range(1, 7)], fail_comment_numbers=range(1, 7))

        stats = retire_open_issues(client, session, pause=no_pause)

        assert (stats["retired"], stats["uncommented"]) == (3, 3)
        assert client.close_attempts == [1, 2, 3]
        assert sorted(client.closed) == [1, 2, 3]
        assert client.comments == {}

    def test_a_success_resets_the_failure_run(self, session):
        client = FakeClient([make_issue(n) for n in range(1, 7)], fail_close_numbers={1, 2, 4, 5})

        stats = retire_open_issues(client, session, pause=no_pause)

        assert client.close_attempts == [1, 2, 3, 4, 5, 6]
        assert (stats["retired"], stats["errors"]) == (2, 4)

    def test_only_a_commented_issue_resets_the_failure_run(self, session):
        """Two comment failures are forgiven by a fully successful issue (3).
        A close that succeeds without its comment (5) forgives nothing, so the
        failed close after it (6) is the third in a row."""
        client = FakeClient(
            [make_issue(n) for n in range(1, 8)],
            fail_close_numbers={4, 6},
            fail_comment_numbers={1, 2, 5},
        )

        stats = retire_open_issues(client, session, pause=no_pause)

        assert client.close_attempts == [1, 2, 3, 4, 5, 6]
        assert (stats["retired"], stats["uncommented"], stats["errors"]) == (4, 3, 2)

    def test_a_pause_follows_every_write(self, session):
        """GitHub asks for a second between mutating requests: after the close
        and after the comment, whether or not each succeeded."""
        client = FakeClient(
            [make_issue(1), make_issue(2), make_issue(3), make_issue(4, comments=1)],
            fail_close_numbers={2},
            fail_comment_numbers={3},
        )

        retire_open_issues(
            client, session, pause=lambda s: client.events.append(("pause", s)), pause_seconds=1.5
        )

        assert client.events == [
            ("close", 1),
            ("pause", 1.5),
            ("comment", 1),
            ("pause", 1.5),
            ("close", 2),
            ("pause", 1.5),
            ("close", 3),
            ("pause", 1.5),
            ("comment", 3),
            ("pause", 1.5),
        ]  # 4 is spared: no write, no pause


class TestReclassifyPlaceholderPlans:
    def test_each_class_becomes_a_placeholder(self, session):
        add_idea(session, "i1", description="The idea, in full.")
        add_plan(session, "empty-none", "i1", final_plan=None)
        add_plan(session, "empty-blank", "i1", final_plan="  \n")
        add_plan(session, "seed", "i1", final_plan=SEED_BODY)
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
            final_plan=SEED_BODY,
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
        assert client.client_closed, "the client must be closed after the pass"


class TestTheBacklogTickRunsTheRetirement:
    """The retirement must not depend on triage. Triage can be switched off, and
    an LLM outage makes it raise; neither may hold the transition back.
    """

    def _process_backlog(self, monkeypatch, tmp_path, triage):
        import agentic_orchestrator.db as db_pkg
        import agentic_orchestrator.llm as llm_pkg

        engine = create_engine(f"sqlite:///{tmp_path / 'backlog.db'}")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        monkeypatch.setattr(
            db_pkg, "get_database", lambda: SimpleNamespace(get_session=session_factory)
        )

        block = {"enabled": True, "max_closes_per_run": 7}
        monkeypatch.setattr(
            tasks_mod,
            "_load_backlog_config",
            lambda: {"triage": triage, "mirror_retirement": block},
        )

        routers = []

        def backend_down():
            routers.append("constructed")
            raise RuntimeError("LLM backend down")

        monkeypatch.setattr(llm_pkg, "HybridLLMRouter", backend_down)

        calls = []

        def record(factory, config):
            calls.append((factory, config))
            return {}

        monkeypatch.setattr(mod, "run_mirror_retirement", record)

        tasks_mod._process_backlog()

        return calls, routers, [(session_factory, block)]

    def test_it_runs_with_triage_switched_off(self, monkeypatch, tmp_path):
        calls, routers, expected = self._process_backlog(monkeypatch, tmp_path, {"enabled": False})

        assert routers == [], "triage must really have been off"
        assert calls == expected

    def test_it_runs_when_triage_raises(self, monkeypatch, tmp_path):
        calls, routers, expected = self._process_backlog(monkeypatch, tmp_path, {"enabled": True})

        assert routers, "triage must really have been attempted"
        assert calls == expected
