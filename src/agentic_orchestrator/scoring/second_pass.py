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

What 3,168 reviews then taught us (measured 2026-08-26, production logs)
------------------------------------------------------------------------
The gate returned 3,166 DEMOTE, 2 REJECT and **zero CONFIRM** across its
whole life, and its own independent score never once exceeded 6.8. Promotion
stopped on 2026-08-05 and plan creation on 2026-08-06; debates kept running
four times a day at ~$2.3/day the entire time. Both promotion paths — the
debate cycle and backlog triage — route through this one object, so a gate
that never says yes stops the pipeline outright.

It was not duplication doing it. Tallying the demote reasons: 75.6% cited a
1-2 week MVP scope that could not be verified, 45.9% a weak direct connection
to Mossland, and only 20.0% mentioned duplication at all. Both of the top two
are questions the reviewer had no way to answer:

- It was asked to judge Mossland relevance while never being told what
  Mossland is. "Cannot tell" reads as "no" — hence ``org_profile``.
- It was asked to confirm only ideas already verifiable as a 1-2 week MVP,
  but promotion is what *sends an idea to the planning stage that writes the
  execution plan*. The prompt demanded the output of the next stage as the
  entry price of reaching it.

Stacked on an inflation warning, a sibling-redundancy rule and an explicit
"when in doubt, do not confirm", every thumb was on one side of the scale.
The prompt also told the reviewer that a wrong demote is cheap, which the
code contradicts: triage turns each DEMOTE into a strike and archives the
idea permanently at two. The gate keeps its teeth — CONFIRM is still required
and absence still never promotes — but it now states the real cost on both
sides and asks a question that can be answered.

A gate that rejects everything is indistinguishable from a strict one unless
someone counts, and for 21 days nobody did, even though ``GET /usage`` was
already reporting ``no_confirmations``. ``log_cycle_summary`` therefore makes
the reviewing process say it out loud rather than waiting to be asked.
"""

import json
import re
from dataclasses import dataclass
from typing import Dict, Optional

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
    # What the reviewer is judging "Mossland relevance" against. Empty by
    # default and filled in from config.yaml, because it is org knowledge
    # rather than code: an operator must be able to sharpen it without a
    # deploy. Empty is handled explicitly in the prompt rather than left to
    # the model -- see ORG_PROFILE_ABSENT.
    "org_profile": "",
    # Reviews in one cycle before "nothing was confirmed" stops being noise
    # and starts being a signal. See ``log_cycle_summary``.
    "starvation_min_reviews": 5,
}

# Shown when no profile is configured. It has to actively neutralise the
# relevance criterion: left to itself the model answers "is this directly
# connected to Mossland's core business?" with "cannot tell", and "cannot
# tell" reads as "no". 45.9% of 3,166 consecutive demotes cited exactly that.
ORG_PROFILE_ABSENT = (
    "(설정되지 않음) Mossland 사업 설명이 이 심사에 제공되지 않았습니다. "
    "**따라서 Mossland 적합도를 근거로 감점하지 마세요** — 판단할 자료가 없는 "
    "항목이며, 대신 아이디어 자체의 구체성과 대표성만으로 판정하세요."
)

REVIEW_PROMPT = """당신은 Mossland 신규 사업 심사위원입니다. 아래 아이디어는 로컬 1차 채점에서 승격 후보로 올라왔습니다. 승격을 확정할지 판단하세요.

## Mossland — 이 아이디어가 봉사해야 할 대상
{org_profile}

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

## 이 판정이 무엇을 결정하는가 — 오해하기 쉬우므로 먼저 읽으세요
- **confirm** 은 "지금 만들자"가 아니라 **"기획서 한 편을 쓸 값어치가 있다"** 는 뜻입니다. 실행 계획·주차별 일정·MVP 범위를 만드는 것은 바로 다음 단계인 기획(planning)의 일입니다. **그것들이 아직 없다는 이유로 demote하지 마세요** — 있을 수 없는 단계이기 때문입니다.
- **demote** 는 보류가 아니라 사실상 탈락입니다. 백로그 트리아지가 같은 아이디어를 재평가해 두 번 demote되면 자동으로 영구 아카이브됩니다. 되돌아오지 않습니다.
- 따라서 두 방향 모두 실제 비용이 있습니다. 잘못된 confirm은 기획서 한 편이 낭비되는 비용이고, 잘못된 demote는 아이디어가 사라지는 비용입니다. **어느 쪽으로도 습관적으로 기울지 마세요.**

## 판단 기준
**confirm** — 아래 셋을 모두 만족할 때:
1. Mossland 이용자·MOC 홀더·DAO 참여자 중 **누가** 쓰는지 말할 수 있다.
2. **무엇을 만들지**가 한 문장으로 말해질 만큼 구체적이다 (기술 스택 나열이 아니라 산출물).
3. 위 유사 아이디어 목록이 비어 있지 않다면, 이 아이디어가 **그 축을 가장 잘 대표한다**. 같은 일을 여러 번 표현한 것 중 하나일 뿐이라면 demote — 한 가지 일에 기획서를 여러 개 만들지 않습니다.

**demote** — 위 셋 중 하나가 빠졌을 때. 이 경우 `reason`에 **빠진 항목 하나를 지목**하고, 무엇이 채워지면 confirm이 되는지 한 문장으로 쓰세요. "관련성이 약함", "범위가 넓음"처럼 어느 아이디어에나 붙는 문장은 근거로 인정되지 않습니다.

**reject** — 승격도 백로그도 아닙니다. 내용이 공허하거나, 제목이 JSON 조각/템플릿 문구이거나, 실행 불가능합니다.

## 응답 형식
JSON으로만 응답하세요:
```json
{{
  "verdict": "confirm" | "demote" | "reject",
  "reason": "<한두 문장으로 근거. demote면 빠진 항목 하나를 반드시 지목>",
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
        # Tallied here rather than at each call site so both promotion paths
        # (debate cycle, backlog triage) report the same thing and cannot
        # drift apart.
        self.verdicts: Dict[str, int] = {CONFIRM: 0, DEMOTE: 0, REJECT: 0, UNAVAILABLE: 0}

    @property
    def org_profile(self) -> str:
        """The business description the relevance criterion is judged against."""
        return str(self.config.get("org_profile") or "").strip() or ORG_PROFILE_ABSENT

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
            org_profile=self.org_profile,
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
            return self._record(ReviewVerdict(UNAVAILABLE, reason=str(e)[:200]))

        # A tier that silently degraded to a local model is not a second
        # opinion — it is the first opinion twice. Refuse to count it.
        provider = getattr(response, "provider", "")
        if provider == "ollama":
            logger.warning(
                f"Second-pass review for '{title[:50]}' resolved to local "
                f"{getattr(response, 'model', '?')} — not an independent review, "
                f"treating as unavailable"
            )
            return self._record(ReviewVerdict(UNAVAILABLE, reason="paid tier degraded to local"))

        data = _parse(getattr(response, "content", "") or "")
        if not data or data.get("verdict") not in (CONFIRM, DEMOTE, REJECT):
            logger.warning(f"Second-pass review returned no usable verdict for '{title[:50]}'")
            return self._record(ReviewVerdict(UNAVAILABLE, reason="unparseable reviewer response"))

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
        return self._record(verdict)

    def _record(self, verdict: ReviewVerdict) -> ReviewVerdict:
        """Tally a verdict on its way back to the caller."""
        if verdict.verdict in self.verdicts:
            self.verdicts[verdict.verdict] += 1
        return verdict

    def log_cycle_summary(self, where: str) -> None:
        """Say what this cycle decided — loudly when it decided nothing.

        ``GET /usage`` has reported ``promotion_review.status`` since v0.6.20
        and correctly said ``no_confirmations`` for twenty-one days while
        promotion was stopped. It was never read. An endpoint is a pull;
        this is the push, emitted by the process that did the reviewing, in
        the log an operator already tails when the pipeline looks quiet.

        Deliberately ERROR, not WARNING: a cycle in which several capable
        candidates were all refused is either a stalled gate or a genuinely
        empty harvest, and both are worth someone's attention. Below
        ``starvation_min_reviews`` it stays INFO — three demotes in a row is
        an ordinary Tuesday, not an incident.
        """
        summary = (
            f"{self.verdicts[CONFIRM]} confirmed, {self.verdicts[DEMOTE]} demoted, "
            f"{self.verdicts[REJECT]} rejected, {self.verdicts[UNAVAILABLE]} unavailable"
        )
        if self.starved:
            logger.error(
                f"Second pass ({where}): {summary} — NOTHING was confirmed out of "
                f"{self.decisive} decisive reviews. Promotion is blocked for this cycle. "
                f"A gate that confirms nothing looks exactly like a strict one: check "
                f"`GET /usage` -> promotion_review before assuming the ideas were bad."
            )
        else:
            logger.info(f"Second pass ({where}): {summary}")

    @property
    def decisive(self) -> int:
        """Reviews that reached a verdict. UNAVAILABLE is not one: counting a
        provider outage as a refusal would report every outage as a stalled
        gate."""
        return sum(self.verdicts[v] for v in (CONFIRM, DEMOTE, REJECT))

    @property
    def starved(self) -> bool:
        """This cycle decided often enough to matter and confirmed nothing."""
        return self.decisive >= int(self.config.get("starvation_min_reviews", 5)) and (
            self.verdicts[CONFIRM] == 0
        )


__all__ = [
    "CONFIRM",
    "DEMOTE",
    "ORG_PROFILE_ABSENT",
    "REJECT",
    "UNAVAILABLE",
    "SECOND_PASS_DEFAULTS",
    "ReviewVerdict",
    "SecondPassReviewer",
]
