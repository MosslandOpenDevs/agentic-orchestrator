"""Tests for idea summary rendering in the scheduler tasks.

Regression cover for a defect that was visible on the public tracker:
``idea_content[:500]`` cut debate output mid-`````json`` block, leaving the fence
unclosed so every following section rendered inside a code span. The summary is
stored as ``ideas.summary`` and the site renders it as markdown, so the fence
still has to close.
"""

import json

from agentic_orchestrator.scheduler.tasks import (
    _format_idea_summary,
    _truncate_markdown,
)


class TestFormatIdeaSummary:
    """Debate output is a fenced JSON object; render it, never bisect it."""

    FENCED = """```json
{
  "idea_title": "Ethereum Validator Security Platform",
  "core_analysis": "The market shows growing demand for secure staking.",
  "opportunity_risk": {
    "opportunities": "Comprehensive security solutions for validators.",
    "risks": "Crowded market."
  },
  "tech_stack": ["Solidity", "FastAPI"]
}
```"""

    def test_renders_json_instead_of_slicing(self):
        out = _format_idea_summary(self.FENCED)
        assert "**Idea Title**" in out
        assert "Ethereum Validator Security Platform" in out
        # The whole point: no dangling fence.
        assert "```" not in out

    def test_renders_nested_objects_and_lists(self):
        out = _format_idea_summary(self.FENCED)
        assert "**Opportunity Risk**" in out
        assert "Crowded market." in out
        assert "- Solidity" in out

    def test_tolerates_trailing_commas(self):
        out = _format_idea_summary('```json\n{"a": "one", "b": "two",}\n```')
        assert "**A**: one" in out
        assert "**B**: two" in out

    def test_bare_json_without_a_fence(self):
        out = _format_idea_summary('{"core_analysis": "no fence here"}')
        assert "no fence here" in out

    def test_falls_back_to_truncation_for_prose(self):
        prose = "Sentence one. " * 400
        out = _format_idea_summary(prose, limit=200)
        assert len(out) < len(prose)
        assert "_(truncated)_" in out

    def test_short_prose_is_returned_whole(self):
        assert _format_idea_summary("A short idea.") == "A short idea."

    def test_empty_input(self):
        assert _format_idea_summary("") == ""
        assert _format_idea_summary(None) == ""

    def test_json_path_respects_the_limit(self):
        # The rendered markdown must be bounded too. An early version applied
        # ``limit`` only to the prose fallback, so a large idea object could
        # produce an unbounded summary.
        big = {"section_%02d" % i: "v" * 200 for i in range(40)}
        out = _format_idea_summary("```json\n" + json.dumps(big) + "\n```", limit=800)
        assert len(out) < 1000
        assert "_(truncated)_" in out

    def test_unparseable_fence_never_leaks_an_open_fence(self):
        # A fenced block that is not JSON and is longer than the limit: the
        # fallback must still balance the fence rather than reproduce the bug.
        broken = "```json\n" + ("x" * 4000)
        out = _format_idea_summary(broken, limit=500)
        assert out.count("```") % 2 == 0


class TestTruncateMarkdown:
    """The fallback path used when there is no JSON to recover."""

    def test_returns_short_text_unchanged(self):
        assert _truncate_markdown("hello", 100) == "hello"

    def test_prefers_a_paragraph_boundary(self):
        text = "para one\n\n" + "y" * 500
        out = _truncate_markdown(text, 300)
        assert out.startswith("para one")

    def test_closes_an_unbalanced_fence(self):
        text = "```\n" + "z" * 500
        out = _truncate_markdown(text, 100)
        assert out.count("```") % 2 == 0

    def test_leaves_a_balanced_fence_alone(self):
        text = "```\ncode\n```\n" + "w" * 500
        out = _truncate_markdown(text, 200)
        assert out.count("```") % 2 == 0

    def test_marks_the_cut(self):
        assert "_(truncated)_" in _truncate_markdown("q" * 500, 100)
