"""Tests for how ``agentic_orchestrator.__version__`` is resolved.

``test_api.py::TestVersionReporting`` covers the *surfaces*: that ``/health``,
``/`` and ``/openapi.json`` all report ``__version__``, and that ``__version__``
equals ``pyproject.toml``. This module covers the *resolution logic* behind
them, which those surface tests cannot distinguish.

The gap that motivates this file: flipping ``_resolve_version()`` to consult
installed metadata *before* the source tree leaves every surface test passing,
because in a checkout without dist-info the metadata lookup raises and the
source tree is consulted anyway. Yet that ordering reintroduces the drift
v0.6.12 fixed — ``importlib.metadata`` returns the snapshot taken at
``pip install`` time, so an editable install whose checkout has since been
bumped keeps reporting the old version. The documented deploy flow is
``git pull`` + ``pm2 restart`` with no reinstall (CLAUDE.md), and every PM2 app
runs ``.venv/bin/python`` with ``PYTHONPATH: './src'`` (ecosystem.config.js), so
the working tree is the code actually being served.
"""

import importlib.metadata
import logging
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import agentic_orchestrator as ao

REPO_ROOT = Path(__file__).resolve().parent.parent
SENTINEL = "0.0.0+unknown"

# Is the ``agentic_orchestrator`` that got imported the one in this checkout?
# It is under a plain ``PYTHONPATH=./src`` run and under ``pip install -e .``
# (setuptools writes a static .pth pointing at src/, and PYTHONPATH/.pth entries
# both land on sys.path ahead of nothing else claiming the name). It is NOT
# under a non-editable ``pip install .``, which copies the package into
# site-packages — there ``parents[2]`` is the venv directory, no pyproject.toml
# sits above the package, and the source-tree branch correctly declines.
RUNNING_FROM_CHECKOUT = (
    Path(ao.__file__).resolve().parent == REPO_ROOT / "src" / "agentic_orchestrator"
)


def declared_version() -> str:
    """The version this checkout's pyproject.toml declares."""
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]


def installed_metadata_version() -> str | None:
    """What installed dist-info reports, or None when not pip-installed."""
    try:
        return importlib.metadata.version("agentic-orchestrator")
    except importlib.metadata.PackageNotFoundError:
        return None


def acceptable_fallbacks() -> set[str]:
    """Versions that are legitimate when the source tree is unusable.

    Depends on how the suite is being run: ``pip install -e .[dev]`` leaves
    dist-info behind (so the metadata fallback answers), while a bare
    ``PYTHONPATH=./src`` run has none (so the sentinel answers). Both are
    correct; only adopting the *foreign* version would be a bug.
    """
    installed = installed_metadata_version()
    return {SENTINEL} | ({installed} if installed else set())


class TestResolutionOrder:
    """The source tree must be consulted before installed metadata."""

    @pytest.mark.skipif(
        not RUNNING_FROM_CHECKOUT,
        reason=(
            "asserts against this checkout's pyproject.toml, which is only the "
            "resolver's answer when the imported package is this checkout; a "
            "non-editable install imports from site-packages, where declining the "
            "source tree is the correct behavior, not a drift bug"
        ),
    )
    def test_source_tree_wins_over_installed_metadata(self, monkeypatch):
        """The property that makes the fix correct — and is otherwise untested.

        With metadata stubbed to a value that is *not* what the checkout
        declares, a correct resolver still returns the checkout's version. A
        metadata-first resolver returns the stub instead.
        """
        monkeypatch.setattr(ao, "_pkg_version", lambda _name: "9.9.9+stale-metadata")

        assert ao._resolve_version() == declared_version()

    def test_falls_back_to_metadata_when_source_tree_unavailable(self, monkeypatch):
        """Wheel / non-editable installs ship no pyproject.toml beside the package."""
        monkeypatch.setattr(ao, "_version_from_source_tree", lambda: None)
        monkeypatch.setattr(ao, "_pkg_version", lambda _name: "1.2.3")

        assert ao._resolve_version() == "1.2.3"

    def test_sentinel_and_warning_when_nothing_resolves(self, monkeypatch, caplog):
        """Neither source nor metadata: report the sentinel and say so in the log."""
        monkeypatch.setattr(ao, "_version_from_source_tree", lambda: None)

        def _not_installed(name):
            raise ao._PackageNotFoundError(name)

        monkeypatch.setattr(ao, "_pkg_version", _not_installed)

        with caplog.at_level(logging.WARNING, logger="agentic_orchestrator"):
            resolved = ao._resolve_version()

        assert resolved == SENTINEL
        # A silently bogus version on /health is the failure mode being avoided.
        assert SENTINEL in caplog.text


def build_tree(tmp_path: Path, pyproject: str | None) -> Path:
    """Copy the package into a synthetic tree carrying ``pyproject`` at its root.

    The package is *copied*, never symlinked: ``_version_from_source_tree`` does
    ``Path(__file__).resolve()``, and ``resolve()`` follows symlinks straight
    back to the real repository — which would silently test nothing.
    """
    root = tmp_path / "tree"
    (root / "src").mkdir(parents=True)
    shutil.copytree(
        REPO_ROOT / "src" / "agentic_orchestrator",
        root / "src" / "agentic_orchestrator",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    if pyproject is not None:
        (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    return root


def version_reported_from(root: Path) -> str:
    """Import the copied package in a subprocess and return its ``__version__``."""
    result = subprocess.run(
        [sys.executable, "-c", "import agentic_orchestrator as a; print(a.__version__)"],
        cwd=root,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": "./src", "HOME": str(root)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"importing the package failed (exit {result.returncode}); resolution must "
        f"degrade, never raise.\nstderr:\n{result.stderr}"
    )
    return result.stdout.strip()


class TestSourceTreeGuards:
    """``_version_from_source_tree`` against trees that are not this checkout."""

    def test_matching_tree_is_adopted(self, tmp_path):
        """Positive control.

        Without this, the negative cases below could pass for the wrong reason
        (e.g. a harness that never reaches the source-tree path at all).
        """
        root = build_tree(tmp_path, '[project]\nname = "agentic-orchestrator"\nversion = "4.5.6"\n')

        assert version_reported_from(root) == "4.5.6"

    def test_foreign_pyproject_is_not_adopted(self, tmp_path):
        """Installed into site-packages, ``parents[2]`` can land on a stranger.

        The ``[project].name`` guard is what stops the API from advertising an
        unrelated project's version number.
        """
        root = build_tree(tmp_path, '[project]\nname = "some-other-project"\nversion = "7.7.7"\n')

        reported = version_reported_from(root)

        assert reported != "7.7.7"
        assert reported in acceptable_fallbacks()

    def test_malformed_pyproject_degrades(self, tmp_path):
        """A broken TOML file must not take the whole API process down on import."""
        root = build_tree(tmp_path, "this is not valid toml {{{")

        assert version_reported_from(root) in acceptable_fallbacks()

    def test_pyproject_without_version_key_degrades(self, tmp_path):
        """``[project]`` present but no ``version`` (e.g. dynamic versioning)."""
        root = build_tree(tmp_path, '[project]\nname = "agentic-orchestrator"\n')

        assert version_reported_from(root) in acceptable_fallbacks()

    def test_pyproject_without_project_table_degrades(self, tmp_path):
        """Valid TOML carrying no ``[project]`` table at all — e.g. Poetry style.

        This is the only case that reaches the ``KeyError`` arm of the guard:
        malformed TOML raises ``TOMLDecodeError``, a missing file raises
        ``OSError``, and a ``[project]`` without ``version`` is handled by
        ``.get()``. Dropping ``KeyError`` from the except clause therefore left
        every other test in this module passing while making a bare
        ``import agentic_orchestrator`` raise — verified by mutation.

        It is also the likeliest shape of the site-packages neighbour the
        ``[project].name`` guard exists for, since a Poetry-managed project
        declares only ``[tool.poetry]``.
        """
        root = build_tree(
            tmp_path, '[tool.poetry]\nname = "some-other-project"\nversion = "7.7.7"\n'
        )

        reported = version_reported_from(root)

        assert reported != "7.7.7"
        assert reported in acceptable_fallbacks()

    def test_missing_pyproject_degrades(self, tmp_path):
        """No pyproject.toml above the package at all."""
        root = build_tree(tmp_path, None)

        assert version_reported_from(root) in acceptable_fallbacks()


class TestNoHardcodedLiterals:
    """Guard against re-hardcoding, the original v0.6.12 defect.

    Three copies had drifted apart: ``FastAPI(version=...)`` and ``/health`` said
    ``0.5.0``, ``/`` said ``0.6.0``, while pyproject.toml declared ``0.6.10``.
    The surface tests catch a reintroduced literal only once it diverges — i.e.
    at the *next* version bump. This catches it at the commit that adds it.
    """

    @pytest.mark.parametrize("module", ["api/main.py", "__init__.py"])
    def test_no_version_literal_assigned_in_source(self, module):
        import re

        source = (REPO_ROOT / "src" / "agentic_orchestrator" / module).read_text(encoding="utf-8")
        # Three shapes: the kwarg `version="0.5.0"` and dict entry
        # `"version": "0.6.0"` that actually drifted, plus any *-version-*
        # binding — `\w*version\w*` is what lets this match `__version__ =
        # "0.6.13"`, the obvious way to re-hardcode __init__.py, which a bare
        # `version\s*=` cannot match across the trailing underscores.
        # `0.0.0+unknown` is the one permitted literal and does not match:
        # the pattern requires the closing quote right after the third group.
        offenders = re.findall(
            r"""(?:\w*version\w*\s*=|["']version["']\s*:)\s*["']\d+\.\d+\.\d+["']""",
            source,
        )

        assert offenders == [], (
            f"{module} hardcodes a version literal {offenders}; read __version__ instead "
            f"(it resolves from pyproject.toml)."
        )
