"""Behavioural tests for scripts/deploy.sh (the pull-based auto-deployer).

The script is what stands between `git push` and production, so it is tested by
actually running it: each test builds a throwaway origin/checkout pair and puts
stub `pm2`, `npm` and `curl` executables first on PATH, so the real script takes
its real code paths against fake infrastructure.

What is deliberately pinned here:

* the no-op fast path (it runs every 5 minutes -- it must stay free and silent),
* the guards that stop a bad deploy (CI red/pending, dirty tree, local commits,
  busy scheduler),
* rollback when the post-deploy health check fails,
* deploy state: the last-success SHA file is the baseline, written only after
  a deploy fully succeeds, so a poller killed mid-deploy (SIGKILL skips the
  EXIT trap) is detected and retried instead of hidden forever,
* failure backoff: a SHA that just failed is not re-deployed -- full cycle,
  snapshot and restarts included -- on every 5-minute tick,
* the atomic frontend build: website/ builds go to a staging dir and are
  swapped in whole, so a failed build never corrupts the live .next,
* and above all that untracked server state -- data/orchestrator.db, .env --
  survives a deploy. That is the 2026-07 outage in test form: the DB is a single
  untracked SQLite file, and a deployer that reaches for `git clean` destroys it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
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
# A commit GitHub has not registered any checks for -- the usual state
# seconds after a push, which the poller sees before CI has started.
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
        # How many more /ready calls answer before the route starts 404ing
        # while /health keeps working. 0 = the database is down from the
        # start; 1 = the pre-deploy check passes and the rollback target
        # then turns out to predate the route.
        self.ready_ok_remaining = tmp_path / "ready_ok_remaining"
        # Deploy bookkeeping lives inside .git/ -- out of reset --hard's reach.
        self.state_file = self.checkout / ".git" / "moss-ao-deployed-sha"
        self.attempt_file = self.checkout / ".git" / "moss-ao-deploy-attempt"

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
        self.ready_ok_remaining.write_text("999")
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
        # `npm run build` is invoked with cwd=website and NEXT_DIST_DIR set to
        # the staging dir; mimic next.config.ts honouring it so the swap path
        # (promote_web_build) is exercised for real. NPM_STUB_EXIT simulates a
        # failed build, which must leave nothing for the swap to pick up.
        _write(
            self.bin / "npm",
            f"""#!/usr/bin/env bash
echo "npm $*" >> "{self.stub_log}"
if [ "$1 ${{2:-}}" = "run build" ] && [ -n "${{NEXT_DIST_DIR:-}}" ] \\
   && [ "${{NPM_STUB_EXIT:-0}}" = "0" ]; then
  mkdir -p "$NEXT_DIST_DIR"
  echo "stub-build" > "$NEXT_DIST_DIR/BUILD_ID"
fi
exit ${{NPM_STUB_EXIT:-0}}
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
    k=$(cat "{self.ready_ok_remaining}" 2>/dev/null || echo 999)
    if [ "$k" -le 0 ]; then exit 22; fi
    echo $((k - 1)) > "{self.ready_ok_remaining}"
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

    def state(self) -> str | None:
        """The last-success SHA the deploy script has recorded, if any."""
        if not self.state_file.exists():
            return None
        return self.state_file.read_text().strip()

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
        assert "pm2 restart" not in server.calls()

    def test_nothing_to_snapshot_is_not_a_failure(self, server: Server):
        """backup-db exits 2 when the database is missing/empty/dataless --
        benign (a fresh server), so the deploy proceeds."""
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 23\n"})

        result = server.run(BACKUP_STUB_EXIT="2")

        assert server.head() == target
        assert "nothing to snapshot yet" in result.stdout
        assert "DEPLOYED" in result.stdout

    def test_a_lock_only_change_still_installs(self, server: Server):
        """uv.lock is tracked now, so a dependency bump can arrive with no
        pyproject change at all. Without a classifier entry that commit reads
        as docs-only and nothing installs -- ever, since the state advances."""
        server.make_uv_managed()
        server.push({"uv.lock": "# bumped\n"})

        result = server.run()

        calls = server.calls()
        assert "uv sync" in calls
        assert "pm2 restart moss-ao-api" in calls
        assert "docs only" not in result.stdout

    def test_uv_sync_never_rewrites_the_tracked_lockfile(self, server: Server):
        """A non-frozen sync re-resolves and can rewrite uv.lock -- a tracked
        file. The dirty-tree guard would then abort every subsequent tick."""
        server.make_uv_managed()
        server.push({"pyproject.toml": 'version = "0.0.20"\n'})

        server.run()

        assert "uv sync --frozen" in server.calls()

    def test_a_pip_venv_wins_over_the_committed_lockfile(self, server: Server):
        """uv.lock is tracked now, so every checkout has one. What the venv
        records about how it was built has to take precedence."""
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
            DEPLOY_REQUIRE_CI="1", CI_JSON=CI_SUCCESS, DEPLOY_REQUIRE_CI_JOBS="test (3.12)"
        )

        assert server.head() == target
        assert "CI: green" in result.stdout

    def test_a_stuck_deferral_eventually_says_so(self, server: Server):
        """Deferring is normal; deferring forever means auto-deploy has
        silently stopped, which is the state nobody notices."""
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 50\n"})

        for _ in range(2):
            result = server.run(
                DEPLOY_REQUIRE_CI="1", CI_JSON=CI_NONE, DEPLOY_DEFER_ALERT_TICKS="3"
            )
            assert "deferring" in result.stdout

        state = server.checkout / "logs" / ".ci-deferred"
        assert state.exists()
        assert state.read_text().split()[1] == "2"

    def test_a_green_run_clears_the_deferral_counter(self, server: Server):
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 51\n"})
        server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=CI_NONE)
        assert (server.checkout / "logs" / ".ci-deferred").exists()

        server.run(DEPLOY_REQUIRE_CI="1", CI_JSON=CI_SUCCESS)

        assert not (server.checkout / "logs" / ".ci-deferred").exists()

    def test_deploy_defers_while_the_database_is_unhealthy(self, server: Server):
        """The post-deploy gate reads the database. With the database down no
        deploy can pass it, so deploying would restart, fail, roll back and
        repeat every five minutes for the length of an unrelated outage."""
        before = server.head()
        server.ready_ok_remaining.write_text("0")  # /ready 404s, /health answers
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 40\n"})

        result = server.run()

        assert result.returncode == 0
        assert server.head() == before
        assert "not ready" in result.stdout
        assert "pm2 restart" not in server.calls()

    def test_deploy_proceeds_when_the_api_is_down_entirely(self, server: Server):
        """A stopped API is a different case: the deploy may be the fix."""
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 41\n"})
        server.health_fail.write_text("2")

        result = server.run()

        assert server.head() == target
        assert "DEPLOYED" in result.stdout

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
        # Call accounting: the pre-deploy readiness gate probes /ready and
        # then /health (2 calls, both failing here -- the "API is down
        # entirely" case, so it proceeds), then 2 retries x 2 probes = 4
        # more. After those 6 the stub is healthy again, so the deploy
        # fails its health check and the rollback comes back up.
        server.health_fail.write_text("6")

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
        # /ready answers once -- for the pre-deploy check -- then 404s, so the
        # forward deploy fails its health check and rolls back onto a target
        # that predates the route. That rollback must still pass.
        server.ready_ok_remaining.write_text("1")

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


class TestDeployState:
    """Deploy state is the SHA of the last SUCCESSFUL deploy, not HEAD.

    `git reset --hard` moves HEAD before the build and health check run, so a
    poller killed mid-deploy (PM2 max_memory_restart SIGKILL, OOM, reboot)
    used to leave HEAD at the new commit with the old build live -- and every
    later tick read "up to date" and hid the failure forever."""

    def test_success_records_the_deployed_sha(self, server: Server):
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 30\n"})
        server.run()

        assert server.state() == target

    def test_docs_only_sync_advances_the_state(self, server: Server):
        """A sync is a success too; without this every later tick re-syncs."""
        target = server.push({"README.md": "docs\n"})
        server.run()

        assert server.state() == target

    def test_failed_deploy_does_not_advance_the_state(self, server: Server):
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 31\n"})
        server.health_fail.write_text("999")

        result = server.run()

        assert result.returncode == 1
        assert server.state() == before

    def test_interrupted_deploy_is_detected_and_retried(self, server: Server):
        """SIGKILL right after reset --hard: HEAD is at the target but nothing
        was built or restarted. HEAD == origin/main must NOT read as done."""
        good = server.push({"src/agentic_orchestrator/api.py": "VERSION = 32\n"})
        server.run()
        assert server.state() == good

        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 33\n"})
        # The crashed tick: the checkout moved, the state file did not.
        _git(server.checkout, "fetch", "origin")
        _git(server.checkout, "reset", "--hard", "origin/main")
        restarts = server.calls().count("pm2 restart moss-ao-api")

        result = server.run()

        assert result.returncode == 0, result.stdout + result.stderr
        assert "incomplete deploy" in result.stdout
        assert server.calls().count("pm2 restart moss-ao-api") == restarts + 1
        assert server.state() == target


class TestLocalCommitGuard:
    """Commits made by hand on the server would be discarded by reset --hard;
    the deploy must stop instead (merge-base --is-ancestor guard)."""

    def test_local_commits_block_the_deploy(self, server: Server):
        _write(server.checkout / "hotfix.txt", "server-side hotfix\n")
        _git(server.checkout, "add", "hotfix.txt")
        _git(server.checkout, "commit", "--quiet", "-m", "server-local hotfix")
        local = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 40\n"})

        result = server.run()

        assert result.returncode == 0
        assert server.head() == local
        assert "ABORT" in result.stdout
        assert "local commits" in result.stdout
        assert "pm2 restart" not in server.calls()
        # The commit itself survived, reachable, on the branch.
        assert "server-local hotfix" in _git(server.checkout, "log", "--oneline")

    def test_force_overrides_the_local_commit_guard(self, server: Server):
        _git(server.checkout, "commit", "--quiet", "--allow-empty", "-m", "server-local hotfix")
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 41\n"})

        result = server.run("--force")

        assert result.returncode == 0, result.stdout + result.stderr
        assert server.head() == target


class TestFailureBackoff:
    """A SHA that just failed to deploy must not re-run the full cycle --
    forced DB snapshot, build, double restart, rollback, webhook -- on every
    5-minute tick. Attempts are journaled per target SHA and retried on an
    exponential backoff; a new commit resets the journal at once."""

    def _fail_once(self, server: Server) -> str:
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 50\n"})
        server.health_fail.write_text("999")
        result = server.run()
        assert result.returncode == 1, result.stdout + result.stderr
        server.health_fail.write_text("0")  # infrastructure is healthy again
        return target

    def _backdate_attempt(self, server: Server, minutes: int) -> None:
        old = time.time() - minutes * 60
        os.utime(server.attempt_file, (old, old))

    def test_repeated_failure_backs_off_instead_of_redeploying(self, server: Server):
        self._fail_once(server)
        assert server.attempt_file.exists()
        snapshots = server.calls().count("scheduler backup-db")

        result = server.run()  # next tick, seconds later

        assert result.returncode == 0
        assert "backing off" in result.stdout
        # None of the expensive cycle ran again.
        assert server.calls().count("scheduler backup-db") == snapshots

    def test_backoff_expires_and_a_clean_retry_clears_the_journal(self, server: Server):
        target = self._fail_once(server)
        self._backdate_attempt(server, minutes=6)  # past the 5-minute base backoff

        result = server.run()

        assert result.returncode == 0, result.stdout + result.stderr
        assert "retrying" in result.stdout
        assert server.state() == target
        assert not server.attempt_file.exists()

    def test_second_failure_extends_the_journal(self, server: Server):
        target = self._fail_once(server)
        self._backdate_attempt(server, minutes=6)
        server.health_fail.write_text("999")

        result = server.run()

        assert result.returncode == 1
        sha, count = server.attempt_file.read_text().split()
        assert count == "2"
        assert sha == target  # HEAD itself was rolled back to the last good SHA

    def test_new_commit_resets_the_backoff(self, server: Server):
        self._fail_once(server)  # journaled seconds ago: in backoff
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 51\n"})

        result = server.run()

        assert result.returncode == 0, result.stdout + result.stderr
        assert "backing off" not in result.stdout
        assert server.state() == target

    def test_force_bypasses_the_backoff(self, server: Server):
        target = self._fail_once(server)  # journaled seconds ago: in backoff

        result = server.run("--force")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "backing off" not in result.stdout
        assert server.state() == target


class TestAtomicWebBuild:
    """website/ builds go to a staging dir (.next.new) and are swapped in
    whole right before the web restart, so a failed build can never leave the
    live .next -- the dir moss-ao-web is serving from -- half-written."""

    def test_web_build_is_staged_then_promoted(self, server: Server):
        _write(server.checkout / "website" / ".next" / "BUILD_ID", "old")
        server.push({"website/page.tsx": "export default () => 7\n"})

        result = server.run()

        assert result.returncode == 0, result.stdout + result.stderr
        live = server.checkout / "website" / ".next"
        assert (live / "BUILD_ID").read_text().strip() == "stub-build"
        assert not (server.checkout / "website" / ".next.new").exists()
        assert not (server.checkout / "website" / ".next.old").exists()

    def test_failed_web_build_never_touches_the_live_next(self, server: Server):
        _write(server.checkout / "website" / ".next" / "BUILD_ID", "old")
        server.push({"website/page.tsx": "export default () => 8\n"})

        result = server.run(NPM_STUB_EXIT="1")

        assert result.returncode == 1
        assert (server.checkout / "website" / ".next" / "BUILD_ID").read_text() == "old"


class TestLockOwnership:
    """A SIGKILLed poller (PM2 max_memory_restart, OOM) never runs its EXIT
    trap. The lock records its owner's PID, so the next tick reclaims a dead
    owner's lock immediately instead of waiting out the 90-minute age check."""

    def _lock_dir(self, server: Server) -> Path:
        d = server.checkout / "logs" / ".deploy.lock"
        d.mkdir(parents=True)
        return d

    def test_dead_owner_lock_is_reclaimed_immediately(self, server: Server):
        lock = self._lock_dir(server)
        proc = subprocess.Popen(["bash", "-c", "exit 0"])
        proc.wait()
        (lock / "pid").write_text(f"{proc.pid}\n")
        target = server.push({"src/agentic_orchestrator/api.py": "VERSION = 60\n"})

        result = server.run()

        assert result.returncode == 0, result.stdout + result.stderr
        assert "reclaiming" in result.stdout
        assert server.head() == target

    def test_live_owner_lock_is_respected(self, server: Server):
        lock = self._lock_dir(server)
        (lock / "pid").write_text(f"{os.getpid()}\n")  # this test process: alive
        before = server.head()
        server.push({"src/agentic_orchestrator/api.py": "VERSION = 61\n"})

        result = server.run(DEPLOY_VERBOSE="1")

        assert result.returncode == 0
        assert server.head() == before
        assert "another deploy is running" in result.stdout


class TestEcosystemChanges:
    """PM2 process definitions are deliberately not re-registered by the
    deployer -- doing that from inside a PM2-managed process is the 2026-08-05
    incident. But the deploy state advances either way and later ticks are
    no-ops, so a single log line was the entire notification."""

    def test_change_is_recorded_and_keeps_reminding(self, server: Server):
        server.push({"ecosystem.config.js": "module.exports = { apps: [] }\n"})
        first = server.run()

        assert "ecosystem" in first.stdout.lower()
        pending = server.checkout / "logs" / ".ecosystem-pending"
        assert pending.exists()

        second = server.run()
        assert "REMINDER" in second.stdout
        assert "pm2 restart ecosystem.config.js" in second.stdout

    def test_reminder_stops_once_the_operator_clears_it(self, server: Server):
        server.push({"ecosystem.config.js": "module.exports = { apps: [] }\n"})
        server.run()
        (server.checkout / "logs" / ".ecosystem-pending").unlink()

        assert "REMINDER" not in server.run().stdout

    def test_an_unwritable_record_does_not_abort_the_deploy(self, server: Server):
        """Recording the pending change happens after `git reset --hard` and
        before the build. Aborting there would leave git on the new commit with
        PM2 still running the old code."""
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

    def test_script_body_is_wrapped_in_main(self):
        """deploy.sh deploys itself, and bash reads scripts incrementally: an
        in-place self-update mid-run would have bash continue at a byte offset
        of the NEW file. Everything must run from main(), invoked at the very
        end, so the whole file is parsed before any of it executes."""
        lines = [
            stripped
            for raw in DEPLOY_SH.read_text().splitlines()
            if (stripped := raw.strip()) and not stripped.startswith("#")
        ]
        assert "main() {" in lines
        assert lines[-2:] == ['main "$@"', "exit $?"]

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

    def test_deploy_poller_has_memory_headroom_for_the_build(self):
        """`npm run build` runs inside the poller's memory budget, and PM2
        enforces max_memory_restart with SIGKILL -- which skips the EXIT trap
        and used to wedge the deploy lock for 90 minutes. 1G was not enough
        for a Next.js production build."""
        app = next(a for a in self._apps("1") if a["name"] == "moss-ao-deploy")

        assert app["max_memory_restart"] == "3G"

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
