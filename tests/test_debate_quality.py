"""Regressions for the debate content-quality defects found in the 2026-08-18 audit.

Each class here pins one defect that ran silently in production for weeks. They
share a theme: the debate kept working -- 51 consecutive sessions completed, no
errors, no alerts -- while producing measurably worse output than it was built
to produce. Nothing in the pipeline can notice that on its own, so it has to be
pinned by tests.
"""

import re
from pathlib import Path

from agentic_orchestrator.debate import protocol as protocol_module
from agentic_orchestrator.debate.multi_stage import Idea, MultiStageDebate
from agentic_orchestrator.debate.protocol import (
    IDEA_SUMMARY_CHARS,
    DebateProtocol,
    DebateProtocolConfig,
)

PROTOCOL_SOURCE = Path(protocol_module.__file__).read_text(encoding="utf-8")

PERSONALITY = {"creativity": "high", "analysis": "high"}


def make_idea(**overrides) -> Idea:
    """A fully-populated idea, as the divergence phase produces one."""
    kwargs = {
        "id": "idea-1",
        "title": "ERC-4337 Paymaster Budget Guard for Mossland Quest Players",
        "content": '```json\n{"idea_title": "ERC-4337 Paymaster Budget Guard", "core_analysis": "..."}\n```',
        "summary": "Account abstraction has made sponsored transactions routine, "
        "but no wallet exposes a per-session spend ceiling to the player.",
        "agent_id": "startup_founder",
        "agent_name": "Startup Founder",
        "round_num": 1,
    }
    kwargs.update(overrides)
    return Idea(**kwargs)


class TestPromptKeyContract:
    """Prompt builders may only read keys that ``Idea.to_dict()`` emits.

    Three prompts read 'agent', 'score' and 'summary'. None of those keys has
    ever existed -- ``git log -S`` finds no commit that removed them -- so
    ``dict.get`` silently returned the default every single time: every
    evaluation prompt said "Proposer: Unknown", every second-round evaluator saw
    "Score: N/A" instead of what round one had decided, and the planning phase
    wrote its plan from ``content[:200]``.

    A literal-string assertion would not have caught this, because the strings
    the code produced were perfectly well-formed. The contract is what broke.
    """

    def test_every_key_the_prompts_read_is_emitted_by_to_dict(self):
        keys_read = set(re.findall(r"""idea\.get\(\s*['"]([A-Za-z_]+)['"]""", PROTOCOL_SOURCE))

        # Guard the scan itself: a refactor that renames the loop variable would
        # otherwise make this test vacuously pass.
        assert keys_read, "found no idea.get(...) reads in protocol.py -- has the scan gone stale?"

        emitted = set(make_idea().to_dict())
        missing = sorted(keys_read - emitted)
        assert not missing, f"prompts read keys Idea.to_dict() never emits: {missing}"


class TestConvergencePromptShowsWhatItClaimsTo:
    def setup_method(self):
        self.protocol = DebateProtocol(DebateProtocolConfig())

    def test_evaluator_is_told_who_proposed_the_idea(self):
        prompt = self.protocol.create_convergence_prompt(
            topic="Wallet UX",
            ideas=[make_idea().to_dict()],
            agent_personality=PERSONALITY,
            round_num=1,
        )

        assert "Startup Founder" in prompt
        assert "Proposer: Unknown" not in prompt

    def test_second_round_evaluator_sees_the_first_rounds_score(self):
        scored = make_idea(scores={"vc_conservative": 8.0, "tech_analyst": 7.0})

        prompt = self.protocol.create_convergence_prompt(
            topic="Wallet UX",
            ideas=[scored.to_dict()],
            agent_personality=PERSONALITY,
            round_num=2,
        )

        assert "7.5/10" in prompt, "round 2 re-scored ideas blind to round 1"

    def test_an_unscored_idea_reads_as_unscored_not_as_a_zero(self):
        """``total_score`` is 0.0 before anyone scores it -- that is absence of
        evidence, and rendering it as "0.0/10" would tell the evaluator the
        previous round rated the idea worthless."""
        prompt = self.protocol.create_convergence_prompt(
            topic="Wallet UX",
            ideas=[make_idea().to_dict()],
            agent_personality=PERSONALITY,
            round_num=1,
        )

        assert "not yet scored" in prompt
        assert "0.0/10" not in prompt


class TestPlanningPromptGetsRealIdeaContent:
    def setup_method(self):
        self.protocol = DebateProtocol(DebateProtocolConfig())

    def test_planning_sees_the_summary_rather_than_a_slice_of_raw_json(self):
        idea = make_idea()

        prompt = self.protocol.create_planning_prompt(
            topic="Wallet UX",
            selected_ideas=[idea.to_dict()],
            agent_personality=PERSONALITY,
            agent_expertise="product management",
            round_num=1,
        )

        assert "per-session spend ceiling" in prompt
        assert "```json" not in prompt.split("## Instructions")[0]

    def test_an_idea_without_a_summary_still_contributes_useful_text(self):
        """Text-extracted ideas carry no summary. They must fall back to real
        content, and to more of it than the 200 characters that used to be the
        whole of what the planning phase ever saw."""
        idea = make_idea(summary="", content="A" * 5000)

        prompt = self.protocol.create_planning_prompt(
            topic="Wallet UX",
            selected_ideas=[idea.to_dict()],
            agent_personality=PERSONALITY,
            agent_expertise="product management",
            round_num=1,
        )

        assert "A" * 1000 in prompt
        assert "A" * (IDEA_SUMMARY_CHARS + 1) not in prompt


class TestIdeaSummaryExtraction:
    def test_summary_is_prose_drawn_from_the_analysis_and_the_proposal(self):
        summary = MultiStageDebate._summarize_idea_json(
            {
                "idea_title": "ERC-4337 Paymaster Budget Guard",
                "core_analysis": "Sponsored transactions are routine now.",
                "proposal": {
                    "description": "A per-session spend ceiling enforced by the paymaster.",
                    "core_features": ["ceiling", "alerts"],
                },
            }
        )

        assert "Sponsored transactions are routine now." in summary
        assert "per-session spend ceiling" in summary
        assert "idea_title" not in summary, "the summary must be prose, not JSON"

    def test_summary_is_bounded(self):
        summary = MultiStageDebate._summarize_idea_json({"core_analysis": "x" * 9000})

        assert len(summary) == IDEA_SUMMARY_CHARS

    def test_missing_and_oddly_typed_fields_do_not_raise(self):
        assert MultiStageDebate._summarize_idea_json({}) == ""
        assert MultiStageDebate._summarize_idea_json({"core_analysis": None}) == ""
        # `proposal` arrives as a bare string from some models.
        assert (
            MultiStageDebate._summarize_idea_json({"proposal": "Ship a budget guard."})
            == "Ship a budget guard."
        )
