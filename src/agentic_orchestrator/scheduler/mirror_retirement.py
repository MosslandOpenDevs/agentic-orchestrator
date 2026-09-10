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
  ``curated:keep`` or ``source:trend``, any issue a person with standing in
  this repo has commented on, and any issue whose comments cannot be read stay
  open.

It runs from the backlog tick rather than as a manual command so the transition
needs no step on the server: the deploy that ships it is what runs it. Both
steps are idempotent, so repeating them every tick is harmless.

The follow-up PR, once the production transition has been verified, removes
all of this:

- this module;
- tests/test_mirror_retirement.py, which holds every transitional test,
  including the backlog-tick wiring;
- the ``backlog.mirror_retirement`` block in config.yaml;
- the TRANSITIONAL call in ``scheduler/tasks.py`` ``_process_backlog``;
- ``GitHubClient.list_issues``, ``GitHubClient.list_comments``, the
  ``state_reason`` parameter of ``GitHubClient.update_issue`` and the
  ``GitHubIssue.comments`` field with its parsing -- this module is the only
  caller of each -- with their tests in tests/test_backlog.py, each marked
  "Deleted with"; ``TestClientEndpoints`` is empty after that and goes too;
- in tests/test_issue_mirror_retired.py, ``users <= {"mirror_retirement.py"}``
  tightens to ``users == set()``, and the module docstring and the name of
  ``test_only_the_transitional_module_reaches_github`` stop naming this module;
- every mention of the transition outside the CHANGELOG, superseded by a
  CHANGELOG entry recording the measured outcome. This must come back empty:
  ``git grep -nE 'mirror_retirement|mirror retirement|issue-mirror retirement|전환 작업|전환용' -- ':!CHANGELOG*'``

Everything here is best-effort: a failure logs a warning and moves on; it must
never break the backlog cycle that hosts it.
"""

import time
from typing import Any, Callable, Dict, Optional

from ..db.models import Idea, Plan, PlanStatus
from ..github_client import GitHubClient, Labels
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

# Carried by the retired lifecycle's comments and by this module's own. The
# bot comments as an account with standing in this repo, so this string is how
# the engagement check discounts those comments; it must not change. Other bot
# comments -- the 2026-01 debate records on #12, anything the manual
# `ao backlog` CLI posts -- are unsigned and count as engagement.
LIFECYCLE_SIGNATURE = "_(automated issue lifecycle)_"

# Invisible on GitHub. An open issue that carries it was closed here and then
# reopened by a person; closing it again every backlog cycle would fight them.
RETIREMENT_MARKER = "<!-- ao:issue-mirror-retired -->"

# `author_association` values that mean the commenter has a real relationship
# with this repository. A drive-by account gets NONE, and that is the whole
# distinction: the exemption exists to protect a maintainer's discussion, not to
# let any stranger pin a bot issue open forever.
ENGAGED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTOR"})

# Issues in a row whose close or closing comment failed mean a rate limit or an
# outage, not bad luck with individual issues. GitHub warns that continuing to
# send requests while limited may get an integration banned, so the pass stops
# instead. A failed comment counts: a limit that rejects only comments would
# otherwise close every remaining issue without its link, for good.
MAX_CONSECUTIVE_ERRORS = 3


def _read_comments(client, issue) -> Optional[list]:
    """The issue's comments; ``[]`` without a request when it has none.

    None means "cannot tell": the read raised, or the issue counts comments and
    none came back (``GitHubClient.list_comments`` answers a failed request with
    ``[]``). The caller leaves such an issue open. A missed close costs one
    stale issue; a wrong close buries a real conversation under a bot's verdict.
    """
    if issue.comments <= 0:
        return []
    try:
        comments = client.list_comments(issue.number)
    except Exception as e:
        logger.warning(f"Could not read comments on #{issue.number}: {e}")
        return None
    return comments or None


def _is_retired(comments: list) -> bool:
    """True if a comment carries the retirement marker."""
    return any(RETIREMENT_MARKER in (comment.get("body") or "") for comment in comments)


def _is_engaged(comments: list) -> bool:
    """True if a person with standing in this repo has commented.

    Any comment used to count, which handed the exemption to anyone on the
    internet: four archived ideas (#3309, #3311, #3312, #3529) were held open by
    a stranger's sales spam or a `/claim` bot reply.
    """
    for comment in comments:
        association = (comment.get("author_association") or "").upper()
        if association in ENGAGED_ASSOCIATIONS:
            # The bot's signed comments carry an association with standing
            # too, so they would otherwise exempt every issue it commented on.
            # Test what the person WROTE, not what they quoted: GitHub's "Quote
            # reply" copies the quoted comment verbatim, so a maintainer
            # answering the bot carries the signature inside their own body.
            if LIFECYCLE_SIGNATURE not in _without_quotes(comment.get("body") or ""):
                return True
    return False


def _without_quotes(body: str) -> str:
    """Comment body with GitHub quote-reply blocks removed."""
    return "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith(">")
    ).strip()


def _close_and_comment(
    client, number: int, comment: str, pause: Callable[[float], Any], pause_seconds: float
) -> str:
    """Close an issue as ``not_planned``, then comment; ``pause`` after each request.

    Returns ``"commented"``, ``"closed"`` (the comment failed) or ``"failed"``
    (the close failed, so nothing was commented).

    The close goes FIRST. A marker comment on an issue whose close then fails
    (``_request`` has no retry: one 5xx or rate limit aborts) would leave it
    open, and every later pass would skip it as already retired.
    """
    try:
        client.update_issue(number, state="closed", state_reason="not_planned")
    except Exception as e:
        logger.warning(f"Could not close issue #{number}: {e}")
        return "failed"
    finally:
        pause(pause_seconds)
    try:
        client.add_comment(number, comment)
    except Exception as e:
        logger.warning(f"Closed issue #{number} but could not add the closing comment: {e}")
        return "closed"
    finally:
        pause(pause_seconds)
    return "commented"


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

    ``pause`` runs after every write request -- the close and the comment, each
    whether it succeeded or not -- because GitHub's REST guidance is to wait at
    least a second between mutating requests. The pass stops after
    ``MAX_CONSECUTIVE_ERRORS`` issues in a row whose close or comment failed.

    ``retired`` counts closed issues, ``uncommented`` those among them whose
    comment failed, and ``errors`` failed closes.
    """
    budget = int(max_closes_per_run)
    stats = {
        "retired": 0,
        "uncommented": 0,
        "errors": 0,
        "spared_curated": 0,
        "spared_engaged": 0,
        "spared_unreadable": 0,
        "already_retired": 0,
    }
    consecutive_failures = 0

    # The list endpoint, not search: search has omitted issues in this repo
    # (CHANGELOG 0.6.15). Neither is complete -- both omitted open issue #36 on
    # 2026-09-10 -- and a sweep that cannot see an issue can neither close it
    # nor exempt it.
    issues = client.list_issues(labels=[Labels.GENERATED_BY_ORCHESTRATOR], state="open")

    for issue in sorted(issues, key=lambda i: i.number):
        if issue.state != "open" or not issue.has_label(Labels.GENERATED_BY_ORCHESTRATOR):
            continue
        if issue.has_any_label(list(EXEMPT_LABELS)):
            stats["spared_curated"] += 1
            continue
        comments = _read_comments(client, issue)
        if comments is None:
            stats["spared_unreadable"] += 1
            continue
        if _is_retired(comments):
            stats["already_retired"] += 1
            continue
        if _is_engaged(comments):
            stats["spared_engaged"] += 1
            continue
        if budget <= 0:
            break

        comment = _retirement_comment(_live_record_link(session, issue.number))
        outcome = _close_and_comment(client, issue.number, comment, pause, pause_seconds)
        if outcome == "failed":
            stats["errors"] += 1
        else:
            stats["retired"] += 1
            budget -= 1
        if outcome == "closed":
            stats["uncommented"] += 1

        if outcome == "commented":
            consecutive_failures = 0
            continue
        consecutive_failures += 1
        if consecutive_failures >= MAX_CONSECUTIVE_ERRORS:
            logger.warning(
                f"Issue mirror retirement stopped after {consecutive_failures} issues in a row "
                "whose close or comment failed (rate limit or outage); the rest wait for the "
                "next backlog cycle"
            )
            break

    logger.info(
        "Issue mirror retirement: "
        f"{stats['retired']} closed ({stats['uncommented']} without the comment), "
        f"{stats['errors']} failed to close, {stats['spared_curated']} spared by label, "
        f"{stats['spared_engaged']} spared by discussion, "
        f"{stats['spared_unreadable']} spared as unreadable, "
        f"{stats['already_retired']} already retired"
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


def run_mirror_retirement(session_factory, config: Optional[dict] = None) -> Dict[str, Any]:
    """Reclassify placeholder plans, then retire open issues. Never raises.

    Each step gets its own session and its own ``try``: the DB step must not
    depend on GitHub being reachable or credentialed, and a failed DB step
    must not stop the issues from closing.
    """
    config = config or {}
    if not config.get("enabled", True):
        return {"skipped": True}

    def retire(session) -> Dict[str, int]:
        with GitHubClient() as client:
            return retire_open_issues(
                client, session, max_closes_per_run=config.get("max_closes_per_run", 100)
            )

    return {
        "plans_reclassified": _run_step(
            "Placeholder plan reclassification", session_factory, reclassify_placeholder_plans
        ),
        "issues": _run_step("Issue mirror retirement", session_factory, retire),
    }
