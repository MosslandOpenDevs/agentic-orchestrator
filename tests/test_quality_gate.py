"""The QA gate must require positive evidence, not the absence of bad news.

Every "nothing to check" branch used to report success: no implementation
directory, no test files, no pytest installed, and no reachable code reviewer
all returned pass/7.0, so an empty project scored 7.0/10 -- the default
required score -- and was routed to DONE.
"""

from pathlib import Path

import pytest

from agentic_orchestrator.stages.quality import RUN_GENERATED_TESTS_ENV, QualityStage
from agentic_orchestrator.state import Stage, State


@pytest.fixture
def stage(tmp_path, monkeypatch):
    monkeypatch.delenv(RUN_GENERATED_TESTS_ENV, raising=False)
    state = State(project_id="proj-1")
    return QualityStage(state=state, base_path=tmp_path, dry_run=True)


def _impl_dir(base: Path, project_id: str) -> Path:
    d = base / "projects" / project_id / "03_implementation"
    d.mkdir(parents=True, exist_ok=True)
    return d


class TestNothingCheckedIsNotAPass:
    def test_missing_implementation_does_not_pass(self, stage):
        result = stage._run_tests()

        assert result["passed"] is False
        assert result["outcome"] == "no_implementation"

    def test_no_test_files_does_not_pass(self, stage, tmp_path):
        _impl_dir(tmp_path, stage.project_id)

        result = stage._run_tests()

        assert result["passed"] is False
        assert result["outcome"] == "no_tests"

    def test_absent_reviewer_is_not_a_default_pass(self, stage, tmp_path):
        impl = _impl_dir(tmp_path, stage.project_id)
        (impl / "app.py").write_text("x = 1\n")

        result = stage._perform_code_review()

        assert result["reviewed"] is False
        assert result["score"] == 0.0

    def test_no_code_to_review_is_not_a_default_pass(self, stage, tmp_path):
        _impl_dir(tmp_path, stage.project_id)

        result = stage._perform_code_review()

        assert result["reviewed"] is False
        assert result["score"] == 0.0

    def test_empty_project_fails_the_overall_gate(self, stage):
        overall = stage._create_overall_report(
            {
                "tests": stage._run_tests(),
                "review": stage._perform_code_review(),
                "security": {"issues_count": 0},
            }
        )

        assert overall["passed"] is False

    def test_a_real_pass_still_passes(self, stage):
        overall = stage._create_overall_report(
            {
                "tests": {"passed": True, "outcome": "passed", "details": "ok"},
                "review": {"score": 8.5, "reviewed": True, "issues_count": 0},
                "security": {"issues_count": 0},
            }
        )

        assert overall["passed"] is True

    def test_security_findings_still_block(self, stage):
        overall = stage._create_overall_report(
            {
                "tests": {"passed": True, "outcome": "passed", "details": "ok"},
                "review": {"score": 9.0, "reviewed": True, "issues_count": 0},
                "security": {"issues_count": 1},
            }
        )

        assert overall["passed"] is False


class TestExecuteRouting:
    """Where a failing QA verdict goes matters as much as the verdict."""

    def _run(self, stage, monkeypatch, tests, review, security=None):
        monkeypatch.setattr(stage, "_run_tests", lambda: tests)
        monkeypatch.setattr(stage, "_perform_code_review", lambda: review)
        monkeypatch.setattr(
            stage, "_security_check", lambda: security or {"report": "", "issues_count": 0}
        )
        monkeypatch.setattr(stage, "save_artifact", lambda *a, **k: Path("artifact.md"))
        monkeypatch.setattr(stage, "commit_changes", lambda *a, **k: None)
        return stage.execute()

    def test_unverifiable_project_halts_instead_of_regenerating(self, stage, monkeypatch):
        """Sending "there was no test runner" back to DEV just burns LLM
        regeneration cycles on something DEV cannot fix."""
        result = self._run(
            stage,
            monkeypatch,
            tests={"passed": False, "outcome": "execution_disabled", "report": "", "details": ""},
            review={"score": 9.0, "reviewed": True, "issues_count": 0, "report": ""},
        )

        assert result.success is False
        assert result.next_stage is None
        assert not result.should_iterate

    def test_max_revisions_stops_rather_than_marking_done(self, stage, monkeypatch):
        """The fail-open this stage exists to close: a project that never
        passed QA used to be recorded as finished once the revisions ran out."""
        stage.state.iteration.dev = stage.state.limits.dev_max

        result = self._run(
            stage,
            monkeypatch,
            tests={"passed": False, "outcome": "failed", "report": "", "details": ""},
            review={"score": 3.0, "reviewed": True, "issues_count": 4, "report": ""},
        )

        assert result.next_stage is not Stage.DONE
        assert result.success is False

    def test_a_fixable_failure_still_goes_back_to_dev(self, stage, monkeypatch):
        result = self._run(
            stage,
            monkeypatch,
            tests={"passed": False, "outcome": "failed", "report": "", "details": ""},
            review={"score": 5.0, "reviewed": True, "issues_count": 2, "report": ""},
        )

        assert result.next_stage is Stage.DEV
        assert result.should_iterate

    def test_a_real_pass_still_reaches_done(self, stage, monkeypatch):
        result = self._run(
            stage,
            monkeypatch,
            tests={"passed": True, "outcome": "passed", "report": "", "details": "ok"},
            review={"score": 9.0, "reviewed": True, "issues_count": 0, "report": ""},
        )

        assert result.success is True
        assert result.next_stage is Stage.DONE


class TestGeneratedTestsAreNotRunByDefault:
    """pytest executes arbitrary code at collection time, and these test files
    are model output derived from public feeds."""

    def test_generated_tests_are_not_executed_without_opt_in(self, stage, tmp_path):
        impl = _impl_dir(tmp_path, stage.project_id)
        # If this ever ran, the marker file would exist.
        marker = tmp_path / "executed.marker"
        (impl / "test_generated.py").write_text(
            f"open({str(marker)!r}, 'w').close()\n\ndef test_ok():\n    assert True\n"
        )

        result = stage._run_tests()

        assert not marker.exists()
        assert result["passed"] is False
        assert result["outcome"] == "execution_disabled"
        assert RUN_GENERATED_TESTS_ENV in result["report"]

    def test_opt_in_env_enables_execution(self, stage, monkeypatch):
        monkeypatch.setenv(RUN_GENERATED_TESTS_ENV, "1")
        assert stage._generated_tests_may_run() is True

    @pytest.mark.parametrize("value", ["", "0", "false", "no"])
    def test_other_values_keep_execution_off(self, stage, monkeypatch, value):
        monkeypatch.setenv(RUN_GENERATED_TESTS_ENV, value)
        assert stage._generated_tests_may_run() is False
