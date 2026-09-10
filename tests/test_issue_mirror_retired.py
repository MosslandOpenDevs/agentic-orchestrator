"""The scheduler no longer mirrors ideas and plans into GitHub issues.

Two source invariants over ``scheduler/*.py`` -- only the transitional
``mirror_retirement.py`` may reach GitHub, and nothing creates an issue -- and
the wiring that keeps that module running from the backlog tick.
"""

from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_orchestrator.db.models import Base
from agentic_orchestrator.scheduler import tasks as tasks_mod

# The imported package, not a path relative to this file: the scan must read
# the code the other tests run.
SCHEDULER_DIR = Path(tasks_mod.__file__).resolve().parent


def scheduler_sources() -> dict:
    sources = {path.name: path.read_text(encoding="utf-8") for path in SCHEDULER_DIR.glob("*.py")}
    # An empty or misdirected scan passes every "appears nowhere" assertion.
    assert len(sources) >= 5, f"scanned only {sorted(sources)} under {SCHEDULER_DIR}"
    return sources


class TestTheSchedulerDoesNotMirror:
    def test_only_the_transitional_module_reaches_github(self):
        users = {
            name
            for name, text in scheduler_sources().items()
            if "github_client" in text or "GitHubClient" in text
        }

        # Detected, so the scan demonstrably sees a user when there is one.
        # When the follow-up PR deletes mirror_retirement.py, no user is left.
        assert "mirror_retirement.py" in users
        assert users == {"mirror_retirement.py"}

    def test_nothing_in_the_scheduler_creates_an_issue(self):
        creators = [name for name, text in scheduler_sources().items() if "create_issue" in text]

        assert creators == []


class TestTheBacklogTickRunsTheRetirement:
    """TRANSITIONAL: goes with scheduler/mirror_retirement.py.

    The retirement must not depend on triage. Triage can be switched off, and
    an LLM outage makes it raise; neither may hold the transition back.
    """

    def _process_backlog(self, monkeypatch, tmp_path, triage):
        import agentic_orchestrator.db as db_pkg
        import agentic_orchestrator.llm as llm_pkg
        import agentic_orchestrator.scheduler.mirror_retirement as retirement_mod

        engine = create_engine(f"sqlite:///{tmp_path / 'backlog.db'}")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        monkeypatch.setattr(
            db_pkg, "get_database", lambda: SimpleNamespace(get_session=session_factory)
        )

        block = {"enabled": True, "max_closes_per_run": 7}
        monkeypatch.setattr(
            tasks_mod,
            "_load_backlog_config",
            lambda: {"triage": triage, "mirror_retirement": block},
        )

        routers = []

        def backend_down():
            routers.append("constructed")
            raise RuntimeError("LLM backend down")

        monkeypatch.setattr(llm_pkg, "HybridLLMRouter", backend_down)

        calls = []

        def record(factory, config):
            calls.append((factory, config))
            return {}

        monkeypatch.setattr(retirement_mod, "run_mirror_retirement", record)

        tasks_mod._process_backlog()

        return calls, routers, [(session_factory, block)]

    def test_it_runs_with_triage_switched_off(self, monkeypatch, tmp_path):
        calls, routers, expected = self._process_backlog(monkeypatch, tmp_path, {"enabled": False})

        assert routers == [], "triage must really have been off"
        assert calls == expected

    def test_it_runs_when_triage_raises(self, monkeypatch, tmp_path):
        calls, routers, expected = self._process_backlog(monkeypatch, tmp_path, {"enabled": True})

        assert routers, "triage must really have been attempted"
        assert calls == expected
