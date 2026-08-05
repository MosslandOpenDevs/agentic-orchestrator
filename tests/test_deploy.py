"""Behavioural tests for scripts/deploy.sh (the pull-based auto-deployer).

The script is what stands between `git push` and production, so it is tested by
actually running it: each test builds a throwaway origin/checkout pair and puts
stub `pm2`, `npm` and `curl` executables first on PATH, so the real script takes
its real code paths against fake infrastructure.

What is deliberately pinned here:

* the no-op fast path (it runs every 5 minutes -- it must stay free and silent),
* the guards that stop a bad deploy (CI red/pending, dirty tree, busy scheduler),
* rollback when the post-deploy health check fails,
* and above all that untracked server state -- data/orchestrator.db, .env --
  survives a deploy. That is the 2026-07 outage in test form: the DB is a single
  untracked SQLite file, and a deployer that reaches for `git clean` destroys it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SH = REPO_ROOT / "scripts" / "deploy.sh"
ECOSYSTEM = REPO_ROOT / "ecosystem.config.js"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("git") is None,
    reason="bash and git are required to exercise the deploy script",
)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}

CI_SUCCESS = json.dumps(
    {"check_runs": [{"name": "test (3.12)", "status": "completed", "conclusion": "success"}]}
)
CI_PENDING = json.dumps({"check_runs": [{"status": "in_progress"}]})
CI_FAILURE = json.dumps({"check_runs": [{"status": "completed", "conclusion": "failure"}]})
# A commit GitHub has not registered any checks for -- the usual state seconds
# after a push, which the poller sees before CI has started.
CI_NONE = json.dumps({"check_runs": []})
CI_SKIPPED = json.dumps({"check_runs": [{"status": "completed", "conclusion": "skipped"}]})
CI_STALE = json.dumps({"check_runs": [{"status": "completed", "conclusion": "stale"}]})
# Shapes the GitHub API should never produce. The gate parser raises on
# these; what matters is that the script still refuses to deploy.
CI_WRONG_SHAPE = json.dumps({"check_runs": {"unexpected": "object"}})
CI_RUNS_NOT_OBJECTS = json.dumps({"check_runs": ["not-an-object"]})


def _git(cwd: Path, *args: str) -> str:
    env = {**os.environ, **GIT_ENV}
    return subprocess.run(
        ["git", *args], cwd=cwd, env=env, capture_output=True, text=True, check=True
    ).stdout.strip()


def _write(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if executable:
        path.chmod(0o755)


class Server:
    """A disposable origin + checkout + stubbed PM2/npm/curl environment."""

    def __init__(self, tmp_path: Path):
        self.root = tmp_path
        self.origin = tmp_path / "origin.git"
        self.checkout = tmp_path / "checkout"
        self.bin = tmp_path / "bin"
        self.stub_log = tmp_path / "stub.log"
        self.jlist = tmp_path / "jlist.json"
        self.health_fail = tmp_path / "health_fail"
        # "1" makes /ready 404 while /health still answers -- what a
        # rollback to a commit predating the /ready route looks like.
        self.ready_missing = tmp_path / "ready_missing"

        subprocess.run(
            ["git", "init", "--quiet", "--bare", "-b", "main", str(self.origin)],
            check=True,
        )

        seed = tmp_path / "seed"
        seed.mkdir()
        _git(seed, "init", "--quiet", "-b", "main")
        _write(seed / "src" / "agentic_orchestrator" / "api.py", "VERSION = 1\n")
        _write(seed / "website" / "package.json", '{"name": "web"}\n')
        _write(seed / "pyproject.toml", 'version = "0.0.1"\n')
        _write(seed / "README.md", "seed\n")
        _git(seed, "add", "-A")
        _git(seed, "commit", "--quiet", "-m", "seed")
        _git(seed, "remote", "add", "origin", str(self.origin))
        _git(seed, "push", "--quiet", "origin", "main")
        self.seed = seed

        subprocess.run(
            ["git", "clone", "--quiet", str(self.origin), str(self.checkout)],
            check=True,
        )
        shutil.copy(DEPLOY_SH, self._scripts_dir() / "deploy.sh")
        (self.checkout / "scripts" / "deploy.sh").chmod(0o755)

        # Untracked server state: exactly what a deploy must never destroy.
        _write(self.checkout / "data" / "orchestrator.db", "SQLITE-DATA")
        _write(self.checkout / ".env", "OLLAMA_HOST=http://localhost:11434\n")
        _write(self.checkout / "website" / ".env.local", "NEXT_PUBLIC_API_URL=/api\n")

        self.jlist.write_text("[]")
        self.health_fail.write_text("0")
        self.ready_missing.write_text("0")
        self._write_stubs()

    def _scripts_dir(self) -> Path:
        d = self.checkout / "scripts"
        d.mkdir(exist_ok=True)
        return d

    def _write_stubs(self) -> None:
        self.bin.mkdir()
        # The real PM2 injects the calling app's config keys (cron_restart,
        # autorestart, ...) into child environments as plain variables. If
        # deploy.sh lets them through, `--update-env` stamps them onto the
        # restarted apps (the 2026-08-05 incident) -- so the stub reports every
        # scrub-list key it can see and TestPm2EnvHygiene asserts it sees none.
        # The name list must match deploy.sh's `unset -v` line: dropping a key
        # there makes the stub report it here.
        _write(
            self.bin / "pm2",
            f"""#!/usr/bin/env bash
echo "pm2 $*" >> "{self.stub_log}"
for k in cron_restart autorestart watch instances exec_mode \\
         max_memory_restart node_args name namespace; do
  if [ -n "${{!k:-}}" ]; then
    echo "pm2-saw-env $k=${{!k}}" >> "{self.stub_log}"
  fi
done
if [ "$1" = "jlist" ]; then cat "{self.jlist}"; fi
exit 0
""",
            executable=True,
        )
        _write(
            self.bin / "npm",
            f"""#!/usr/bin/env bash
echo "npm $*" >> "{self.stub_log}"
exit 0
""",
            executable=True,
        )
        # curl serves three callers: the GitHub check-runs API, the two health
        # probes, and the (unset) alert webhook.
        _write(
            self.bin / "curl",
            f"""#!/usr/bin/env bash
url=""
for a in "$@"; do url="$a"; done
echo "curl $url" >> "{self.stub_log}"
case "$url" in
  *api.github.com*)
    printf '%s' "$CI_JSON"
    exit 0
    ;;
  */ready)
    if [ "$(cat "{self.ready_missing}" 2>/dev/null || echo 0)" = "1" ]; then
      exit 22
    fi
    n=$(cat "{self.health_fail}" 2>/dev/null || echo 0)
    if [ "$n" -gt 0 ]; then
      echo $((n - 1)) > "{self.health_fail}"
      exit 22
    fi
    printf '{{"status":"ready"}}'
    exit 0
    ;;
  *)
    n=$(cat "{self.health_fail}" 2>/dev/null || echo 0)
    if [ "$n" -gt 0 ]; then
      echo $((n - 1)) > "{self.health_fail}"
      exit 22
    fi
    printf '{{"status":"healthy"}}'
    exit 0
    ;;
esac
""",
            executable=True,
        )
        # Stands in for .venv/bin/python (backup-db, pip install -e .). The two
        # callers get separate exit codes: the deploy refuses to run at all
        # when the pre-deploy snapshot fails, so a test about a failing
        # `pip install` must still be able to take a snapshot first.
        _write(
            self.bin / "venv-python",
            f"""#!/usr/bin/env bash
echo "python $*" >> "{self.stub_log}"
case "$*" in
  *backup-db*) exit ${{BACKUP_STUB_EXIT:-0}} ;;
esac
exit ${{PYTHON_STUB_EXIT:-0}}
""",
            executable=True,
        )
        _write(
            self.bin / "uv",
            f"""#!/usr/bin/env bash
echo "uv $*" >> "{self.stub_log}"
exit ${{UV_STUB_EXIT:-0}}
""",
            executable=True,
        )

    def make_uv_managed(self, *, via: str = "lockfile") -> None:
        """Mark the checkout as uv-managed the way the real server is."""
        if via == "lockfile":
            _write(self.checkout / "uv.lock", "# lock\n")
        else:
            _write(
                self.checkout / ".venv" / "pyvenv.cfg",
                "home = /home/atrn/.local/share/uv/python/cpython-3.12.13\nuv = 0.11.21\n",
            )

    # -- helpers ---------------------------------------------------------
    def push(self, files: dict[str, str], message: str = "update") -> str:
        for rel, content in files.items():
            _write(self.seed / rel, content)
        _git(self.seed, "add", "-A")
        _git(self.seed, "commit", "--quiet", "-m", message)
        _git(self.seed, "push", "--quiet", "origin", "main")
        return _git(self.seed, "rev-parse", "HEAD")

    def head(self) -> str:
        return _git(self.checkout, "rev-parse", "HEAD")

    def run(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        full_env = {
            **os.environ,
            **GIT_ENV,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "PYTHON_BIN": str(self.bin / "venv-python"),
            "UV_BIN": str(self.bin / "uv"),
            "DEPLOY_GITHUB_REPO": "test/repo",
            "DEPLOY_REQUIRE_CI": "0",
            "CI_JSON": CI_SUCCESS,
            "DEPLOY_HEALTH_RETRIES": "2",
            "DEPLOY_HEALTH_INTERVAL": "0",
            **env,
        }
        return subprocess.run(
            ["bash", str(self.checkout / "scripts" / "deploy.sh"), *args],
            cwd=self.checkout,
            env=full_env,
            capture_output=True,
            text=True,
        )

    def calls(self) -> str:
        return self.stub_log.read_text() if self.stub_log.exists() else ""


@pytest.fixture()
def server(tmp_path: Path) -> Server:
    return Server(tmp_path)


class TestNoOpPath:
    def test_up_to_date_is_a_silent_no_op(self, server: Server):
        before = server.head()
        result = server.run()

        assert result.returncode == 0
        assert server.head() == before
        # Runs every 5 minutes: no log line, no pm2/npm/curl work.
        assert result.stdout.strip() == ""
        assert "pm2" not in server.calls()
        assert not (server.checkout / "logs" / "deploy.log").exists()

    def test_verbose_reports_up_to_date(self, server: Server):
        result = server.run(DEPLOY_VERBOSE="1")
        assert "up to date" in result.stdout


class TestDeploy:
    def test_deploys_backend_and_frontend_change(self, server: Server):
        target = server.push(
            {
                "src/agentic_orchestrator/api.py": "VERSION = 2\n",
                "website/page.tsx": "export default () => null\n",
            }
        )
        result = server.run()

        assert result.returncode == 0, result.stdout + result.stderr
        assert server.head() == target
        calls = server.calls()
        assert "npm run build" in calls
        assert "pm2 restart moss-ao-api" in calls
        assert "pm2 restart moss-ao-web" in calls
        assert "DEPLOYED" in result.stdout
        # Readiness, not liveness: /health answered 200 all through the 2026-07
        # incident while every DB-backed endpoint was returning 500.
        assert "/ready" in calls
        assert "/health" not in calls

    def test_untracked_server_state_survives_a_deploy(self, server: Server):
        """The 2026-07 outage, pinned: the DB and .env are untracked."""
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 3\n"})
        server.run()

        assert (server.checkout / "data" / "orchestrator.db").read_text() == "SQLITE-DATA"
        assert (server.checkout / ".env").exists()
        assert (server.checkout / "website" / ".env.local").exists()

    def test_failed_snapshot_refuses_to_deploy(self, server: Server):
        """The snapshot IS the restore point for the change being applied.
        Deploying after it failed is the 2026-07 outage with no way back."""
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 22\n"})

        result = server.run(BACKUP_STUB_EXIT="1")

        assert result.returncode == 1
        assert server.head() == before
        assert "refusing to deploy without a restore point" in result.stdout
        # Nothing was built or restarted.
        assert "pm2 restart" not in server.calls()

    def test_nothing_to_snapshot_is_not_a_failure(self, server: Server):
        """backup-db exits 2 when the database is missing/empty/dataless --
        benign (a fresh server), so the deploy proceeds."""
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 23\n"})

        result = server.run(BACKUP_STUB_EXIT="2")

        assert server.head() == target
        assert "nothing to snapshot yet" in result.stdout
        assert "DEPLOYED" in result.stdout

    def test_missing_python_refuses_to_deploy(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 24\n"})

        result = server.run(PYTHON_BIN=str(server.bin / "no-such-python"))

        assert result.returncode == 1
        assert server.head() == before
        assert "refusing to deploy without a DB snapshot" in result.stdout

    def test_pre_deploy_database_snapshot_is_taken(self, server: Server):
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 4\n"})
        server.run()

        assert "scheduler backup-db" in server.calls()

    def test_dependency_install_only_when_pyproject_changes(self, server: Server):
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 5\n"})
        server.run()
        assert "pip install" not in server.calls()

        server.push({"pyproject.toml": 'version = "0.0.2"\n'})
        server.run()
        assert "pip install" in server.calls()

    def test_a_lock_only_change_still_installs(self, server: Server):
        """uv.lock is tracked now, so a dependency bump can arrive with no
        pyproject change at all. Without a classifier entry that commit reads
        as docs-only: HEAD advances, nothing installs, and because HEAD has
        moved no later tick will either."""
        server.make_uv_managed()
        server.push({"uv.lock": "# bumped\n"})

        result = server.run()

        calls = server.calls()
        assert "uv sync" in calls
        assert "pm2 restart moss-ao-api" in calls
        assert "docs only" not in result.stdout

    def test_uv_sync_never_rewrites_the_tracked_lockfile(self, server: Server):
        """A non-frozen sync re-resolves and can rewrite uv.lock -- a tracked
        file. The dirty-tree guard would then abort every subsequent tick until
        a human intervened, wedging the 5-minute loop."""
        server.make_uv_managed()
        server.push({"pyproject.toml": 'version = "0.0.20"\n'})

        server.run()

        assert "uv sync --frozen" in server.calls()

    def test_uv_managed_checkout_syncs_with_uv(self, server: Server):
        """The production .venv is built by uv and contains no pip at all."""
        server.make_uv_managed()
        server.push({"pyproject.toml": 'version = "0.0.9"\n'})
        server.run()

        calls = server.calls()
        assert "uv sync" in calls
        assert "pip install" not in calls

    def test_uv_detected_from_the_venv_when_no_lockfile_is_present(self, server: Server):
        server.make_uv_managed(via="pyvenv")
        server.push({"pyproject.toml": 'version = "0.0.10"\n'})
        server.run()

        assert "uv sync" in server.calls()

    def test_plain_venv_checkout_still_uses_pip(self, server: Server):
        server.push({"pyproject.toml": 'version = "0.0.11"\n'})
        server.run()

        calls = server.calls()
        assert "pip install" in calls
        assert "uv sync" not in calls

    def test_a_pip_venv_wins_over_the_committed_lockfile(self, server: Server):
        """uv.lock is tracked now, so every checkout has one. What the venv
        records about how it was built has to take precedence, or a pip-managed
        machine would be handed to `uv sync`."""
        _write(server.checkout / "uv.lock", "# lock\n")
        _write(
            server.checkout / ".venv" / "pyvenv.cfg",
            "home = /usr/bin\ninclude-system-site-packages = false\n",
        )
        server.push({"pyproject.toml": 'version = "0.0.12"\n'})
        server.run()

        calls = server.calls()
        assert "pip install" in calls
        assert "uv sync" not in calls

    def test_failed_uv_sync_rolls_back(self, server: Server):
        before = server.head()
        server.make_uv_managed()
        server.push({"pyproject.toml": 'version = "0.0.12"\n'})

        result = server.run(UV_STUB_EXIT="1")

        assert result.returncode == 1
        assert server.head() == before
        assert "uv sync failed" in result.stdout

    def test_docs_only_change_restarts_nothing(self, server: Server):
        target = server.push({"README.md": "docs only\n"})
        server.run()

        assert server.head() == target
        assert "pm2 restart" not in server.calls()
        assert "npm run build" not in server.calls()

    def test_docs_only_change_skips_the_db_snapshot(self, server: Server):
        """Nothing restarts, so a snapshot protects nothing — and each one
        rotates the 7-slot backup window. A docs merge burst must not churn
        days of restore points into minutes."""
        server.push({"README.md": "docs only again\n"})
        result = server.run()

        assert "scheduler backup-db" not in server.calls()
        assert "skipping DB snapshot" in result.stdout

    def test_frontend_change_alone_does_not_restart_the_api(self, server: Server):
        server.push({"website/page.tsx": "export default () => 1\n"})
        server.run()

        calls = server.calls()
        assert "pm2 restart moss-ao-web" in calls
        assert "pm2 restart moss-ao-api" not in calls

    def test_check_mode_changes_nothing(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 6\n"})
        result = server.run("--check")

        assert server.head() == before
        assert "would deploy" in result.stdout
        assert "pm2 restart" not in server.calls()


class TestGuards:
    def test_local_edits_to_tracked_files_block_the_deploy(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 7\n"})
        (server.checkout / "README.md").write_text("hand-edited on the server\n")

        result = server.run()

        assert server.head() == before
        assert "ABORT" in result.stdout
        assert (server.checkout / "README.md").read_text() == "hand-edited on the server\n"

    def test_force_overrides_the_dirty_tree_guard(self, server: Server):
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 8\n"})
        (server.checkout / "README.md").write_text("hand-edited\n")

        server.run("--force")

        assert server.head() == target

    def test_wrong_branch_checkout_is_left_alone(self, server: Server):
        _git(server.checkout, "checkout", "--quiet", "-b", "hotfix")
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 9\n"})

        result = server.run()

        assert server.head() == before
        assert "not touching it" in result.stdout

    def test_red_ci_blocks_the_deploy(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 10\n"})

        result = server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=CI_FAILURE)

        assert server.head() == before
        assert "CI: FAILED" in result.stdout

    def test_pending_ci_defers_rather_than_failing(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 11\n"})

        result = server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=CI_PENDING)

        assert result.returncode == 0
        assert server.head() == before
        assert "deferring" in result.stdout

    def test_green_ci_deploys(self, server: Server):
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 12\n"})

        result = server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=CI_SUCCESS)

        assert server.head() == target
        assert "CI: green" in result.stdout

    def test_unreachable_ci_api_defers_instead_of_deploying_blind(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 13\n"})

        result = server.run(DEPLOY_REQUIRE_CI="1", CI_JSON="not json at all")

        assert server.head() == before
        assert "status unavailable" in result.stdout

    def test_no_checks_reported_defers_instead_of_deploying_unverified(self, server: Server):
        """Zero checks is not a green build. It is usually just CI not having
        registered yet -- the poller runs every 5 minutes and can easily fire
        seconds after the push. Deploying on it shipped unverified commits."""
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 18\n"})

        result = server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=CI_NONE)

        assert result.returncode == 0
        assert server.head() == before
        assert "no checks reported" in result.stdout
        assert "deferring" in result.stdout

    @pytest.mark.parametrize("ci_json", [CI_SKIPPED, CI_STALE], ids=["skipped", "stale"])
    def test_checks_that_verified_nothing_defer(self, server: Server, ci_json: str):
        """skipped/stale conclusions used to fall through to "success" because
        they were merely absent from the failure list."""
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 19\n"})

        result = server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=ci_json)

        assert result.returncode == 0
        assert server.head() == before
        assert "none verified the commit" in result.stdout

    @pytest.mark.parametrize(
        "ci_json",
        [CI_WRONG_SHAPE, CI_RUNS_NOT_OBJECTS],
        ids=["check_runs-is-an-object", "runs-are-not-objects"],
    )
    def test_unexpected_api_shapes_never_deploy(self, server: Server, ci_json: str):
        """The parser cannot make sense of these and raises. The wrapper has to
        turn that into a deferral, not a green light."""
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 25\n"})

        result = server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=ci_json)

        assert result.returncode == 0
        assert server.head() == before
        assert "pm2 restart" not in server.calls()

    def test_required_jobs_must_all_have_passed(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 20\n"})

        result = server.run(
            DEPLOY_REQUIRE_CI="1",
            CI_JSON=CI_SUCCESS,  # only reports "test (3.12)"
            DEPLOY_REQUIRE_CI_JOBS="test (3.12),lint",
        )

        assert server.head() == before
        assert "required jobs" in result.stdout

    def test_required_jobs_present_deploys(self, server: Server):
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 21\n"})

        result = server.run(
            DEPLOY_REQUIRE_CI="1",
            CI_JSON=CI_SUCCESS,
            DEPLOY_REQUIRE_CI_JOBS="test (3.12)",
        )

        assert server.head() == target
        assert "CI: green" in result.stdout

    def test_backend_deploy_waits_for_a_running_debate(self, server: Server):
        before = server.head()
        server.jlist.write_text(
            json.dumps([{"name": "moss-ao-debate", "pm2_env": {"status": "online"}}])
        )
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 14\n"})

        result = server.run()

        assert server.head() == before
        assert "scheduler busy" in result.stdout

    def test_frontend_deploy_proceeds_during_a_debate(self, server: Server):
        server.jlist.write_text(
            json.dumps([{"name": "moss-ao-debate", "pm2_env": {"status": "online"}}])
        )
        target = server.push({"website/page.tsx": "export default () => 2\n"})

        server.run()

        assert server.head() == target

    def test_concurrent_run_is_skipped(self, server: Server):
        (server.checkout / "logs").mkdir(exist_ok=True)
        (server.checkout / "logs" / ".deploy.lock").mkdir()
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 15\n"})

        result = server.run(DEPLOY_VERBOSE="1")

        assert result.returncode == 0
        assert server.head() == before
        assert "another deploy is running" in result.stdout


class TestRollback:
    def test_failed_health_check_rolls_back(self, server: Server):
        before = server.head()
        server.push(
            {
                "src/agentic_orchestrator/api.py": "VERSION = 16\n",
                "website/page.tsx": "export default () => 3\n",
            }
        )
        # 2 retries x 2 probes = 4 failing health calls, then healthy again, so
        # the deploy fails and the rollback comes back up.
        server.health_fail.write_text("4")

        result = server.run()

        assert result.returncode == 1
        assert server.head() == before
        assert "ROLLBACK" in result.stdout
        assert "rollback healthy" in result.stdout
        # The rollback rebuilt the frontend rather than leaving the new bundle.
        assert server.calls().count("npm run build") == 2

    def test_failed_build_rolls_back_without_restarting(self, server: Server):
        before = server.head()
        server.push({"pyproject.toml": 'version = "0.0.3"\n'})
        result = server.run(PYTHON_STUB_EXIT="1")

        assert result.returncode == 1
        assert server.head() == before
        assert "pip install failed" in result.stdout

    def test_rollback_accepts_a_target_that_predates_ready(self, server: Server):
        """/ready is new. A rollback target may not have it, and a 404 there
        would report a healthy rollback as CRITICAL."""
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 31\n"})
        # /ready always 404s; /health answers. The forward deploy therefore
        # fails its health check and rolls back, and the rollback must pass.
        server.ready_missing.write_text("1")

        result = server.run()

        assert server.head() == before
        assert "rollback healthy" in result.stdout
        assert "CRITICAL" not in result.stdout

    def test_unhealthy_rollback_is_reported_as_critical(self, server: Server):
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 17\n"})
        server.health_fail.write_text("999")

        result = server.run()

        assert result.returncode == 1
        assert "CRITICAL" in result.stdout


class TestEcosystemChanges:
    """PM2 process definitions (cron, env) are not re-registered automatically
    -- doing that from inside a PM2-managed process is the 2026-08-05 incident.
    But HEAD moves past the commit either way and the next tick is a no-op, so
    a single log line was the entire notification: a cron or env change could
    sit unapplied indefinitely with nothing left pointing at it."""

    def test_change_is_recorded_and_keeps_reminding(self, server: Server):
        server.push({"ecosystem.config.js": "module.exports = { apps: [] }\n"})
        first = server.run()

        assert "ecosystem" in first.stdout.lower()
        pending = server.checkout / "logs" / ".ecosystem-pending"
        assert pending.exists()

        # Nothing new to deploy: the reminder still has to appear.
        second = server.run()
        assert "REMINDER" in second.stdout
        assert "pm2 restart ecosystem.config.js" in second.stdout

    def test_an_unwritable_record_does_not_abort_the_deploy(self, server: Server):
        """Recording the pending change happens after `git reset --hard` and
        before the build. Aborting there would leave git on the new commit with
        PM2 still running the old code, and no later tick would retry."""
        logs = server.checkout / "logs"
        logs.mkdir(exist_ok=True)
        pending = logs / ".ecosystem-pending"
        pending.write_text("")
        pending.chmod(0o444)
        try:
            target = server.push(
                {
                    "ecosystem.config.js": "module.exports = { apps: [] }\n",
                    "src/agentic_orchestrator/api.py": "VERSION = 30\n",
                }
            )
            result = server.run()

            assert result.returncode == 0, result.stdout + result.stderr
            assert server.head() == target
            assert "pm2 restart moss-ao-api" in server.calls()
        finally:
            pending.chmod(0o644)

    def test_reminder_stops_once_the_operator_clears_it(self, server: Server):
        server.push({"ecosystem.config.js": "module.exports = { apps: [] }\n"})
        server.run()
        (server.checkout / "logs" / ".ecosystem-pending").unlink()

        assert "REMINDER" not in server.run().stdout

    def test_no_reminder_when_nothing_is_pending(self, server: Server):
        server.push({"README.md": "docs\n"})

        assert "REMINDER" not in server.run().stdout


class TestPm2EnvHygiene:
    """PM2 injects the deploy poller's own config keys (cron_restart,
    autorestart, ...) into this script's environment as plain variables, and
    PM2 reads those same names back as config. Combined with
    `pm2 restart --update-env` that stamped the poller's 5-minute cron onto
    moss-ao-api/web, force-restarting them every 5 minutes until the entries
    were deleted and re-registered (2026-08-05 incident, docs/deployment.md).
    These tests run the deploy with that injection simulated and pin both
    halves of the fix: no --update-env, and the injected keys are scrubbed."""

    # Every key deploy.sh's `unset -v` scrubs, with the value PM2 would inject.
    PM2_INJECTED = {
        "cron_restart": "4-59/5 * * * *",
        "autorestart": "false",
        "watch": "true",
        "instances": "1",
        "exec_mode": "fork_mode",
        "max_memory_restart": "1073741824",
        "node_args": "--max-old-space-size=512",
        "name": "moss-ao-deploy",
        "namespace": "default",
    }

    def test_restarts_never_pass_update_env(self, server: Server):
        server.push(
            {
                "src/agentic_orchestrator/api.py": "VERSION = 18\n",
                "website/page.tsx": "export default () => 4\n",
            }
        )
        result = server.run(**self.PM2_INJECTED)

        assert result.returncode == 0, result.stdout + result.stderr
        restarts = [c for c in server.calls().splitlines() if c.startswith("pm2 restart")]
        assert restarts, "expected pm2 restarts to happen"
        # Whole-log, not restart-lines-only: --update-env on ANY pm2 verb
        # (start/reload/startOrRestart) re-creates the incident just as well.
        assert "--update-env" not in server.calls()

    def test_deploy_only_uses_safe_pm2_verbs(self, server: Server):
        """A deploy may query (jlist) and plain-restart -- never register
        (`pm2 start`), never `pm2 save`: registration from inside the poller
        captures the poller's entire environment (GITHUB_TOKEN, DEPLOY_*, and
        config-shaped keys beyond the scrub list) into every app's stored
        definition, --update-env or not."""
        server.push(
            {
                "src/agentic_orchestrator/api.py": "VERSION = 20\n",
                "website/page.tsx": "export default () => 6\n",
            }
        )
        result = server.run(**self.PM2_INJECTED)

        assert result.returncode == 0, result.stdout + result.stderr
        verbs = {c.split()[1] for c in server.calls().splitlines() if c.startswith("pm2 ")}
        assert verbs, "expected pm2 to be invoked"
        assert verbs <= {"jlist", "restart"}, verbs

    def test_pm2_never_sees_the_pollers_injected_config_keys(self, server: Server):
        server.push(
            {
                "src/agentic_orchestrator/api.py": "VERSION = 19\n",
                "website/page.tsx": "export default () => 5\n",
            }
        )
        result = server.run(**self.PM2_INJECTED)

        assert result.returncode == 0, result.stdout + result.stderr
        calls = server.calls()
        assert "pm2 restart moss-ao-api" in calls
        assert "pm2 restart moss-ao-web" in calls
        assert "pm2-saw-env" not in calls


class TestSourceInvariants:
    def test_deploy_script_never_runs_git_clean(self):
        """`git clean` on the server deletes the SQLite DB and .env."""
        source = DEPLOY_SH.read_text()
        code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
        assert "git clean" not in code

    def test_pm2_invocations_never_pass_update_env(self):
        """--update-env may only appear in operator-facing log text, never on
        an actual pm2 invocation (see TestPm2EnvHygiene for why)."""
        for line in DEPLOY_SH.read_text().splitlines():
            if "--update-env" in line:
                assert line.lstrip().startswith(("log ", "#")), line

    def test_deploy_script_is_executable(self):
        assert os.access(DEPLOY_SH, os.X_OK)

    def test_deploy_script_passes_bash_syntax_check(self):
        result = subprocess.run(["bash", "-n", str(DEPLOY_SH)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
class TestEcosystemRegistration:
    def _apps(self, auto_deploy: str | None) -> list[dict]:
        env = {**os.environ}
        env.pop("MOSS_AO_AUTO_DEPLOY", None)
        if auto_deploy is not None:
            env["MOSS_AO_AUTO_DEPLOY"] = auto_deploy
        out = subprocess.run(
            [
                "node",
                "-e",
                f"console.log(JSON.stringify(require({str(ECOSYSTEM)!r}).apps))",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=True,
        ).stdout
        return json.loads(out)

    def _names(self, auto_deploy: str | None) -> set[str]:
        return {app["name"] for app in self._apps(auto_deploy)}

    def test_auto_deploy_is_off_by_default(self):
        assert "moss-ao-deploy" not in self._names(None)
        assert "moss-ao-deploy" not in self._names("0")

    def test_auto_deploy_is_registered_when_opted_in(self):
        assert "moss-ao-deploy" in self._names("1")

    def test_deploy_app_is_cron_driven_and_does_not_respawn(self):
        app = next(a for a in self._apps("1") if a["name"] == "moss-ao-deploy")

        assert app["script"] == "scripts/deploy.sh"
        assert app["interpreter"] == "bash"
        assert app["autorestart"] is False
        assert app["cron_restart"]

    def test_long_running_apps_have_no_cron_restart(self):
        """api/web are always-on: a cron_restart here (or leaked onto the
        live registration, as in the 2026-08-05 incident) bounces them every
        few minutes."""
        apps = self._apps("1")
        for app_name in ("moss-ao-api", "moss-ao-web"):
            app = next(a for a in apps if a["name"] == app_name)
            assert "cron_restart" not in app, app_name
            assert app["autorestart"] is True, app_name

    def test_deploy_cron_does_not_collide_with_the_health_cron(self):
        apps = self._apps("1")
        health = next(a for a in apps if a["name"] == "moss-ao-health")
        deploy = next(a for a in apps if a["name"] == "moss-ao-deploy")

        assert deploy["cron_restart"] != health["cron_restart"]
