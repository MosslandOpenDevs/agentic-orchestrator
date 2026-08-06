"""Backlog triage: the consumer that matches idea production with decisions.

Debates produce ~40 ideas a day but only auto-promoted ones (score >= 7 at
debate time) ever left the backlog; the other ~85% sat in ``scored`` forever
and their GitHub issues waited for the 30-day aging timer. Production had no
matching consumer, so the open-issue count could only climb.

This module is that consumer. Each backlog cycle (every 4h in production) it
re-scores the OLDEST backlog ideas against the trends of today — not the
trends of the debate that produced them — and forces a terminal decision:

- score >= promote threshold → ``promoted`` + a draft plan (a human approves
  it via ``POST /plans/{id}/approve``); the issue lifecycle then closes the
  [Idea] issue as ``completed``;
- score < archive threshold → ``archived``; the issue lifecycle closes the
  issue as ``not_planned`` with the verdict;
- middle band → one strike; at ``max_strikes`` the idea archives anyway
  ("re-evaluated N times, never promotable").

Every idea therefore reaches ``promoted`` or ``archived`` within at most
``max_strikes`` touches, and the steady-state backlog is bounded by
production_rate x days_to_decision instead of growing without limit. Sizing
rule: ``per_run x 6 runs/day`` must exceed daily idea production, or the
queue still grows (25 x 6 = 150 touches/day vs ~40/day produced leaves a
wide margin and drains bursts within two cycles).

Triage writes ONLY to the DB — SQLite is the source of truth. Closing the
mirrored GitHub issues is the issue lifecycle's job (it runs right after
triage in the same backlog cycle and self-heals if GitHub was down).
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..timeutil import utcnow
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Statuses triage may consume. "pending" is the legacy pre-scoring status —
# nothing writes it anymore, but old rows must drain too.
TRIAGE_STATUSES = ("scored", "pending")

TRIAGE_DEFAULTS = {
    "enabled": True,
    "per_run": 25,
    # 6h, not 24h: a whole-day quarantine meant day-one consumption was
    # exactly zero and every idea idled untouchable until D+1. Trends
    # refresh every 2h, so a 6h-old idea already faces a materially
    # different context than the debate that produced it.
    "min_age_hours": 6,
    "max_strikes": 2,
    # Circuit breaker. A wedged Ollama fails every scoring call identically,
    # so grinding through the whole quota only multiplies one dead GPU by
    # `per_run` — 25 ideas x the scoring timeout, consuming nothing and
    # holding the PM2 process "online" for deploy.sh to trip over. After this
    # many consecutive scorer-unavailable results the run gives up and waits
    # for the next tick. Consecutive, not cumulative: an isolated hiccup
    # mid-run resets it, so only a sustained outage trips the breaker.
    "max_consecutive_scorer_failures": 3,
}


def _is_scorer_fallback(score) -> bool:
    """Detect the scorer's transport-error fallback (flat 5.0, no reasoning).

    ``IdeaScorer.score_idea`` swallows LLM failures and returns a neutral
    5.0 score. Treating that as a real "middle band" verdict would hand out
    strikes — and eventually archive ideas — just because Ollama was down.
    A real all-5.0 score with empty reasoning is possible but vanishingly
    rare, and the cost of a false positive is one skipped cycle.
    """
    return (
        score.feasibility == 5.0
        and score.relevance == 5.0
        and score.novelty == 5.0
        and score.impact == 5.0
        and not getattr(score, "reasoning", "")
    )


def _build_trend_context(trend_repo, limit: int = 5) -> str:
    """Current top trends as re-scoring context, best-effort."""
    trends: List = []
    try:
        trends = trend_repo.get_latest(period="24h", limit=limit)
        if not trends:
            trends = trend_repo.get_all(limit=limit)
    except Exception as e:
        logger.warning(f"Triage could not load trends for context: {e}")
    if not trends:
        return "현재 트렌드 정보 없음"
    lines = []
    for trend in trends:
        name = getattr(trend, "name", None) or ""
        desc = (getattr(trend, "description", None) or "")[:200]
        lines.append(f"- {name}: {desc}" if desc else f"- {name}")
    return "현재 주요 트렌드:\n" + "\n".join(lines)


def _merged_triage_metadata(idea, patch: Dict) -> Dict:
    """New extra_metadata dict with the ``triage`` record replaced.

    Must be a NEW dict — the SQLAlchemy JSON column does not track in-place
    mutation.
    """
    metadata = dict(idea.extra_metadata or {})
    triage = dict(metadata.get("triage") or {})
    triage.update(patch)
    metadata["triage"] = triage
    return metadata


async def run_backlog_triage(
    idea_repo,
    plan_repo,
    trend_repo,
    scorer,
    config: Optional[dict] = None,
    now: Optional[datetime] = None,
) -> Dict[str, int]:
    """Re-evaluate the oldest backlog ideas and force terminal decisions.

    DB-only; commits per idea so a crash mid-run keeps finished decisions.
    Never raises — the backlog cycle that hosts it must survive LLM or DB
    hiccups.
    """
    config = {**TRIAGE_DEFAULTS, **(config or {})}
    now = now or utcnow()
    stats = {
        "examined": 0,
        "promoted": 0,
        "archived": 0,
        "strikes": 0,
        "strike_outs": 0,
        "scorer_unavailable": 0,
        "errors": 0,
        "aborted": 0,
    }
    if not config.get("enabled", True):
        return stats

    per_run = int(config.get("per_run", 25))
    min_age = timedelta(hours=float(config.get("min_age_hours", 6)))
    max_strikes = int(config.get("max_strikes", 2))
    max_consecutive_failures = int(config.get("max_consecutive_scorer_failures", 3))

    try:
        candidates = idea_repo.get_oldest_by_status(
            list(TRIAGE_STATUSES),
            created_before=now - min_age,
            limit=per_run,
        )
    except Exception as e:
        logger.error(f"Triage could not load candidates: {e}")
        stats["errors"] += 1
        return stats

    if not candidates:
        logger.info("Backlog triage: nothing old enough to re-evaluate")
        return stats

    context = _build_trend_context(trend_repo)
    logger.info(
        f"Backlog triage: re-evaluating {len(candidates)} idea(s) "
        f"(quota {per_run}, min age {min_age})"
    )

    consecutive_scorer_failures = 0

    for idea in candidates:
        stats["examined"] += 1
        try:
            age_days = max((now - idea.created_at).days, 0) if idea.created_at else 0
            content = (idea.description or idea.summary or "")[:2000]
            score, decision = await scorer.score_and_decide(
                idea_content=f"제목: {idea.title}\n내용: {content}",
                context=(
                    f"백로그 재평가: 이 아이디어는 {age_days}일 전에 생성되어 "
                    f"아직 채택되지 않았다. 오늘의 트렌드 기준으로 다시 평가하라.\n\n{context}"
                ),
            )

            if _is_scorer_fallback(score):
                # LLM unavailable — no verdict, no strike; retry next cycle.
                stats["scorer_unavailable"] += 1
                consecutive_scorer_failures += 1
                logger.warning(f"Triage skipped idea {idea.id}: scorer unavailable")
                if consecutive_scorer_failures >= max_consecutive_failures:
                    stats["aborted"] = 1
                    logger.error(
                        f"Backlog triage aborting run: scorer unavailable for "
                        f"{consecutive_scorer_failures} consecutive ideas — the LLM "
                        f"backend looks down. Skipping the remaining "
                        f"{len(candidates) - stats['examined']} candidate(s); the next "
                        f"cycle retries."
                    )
                    break
                continue

            consecutive_scorer_failures = 0
            prior_strikes = int(((idea.extra_metadata or {}).get("triage") or {}).get("strikes", 0))
            record = {
                "last_score": round(score.total, 2),
                "last_decision": decision,
                "last_at": now.isoformat(),
                "strikes": prior_strikes,
            }

            if decision == "promote":
                _promote(idea_repo, plan_repo, idea, score, record)
                stats["promoted"] += 1
            elif decision == "archive":
                record["reason"] = "re-scored below archive threshold"
                _archive(idea_repo, idea, score, record)
                stats["archived"] += 1
            else:  # middle band → strike
                record["strikes"] = prior_strikes + 1
                if record["strikes"] >= max_strikes:
                    record["reason"] = f"re-evaluated {record['strikes']}x, never reached promotion"
                    _archive(idea_repo, idea, score, record)
                    stats["strike_outs"] += 1
                else:
                    idea_repo.update_fields(
                        idea.id,
                        {
                            "score": score.total,
                            "extra_metadata": _merged_triage_metadata(idea, record),
                        },
                    )
                    stats["strikes"] += 1
                    logger.info(
                        f"Triage strike {record['strikes']}/{max_strikes} for idea "
                        f"{idea.id} (score {score.total:.1f}): {idea.title[:50]}"
                    )
            idea_repo.session.commit()
        except Exception as e:
            stats["errors"] += 1
            logger.warning(f"Triage failed for idea {getattr(idea, 'id', '?')}: {e}")
            try:
                idea_repo.session.rollback()
            except Exception:
                pass

    logger.info(
        "Backlog triage done: "
        f"{stats['promoted']} promoted, {stats['archived']} archived, "
        f"{stats['strike_outs']} struck out, {stats['strikes']} strike(s) recorded, "
        f"{stats['scorer_unavailable']} scorer-unavailable, {stats['errors']} error(s)"
        + (" [ABORTED: LLM backend down]" if stats["aborted"] else "")
    )
    return stats


def _archive(idea_repo, idea, score, record: Dict) -> None:
    """Terminal reject. The issue lifecycle closes the mirror issue next."""
    idea_repo.update_fields(
        idea.id,
        {
            "status": "archived",
            "score": score.total,
            "extra_metadata": _merged_triage_metadata(idea, record),
        },
    )
    logger.info(
        f"Triage archived idea {idea.id} (score {score.total:.1f}, "
        f"{record.get('reason', '')}): {idea.title[:50]}"
    )


def _promote(idea_repo, plan_repo, idea, score, record: Dict) -> None:
    """Terminal accept: promoted + a DRAFT plan for human approval.

    Unlike debate-time promotion this never auto-approves and never creates a
    [Plan] GitHub issue — the plan shows up in the pending-approval queue
    (``GET /plans/pending-approval``) and the existing lifecycle close of the
    [Idea] issue links to it by plan id.
    """
    plan_id = str(uuid.uuid4())[:8]
    title = f"Plan: {(idea.title or '')[:200]}"
    title_ko = f"Plan: {(idea.title_ko or idea.title or '')[:200]}"
    seed = idea.description or idea.summary or ""
    plan_repo.create(
        {
            "id": plan_id,
            "idea_id": idea.id,
            "debate_session_id": idea.debate_session_id,
            "title": title,
            "title_ko": title_ko,
            "version": 1,
            "status": "draft",
            "final_plan": seed,
            "final_plan_ko": idea.description_ko or idea.summary_ko,
            "extra_metadata": {
                "auto_promoted": False,
                "promoted_by": "backlog_triage",
                "promotion_score": score.total,
                "auto_approved": False,
            },
        }
    )
    idea_repo.update_fields(
        idea.id,
        {
            "status": "promoted",
            "score": score.total,
            "extra_metadata": _merged_triage_metadata(idea, record),
        },
    )
    logger.info(
        f"Triage promoted idea {idea.id} (score {score.total:.1f}) → draft plan "
        f"{plan_id}: {idea.title[:50]}"
    )
