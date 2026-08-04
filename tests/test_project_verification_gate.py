"""Tests for the scaffold verify+repair gate (ProjectScaffold._verify_and_repair).

The gate must never block generation (the chosen policy is "repair, record, and
proceed"), so these tests assert it mutates files in place, records an accurate
summary, and applies the LLM repair retry only when it actually resolves a
failure.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.db.models import (
    COMPLETED_PROJECT_STATUSES,
    Base,
    Project,
)
from agentic_orchestrator.project.scaffold import (
    ProjectScaffold,
    _summarize_verification,
)
from agentic_orchestrator.project.templates import TemplateFile


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)  # noqa: N806
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _scaffold(tmp_path, router=None):
    return ProjectScaffold(
        router=router,
        projects_dir=str(tmp_path / "projects"),
        db_session=None,
    )


class _Resp:
    def __init__(self, content):
        self.content = content


class _StubRouter:
    """Returns a fixed payload for every route() call."""

    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    async def route(self, prompt, **kwargs):
        self.calls += 1
        return _Resp(self.payload)


class TestDeterministicPath:
    async def test_repairs_in_place_and_records_unresolved(self, tmp_path):
        sc = _scaffold(tmp_path)  # router=None -> no LLM retry
        sol = TemplateFile(
            "contracts/contracts/M.sol",
            'import "@openzeppelin/contracts/access/Ownable.sol";\n'
            "contract M is Ownable {\n"
            "  function f(string memory s) public pure returns (uint){ return s.length(); }\n"
            "  constructor() Ownable(msg.sender) {}\n}\n",
        )
        pkg = TemplateFile(
            "contracts/package.json", '{\n  "name": "contracts",\n  "devDependencies": {}\n}\n'
        )
        good = TemplateFile("src/backend/app/good.py", "def f():\n    return 1\n")
        bad = TemplateFile("src/backend/app/bad.py", "def f(:\n    pass\n")
        readme = TemplateFile("README.md", "# hi")

        files = [sol, pkg, good, bad, readme]
        summary = await sc._verify_and_repair(files)

        # Solidity repaired in place.
        assert "pragma solidity" in sol.content
        assert "s.length()" not in sol.content
        assert "Ownable(msg.sender)" not in sol.content
        # OZ dependency injected into package.json.
        assert "@openzeppelin/contracts" in pkg.content
        # Only code files are checked (sol, good.py, bad.py); package.json and
        # README.md are unknown languages and skipped from verification.
        assert summary["checked"] == 3
        # bad.py cannot be fixed without a router -> unresolved.
        assert summary["unresolved"] == ["src/backend/app/bad.py"]
        assert summary["failed"] == 1
        assert summary["deterministic_repairs"] >= 1
        assert summary["llm_repairs"] == 0
        assert any("@openzeppelin" in fx for fx in summary["dependency_fixes"])


class TestLLMRepairPath:
    async def test_llm_fix_accepted_when_it_resolves(self, tmp_path):
        router = _StubRouter("def f():\n    pass\n")  # valid python
        sc = _scaffold(tmp_path, router=router)
        bad = TemplateFile("src/backend/app/bad.py", "def f(:\n    pass\n")

        summary = await sc._verify_and_repair([bad])

        assert router.calls == 1
        assert summary["failed"] == 0
        assert summary["llm_repairs"] == 1
        assert summary["unresolved"] == []
        assert bad.content.strip() == "def f():\n    pass".strip()

    async def test_llm_fix_rejected_when_still_broken(self, tmp_path):
        router = _StubRouter("def f( still broken")  # still invalid
        sc = _scaffold(tmp_path, router=router)
        original = "def g(:\n    pass\n"
        bad = TemplateFile("x.py", original)

        summary = await sc._verify_and_repair([bad])

        assert router.calls == 1
        assert summary["llm_repairs"] == 0
        assert summary["failed"] == 1
        assert summary["unresolved"] == ["x.py"]
        # original (best-effort) content kept since the LLM output was worse.
        assert bad.content == original


class TestSummaryHelpers:
    def test_summarize_clean(self):
        line = _summarize_verification(
            {"passed": 5, "failed": 0, "skipped": 2, "deterministic_repairs": 1, "llm_repairs": 0}
        )
        assert "5 passed" in line and "0 failed" in line
        assert "Unresolved" not in line

    def test_summarize_with_unresolved(self):
        line = _summarize_verification(
            {
                "passed": 1,
                "failed": 2,
                "skipped": 0,
                "deterministic_repairs": 0,
                "llm_repairs": 0,
                "unresolved": ["a.py", "b.sol"],
            }
        )
        assert "Unresolved: a.py, b.sol" in line

    async def test_final_status_maps_to_warnings(self, tmp_path):
        """An unresolved failure should drive the ready_with_warnings branch."""
        sc = _scaffold(tmp_path)
        bad = TemplateFile("x.py", "def f(:\n  pass\n")
        summary = await sc._verify_and_repair([bad])
        final_status = "ready_with_warnings" if summary.get("unresolved") else "ready"
        assert final_status == "ready_with_warnings"


class TestDuplicatePreventionWithWarnings:
    """ready_with_warnings is a terminal-success status and must dedupe (must-fix)."""

    def test_completed_statuses_constant(self):
        assert "ready" in COMPLETED_PROJECT_STATUSES
        assert "ready_with_warnings" in COMPLETED_PROJECT_STATUSES

    async def test_warned_project_is_not_duplicated(self, tmp_path, db_session):
        db_session.add(
            Project(id="existing1", plan_id="plan-1", name="x", status="ready_with_warnings")
        )
        db_session.flush()
        sc = ProjectScaffold(
            router=None, projects_dir=str(tmp_path / "projects"), db_session=db_session
        )
        returned = await sc._create_project_record(
            plan_id="plan-1", name="x2", tech_stack={}, status="generating"
        )
        assert returned == "existing1"  # deduped, no second row
        assert db_session.query(Project).filter(Project.plan_id == "plan-1").count() == 1

    async def test_errored_project_does_not_block_regeneration(self, tmp_path, db_session):
        db_session.add(Project(id="err1", plan_id="plan-2", name="x", status="error"))
        db_session.flush()
        sc = ProjectScaffold(
            router=None, projects_dir=str(tmp_path / "projects"), db_session=db_session
        )
        returned = await sc._create_project_record(
            plan_id="plan-2", name="x2", tech_stack={}, status="generating"
        )
        assert returned != "err1"  # a fresh record is created
        assert db_session.query(Project).filter(Project.plan_id == "plan-2").count() == 2
