"""GitHub issue lifecycle: pipeline-linked closes and the aging sweep.

The tracker used to be write-only — the orchestrator created an issue per idea
and per plan but nothing ever closed one (0.07% closure rate, 2,866 open issues
by 2026-06). SQLite is the source of truth and GitHub is a visibility mirror,
so the mirror must FOLLOW the pipeline:

- an [Idea] issue closes as ``completed`` once the idea is promoted and its
  plan exists (the [Plan] issue carries the work forward);
- a [Plan] issue closes as ``completed`` once a project has been generated
  from it;
- an [Idea] issue closes as ``not_planned`` once the DB row is ``archived``
  (backlog triage rejects write only to the DB; this loop is where their
  mirror issues actually close, self-healing if GitHub was down at decision
  time) — unless a human engaged with the issue;
- a bot-generated backlog issue that nobody engaged with for
  ``max_age_days`` closes as ``not_planned`` (the DB row is untouched and
  the issue can always be reopened).

Aging never touches issues labeled ``curated:keep`` or ``source:trend``, nor
any issue a person with standing in this repo has commented on. That test used
to be a bare comment count, which handed the exemption to anyone on the
internet: four archived ideas are open permanently because a stranger left
sales spam on them. It is now ``author_association``, and it fails toward
leaving the issue open.

Everything here is best-effort: a GitHub failure logs a warning and moves on;
it must never break the backlog cycle that hosts it.
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from ..github_client import GitHubClient, GitHubIssue, Labels
from ..timeutil import utcnow
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Labels that exempt an issue from the aging sweep. curated:keep is the
# explicit human "keep this open" marker; source:trend marks the settled
# 2026-06 keep-set of trend-generated ideas.
AGING_EXEMPT_LABELS = (Labels.CURATED_KEEP, Labels.SOURCE_TREND)

LIFECYCLE_SIGNATURE = "_(automated issue lifecycle)_"

# `author_association` values that mean the commenter has a real relationship
# with this repository. A drive-by account gets NONE, and that is the whole
# distinction: the exemption exists to protect a maintainer's discussion, not to
# let any stranger pin a bot issue open forever.
ENGAGED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTOR"})


def has_human_engagement(client, issue) -> bool:
    """True if a person with standing in this repo has commented.

    ``issue.comments > 0`` was the test, and it handed the exemption to anyone
    on the internet. Four archived ideas (#3309, #3311, #3312, #3529) are open
    on GitHub permanently because a stranger dropped sales spam or a `/claim`
    bot reply on them — two of those comments were byte-identical, posted 32
    seconds apart, by the same account.

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
            # the issue -- and since the DB row never changes, reopening it just
            # got it closed again on the next four-hour cycle.
            if LIFECYCLE_SIGNATURE not in _without_quotes(comment.get("body") or ""):
                return True

    return False


def _without_quotes(body: str) -> str:
    """Comment body with GitHub quote-reply blocks removed."""
    return "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith(">")
    ).strip()


def _parse_github_timestamp(value: str) -> datetime:
    """GitHub ISO-8601 (``2026-08-05T02:34:59Z``) → naive UTC.

    Naive UTC matches ``timeutil.utcnow()`` so ages can be computed by plain
    subtraction.
    """
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def should_age_out(
    issue: GitHubIssue,
    now: datetime,
    max_age_days: int,
    client=None,
) -> Tuple[bool, str]:
    """Decide whether the aging sweep may close this issue.

    Returns ``(decision, reason)``; the reason is for logs and tests.

    ``client`` is optional so the pure age/label rules stay unit-testable
    without one; when it is absent any comment counts as engagement, which is
    the old, safe-but-too-broad behaviour.
    """
    if issue.state != "open":
        return False, "not open"
    if not issue.has_label(Labels.GENERATED_BY_ORCHESTRATOR):
        return False, "not bot-generated"
    if issue.has_any_label(list(AGING_EXEMPT_LABELS)):
        return False, "exempt label"
    if client is not None:
        if has_human_engagement(client, issue):
            return False, "has discussion"
    elif issue.comments > 0:
        return False, "has discussion"
    age_days = (now - _parse_github_timestamp(issue.created_at)).days
    if age_days < max_age_days:
        return False, f"only {age_days}d old"
    return True, f"{age_days}d without engagement"


def close_idea_issue_for_plan(
    client: GitHubClient,
    idea_issue_number: int,
    plan_issue_number: Optional[int],
    plan_id: str,
) -> bool:
    """Close a promoted idea's issue, pointing at the plan that superseded it.

    Used inline right after plan creation in the debate task. Never raises —
    a lost GitHub call must not fail the pipeline (the reconciliation sweep
    will retry on the next backlog cycle).
    """
    try:
        link = f"#{plan_issue_number}" if plan_issue_number else f"plan `{plan_id}`"
        client.add_comment(
            idea_issue_number,
            f"Promoted to a plan — tracking continues in {link}. {LIFECYCLE_SIGNATURE}",
        )
        client.mark_idea_as_planned(idea_issue_number)
        client.update_issue(idea_issue_number, state="closed", state_reason="completed")
        logger.info(f"Closed idea issue #{idea_issue_number} (promoted to {link})")
        return True
    except Exception as e:
        logger.warning(f"Could not close idea issue #{idea_issue_number}: {e}")
        return False


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
    ``_request`` — one 5xx or rate-limit aborts), the still-open issue now
    has a bot comment that the comment-gated paths (archived reconciliation,
    aging sweep) read as human engagement, permanently blocking every future
    auto-close. Commenting on a closed issue is fine, and a comment lost
    after a successful close costs only context, never a stuck issue.
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


def run_issue_lifecycle(
    client: GitHubClient,
    idea_repo,
    plan_repo,
    project_repo,
    config: Optional[dict] = None,
    now: Optional[datetime] = None,
) -> Dict[str, int]:
    """Reconcile issue states with the DB pipeline, then age out stale issues.

    Runs from the backlog cycle. One ``list_issues`` call feeds both halves,
    so the sweep costs a handful of API requests plus one PATCH per close,
    bounded by ``max_closes_per_run``.
    """
    config = config or {}
    now = now or utcnow()
    max_age_days = int(config.get("max_age_days", 14))
    budget = int(config.get("max_closes_per_run", 50))
    stats = {
        "reconciled_ideas": 0,
        "reconciled_plans": 0,
        "reconciled_archived": 0,
        "aged_out": 0,
        "errors": 0,
    }

    # The list endpoint, not search: the search index silently omits some
    # issues in this repo, and a sweep that cannot see an issue can neither
    # close it nor exempt it.
    open_issues: Dict[int, GitHubIssue] = {
        issue.number: issue
        for issue in client.list_issues(labels=[Labels.GENERATED_BY_ORCHESTRATOR], state="open")
    }
    logger.info(f"Issue lifecycle: {len(open_issues)} open bot issues to consider")

    # --- Pipeline reconciliation: the DB is the truth, issues follow it. ---

    # Promoted ideas whose plan exists: the [Idea] issue's job is done.
    for idea in idea_repo.get_by_status("promoted", limit=500):
        if budget <= 0:
            break
        number = getattr(idea, "github_issue_id", None)
        if not number or number not in open_issues:
            continue
        plans = plan_repo.get_by_idea(idea.id)
        if not plans:
            continue
        plan = plans[0]
        plan_issue = getattr(plan, "github_issue_id", None)
        link = f"#{plan_issue}" if plan_issue else f"plan `{plan.id}`"
        issue = open_issues[number]
        labels = [
            label
            for label in issue.labels
            if label not in (Labels.PROMOTE_TO_PLAN, Labels.STATUS_BACKLOG)
        ]
        labels = sorted(set(labels) | {Labels.STATUS_PLANNED, Labels.PROCESSED_TO_PLAN})
        if _close_issue(
            client,
            issue,
            "completed",
            labels,
            f"Promoted to a plan — tracking continues in {link}. {LIFECYCLE_SIGNATURE}",
        ):
            stats["reconciled_ideas"] += 1
            budget -= 1
            open_issues.pop(number)
        else:
            stats["errors"] += 1

    # Plans whose project has been generated: the [Plan] issue is delivered.
    # Only a SUCCESSFULLY generated project counts — a pending/generating/error
    # project must keep the plan issue open.
    from ..db.models import COMPLETED_PROJECT_STATUSES

    for plan in plan_repo.get_all(limit=500):
        if budget <= 0:
            break
        number = getattr(plan, "github_issue_id", None)
        if not number or number not in open_issues:
            continue
        project = project_repo.get_by_plan(plan.id)
        if project is None or project.status not in COMPLETED_PROJECT_STATUSES:
            continue
        issue = open_issues[number]
        labels = [
            label
            for label in issue.labels
            if label not in (Labels.PROMOTE_TO_DEV, Labels.STATUS_BACKLOG)
        ]
        labels = sorted(set(labels) | {Labels.STATUS_DONE, Labels.PROCESSED_TO_DEV})
        project_name = getattr(project, "name", None) or project.id
        if _close_issue(
            client,
            issue,
            "completed",
            labels,
            f"Project `{project_name}` was generated from this plan. {LIFECYCLE_SIGNATURE}",
        ):
            stats["reconciled_plans"] += 1
            budget -= 1
            open_issues.pop(number)
        else:
            stats["errors"] += 1

    # Archived ideas whose issue is still open: the pipeline rejected them
    # (triage re-score or strike-out), so the mirror follows with the verdict.
    # Human engagement overrides the bot: exempt labels and any comment keep
    # the issue open exactly like the aging sweep would.
    for idea in idea_repo.get_by_status("archived", limit=500):
        if budget <= 0:
            break
        number = getattr(idea, "github_issue_id", None)
        if not number or number not in open_issues:
            continue
        issue = open_issues[number]
        if issue.has_any_label(list(AGING_EXEMPT_LABELS)) or has_human_engagement(client, issue):
            continue
        triage = (getattr(idea, "extra_metadata", None) or {}).get("triage") or {}
        if triage.get("last_score") is not None:
            when = str(triage.get("last_at", ""))[:10]
            reason = triage.get("reason") or "below promotion threshold"
            comment = (
                f"Backlog triage re-scored this idea at {triage['last_score']}/10"
                f"{f' on {when}' if when else ''} — archived ({reason}). "
                f"{LIFECYCLE_SIGNATURE}"
            )
        else:
            comment = f"Archived by the pipeline. {LIFECYCLE_SIGNATURE}"
        labels = [
            label
            for label in issue.labels
            if label not in (Labels.PROMOTE_TO_PLAN, Labels.STATUS_BACKLOG)
        ]
        labels = sorted(set(labels) | {Labels.STATUS_ARCHIVED})
        if _close_issue(client, issue, "not_planned", labels, comment):
            stats["reconciled_archived"] += 1
            budget -= 1
            open_issues.pop(number)
        else:
            stats["errors"] += 1

    # --- Aging sweep: close what nobody has touched, oldest first. ---
    for issue in sorted(open_issues.values(), key=lambda i: i.created_at):
        if budget <= 0:
            break
        decision, reason = should_age_out(issue, now, max_age_days, client=client)
        if not decision:
            continue
        if _close_issue(client, issue, "not_planned"):
            stats["aged_out"] += 1
            budget -= 1
            logger.info(f"Aged out issue #{issue.number} ({reason}): {issue.title[:60]}")
        else:
            stats["errors"] += 1

    logger.info(
        "Issue lifecycle done: "
        f"{stats['reconciled_ideas']} idea(s) reconciled, "
        f"{stats['reconciled_plans']} plan(s) reconciled, "
        f"{stats['reconciled_archived']} archived close(s), "
        f"{stats['aged_out']} aged out, {stats['errors']} error(s)"
    )
    return stats
