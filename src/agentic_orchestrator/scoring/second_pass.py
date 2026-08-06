"""Second-pass review: a capable model confirms what the small one promoted.

The pipeline had an inversion. Debates run on gpt-5.4-mini, but the gate that
decides whether a debate's output becomes a plan — and then a scaffolded
project — was a local gemma3:4b re-score. The strong model produced the work
and the weak model graded it, which showed up exactly as you would predict:
on 2026-08-05 the local scorer returned 8.0 for twenty-two consecutive ideas,
including near-duplicates of each other, and three of them each scaffolded a
project.

So promotion now takes two signatures. The local scorer still grades every
candidate — it is free, and it is a perfectly good filter for the obvious
rejects. Only ideas it wants to *promote* are sent to the paid reviewer,
which sees the same idea plus the local verdict and returns
CONFIRM / DEMOTE / REJECT with a reason.

The safety property that matters most is what happens when the reviewer
cannot run — no API key, exhausted budget, provider outage, tier disabled.
The answer is deliberately NOT "promote anyway": an unreviewed idea is held
at ``scored`` for the backlog to re-offer later. Auto-approval and project
generation are downstream of promotion, so a silent reviewer can never let
an unvetted idea reach either. It costs us a delayed promotion; the
alternative costs a scaffolded project nobody vetted.

Cost is small because the funnel is narrow: a debate yields ~11 cluster
representatives, of which only the promotion candidates are reviewed —
roughly $0.03 per debate at gpt-5.4-mini prices.
"""

import json
import re
from dataclasses import dataclass
from typing import Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)

# Verdicts the reviewer may return.
CONFIRM = "confirm"
DEMOTE = "demote"
REJECT = "reject"
UNAVAILABLE = "unavailable"

SECOND_PASS_DEFAULTS = {
    "enabled": True,
    "paid_tier": "review",
    # Only ideas the local scorer wants to promote are worth paying to review.
    "min_local_score": 7.0,
    "max_reviews_per_cycle": 8,
    "max_tokens": 700,
}

REVIEW_PROMPT = """당신은 Mossland 신규 사업 심사위원입니다. 아래 아이디어는 로컬 1차 채점에서 승격 후보로 올라왔습니다. 승격을 확정할지 판단하세요.

## 아이디어
제목: {title}

{content}

## 1차 채점 (로컬 소형 모델, 참고용)
총점 {local_score:.1f}/10

⚠️ 1차 채점기는 점수를 후하게 주는 경향이 확인되었습니다(같은 아이디어 22건에 연속으로 8.0을 부여). 1차 점수에 끌려가지 말고 독립적으로 판단하세요.

## 같은 토론에서 나온 유사 주제 아이디어
{siblings}

## 토론 맥락
{context}

## 판단 기준
- **confirm**: 승격할 가치가 있다. 구체적이고, Mossland와 관련 있으며, 1-2주 MVP로 검증 가능하고, 기존 아이디어의 재탕이 아니다.
- **demote**: 나쁘지 않지만 지금 플랜을 쓸 정도는 아니다. 백로그에 남긴다.
- 위 유사 아이디어 목록이 비어 있지 않다면, 이 아이디어가 그중 **가장 구체적이고 실행 가능한 것**인지 따져라. 같은 일을 다르게 표현한 것 중 하나일 뿐이라면 demote하라 — 한 가지 일에 플랜을 여러 개 만들지 않는다.
- **reject**: 승격도 백로그도 아니다. 내용이 공허하거나, 제목이 JSON 조각/템플릿 문구이거나, 실행 불가능하다.

의심스러우면 confirm하지 마세요. 승격은 플랜 문서와 프로젝트 스캐폴드로 이어지므로 잘못된 confirm이 잘못된 demote보다 훨씬 비쌉니다.

## 응답 형식
JSON으로만 응답하세요:
```json
{{
  "verdict": "confirm" | "demote" | "reject",
  "reason": "<한두 문장으로 근거>",
  "score": <0-10 사이 숫자, 당신의 독립 평가>
}}
```"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": [CONFIRM, DEMOTE, REJECT]},
        "reason": {"type": "string"},
        "score": {"type": "number"},
    },
    "required": ["verdict", "reason"],
}


def _render_siblings(siblings: Optional[list]) -> str:
    """Same-theme ideas from this debate, for the reviewer to compare against.

    A debate routinely emits four or five wordings of one idea. Judged one
    at a time each looks reasonable; seen together, four of them are
    redundant. The reviewer cannot notice that unless it is shown them.
    """
    if not siblings:
        return "없음 (이 주제로는 이 아이디어 하나)"
    return "\n".join(f"- {str(s)[:120]}" for s in siblings[:6])


@dataclass
class ReviewVerdict:
    """One reviewer decision, or the fact that no review happened."""

    verdict: str
    reason: str = ""
    score: Optional[float] = None
    model: Optional[str] = None

    @property
    def promotes(self) -> bool:
        """Only an explicit confirm allows promotion. Absence never does."""
        return self.verdict == CONFIRM

    @property
    def rejects(self) -> bool:
        return self.verdict == REJECT

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "score": self.score,
            "model": self.model,
        }


def _parse(content: str) -> Optional[dict]:
    """Pull the JSON object out of a reply, fenced or not."""
    match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    body = match.group(1) if match else content
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        start, end = body.find("{"), body.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(body[start : end + 1])
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


class SecondPassReviewer:
    """Confirms or overturns the local scorer's promotion decisions."""

    def __init__(self, router, config: Optional[dict] = None):
        self.router = router
        self.config = {**SECOND_PASS_DEFAULTS, **(config or {})}
        self.reviews_used = 0

    @property
    def enabled(self) -> bool:
        return bool(self.config.get("enabled", True))

    def should_review(self, local_score: float) -> bool:
        """Only promotion candidates are worth paying for."""
        if not self.enabled:
            return False
        if self.reviews_used >= int(self.config.get("max_reviews_per_cycle", 8)):
            return False
        return local_score >= float(self.config.get("min_local_score", 7.0))

    async def review(
        self,
        title: str,
        content: str,
        local_score: float,
        context: str = "",
        siblings: Optional[list] = None,
    ) -> ReviewVerdict:
        """Return the reviewer's verdict, or UNAVAILABLE if it could not run.

        Never raises: every failure path becomes UNAVAILABLE, which the
        caller must treat as "not promoted" rather than "promoted".
        """
        prompt = REVIEW_PROMPT.format(
            title=title[:300],
            content=(content or "")[:4000],
            local_score=local_score,
            context=(context or "없음")[:800],
            siblings=_render_siblings(siblings),
        )
        try:
            response = await self.router.route(
                prompt=prompt,
                task_type="evaluation",
                quality="high",
                temperature=0.2,
                max_tokens=int(self.config.get("max_tokens", 700)),
                response_schema=RESPONSE_SCHEMA,
                paid_tier=self.config.get("paid_tier", "review"),
            )
        except Exception as e:
            logger.warning(f"Second-pass review unavailable for '{title[:50]}': {e}")
            return ReviewVerdict(UNAVAILABLE, reason=str(e)[:200])

        # A tier that silently degraded to a local model is not a second
        # opinion — it is the first opinion twice. Refuse to count it.
        provider = getattr(response, "provider", "")
        if provider == "ollama":
            logger.warning(
                f"Second-pass review for '{title[:50]}' resolved to local "
                f"{getattr(response, 'model', '?')} — not an independent review, "
                f"treating as unavailable"
            )
            return ReviewVerdict(UNAVAILABLE, reason="paid tier degraded to local")

        data = _parse(getattr(response, "content", "") or "")
        if not data or data.get("verdict") not in (CONFIRM, DEMOTE, REJECT):
            logger.warning(f"Second-pass review returned no usable verdict for '{title[:50]}'")
            return ReviewVerdict(UNAVAILABLE, reason="unparseable reviewer response")

        self.reviews_used += 1
        raw_score = data.get("score")
        try:
            score = float(raw_score) if raw_score is not None else None
        except (TypeError, ValueError):
            score = None

        verdict = ReviewVerdict(
            verdict=data["verdict"],
            reason=str(data.get("reason", ""))[:500],
            score=score,
            model=getattr(response, "model", None),
        )
        logger.info(
            f"Second pass {verdict.verdict.upper()} for '{title[:50]}' "
            f"(local {local_score:.1f}, reviewer {score if score is not None else '-'}): "
            f"{verdict.reason[:120]}"
        )
        return verdict


__all__ = [
    "CONFIRM",
    "DEMOTE",
    "REJECT",
    "UNAVAILABLE",
    "SECOND_PASS_DEFAULTS",
    "ReviewVerdict",
    "SecondPassReviewer",
]
