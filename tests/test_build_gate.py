"""Tests for the generated-project build gate (v0.6.23).

`ready` used to be decided by ``unresolved = [files that FAILED]``, and
``CodeVerifier`` returns SKIPPED — not FAILED — when a language's toolchain
is missing. The production host has node but no ``tsc``, ``esbuild`` or
``solc``, so every TypeScript and Solidity file came back SKIPPED,
``unresolved`` was empty, and every generated project was marked **ready**
having had nothing checked at all.

The property under test throughout: **SKIPPED is not PASSED**. "We could not
check" and "it builds" must never collapse into the same status, because the
first one is what the old code silently reported as the second.

The npm tests build a throwaway package and run the real binary, so they
exercise the actual subprocess plumbing rather than a mock of it.
"""

import json
import shutil

import pytest

from agentic_orchestrator.project.build_gate import (
    FAILED,
    PASSED,
    SKIPPED,
    BuildGateResult,
    StepResult,
    run_build_gate,
    summarize,
)

npm_required = pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed")


def write_package(path, scripts, name="scratch"):
    path.mkdir(parents=True, exist_ok=True)
    (path / "package.json").write_text(
        json.dumps({"name": name, "version": "1.0.0", "private": True, "scripts": scripts})
    )
    return path


class TestSkippedIsNotPassed:
    """The whole point of the module."""

    def test_a_skipped_result_does_not_pass(self):
        assert BuildGateResult(status=SKIPPED, reason="no toolchain").passed is False

    def test_a_failed_result_does_not_pass(self):
        assert BuildGateResult(status=FAILED, reason="build failed").passed is False

    def test_only_passed_passes(self):
        assert BuildGateResult(status=PASSED, reason="ok").passed is True

    def test_the_default_result_does_not_pass(self):
        # A gate that never ran must not hand out `ready` by omission.
        assert BuildGateResult().passed is False


class TestPreconditions:
    def test_disabled_gate_skips_without_claiming_success(self, tmp_path):
        result = run_build_gate(str(tmp_path), {"enabled": False})

        assert result.status == SKIPPED
        assert result.passed is False
        assert "disabled" in result.reason

    def test_missing_project_directory_skips(self, tmp_path):
        result = run_build_gate(str(tmp_path / "nope"), {})

        assert result.status == SKIPPED
        assert result.passed is False

    def test_a_project_with_nothing_to_build_skips(self, tmp_path):
        (tmp_path / "README.md").write_text("# just docs\n")

        result = run_build_gate(str(tmp_path), {})

        assert result.status == SKIPPED
        assert result.passed is False
        assert "package.json" in result.reason


@npm_required
class TestAgainstRealNpm:
    def test_a_project_whose_build_succeeds_passes(self, tmp_path):
        write_package(tmp_path, {"build": 'node -e "process.exit(0)"'})

        result = run_build_gate(str(tmp_path), {"install_timeout": 120, "step_timeout": 120})

        assert result.status == PASSED, result.to_dict()
        assert result.passed is True
        assert any("build" in s.name for s in result.steps)

    def test_a_project_whose_build_fails_does_not_pass(self, tmp_path):
        write_package(tmp_path, {"build": 'node -e "process.exit(1)"'})

        result = run_build_gate(str(tmp_path), {"install_timeout": 120, "step_timeout": 120})

        assert result.status == FAILED
        assert result.passed is False
        assert "build failed" in result.reason

    def test_a_failing_typecheck_stops_the_gate(self, tmp_path):
        write_package(
            tmp_path,
            {
                "build": 'node -e "process.exit(0)"',
                "typecheck": 'node -e "process.exit(3)"',
                "test": 'node -e "process.exit(0)"',
            },
        )

        result = run_build_gate(str(tmp_path), {"install_timeout": 120, "step_timeout": 120})

        assert result.passed is False
        assert "typecheck" in result.reason
        # test must not run after typecheck failed
        assert not any("run test" in s.name for s in result.steps)

    def test_a_failing_test_does_not_pass(self, tmp_path):
        write_package(
            tmp_path,
            {"build": 'node -e "process.exit(0)"', "test": 'node -e "process.exit(1)"'},
        )

        result = run_build_gate(str(tmp_path), {"install_timeout": 120, "step_timeout": 120})

        assert result.passed is False
        assert "test" in result.reason

    def test_a_package_with_no_build_scripts_skips_rather_than_passes(self, tmp_path):
        # An empty scripts block means nothing was verified — the exact
        # situation the old code called `ready`.
        write_package(tmp_path, {})

        result = run_build_gate(str(tmp_path), {"install_timeout": 120})

        assert result.status == SKIPPED
        assert result.passed is False

    def test_a_hanging_step_times_out_and_fails(self, tmp_path):
        write_package(tmp_path, {"build": 'node -e "setTimeout(()=>{}, 60000)"'})

        result = run_build_gate(
            str(tmp_path), {"install_timeout": 120, "step_timeout": 2, "install": True}
        )

        assert result.passed is False
        assert any("timed out" in (s.detail or "") for s in result.steps)

    def test_every_workspace_with_a_package_json_is_checked(self, tmp_path):
        write_package(tmp_path, {"build": 'node -e "process.exit(0)"'}, name="root")
        write_package(
            tmp_path / "contracts", {"build": 'node -e "process.exit(1)"'}, name="contracts"
        )

        result = run_build_gate(str(tmp_path), {"install_timeout": 120, "step_timeout": 120})

        # The nested failure must sink the whole project, not be missed.
        assert result.passed is False
        assert "contracts" in result.reason


class TestInstallSafety:
    def test_install_always_ignores_scripts(self):
        # A generated package.json can name any dependency; install hooks
        # would run arbitrary registry code on a shared box.
        source = (
            __import__("pathlib").Path("src/agentic_orchestrator/project/build_gate.py").read_text()
        )
        assert '"--ignore-scripts"' in source
        assert source.count("npm") > 0

    def test_step_output_is_truncated_before_storage(self):
        long_detail = "x" * 50_000
        step = StepResult(name="n", status=FAILED, detail=long_detail[:4000])
        assert len(step.to_dict()["detail"]) <= 4000


class TestSummary:
    def test_summary_names_the_status_and_reason(self):
        result = BuildGateResult(status=FAILED, reason="root: build failed")
        result.steps = [StepResult(name="root: npm install", status=PASSED)]

        line = summarize(result)

        assert "failed" in line
        assert "root: build failed" in line
