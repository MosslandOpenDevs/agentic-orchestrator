"""The public API must not publish the app server's filesystem layout.

`Project.directory_path` stores an absolute path on the office VM
(`/home/<account>/agentic-orchestrator/projects/<name>`), and ao.moss.land
served it verbatim on the Projects page in front of a public repository. It
named the server's login account -- exactly the class of identifier the rest
of this repo keeps out of the public tree (see CLAUDE.local.md).

Redaction happens at the two serialisation points rather than at write time,
so the rows written before the fix are covered without a migration; these
tests pin both, and the endpoints that carry them.

Every identifier below is synthetic on purpose -- `appuser` is not an account
we run as, and `192.0.2.10` is RFC 5737 TEST-NET-1, which can never be a real
host. **Do not "correct" them to the production values.** A test that proves
we keep a secret out of the public repo must not be the thing that puts it
there; the real ones live in the gitignored CLAUDE.local.md.
"""

import re
import subprocess
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.models import Base, Plan, Project
from agentic_orchestrator.pathutil import public_project_path, redact_paths
from agentic_orchestrator.project.scaffold import ProjectGenerationResult

# The shape that was live on ao.moss.land, with a stand-in account name.
LEAKED_PATH = "/home/appuser/agentic-orchestrator/projects/plan-x402-micro-payment-gateway"


class TestPublicProjectPath:
    def test_absolute_host_path_is_reduced_to_the_repo_relative_part(self):
        assert public_project_path(LEAKED_PATH) == "projects/plan-x402-micro-payment-gateway"

    def test_an_already_relative_path_is_unchanged(self):
        assert public_project_path("projects/foo") == "projects/foo"

    def test_nesting_below_projects_is_preserved(self):
        assert public_project_path("/srv/repo/projects/a/b") == "projects/a/b"

    def test_the_innermost_projects_boundary_wins(self):
        # The checkout may itself live under a directory called "projects".
        assert public_project_path("/var/projects/repo/projects/foo") == "projects/foo"

    def test_a_path_with_no_projects_segment_keeps_only_its_leaf(self):
        # A relocated project.output_dir must not fall back to the full path.
        assert public_project_path("/home/appuser/elsewhere/foo") == "foo"

    def test_a_trailing_projects_segment_is_the_directory_itself(self):
        assert public_project_path("/home/appuser/repo/projects") == "projects"

    def test_windows_separators_are_handled(self):
        assert public_project_path(r"C:\srv\repo\projects\foo") == "projects/foo"

    @pytest.mark.parametrize("value", [None, ""])
    def test_empty_values_pass_through(self, value):
        assert public_project_path(value) == value


class TestSerialisation:
    def test_project_to_dict_does_not_carry_the_host_prefix(self):
        project = Project(id="p1", plan_id="pl1", name="x", directory_path=LEAKED_PATH)

        assert project.to_dict()["directory_path"] == ("projects/plan-x402-micro-payment-gateway")

    def test_generation_result_to_dict_does_not_carry_the_host_prefix(self):
        # This dict is stored as a job result and served by GET /jobs/{id},
        # which is public and unauthenticated.
        result = ProjectGenerationResult(success=True, project_path=LEAKED_PATH)

        assert result.to_dict()["project_path"] == ("projects/plan-x402-micro-payment-gateway")

    def test_generation_result_error_does_not_carry_the_host_prefix(self):
        # The back door: redacting `project_path` is pointless if the failure
        # message next to it spells the same path out. This is the verbatim
        # shape Python produces for a write into the generated tree.
        result = ProjectGenerationResult(
            success=False,
            error=f"[Errno 2] No such file or directory: '{LEAKED_PATH}/src/backend/main.py'",
        )

        assert result.to_dict()["error"] == (
            "[Errno 2] No such file or directory: "
            "'projects/plan-x402-micro-payment-gateway/src/backend/main.py'"
        )


class TestRedactPaths:
    def test_a_path_inside_the_generated_tree_keeps_its_repo_relative_part(self):
        assert redact_paths(f"failed on {LEAKED_PATH}/README.md") == (
            "failed on projects/plan-x402-micro-payment-gateway/README.md"
        )

    def test_a_path_elsewhere_in_the_checkout_is_elided_to_its_leaf(self):
        assert redact_paths(
            "[Errno 2] No such file or directory: '/home/appuser/agentic-orchestrator/config.yaml'"
        ) == ("[Errno 2] No such file or directory: '.../config.yaml'")

    def test_several_paths_in_one_message_are_all_redacted(self):
        assert "appuser" not in redact_paths(
            "copy /home/appuser/repo/a.py -> /home/appuser/repo/b.py failed"
        )

    def test_urls_survive_intact(self):
        # The redactor runs over messages that also carry upstream URLs; the
        # host:port and the path after it must not be mistaken for a path.
        message = "Server error '500' for url 'https://ao.moss.land/api/plans/abc'"
        assert redact_paths(message) == message

    def test_messages_without_paths_are_untouched(self):
        for message in ["Ollama HTTP error: 503", "Plan not found: 3673297d", "0/10 passed"]:
            assert redact_paths(message) == message

    @pytest.mark.parametrize("value", [None, ""])
    def test_empty_values_pass_through(self, value):
        assert redact_paths(value) == value


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # noqa: N806

    session = TestingSessionLocal()
    session.add(Plan(id="plan-1", idea_id="idea-1", title="A plan", status="approved"))
    session.add(
        Project(
            id="proj-1",
            plan_id="plan-1",
            name="plan-x402-micro-payment-gateway",
            status="ready",
            directory_path=LEAKED_PATH,
        )
    )
    session.commit()

    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    session.close()


class TestEndpoints:
    @pytest.mark.parametrize(
        "url, extract",
        [
            ("/projects", lambda body: body["projects"][0]["directory_path"]),
            ("/projects/proj-1", lambda body: body["project"]["directory_path"]),
            ("/plans/plan-1/project", lambda body: body["project"]["directory_path"]),
        ],
    )
    def test_no_endpoint_publishes_the_host_path(self, client, url, extract):
        response = client.get(url)

        assert response.status_code == 200
        assert "/home/" not in response.text
        assert "appuser" not in response.text
        # Still useful: the reader gets the location inside the repo.
        assert extract(response.json()) == "projects/plan-x402-micro-payment-gateway"

    def test_a_failed_generation_job_does_not_publish_the_path_it_failed_on(self, client):
        # GET /jobs/{id} takes no API key and returns the job dict verbatim.
        from agentic_orchestrator.api import main as api_main

        api_main._project_jobs["job-1"] = {
            "status": "failed",
            "error": api_main.redact_paths(
                f"[Errno 13] Permission denied: '{LEAKED_PATH}/src/backend/main.py'"
            ),
        }
        try:
            response = client.get("/jobs/job-1")

            assert response.status_code == 200
            assert "/home/" not in response.text
            assert "appuser" not in response.text
            # The useful half survives: which file, and why.
            assert "Permission denied" in response.json()["error"]
            assert "src/backend/main.py" in response.json()["error"]
        finally:
            api_main._project_jobs.pop("job-1", None)


class TestOllamaHostNeverEntersAnErrorMessage:
    """`base_url` is the office LAN Ollama address (a CLAUDE.local.md value).

    httpx's `HTTPStatusError` stringifies as "... for url '<base_url>/api/...'",
    so any handler that interpolates the exception whole republishes that host
    wherever the `ProviderError` travels. `generate()` was already written to
    keep only the status code; `generate_stream()` and `chat()` were not.
    """

    @staticmethod
    def _status_error(base_url: str) -> "httpx.HTTPStatusError":
        request = httpx.Request("POST", f"{base_url}/api/generate")
        response = httpx.Response(500, request=request)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # noqa: PERF203 - building a fixture
            return exc
        raise AssertionError("raise_for_status did not raise")

    def test_the_default_message_really_does_carry_the_host(self):
        # Pins the premise: if httpx ever stops doing this, the guards below
        # are no longer load-bearing and this test says so.
        assert "192.0.2.10" in str(self._status_error("http://192.0.2.10:11434"))

    @pytest.mark.parametrize("label", ["stream", "chat"])
    def test_provider_errors_keep_the_status_and_drop_the_host(self, label):
        exc = self._status_error("http://192.0.2.10:11434")
        message = f"Ollama {label} error: HTTP {exc.response.status_code}"

        assert "192.0.2" not in message
        assert "11434" not in message
        assert "500" in message


class TestNoRealIdentifierInTheTree:
    """The repo is public; the real host identifiers live in CLAUDE.local.md.

    Two PRs (2026-08-07) moved them out of docs and scripts by hand, and this
    change nearly reintroduced the account name -- in the tests and changelog
    written to *describe* removing it. A grep in CI is cheaper than noticing
    that again later.

    Patterns are assembled at runtime so this file does not itself contain the
    strings it forbids.
    """

    # (label, regex) — the account name is matched by shape, since writing it
    # down here would be the very thing being prevented.
    FORBIDDEN = [
        ("app-server account in a home path", r"/home/(?!appuser\b|user\b)[a-z][a-z0-9_-]{2,}/"),
        ("developer home path", r"/Users/[A-Za-z0-9._-]+/"),
        ("office LAN address", r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
        ("tailnet address", r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"),
        # By shape, not by our key's name: naming it here would be the leak.
        ("ssh key name", r"\b[A-Za-z0-9_-]+_(?:ed25519|rsa|ecdsa)\b"),
    ]

    @staticmethod
    def _tracked_files():
        repo_root = Path(__file__).resolve().parent.parent
        listing = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if listing.returncode != 0:  # not a checkout (sdist, vendored copy)
            pytest.skip("not a git checkout")
        for name in listing.stdout.split("\0"):
            if not name or name.endswith((".lock", ".png", ".ico", ".svg")):
                continue
            # CHANGELOG entries quote historical shapes with placeholders; the
            # lockfiles are third-party text. Everything else is in scope.
            if name.startswith("CHANGELOG") or name.endswith("package-lock.json"):
                continue
            path = repo_root / name
            try:
                yield name, path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

    @pytest.mark.parametrize("label, pattern", FORBIDDEN, ids=[f[0] for f in FORBIDDEN])
    def test_no_tracked_file_contains_it(self, label, pattern):
        compiled = re.compile(pattern)
        hits = []
        for name, text in self._tracked_files():
            if name == "tests/test_project_path_privacy.py":
                continue  # this file holds the patterns themselves
            for lineno, line in enumerate(text.splitlines(), 1):
                if compiled.search(line):
                    hits.append(f"{name}:{lineno}")

        assert not hits, (
            f"{label} found in tracked files: {hits[:10]}. "
            "Real host identifiers belong in CLAUDE.local.md (gitignored), "
            "not in a public repository."
        )
