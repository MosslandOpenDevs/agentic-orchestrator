"""Tests for the 2026-08-05 hardening sweep.

Three unrelated defects found while restoring production, pinned together:

1. **Scaffold pushed to origin/main from the server.** `_git_commit_and_push`
   ran unconditionally after every generated project — `git add` + `commit` +
   `push origin main` on the production checkout. Today it fails only because
   /projects/ is gitignored (the June 2026 "feat: generate production-quality
   code…" commits on the server were this path succeeding). config.yaml has
   carried `git.auto_push: false` all along; nothing read it.

2. **Idea scoring parsed LLM JSON with no schema and no output budget**, and
   its except-path *invents* a neutral 5.0 score — a parse failure silently
   files every idea in the backlog band. Structured outputs make the neutral
   fallback a transport-error path instead of a content-quality path.

3. (Website `metadataBase` — build-level, verified via the deployed page's
   og:image URL rather than unit-testable here.)
"""

import json

import pytest

from agentic_orchestrator.project.scaffold import ProjectScaffold
from agentic_orchestrator.scoring import IdeaScorer


class TestScaffoldAutoPushGate:
    def test_auto_push_defaults_off(self, tmp_path, monkeypatch):
        """config.yaml ships git.auto_push: false — the default must obey it."""
        scaffold = ProjectScaffold(projects_dir=str(tmp_path / "p"))
        assert scaffold.auto_push is False

    def test_auto_push_reads_config_when_enabled(self, tmp_path, monkeypatch):
        class FakeConfig:
            git_auto_push = True

        monkeypatch.setattr(
            "agentic_orchestrator.utils.config.load_config", lambda *a, **k: FakeConfig()
        )
        scaffold = ProjectScaffold(projects_dir=str(tmp_path / "p"))
        assert scaffold.auto_push is True

    def test_explicit_argument_beats_config(self, tmp_path):
        scaffold = ProjectScaffold(projects_dir=str(tmp_path / "p"), auto_push=True)
        assert scaffold.auto_push is True

    def test_unreadable_config_fails_closed(self, tmp_path, monkeypatch):
        """Never push because a YAML file was broken."""

        def boom(*a, **k):
            raise OSError("config unreadable")

        monkeypatch.setattr("agentic_orchestrator.utils.config.load_config", boom)
        scaffold = ProjectScaffold(projects_dir=str(tmp_path / "p"))
        assert scaffold.auto_push is False

    def test_source_gates_the_push_call(self):
        """generate_project must consult self.auto_push before any git call.

        Static check: the only call site of _git_commit_and_push (other than
        its definition) sits inside an `if self.auto_push:` block. A behavioral
        test through generate_project would need the full plan/DB/LLM stack;
        this pins the load-bearing line directly.
        """
        import inspect

        from agentic_orchestrator.project import scaffold as mod

        source = inspect.getsource(mod.ProjectScaffold.generate_project)
        assert "if self.auto_push:" in source
        call_at = source.find("await self._git_commit_and_push")
        gate_at = source.find("if self.auto_push:")
        assert call_at != -1 and gate_at != -1 and gate_at < call_at


class TestScoringStructuredOutputs:
    def _scorer_with_fake_router(self, content: str):
        captured = {}

        class FakeRouter:
            async def route(self, **kwargs):
                captured.update(kwargs)

                class R:
                    pass

                R.content = content
                return R()

        scorer = IdeaScorer(router=FakeRouter())
        return scorer, captured

    async def test_route_carries_schema_and_output_budget(self):
        scorer, captured = self._scorer_with_fake_router(
            '{"feasibility": 8, "relevance": 7, "novelty": 6, "impact": 7}'
        )
        await scorer.score_idea("idea text")

        assert captured["response_schema"] == IdeaScorer.SCORE_RESPONSE_SCHEMA
        assert captured["max_tokens"] == 1024

    async def test_bare_constrained_json_parses(self):
        """Constrained output is pure JSON — no fence. The parser must accept it."""
        scorer, _ = self._scorer_with_fake_router(
            json.dumps(
                {
                    "feasibility": 9.0,
                    "relevance": 8.0,
                    "novelty": 7.0,
                    "impact": 6.0,
                    "reasoning": "r",
                }
            )
        )
        score = await scorer.score_idea("idea text")

        assert score.feasibility == 9.0
        assert score.impact == 6.0

    async def test_parse_failure_still_falls_back_to_neutral(self):
        """The neutral fallback stays — as a transport-error path."""
        scorer, _ = self._scorer_with_fake_router("not json at all")
        score = await scorer.score_idea("idea text")

        assert score.feasibility == 5.0
        assert score.total == pytest.approx(5.0)

    def test_schema_requires_exactly_the_scored_dimensions(self):
        assert set(IdeaScorer.SCORE_RESPONSE_SCHEMA["required"]) == {
            "feasibility",
            "relevance",
            "novelty",
            "impact",
        }
