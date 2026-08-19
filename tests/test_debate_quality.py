"""Regressions for the debate content-quality defects found in the 2026-08-18 audit.

Each class here pins one defect that ran silently in production for weeks. They
share a theme: the debate kept working -- 51 consecutive sessions completed, no
errors, no alerts -- while producing measurably worse output than it was built
to produce. Nothing in the pipeline can notice that on its own, so it has to be
pinned by tests.
"""

import asyncio
import re
from pathlib import Path

from agentic_orchestrator.debate import protocol as protocol_module
from agentic_orchestrator.debate.multi_stage import Idea, MultiStageDebate
from agentic_orchestrator.debate.protocol import (
    IDEA_SUMMARY_CHARS,
    PLAN_REQUIRED_SECTIONS,
    DebateProtocol,
    DebateProtocolConfig,
    plan_completeness,
)
from agentic_orchestrator.scheduler.tasks import _debate_config_from_dict, _load_debate_config

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


class TestEvaluationTokenBudget:
    """A convergence evaluation writes one block per idea, so a flat cap truncates.

    In production every one of 416 paid evaluations hit the 2000-token cap: the
    length distribution had a coefficient of variation of 0.031, none contained
    the closing analysis the template requires, and round 3's ideas -- the least
    duplicative of the debate -- were scored 1.6% of the time.
    """

    def test_budget_grows_with_the_number_of_ideas_on_the_ballot(self):
        config = DebateProtocolConfig(max_tokens_per_response=2000, evaluation_tokens_per_idea=200)

        assert config.evaluation_max_tokens(5) == 3000
        assert config.evaluation_max_tokens(24) == 6800

    def test_a_full_production_ballot_gets_more_than_the_flat_cap(self):
        config = DebateProtocolConfig()

        assert config.evaluation_max_tokens(24) > config.max_tokens_per_response * 3

    def test_empty_ballot_does_not_produce_a_negative_budget(self):
        config = DebateProtocolConfig()

        assert config.evaluation_max_tokens(0) == config.max_tokens_per_response
        assert config.evaluation_max_tokens(-1) == config.max_tokens_per_response


class TestDebateConfigWiring:
    """The token settings must actually be reachable from config.yaml.

    ``max_tokens_per_response`` was a real field, used on every LLM call, that
    the config loader never read -- so the only way to change it was to edit the
    dataclass default. That is the failure this pins.
    """

    def test_token_settings_are_read_from_the_shared_debate_block(self):
        config = _debate_config_from_dict(
            {"test_mode": False, "max_tokens_per_response": 4096, "evaluation_tokens_per_idea": 250}
        )

        assert config.max_tokens_per_response == 4096
        assert config.evaluation_tokens_per_idea == 250

    def test_mode_settings_win_over_the_shared_block(self):
        config = _debate_config_from_dict(
            {
                "test_mode": True,
                "max_tokens_per_response": 4096,
                "test": {"max_tokens_per_response": 512},
            }
        )

        assert config.max_tokens_per_response == 512

    def test_absent_keys_fall_back_to_the_dataclass_defaults(self):
        defaults = DebateProtocolConfig()

        config = _debate_config_from_dict({})

        assert config.max_tokens_per_response == defaults.max_tokens_per_response
        assert config.evaluation_tokens_per_idea == defaults.evaluation_tokens_per_idea

    def test_the_shipped_config_file_is_wired_through(self):
        """End-to-end against the real config.yaml, so a key renamed in one place
        and not the other fails here rather than in a debate at 06:25."""
        config = _load_debate_config()

        assert config.evaluation_max_tokens(24) > config.max_tokens_per_response


def evaluation_block(number: int, title: str, feasibility: int, total: str) -> str:
    """One idea's evaluation, in the shape the convergence template asks for."""
    return f"""### Idea {number}: {title}
- Feasibility: {feasibility}/10 - the bundler work is well understood by the team
- Impact: 5/10 - limited to power users until wallets ship session keys natively
- Innovation: 4/10 - overlaps heavily with existing session-key proposals
- Risk: 5/10 - paymaster griefing remains an unsolved operational concern
- Urgency: 5/10 - nothing forces this into the current quarter
- **Total Score**: {total}
"""


def ballot(count: int) -> list:
    return [
        make_idea(id=f"idea-{n}", title=f"Idea number {n}").to_dict() for n in range(1, count + 1)
    ]


class TestConvergenceScoreExtraction:
    """Scores must come from the block written about that idea, and nowhere else."""

    def setup_method(self):
        self.debate = MultiStageDebate(router=None)

    def test_reads_the_total_not_the_first_number_in_the_block(self):
        """The production defect, exactly: the evaluator wrote 5.15/10 and the
        stored score was 7.0 -- the Feasibility line, because it is the first
        number after the title."""
        content = evaluation_block(1, "Idea number 1", feasibility=7, total="5.15/10")

        scores = self.debate._extract_scores_from_response(content, ballot(1))

        assert scores == {"idea-1": 5.15}

    def test_normalises_the_fifty_point_scale_the_template_asks_for(self):
        content = evaluation_block(1, "Idea number 1", feasibility=7, total="41/50")

        scores = self.debate._extract_scores_from_response(content, ballot(1))

        assert scores == {"idea-1": 8.2}

    def test_infers_the_scale_when_the_denominator_is_missing(self):
        ten = evaluation_block(1, "Idea number 1", feasibility=7, total="8.5")
        fifty = evaluation_block(1, "Idea number 1", feasibility=7, total="41")

        assert self.debate._extract_scores_from_response(ten, ballot(1)) == {"idea-1": 8.5}
        assert self.debate._extract_scores_from_response(fifty, ballot(1)) == {"idea-1": 8.2}

    def test_an_idea_with_no_block_gets_no_score(self):
        """The ghost-score defect: 51.5% of stored (idea, evaluator) pairs were
        a number scraped from a different idea's block. An idea the evaluator
        never reached must come back absent, not inherit Idea 1's score."""
        content = evaluation_block(
            1, "Idea number 1", feasibility=8, total="8/10"
        ) + evaluation_block(2, "Idea number 2", feasibility=6, total="6/10")

        scores = self.debate._extract_scores_from_response(content, ballot(5))

        assert scores == {"idea-1": 8.0, "idea-2": 6.0}
        assert "idea-3" not in scores

    def test_partial_coverage_is_reported(self, caplog):
        content = evaluation_block(1, "Idea number 1", feasibility=8, total="8/10")

        with caplog.at_level("WARNING"):
            self.debate._extract_scores_from_response(content, ballot(24))

        assert "scored 1 of 24 ideas" in caplog.text

    def test_falls_back_to_the_criteria_inside_the_same_block(self):
        """Some evaluations drop the total line. Averaging the criteria the
        evaluator did write stays anchored; reaching outside the block does not."""
        content = """### Idea 1: Idea number 1
- Feasibility: 8/10 - well understood
- Impact: 6/10 - moderate reach
- Innovation: 7/10 - a genuinely new angle on fee smoothing

### Idea 2: Idea number 2
- Feasibility: 2/10 - needs a hard fork
- **Total Score**: 3/10
"""

        scores = self.debate._extract_scores_from_response(content, ballot(2))

        assert scores == {"idea-1": 7.0, "idea-2": 3.0}

    def test_bold_headers_are_accepted_but_prose_is_not(self):
        content = """**Idea 1** — strong candidate
- **Total Score**: 9/10

Idea 2 is also worth considering, I would give it a 9 as well.
"""

        scores = self.debate._extract_scores_from_response(content, ballot(2))

        assert scores == {"idea-1": 9.0}, "a sentence starting 'Idea 2' must not open a block"

    def test_out_of_range_and_off_ballot_numbers_are_dropped(self):
        content = evaluation_block(
            1, "Idea number 1", feasibility=8, total="0/10"
        ) + evaluation_block(9, "Hallucinated idea", feasibility=8, total="8/10")

        scores = self.debate._extract_scores_from_response(content, ballot(2))

        # 0/10 is the sentinel `Idea.total_score` uses for "unscored", so it is
        # dropped rather than stored; Idea 9 was never on the ballot.
        assert scores == {}


def plan_text(sections: int = 6, filler: str = "") -> str:
    """A plan carrying the first ``sections`` required headings."""
    body = "\n".join(f"## {name}\ndetail\n" for name in PLAN_REQUIRED_SECTIONS[:sections])
    return body + filler


class FakeResponse:
    def __init__(self, content):
        self.content = content
        self.model = "test-model"
        self.provider = "test"
        self.input_tokens = 10
        self.output_tokens = 20
        self.cost = 0.0


class FakeRouter:
    """Answers by task type, and tells a revision prompt apart from a draft."""

    def __init__(self, draft, review, revision=None, fail_revision=False):
        self.draft = draft
        self.review = review
        self.revision = revision
        self.fail_revision = fail_revision
        self.revision_calls = 0

    async def route(self, *, prompt, task_type, **kwargs):
        if task_type == "quality_check":
            return FakeResponse(self.review)
        if "Reviewer Feedback" in prompt:
            self.revision_calls += 1
            if self.fail_revision:
                raise RuntimeError("provider is down")
            return FakeResponse(self.revision)
        return FakeResponse(self.draft)


def run_planning(router, rounds=2, agents_per_round=2):
    config = DebateProtocolConfig(
        planning_rounds=rounds, planning_agents_per_round=agents_per_round
    )
    debate = MultiStageDebate(router=router, protocol=DebateProtocol(config))
    debate.ideas = [make_idea(scores={"a": 8.0})]
    return asyncio.run(debate._run_planning_phase("Wallet UX"))


class TestPlanCompleteness:
    def test_counts_the_required_sections(self):
        assert plan_completeness(plan_text(6)) == 6
        assert plan_completeness(plan_text(2)) == 2

    def test_absent_or_empty_plans_score_zero(self):
        assert plan_completeness(None) == 0
        assert plan_completeness("") == 0
        assert plan_completeness("Here is a nice paragraph about wallets.") == 0

    def test_a_long_shapeless_draft_loses_to_a_short_structured_one(self):
        """The selection rule that shipped was `max(drafts, key=len)`, which is
        why verbosity won: across 54 debates the longest draft was not the first
        one 63% of the time, and nothing checked structure at all."""
        rambling = "words " * 5000
        structured = plan_text(6)

        winner = max([rambling, structured], key=lambda d: (plan_completeness(d), len(d)))

        assert winner == structured


class TestPlanningRevision:
    """The review round has to change the plan, or it is decorative.

    In production it was decorative: 141 of 162 reviews said "[Needs Revision]",
    none said approved, and `final_plan` was byte-identical to the longest draft
    in all 54 debates -- the `feedback` value was unpacked and never read.
    """

    def test_reviewer_objections_produce_a_revised_plan(self):
        router = FakeRouter(
            draft=plan_text(6, filler="original"),
            review="The 20-40% figure is unsupported. [Needs Revision]",
            revision=plan_text(6, filler="revised against the reviewers"),
        )

        result = run_planning(router)

        assert "revised against the reviewers" in result.output["final_plan"]
        assert router.revision_calls == 1

    def test_an_approved_plan_is_not_rewritten(self):
        router = FakeRouter(
            draft=plan_text(6, filler="original"),
            review="Solid, ship it. [Approved]",
            revision=plan_text(6, filler="should never be used"),
        )

        result = run_planning(router)

        assert "original" in result.output["final_plan"]
        assert router.revision_calls == 0

    def test_a_revision_that_drops_sections_is_refused(self):
        """A model that answers a review with a changelog, or that rewrites one
        section and forgets the rest, must not be able to make the output worse
        than leaving the draft alone."""
        router = FakeRouter(
            draft=plan_text(6, filler="original"),
            review="Needs work. [Needs Revision]",
            revision="I have updated the KPI section as requested.",
        )

        result = run_planning(router)

        assert "original" in result.output["final_plan"]

    def test_a_failed_revision_leaves_the_reviewed_draft_in_place(self):
        router = FakeRouter(
            draft=plan_text(6, filler="original"),
            review="Needs work. [Needs Revision]",
            fail_revision=True,
        )

        result = run_planning(router)

        assert "original" in result.output["final_plan"]

    def test_the_revision_prompt_carries_the_reviewers_words(self):
        protocol = DebateProtocol(DebateProtocolConfig())

        prompt = protocol.create_plan_revision_prompt(
            topic="Wallet UX",
            draft_plan=plan_text(6),
            reviews=[("Tech Lead", "The 20-40% token reduction figure looks invented.")],
            agent_expertise="engineering",
            round_num=2,
        )

        assert "Tech Lead" in prompt
        assert "looks invented" in prompt
        # It must ask for the whole plan back: the return value replaces it.
        assert "complete revised plan" in prompt


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


class TestDivergenceRoundOneDifferentiation:
    """Round 1 had no differentiation channel at all.

    Both of them key off `previous_ideas`, which is empty on the first round: the
    prompt's "be clearly different from these" block and the similarity feedback
    go quiet together, and all eight agents anchor on the same seed. Measured
    across 54 debates, round 1 titles sit at 0.300 pairwise Jaccard against
    0.177/0.178 later (p < 0.00005), and 65.8% of round 1 output is discarded as
    duplicate — after being generated on the paid tier.
    """

    def setup_method(self):
        self.protocol = DebateProtocol(DebateProtocolConfig())

    def _prompt(self, agent_index, previous=None):
        return self.protocol.create_divergence_prompt(
            topic="Wallet UX",
            context="Trend: account abstraction adoption",
            agent_personality=PERSONALITY,
            round_num=1 if previous is None else 2,
            previous_ideas=previous or [],
            agent_index=agent_index,
        )

    def test_each_agent_gets_a_different_vantage_point(self):
        angles = {
            self._prompt(i).split("approaching this from **")[1].split("**")[0] for i in range(8)
        }

        assert len(angles) == 8, f"agents shared a vantage point: {angles}"

    def test_the_vantage_point_is_orthogonal_to_the_creativity_technique(self):
        """Two axes, not one: the technique says how to think, the angle says
        what to look at. Sharing an index must not collapse them."""
        first, second = self._prompt(0), self._prompt(1)

        assert "end-user experience" in first
        assert "protocol and infrastructure" in second
        # The SCAMPER block is still there and still differs between them.
        assert "Creativity Technique" in first
        assert (
            first.split("Creativity Technique")[1][:60]
            != second.split("Creativity Technique")[1][:60]
        )

    def test_later_rounds_keep_the_stronger_channel_instead(self):
        """Round 3 is the most diverse output a debate produces; do not
        constrain it with a fixed angle it never needed."""
        prompt = self._prompt(0, previous=["An ERC-4337 paymaster budget guard"])

        assert "Your Vantage Point" not in prompt
        assert "clearly different" in prompt
        assert "ERC-4337 paymaster budget guard" in prompt

    def test_a_caller_without_an_agent_index_is_unaffected(self):
        prompt = self.protocol.create_divergence_prompt(
            topic="Wallet UX",
            context="ctx",
            agent_personality=PERSONALITY,
            round_num=1,
            previous_ideas=[],
        )

        assert "Your Vantage Point" not in prompt

    def test_more_agents_than_angles_wraps_without_failing(self):
        assert "Your Vantage Point" in self._prompt(11)


class TestTheRequiredClosingSectionIsNotMinedForScores:
    """The evaluation template REQUIRES a "Final Analysis" whose "Top 3 Ideas"
    lines open as ``**Idea 3** is the strongest...``. Read as a block header,
    that sentence became the last block for idea 3 — and it carries no score, so
    last-one-wins erased the real one. The bias is the worst part: the ideas
    named in "Top 3" are the highest-scoring ones, so the erasure hit exactly
    the ideas planning most needed.
    """

    def setup_method(self):
        self.debate = MultiStageDebate(router=None)
        self.ballot = [{"id": f"idea-{n}", "title": f"Idea {n}"} for n in range(1, 6)]
        self.blocks = "".join(
            f"### Idea {n}: Idea {n}\n- Feasibility: 8/10 - r\n- **Total Score**: {s}/10\n\n"
            for n, s in [(1, 7.4), (2, 5.0), (3, 9.2), (4, 6.0), (5, 4.0)]
        )
        self.expected = {
            "idea-1": 7.4, "idea-2": 5.0, "idea-3": 9.2, "idea-4": 6.0, "idea-5": 4.0
        }

    def test_top_three_prose_does_not_erase_the_top_scores(self):
        final = (
            "### Final Analysis\n"
            "**Idea 3** is the strongest: novel and shippable this quarter.\n"
            "**Idea 1** follows closely on feasibility grounds.\n"
        )

        assert self.debate._extract_scores_from_response(self.blocks + final, self.ballot) == self.expected

    def test_consolidation_notes_cannot_overwrite_a_real_score(self):
        """The nastier variant: this one *does* carry a number, so it would have
        silently replaced idea 4's 6.0 with 7.0 and logged nothing."""
        notes = (
            "### Final Analysis\n"
            "**Idea 4** and **Idea 6** overlap; combined Total Score: 35/50.\n"
        )

        assert self.debate._extract_scores_from_response(self.blocks + notes, self.ballot) == self.expected

    def test_a_sentence_is_not_a_block_header_even_in_bold(self):
        prose = "**Idea 2** deserves a mention here.\n- **Total Score**: 10/10\n"

        scores = self.debate._extract_scores_from_response(self.blocks + prose, self.ballot)

        assert scores["idea-2"] == 5.0, "prose overwrote a real evaluation block"

    def test_real_header_shapes_still_open_a_block(self):
        for header in ("### Idea 1: Title", "**Idea 1**: Title", "## Idea 1 - Title"):
            body = f"{header}\n- **Total Score**: 9/10\n"
            scores = self.debate._extract_scores_from_response(body, self.ballot[:1])
            assert scores == {"idea-1": 9.0}, f"{header!r} stopped being a header"


class TestTotalScoreShapesModelsActuallyWrite:
    """Every miss here is an idea that ends the debate at ``total_score == 0.0``."""

    def test_the_colon_may_sit_inside_the_emphasis(self):
        assert MultiStageDebate._score_from_block("**Total Score:** 41/50") == 8.2
        assert MultiStageDebate._score_from_block("***Total Score***: 41/50") == 8.2

    def test_other_separators(self):
        assert MultiStageDebate._score_from_block("Total Score = 41/50") == 8.2
        assert MultiStageDebate._score_from_block("| Total Score | 41/50 |") == 8.2

    def test_the_criteria_fallback_knows_the_rubrics_own_names(self):
        """The prompt uses two naming schemes: the weighted rubric says
        "Novelty" and "Mossland Relevance", the output template two sections
        later says "Innovation" and "Risk". Knowing only one produced a partial
        mean — and it dropped Novelty, which carries the largest weight."""
        block = (
            "- Feasibility: 8/10 - r\n"
            "- Mossland Relevance: 9/10 - r\n"
            "- Novelty: 7/10 - r\n"
            "- Impact: 9/10 - r\n"
        )

        assert MultiStageDebate._score_from_block(block) == 8.25


class TestARevisionCannotReplaceAPlanWithAnOutline:
    """The revision guard has to stop two different non-answers.

    Section coverage alone let both through: a one-line reply that merely NAMES
    the six sections scored a perfect 6/6 — and ``create_plan_revision_prompt``
    hands the model that exact list, so the cheapest possible non-answer scored
    as well as a full rewrite. A skeleton of six headings over "TBD" carries all
    six for real, in 165 characters against a 14,000-character plan.
    """

    def test_naming_the_sections_is_not_carrying_them(self):
        changelog = (
            "I updated the " + ", ".join(PLAN_REQUIRED_SECTIONS) + " sections as requested."
        )

        assert plan_completeness(changelog) == 0

    def test_a_real_heading_still_counts_in_its_usual_shapes(self):
        for shape in ("## Project Overview", "**Project Overview**", "### 1. Project Overview"):
            assert plan_completeness(shape) == 1, shape

    def test_a_heading_skeleton_is_refused_by_the_length_floor(self):
        router = FakeRouter(
            draft=plan_text(6, filler="original " * 500),
            review="Needs work. [Needs Revision]",
            revision="\n".join(f"## {s}\nTBD" for s in PLAN_REQUIRED_SECTIONS),
        )

        result = run_planning(router)

        assert "original" in result.output["final_plan"]

    def test_a_genuine_rewrite_of_similar_length_is_accepted(self):
        router = FakeRouter(
            draft=plan_text(6, filler="original " * 500),
            review="The 20-40% figure is unsupported. [Needs Revision]",
            revision=plan_text(6, filler="revised with a stated baseline " * 300),
        )

        result = run_planning(router)

        assert "revised with a stated baseline" in result.output["final_plan"]
