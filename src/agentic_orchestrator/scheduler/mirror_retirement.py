"""TRANSITIONAL: finish retiring the per-item GitHub issue mirror.

The orchestrator no longer mirrors ideas and plans into GitHub issues, and it
writes a plan row only where a plan document exists. Two things written under
the old rules are still live, and this module settles both:

- ``reclassify_placeholder_plans`` marks draft plan rows with no plan document
  behind them -- empty, a triage seed, or a byte copy of the idea's
  description -- as ``placeholder``. The row stays; PlanRepository leaves it
  out of plan lists and counts.
- ``retire_open_issues`` closes each open bot issue once, as ``not_planned``,
  with a comment linking the idea's live page on the site. Issues labeled
  ``curated:keep`` or ``source:trend``, and any issue a person with standing in
  this repo has commented on, stay open.

It runs from the backlog tick rather than as a manual command so the transition
needs no step on the server: the deploy that ships it is what runs it. Both
steps are idempotent, so repeating them every tick is harmless.

Delete this module, tests/test_mirror_retirement.py, the
``backlog.mirror_retirement`` config block and its call site in
``scheduler/tasks.py`` in the follow-up PR, once the production transition has
been verified.

Everything here is best-effort: a failure logs a warning and moves on; it must
never break the backlog cycle that hosts it.
"""

import time
from typing import Any, Callable, Dict, Optional

from ..db.models import Idea, Plan, PlanStatus
from ..github_client import GitHubClient, GitHubIssue, Labels
from ..utils.logging import get_logger

logger = get_logger(__name__)

SITE_URL = "https://ao.moss.land"

# The opening of the notice backlog triage put at the top of the drafts it
# seeded from an idea. Copied, not imported: those rows outlive the code that
# wrote them.
SEED_NOTICE_PREFIX = "> **Not an authored plan yet.**"

# Labels that exempt an issue from retirement. curated:keep is the explicit
# human "keep this open" marker; source:trend marks the settled 2026-06
# keep-set of trend-generated ideas.
EXEMPT_LABELS = (Labels.CURATED_KEEP, Labels.SOURCE_TREND)

# Carried by every comment the bot posts. The bot comments as an account with
# standing in this repo, so this string is how has_human_engagement tells its
# comments from a person's -- including the ones already on GitHub, which is
# why it must not change.
LIFECYCLE_SIGNATURE = "_(automated issue lifecycle)_"

# Invisible on GitHub. An open issue that carries it was closed here and then
# reopened by a person; closing it again every backlog cycle would fight them.
RETIREMENT_MARKER = "<!-- ao:issue-mirror-retired -->"

# `author_association` values that mean the commenter has a real relationship
# with this repository. A drive-by account gets NONE, and that is the whole
# distinction: the exemption exists to protect a maintainer's discussion, not to
# let any stranger pin a bot issue open forever.
ENGAGED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTOR"})

# Failed closes in a row mean a rate limit or an outage, not bad luck with
# individual issues. GitHub warns that continuing to send requests while
# limited may get an integration banned, so the pass stops instead.
MAX_CONSECUTIVE_ERRORS = 3


def has_human_engagement(client, issue) -> bool:
    """True if a person with standing in this repo has commented.

    ``issue.comments > 0`` was the test, and it handed the exemption to anyone
    on the internet. Four archived ideas (#3309, #3311, #3312, #3529) were held
    open on GitHub because a stranger dropped sales spam or a `/claim` bot reply
    on them — two of those comments were byte-identical, posted 32 seconds
    apart, by the same account.

    Fails toward leaving the issue open: if the comments cannot be read, or the
    API answers with something unexpected, the issue is treated as engaged. A
    missed close costs one stale issue; a wrong close buries a real
    conversation under a bot's verdict.
    """
    if issue.comments <= 0:
        return False

    try:
        comments = client.list_comments(issue.number)
    except Exception as e:
        # Includes a client that has no `list_comments` at all. Everything in
        # this module is best-effort, and "cannot tell" must mean "leave it".
        logger.warning(f"Could not read comments on #{issue.number}, sparing it: {e}")
        return True

    if not comments:
        # `comments > 0` but nothing came back: an error, or a permission
        # problem. Do not close on a blank answer.
        return True

    for comment in comments:
        association = (comment.get("author_association") or "").upper()
        if association in ENGAGED_ASSOCIATIONS:
            # Our own lifecycle comments carry the bot's association, so they
            # would otherwise exempt every issue the bot has ever commented on.
            # Test what the person WROTE, not what they quoted: GitHub's "Quote
            # reply" copies the quoted comment verbatim, so a maintainer
            # answering the bot's verdict carries the signature inside their own
            # body. A bare `in` read that as the bot talking to itself and closed
            # the issue.
            if LIFECYCLE_SIGNATURE not in _without_quotes(comment.get("body") or ""):
                return True

    return False


def _without_quotes(body: str) -> str:
    """Comment body with GitHub quote-reply blocks removed."""
    return "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith(">")
    ).strip()


def _already_retired(client, issue) -> bool:
    """True if a comment on this issue carries the retirement marker.

    Fails toward leaving the issue open, like ``has_human_engagement``:
    comments that cannot be read count as retired.
    """
    if issue.comments <= 0:
        return False

    try:
        comments = client.list_comments(issue.number)
    except Exception as e:
        logger.warning(f"Could not read comments on #{issue.number}, leaving it open: {e}")
        return True

    if not comments:
        return True

    return any(RETIREMENT_MARKER in (comment.get("body") or "") for comment in comments)


def _close_issue(
    client: GitHubClient,
    issue: GitHubIssue,
    state_reason: str,
    labels: Optional[list] = None,
    comment: Optional[str] = None,
) -> bool:
    """Best-effort close with optional label replacement and comment.

    The close PATCH goes FIRST. Commenting first would poison the retry: if
    the comment lands and the close then fails (GitHub has no retry in
    ``_request`` — one 5xx or rate-limit aborts), the still-open issue carries
    the retirement marker, and every later pass skips it as already retired.
    Commenting on a closed issue is fine, and a comment lost after a successful
    close costs only context, never a stuck issue.
    """
    try:
        client.update_issue(
            issue.number,
            state="closed",
            state_reason=state_reason,
            labels=labels,
        )
    except Exception as e:
        logger.warning(f"Could not close issue #{issue.number}: {e}")
        return False
    if comment:
        try:
            client.add_comment(issue.number, comment)
        except Exception as e:
            logger.warning(
                f"Closed issue #{issue.number} but could not add the closing comment: {e}"
            )
    return True


def _live_record_link(session, number: int) -> str:
    """The site page that is the live record behind an issue.

    The idea page for both kinds of issue: a [Plan] issue may point at a
    placeholder, whose own page has nothing on it. Raw queries for the same
    reason -- PlanRepository leaves placeholders out.
    """
    idea_id = session.query(Idea.id).filter(Idea.github_issue_id == number).limit(1).scalar()
    if idea_id is None:
        idea_id = (
            session.query(Plan.idea_id).filter(Plan.github_issue_id == number).limit(1).scalar()
        )
    return f"{SITE_URL}/ideas/{idea_id}" if idea_id else SITE_URL


def _retirement_comment(link: str) -> str:
    return (
        "The per-item GitHub issue mirror has been retired, so this issue is closed. "
        "This is not a decision about the idea or plan itself: its live record and "
        f"current status are at {link}\n\n{RETIREMENT_MARKER}\n{LIFECYCLE_SIGNATURE}"
    )


def retire_open_issues(
    client,
    session,
    max_closes_per_run: int = 100,
    pause: Callable[[float], Any] = time.sleep,
    pause_seconds: float = 1.0,
) -> Dict[str, int]:
    """Close each open bot issue once, oldest first, linking its live record.

    ``pause`` runs after every close attempt: GitHub's REST guidance is to wait
    at least a second between mutating requests, and a close here is a PATCH
    followed by a comment POST.
    """
    budget = int(max_closes_per_run)
    stats = {
        "retired": 0,
        "spared_curated": 0,
        "spared_engaged": 0,
        "already_retired": 0,
        "errors": 0,
    }
    consecutive_errors = 0

    # The list endpoint, not search: the search index silently omits some
    # issues in this repo, and a sweep that cannot see an issue can neither
    # close it nor exempt it.
    issues = client.list_issues(labels=[Labels.GENERATED_BY_ORCHESTRATOR], state="open")

    for issue in sorted(issues, key=lambda i: i.number):
        if budget <= 0:
            break
        if issue.state != "open" or not issue.has_label(Labels.GENERATED_BY_ORCHESTRATOR):
            continue
        if issue.has_any_label(list(EXEMPT_LABELS)):
            stats["spared_curated"] += 1
            continue
        if _already_retired(client, issue):
            stats["already_retired"] += 1
            continue
        if has_human_engagement(client, issue):
            stats["spared_engaged"] += 1
            continue

        comment = _retirement_comment(_live_record_link(session, issue.number))
        # labels=None leaves the labels alone. An empty list would strip every
        # label on the way out, curated markers included.
        closed = _close_issue(client, issue, "not_planned", labels=None, comment=comment)
        pause(pause_seconds)
        if closed:
            stats["retired"] += 1
            budget -= 1
            consecutive_errors = 0
            continue

        stats["errors"] += 1
        consecutive_errors += 1
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            logger.warning(
                f"Issue mirror retirement stopped after {consecutive_errors} failed closes "
                "in a row (rate limit or outage); the rest wait for the next backlog cycle"
            )
            break

    logger.info(
        "Issue mirror retirement: "
        f"{stats['retired']} closed, {stats['spared_curated']} spared by label, "
        f"{stats['spared_engaged']} spared by discussion, "
        f"{stats['already_retired']} already retired, {stats['errors']} error(s)"
    )
    return stats


def _placeholder_reason(final_plan: Optional[str], description: Optional[str]) -> Optional[str]:
    """Which kind of non-plan a draft's body is, or None for an authored plan."""
    if final_plan is None or not final_plan.strip():
        return "empty"
    if final_plan.startswith(SEED_NOTICE_PREFIX):
        return "seed"
    if final_plan == description:
        # Byte-identical, and non-blank by now, so a blank description can
        # never match.
        return "idea_copy"
    return None


def reclassify_placeholder_plans(session) -> Dict[str, int]:
    """Mark draft plan rows that are not plan documents as ``placeholder``.

    A draft with a project row is left alone whatever its body: something was
    built from it. Commits once at the end; the caller owns the session.
    Idempotent, because a placeholder no longer matches ``draft``.
    """
    counts = {"empty": 0, "seed": 0, "idea_copy": 0}
    rows = (
        session.query(Plan, Idea.description)
        .outerjoin(Idea, Idea.id == Plan.idea_id)
        .filter(Plan.status == PlanStatus.DRAFT.value, ~Plan.projects.any())
        .all()
    )
    for plan, description in rows:
        reason = _placeholder_reason(plan.final_plan, description)
        if reason is None:
            continue
        # A new dict: the JSON column does not track in-place mutation, so
        # changes to the old one would be dropped at commit.
        plan.extra_metadata = {
            **(plan.extra_metadata or {}),
            "reclassified_from": plan.status,
            "reclassified_reason": reason,
        }
        plan.status = PlanStatus.PLACEHOLDER.value
        counts[reason] += 1

    session.commit()
    logger.info(
        "Placeholder plans reclassified from draft: "
        f"{counts['empty']} empty, {counts['seed']} seed, {counts['idea_copy']} idea copy"
    )
    return counts


def _run_step(name: str, session_factory, step: Callable[[Any], Dict[str, Any]]) -> Dict[str, Any]:
    """Run one step in its own session. A failure is logged and returned, never raised."""
    session = None
    try:
        session = session_factory()
        return step(session)
    except Exception as e:
        logger.warning(f"{name} failed: {e}")
        if session is not None:
            try:
                session.rollback()
            except Exception:
                pass
        return {"error": str(e)}
    finally:
        if session is not None:
            session.close()


def _retire_with_new_client(session, max_closes_per_run) -> Dict[str, int]:
    client = GitHubClient()
    try:
        return retire_open_issues(client, session, max_closes_per_run=max_closes_per_run)
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def run_mirror_retirement(session_factory, config: Optional[dict] = None) -> Dict[str, Any]:
    """Reclassify placeholder plans, then retire open issues. Never raises.

    Each step gets its own session and its own ``try``: the DB step must not
    depend on GitHub being reachable or credentialed, and a failed DB step
    must not stop the issues from closing.
    """
    config = config or {}
    if not config.get("enabled", True):
        return {"skipped": True}

    return {
        "plans_reclassified": _run_step(
            "Placeholder plan reclassification", session_factory, reclassify_placeholder_plans
        ),
        "issues": _run_step(
            "Issue mirror retirement",
            session_factory,
            lambda session: _retire_with_new_client(session, config.get("max_closes_per_run", 100)),
        ),
    }
