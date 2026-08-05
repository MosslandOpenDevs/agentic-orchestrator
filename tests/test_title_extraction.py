"""Regression tests for idea-title extraction in the multi-stage debate.

The 2026-08-05 debate cycle produced GitHub issues titled with raw JSON array
elements, e.g.::

    [Idea] "Decentralized Oracle Integration (Chainlink)",
    [Idea] "Integration with Mossland's existing NFT infrastructure ...",

Root cause: when the idea JSON fails to parse (typically a truncated
generation), the text fallback scans raw lines. ``_is_json_noise_line`` caught
``"key": value`` property lines but NOT bare string values (array elements),
which are exactly what long ``tech_stack``/roadmap arrays are full of.
"""

import pytest

from agentic_orchestrator.debate.multi_stage import MultiStageDebate


@pytest.fixture(scope="module")
def debate() -> MultiStageDebate:
    # The router is only used when actually running a debate; extraction
    # helpers never touch it.
    return MultiStageDebate(router=None)


@pytest.fixture(scope="module")
def agent(debate: MultiStageDebate):
    return debate.divergence_agents[0]


class TestIsJsonNoiseLine:
    def test_property_line_is_noise(self):
        assert MultiStageDebate._is_json_noise_line('"idea_title": "Something great",')

    def test_brace_lines_are_noise(self):
        assert MultiStageDebate._is_json_noise_line("{")
        assert MultiStageDebate._is_json_noise_line("},")
        assert MultiStageDebate._is_json_noise_line("],")

    def test_bare_array_element_is_noise(self):
        # The exact shape that became issue #2910's title.
        assert MultiStageDebate._is_json_noise_line(
            '"Decentralized Oracle Integration (Chainlink)",'
        )

    def test_bare_string_without_trailing_comma_is_noise(self):
        assert MultiStageDebate._is_json_noise_line('"Next.js (Frontend - User Interface)"')

    def test_truncated_open_string_is_noise(self):
        # Generation cut off mid-string: opening quote, no closing one.
        assert MultiStageDebate._is_json_noise_line(
            '"Dynamic website domain verification and reputation scoring using'
        )

    def test_curly_quoted_title_is_not_noise(self):
        # LLMs use curly quotes decoratively in real titles — keep those.
        assert not MultiStageDebate._is_json_noise_line(
            "“Genesis Protocol” - AI-Powered Adaptive Liquidity Shield"
        )

    def test_plain_prose_is_not_noise(self):
        assert not MultiStageDebate._is_json_noise_line(
            "Real-Time Metaverse Asset Value Tracker for Mossland NFT Holders"
        )


class TestExtractIdeaFallbackTitles:
    def test_truncated_json_array_element_never_becomes_title(self, debate, agent):
        # Unparseable (truncated) JSON whose longest specific lines are array
        # elements. Before the fix, Priority-5 promoted the first element to
        # the title, quotes and trailing comma included.
        content = (
            "```json\n"
            "{\n"
            '  "idea_titl'  # truncated mid-key: json.loads fails
            '  "tech_stack": [\n'
            '    "Decentralized Oracle Integration (Chainlink) for Mossland",\n'
            '    "Next.js (Frontend - User Interface & Data Visualization)",\n'
            "  ]\n"
        )
        idea = debate._extract_idea_from_response(content, agent, round_num=1)
        assert idea is not None
        assert not idea.title.startswith('"')
        assert "Chainlink) for Mossland" not in idea.title
        assert not idea.title.endswith(",")

    def test_valid_json_idea_title_still_wins(self, debate, agent):
        content = (
            "```json\n"
            "{\n"
            '  "idea_title": "GPT-5 Powered Real-Time Scam Token Detection for Mossland",\n'
            '  "core_analysis": "x",\n'
            '  "proposal": {}\n'
            "}\n"
            "```"
        )
        idea = debate._extract_idea_from_response(content, agent, round_num=1)
        assert idea is not None
        assert idea.title == "GPT-5 Powered Real-Time Scam Token Detection for Mossland"

    def test_fallback_title_is_sanitized(self, debate, agent):
        # Even a header-derived title must not keep JSON punctuation.
        content = (
            '## Idea: "Mossland NFT Holder Analytics Dashboard with GPT-5 Insights",\n'
            "Body text explaining the idea in enough detail to matter.\n"
        )
        idea = debate._extract_idea_from_response(content, agent, round_num=1)
        assert idea is not None
        assert idea.title == "Mossland NFT Holder Analytics Dashboard with GPT-5 Insights"

    def test_prose_title_still_extracted(self, debate, agent):
        content = (
            "Some preamble line.\n"
            "Real-Time Metaverse Asset Value Tracker for Mossland NFT Holders\n"
            "More detail follows here.\n"
        )
        idea = debate._extract_idea_from_response(content, agent, round_num=1)
        assert idea is not None
        assert idea.title == "Real-Time Metaverse Asset Value Tracker for Mossland NFT Holders"
