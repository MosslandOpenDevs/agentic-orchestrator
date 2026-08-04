"""
Mossland Agentic Orchestrator

An autonomous orchestration system that performs the complete software development lifecycle:
Idea Discovery → Detailed Planning → Development → Testing/Evaluation → Feedback Integration
"""

import logging as _logging
import tomllib as _tomllib
from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path as _Path

_DIST_NAME = "agentic-orchestrator"


def _version_from_source_tree() -> str | None:
    """Read ``[project].version`` from the pyproject.toml above this package.

    This is the authoritative source when running from a checkout, which is how
    production actually runs: every PM2 app in ecosystem.config.js launches
    ``.venv/bin/python`` with ``PYTHONPATH: './src'``, so the working tree — not
    any installed dist-info — is the code being served. Installed metadata is
    only a snapshot taken at ``pip install`` time and goes stale on the very
    commit that bumps the version.
    """
    pyproject = _Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        project = _tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]
    except (OSError, _tomllib.TOMLDecodeError, KeyError):
        return None
    # Guard against picking up an unrelated pyproject.toml when this package is
    # installed into site-packages rather than run from a checkout.
    if project.get("name") != _DIST_NAME:
        return None
    return project.get("version")


def _resolve_version() -> str:
    """Resolve the single source of truth for the version: pyproject.toml.

    Falls back to installed distribution metadata (wheel/non-editable installs,
    where pyproject.toml is not shipped alongside the package).
    """
    from_source = _version_from_source_tree()
    if from_source:
        return from_source
    try:
        return _pkg_version(_DIST_NAME)
    except _PackageNotFoundError:
        # Neither a readable checkout nor an install — never silently publish a
        # bogus version on /health and /; make it findable in the logs.
        _logging.getLogger(__name__).warning(
            "Could not resolve the package version from pyproject.toml or installed "
            "metadata; reporting 0.0.0+unknown. Run `pip install -e .` or serve from "
            "a complete checkout."
        )
        return "0.0.0+unknown"


__version__ = _resolve_version()
__author__ = "Mossland"

from .orchestrator import Orchestrator
from .state import Stage, State

__all__ = ["Orchestrator", "State", "Stage", "__version__"]
