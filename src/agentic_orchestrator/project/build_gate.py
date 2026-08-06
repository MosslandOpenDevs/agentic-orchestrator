"""Build gate: `ready` has to mean the thing actually builds.

Until v0.6.23 a generated project's status was decided by
``unresolved = [files that FAILED verification]`` — and ``CodeVerifier``
returns SKIPPED, not FAILED, when the toolchain for a language is missing.
The production box has node but no ``tsc``, no ``esbuild`` and no ``solc``,
so every TypeScript and Solidity file in every generated project came back
SKIPPED, ``unresolved`` was empty, and the project was marked **ready**
having had nothing checked at all.

This module makes the word mean something. It runs the project's real
toolchain — install, build, typecheck, test — and only a clean pass earns
``ready``. Anything else (a failure, a missing toolchain, the gate disabled)
lands on ``ready_with_warnings``: the files are still delivered and the plan
issue still closes, but nobody is told the thing compiles when nobody
checked.

Safety notes, because this executes code written by a 4B model:

* ``npm`` runs with ``--ignore-scripts``. A generated ``package.json`` can
  name any dependency, and install scripts would execute arbitrary code from
  the registry on a box that hosts 37 other projects. Ignoring scripts costs
  us native rebuilds — which these scaffolds do not need — and removes the
  entire install-time execution surface.
* Every step has a hard timeout and its output is truncated before being
  stored, so a runaway build cannot wedge the scheduler or bloat the DB.
* Nothing here raises: a broken gate degrades to "not verified", never to a
  failed generation.
"""

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)

BUILD_GATE_DEFAULTS = {
    "enabled": True,
    # Installing is the expensive step and the one with a real (if reduced)
    # supply-chain surface, so it is opt-in separately from the rest.
    "install": True,
    "install_timeout": 300,
    "step_timeout": 300,
    "max_output_chars": 4000,
}

PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"


@dataclass
class StepResult:
    name: str
    status: str
    command: str = ""
    detail: str = ""
    duration_seconds: float = 0.0
    # True only for steps that are evidence the code works (build, typecheck,
    # test). `install` is setup: it can pass on a project with no build at all.
    verifies: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "command": self.command,
            "detail": self.detail,
            "duration_seconds": round(self.duration_seconds, 1),
            "verifies": self.verifies,
        }


@dataclass
class BuildGateResult:
    """Outcome of the whole gate. ``passed`` is what earns ``ready``."""

    status: str = SKIPPED
    reason: str = ""
    steps: List[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True only when the gate ran real checks and all of them passed.

        SKIPPED is deliberately not passing: "we could not check" and "it
        builds" are the two states this module exists to keep apart.
        """
        return self.status == PASSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "steps": [s.to_dict() for s in self.steps],
        }


def _run(
    command: List[str],
    cwd: Path,
    timeout: int,
    max_output: int,
) -> StepResult:
    """Run one command, never raising; returns a StepResult."""
    import time

    name = " ".join(command[:2])
    started = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return StepResult(
            name=name,
            status=FAILED,
            command=" ".join(command),
            detail=f"timed out after {timeout}s",
            duration_seconds=time.monotonic() - started,
        )
    except Exception as e:  # missing binary, permission, ...
        return StepResult(
            name=name,
            status=SKIPPED,
            command=" ".join(command),
            detail=str(e)[:200],
            duration_seconds=time.monotonic() - started,
        )

    duration = time.monotonic() - started
    if proc.returncode == 0:
        return StepResult(
            name=name, status=PASSED, command=" ".join(command), duration_seconds=duration
        )

    output = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()
    return StepResult(
        name=name,
        status=FAILED,
        command=" ".join(command),
        detail=output[-max_output:],
        duration_seconds=duration,
    )


def _npm_scripts(package_json: Path) -> Dict[str, str]:
    import json

    try:
        return json.loads(package_json.read_text()).get("scripts") or {}
    except Exception:
        return {}


def _node_roots(project_path: Path) -> List[Path]:
    """Directories holding a package.json, shallowly (root, src/*, contracts)."""
    roots = []
    if (project_path / "package.json").is_file():
        roots.append(project_path)
    for candidate in sorted(project_path.glob("*/package.json")) + sorted(
        project_path.glob("*/*/package.json")
    ):
        roots.append(candidate.parent)
    return roots


def run_build_gate(
    project_path: str,
    config: Optional[dict] = None,
) -> BuildGateResult:
    """Install, build, typecheck and test the generated project.

    Returns SKIPPED (not PASSED) whenever the checks could not actually run —
    the caller must treat that as "unverified", never as "ready".
    """
    settings = {**BUILD_GATE_DEFAULTS, **(config or {})}
    result = BuildGateResult()

    if not settings.get("enabled", True):
        result.reason = "build gate disabled in config"
        return result

    path = Path(project_path)
    if not path.is_dir():
        result.reason = f"project path not found: {project_path}"
        return result

    step_timeout = int(settings.get("step_timeout", 300))
    install_timeout = int(settings.get("install_timeout", 300))
    max_output = int(settings.get("max_output_chars", 4000))

    roots = _node_roots(path)
    if not roots:
        result.reason = "no package.json found — nothing this gate knows how to build"
        return result

    npm = shutil.which("npm")
    if not npm:
        result.reason = "npm not installed on this host"
        return result

    for root in roots:
        label = root.relative_to(path).as_posix() or "."
        scripts = _npm_scripts(root / "package.json")

        if settings.get("install", True):
            # --ignore-scripts: a generated package.json can name any
            # dependency, and install hooks would run arbitrary registry code
            # on a box hosting 37 other projects.
            step = _run(
                [npm, "install", "--ignore-scripts", "--no-audit", "--no-fund"],
                root,
                install_timeout,
                max_output,
            )
            step.name = f"{label}: npm install"
            step.verifies = False  # setup, not evidence that anything works
            result.steps.append(step)
            if step.status != PASSED:
                result.status = FAILED if step.status == FAILED else SKIPPED
                result.reason = f"{label}: install {step.status}"
                return result

        for script in ("build", "typecheck", "test"):
            if script not in scripts:
                continue
            command = [npm, "run", script, "--if-present"]
            if script == "test":
                # Generated test scripts routinely sit in watch mode, which
                # would hang until the step timeout.
                command += ["--", "--watch=false"] if "vitest" in scripts.get("test", "") else []
            step = _run(command, root, step_timeout, max_output)
            step.name = f"{label}: npm run {script}"
            step.verifies = True
            result.steps.append(step)
            if step.status == FAILED:
                result.status = FAILED
                result.reason = f"{label}: {script} failed"
                return result

    # `install` succeeding proves nothing about the code. Only build,
    # typecheck and test are evidence, and without at least one of them the
    # gate has verified nothing — which is SKIPPED, not PASSED. This is the
    # same conflation the module exists to undo, one level up.
    verified = [s for s in result.steps if s.verifies and s.status == PASSED]
    if not verified:
        result.reason = "no build/typecheck/test script to run — nothing was verified"
        return result

    result.status = PASSED
    result.reason = f"{len(verified)} check(s) passed"
    return result


def summarize(result: BuildGateResult) -> str:
    """One-line human summary for the generation log."""
    counts: Dict[str, int] = {}
    for step in result.steps:
        counts[step.status] = counts.get(step.status, 0) + 1
    detail = ", ".join(f"{n} {status}" for status, n in sorted(counts.items())) or "no steps"
    return f"Build gate: {result.status} ({detail}) — {result.reason}"


__all__ = [
    "BUILD_GATE_DEFAULTS",
    "PASSED",
    "FAILED",
    "SKIPPED",
    "BuildGateResult",
    "StepResult",
    "run_build_gate",
    "summarize",
]
