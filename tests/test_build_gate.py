"""Security regression tests for the generated-project build gate.

The core invariant is stronger than "we usually use Docker": no model-written
build or test command may ever execute on the host, and a missing/unverifiable
sandbox must fail closed.  Docker is not required on the test machine; the
tests inspect the exact trusted CLI boundary and emulate daemon responses.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import agentic_orchestrator.project.build_gate as build_gate
from agentic_orchestrator.project.build_gate import (
    BUILD_GATE_DEFAULTS,
    FAILED,
    PASSED,
    SKIPPED,
    BuildGateResult,
    StepResult,
    run_build_gate,
    summarize,
)


def write_package(path, scripts, name="scratch", dependencies=None):
    path.mkdir(parents=True, exist_ok=True)
    dependencies = dependencies or {}
    trusted_test_commands = {
        "build": "tsc",
        "typecheck": "tsc --noEmit",
        "test": "jest",
    }
    scripts = {
        script: (
            trusted_test_commands.get(script, command) if command.startswith("node -e") else command
        )
        for script, command in scripts.items()
    }
    (path / "package.json").write_text(
        json.dumps(
            {
                "name": name,
                "version": "1.0.0",
                "private": True,
                "scripts": scripts,
                "dependencies": dependencies,
            }
        )
    )
    (path / "package-lock.json").write_text(
        json.dumps(
            {
                "name": name,
                "version": "1.0.0",
                "lockfileVersion": 3,
                "requires": True,
                "packages": {
                    "": {
                        "name": name,
                        "version": "1.0.0",
                        "dependencies": dependencies,
                    }
                },
            }
        )
    )
    return path


def enabled_config(**overrides):
    return {**BUILD_GATE_DEFAULTS, "enabled": True, **overrides}


def run_enabled(path, config, *, extra_files=()):
    """Call the gate with the exact files this test pretends were generated."""
    project = Path(path)
    manifests = []
    if project.is_dir():
        manifests = [
            candidate.relative_to(project).as_posix()
            for candidate in project.rglob("package*.json")
        ]
    return run_build_gate(str(project), config, [*sorted(manifests), *list(extra_files)])


class FakeDocker:
    def __init__(self):
        self.calls = []
        self.create_command = None
        self.fail_on = None
        self.skip_on = None
        self.timeout_on = None
        self.cleanup_fails = False
        self.invalid_inspect = False
        self.insecure_inspect = False
        self.long_failure = False
        self.staged_files = []
        self.security_options = [
            "name=seccomp,profile=builtin",
            "name=rootless",
            "name=cgroupns",
        ]
        self.cgroup_info = "2|systemd"
        self.runtime_endpoint = "unix:///run/user/1000/docker.sock"
        self.bad_live_memory = False
        self.stale_container_id = None
        self.stale_expiry = 1

    @staticmethod
    def _option(command, prefix):
        return next(arg[len(prefix) :] for arg in command if arg.startswith(prefix))

    def _inspect(self):
        command = self.create_command
        assert command is not None
        mount_index = command.index("--mount")
        mount = command[mount_index + 1]
        mount_fields = dict(field.split("=", 1) for field in mount.split(",") if "=" in field)
        source = mount_fields["src"]
        tmpfs_values = [
            command[index + 1] for index, value in enumerate(command) if value == "--tmpfs"
        ]
        tmpfs = {value.split(":", 1)[0]: value.split(":", 1)[1] for value in tmpfs_values}
        labels = {}
        for value in command:
            if value.startswith("--label="):
                key, label_value = value.removeprefix("--label=").split("=", 1)
                labels[key] = label_value
        return [
            {
                "Config": {
                    "User": self._option(command, "--user="),
                    "Volumes": None,
                    "Labels": labels,
                },
                "HostConfig": {
                    "NetworkMode": "none",
                    "ReadonlyRootfs": True,
                    "Privileged": False,
                    "AutoRemove": True,
                    "PidMode": "",
                    "IpcMode": "private",
                    "CgroupnsMode": "private",
                    "Memory": int(self._option(command, "--memory=")),
                    "MemorySwap": int(self._option(command, "--memory-swap=")),
                    "NanoCpus": int(float(self._option(command, "--cpus=")) * 1_000_000_000),
                    "PidsLimit": int(self._option(command, "--pids-limit=")),
                    "CapDrop": ["ALL"],
                    "CapAdd": [],
                    "SecurityOpt": ["no-new-privileges:true", "seccomp=builtin"],
                    "Devices": [],
                    "DeviceRequests": [],
                    "LogConfig": {"Type": "none"},
                    "ShmSize": 64 * 1024**2,
                    "RestartPolicy": {"Name": "no", "MaximumRetryCount": 0},
                    "PortBindings": {},
                    "PublishAllPorts": False,
                    "Ulimits": [
                        {"Name": "nofile", "Soft": 1024, "Hard": 1024},
                        {
                            "Name": "fsize",
                            "Soft": 268435456,
                            "Hard": 268435456,
                        },
                    ],
                    "Mounts": [
                        {
                            "Type": "bind",
                            "Source": source,
                            "Target": "/input",
                            "ReadOnly": True,
                        }
                    ],
                    "Tmpfs": tmpfs,
                },
            }
        ]

    def run(self, command, timeout):
        command = list(command)
        self.calls.append((command, timeout))
        joined = " ".join(command)
        operation = command[1]

        if operation == "context":
            return subprocess.CompletedProcess(
                command, 0, stdout=json.dumps(self.runtime_endpoint), stderr=""
            )
        if operation == "info":
            if "SecurityOptions" in joined:
                return subprocess.CompletedProcess(
                    command, 0, stdout=json.dumps(self.security_options), stderr=""
                )
            return subprocess.CompletedProcess(
                command, 0, stdout=self.cgroup_info + "\n", stderr=""
            )
        if operation == "ps":
            output = f"{self.stale_container_id}\n" if self.stale_container_id else ""
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")
        if operation == "create":
            self.create_command = command
            source = Path(
                command[command.index("--mount") + 1].split("src=", 1)[1].split(",", 1)[0]
            )
            self.staged_files = sorted(
                path.relative_to(source).as_posix() for path in source.rglob("*")
            )
            return subprocess.CompletedProcess(command, 0, stdout="fake-id\n", stderr="")
        if operation == "inspect":
            if self.stale_container_id and command[-1] == self.stale_container_id:
                payload = [
                    {
                        "Name": "/moss-build-gate-expired",
                        "Config": {
                            "Labels": {
                                "moss.build-gate": "true",
                                "moss.build-gate.expires": str(self.stale_expiry),
                            }
                        },
                    }
                ]
                return subprocess.CompletedProcess(
                    command, 0, stdout=json.dumps(payload), stderr=""
                )
            inspected = self._inspect()
            if self.insecure_inspect:
                inspected[0]["HostConfig"]["NetworkMode"] = "bridge"
            payload = "not-json" if self.invalid_inspect else json.dumps(inspected)
            return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")
        if operation == "rm" and self.cleanup_fails:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="cleanup denied")
        if operation == "exec" and "/proc/self/status" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "Seccomp:\t2\nNoNewPrivs:\t1\nCapEff:\t0000000000000000\n"
                    "Uid:\t65532\t65532\t65532\t65532\n"
                    "Gid:\t65532\t65532\t65532\t65532\n"
                ),
                stderr="",
            )
        if operation == "exec" and "/sys/fs/cgroup/memory.max" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "max"
                    if self.bad_live_memory
                    else self._option(self.create_command, "--memory=")
                )
                + "\n",
                stderr="",
            )
        if operation == "exec" and "/sys/fs/cgroup/memory.swap.max" in command:
            return subprocess.CompletedProcess(command, 0, stdout="0\n", stderr="")
        if operation == "exec" and "/sys/fs/cgroup/pids.max" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=self._option(self.create_command, "--pids-limit=") + "\n",
                stderr="",
            )
        if operation == "exec" and "/sys/fs/cgroup/cpu.max" in command:
            cpus = float(self._option(self.create_command, "--cpus="))
            return subprocess.CompletedProcess(
                command, 0, stdout=f"{int(cpus * 100000)} 100000\n", stderr=""
            )
        if self.timeout_on and self.timeout_on in joined:
            raise subprocess.TimeoutExpired(command, timeout)
        if self.skip_on and self.skip_on in joined:
            raise OSError("runtime disappeared")
        if self.fail_on and self.fail_on in joined:
            detail = "x" * 50_000 if self.long_failure else "sandboxed command failed"
            return subprocess.CompletedProcess(command, 1, stdout="", stderr=detail)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


@pytest.fixture
def fake_docker(monkeypatch):
    fake = FakeDocker()
    monkeypatch.setattr(
        build_gate.shutil,
        "which",
        lambda name: "/usr/bin/docker" if name == "docker" else None,
    )
    monkeypatch.setattr(build_gate, "_run_cli", fake.run)
    monkeypatch.setattr(
        build_gate,
        "_run_cli_bounded",
        lambda command, timeout, _output_limit: fake.run(command, timeout),
    )
    return fake


class TestSkippedIsNotPassed:
    def test_a_skipped_result_does_not_pass(self):
        assert BuildGateResult(status=SKIPPED, reason="no toolchain").passed is False

    def test_a_failed_result_does_not_pass(self):
        assert BuildGateResult(status=FAILED, reason="build failed").passed is False

    def test_only_passed_passes(self):
        assert BuildGateResult(status=PASSED, reason="ok").passed is True

    def test_the_default_result_does_not_pass(self):
        assert BuildGateResult().passed is False


class TestFailClosedDefaults:
    def test_build_gate_is_disabled_by_default(self, tmp_path, monkeypatch):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        monkeypatch.setattr(
            build_gate,
            "_run_cli",
            lambda *_args, **_kwargs: pytest.fail("disabled gate started a subprocess"),
        )

        result = run_build_gate(str(tmp_path))

        assert BUILD_GATE_DEFAULTS["enabled"] is False
        assert result.status == SKIPPED
        assert "disabled" in result.reason

    def test_shipped_config_disables_build_gate(self):
        config = yaml.safe_load(Path("config.yaml").read_text())
        assert config["project"]["build_gate"]["enabled"] is False

    def test_build_gate_config_read_failure_stays_disabled(self, monkeypatch):
        from agentic_orchestrator.project.scaffold import _load_build_gate_config

        def fail_open(*_args, **_kwargs):
            raise OSError("config unavailable")

        monkeypatch.setattr("builtins.open", fail_open)
        assert _load_build_gate_config()["enabled"] is False

    def test_malformed_build_gate_config_stays_disabled(self, monkeypatch):
        from agentic_orchestrator.project.scaffold import _load_build_gate_config

        monkeypatch.setattr(
            yaml,
            "safe_load",
            lambda _stream: {"project": {"build_gate": "not-a-mapping"}},
        )
        assert _load_build_gate_config()["enabled"] is False

    def test_auto_generation_config_read_failure_stays_disabled(self, monkeypatch):
        from agentic_orchestrator.scheduler.tasks import _load_project_config

        def fail_open(*_args, **_kwargs):
            raise OSError("config unavailable")

        monkeypatch.setattr("builtins.open", fail_open)
        assert _load_project_config()["auto_generate"]["enabled"] is False

    @pytest.mark.parametrize("value", ["true", "false", "yes", 1, None, [], {}])
    def test_auto_generation_rejects_non_boolean_enabled(self, monkeypatch, value):
        from agentic_orchestrator.scheduler.tasks import _load_project_config

        monkeypatch.setattr(
            yaml,
            "safe_load",
            lambda _stream: {"project": {"auto_generate": {"enabled": value}}},
        )
        assert _load_project_config()["auto_generate"]["enabled"] is False

    def test_missing_project_directory_skips(self, tmp_path):
        result = run_enabled(tmp_path / "nope", enabled_config())
        assert result.status == SKIPPED
        assert result.passed is False

    def test_a_project_with_nothing_to_build_skips(self, tmp_path, fake_docker):
        (tmp_path / "README.md").write_text("# just docs\n")
        result = run_enabled(tmp_path, enabled_config(install=False))
        assert result.status == SKIPPED
        assert "package.json" in result.reason
        assert not fake_docker.calls

    def test_missing_docker_never_falls_back_to_host_npm(self, tmp_path, monkeypatch):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        monkeypatch.setattr(
            build_gate.shutil,
            "which",
            lambda name: "/usr/bin/npm" if name == "npm" else None,
        )
        calls = []
        monkeypatch.setattr(build_gate, "_run_cli", lambda *args: calls.append(args))

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == SKIPPED
        assert "host fallback is forbidden" in result.reason
        assert calls == []


class TestSandboxedExecution:
    def test_cross_process_worker_lease_refuses_concurrency(self, tmp_path, monkeypatch):
        lease_path = tmp_path / "sandbox-worker.lock"
        monkeypatch.setattr(build_gate, "_worker_lock_path", lambda: lease_path)
        held = build_gate._acquire_worker_lease()
        try:
            result = run_build_gate(str(tmp_path), enabled_config(), [])
        finally:
            build_gate._release_worker_lease(held)

        assert result.status == SKIPPED
        assert "concurrent execution refused" in result.reason

    def test_successful_build_passes_only_through_docker(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == PASSED, result.to_dict()
        assert result.passed is True
        assert any(step.command.startswith("npm run build") for step in result.steps)
        assert all(Path(command[0]).name == "docker" for command, _timeout in fake_docker.calls)
        assert not any(
            Path(command[0]).name in {"npm", "node", "npx", "sh", "bash"}
            for command, _ in fake_docker.calls
        )

    def test_noop_verification_script_is_rejected_before_runtime(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "true"})

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == FAILED
        assert "untrusted npm build script" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    def test_verification_lifecycle_hook_is_rejected_before_runtime(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "tsc", "prebuild": "true"})

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == FAILED
        assert "lifecycle hook rejected" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    def test_failing_typecheck_stops_before_test(self, tmp_path, fake_docker):
        write_package(
            tmp_path,
            {
                "build": "node -e 'process.exit(0)'",
                "typecheck": "node -e 'process.exit(3)'",
                "test": "node -e 'process.exit(0)'",
            },
        )
        fake_docker.fail_on = "npm run typecheck"

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == FAILED
        assert "typecheck failed" in result.reason
        assert not any(step.name.endswith("npm run test") for step in result.steps)

    def test_every_workspace_is_checked(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"}, name="root")
        write_package(
            tmp_path / "contracts",
            {"build": "node -e 'process.exit(1)'"},
            name="contracts",
        )
        fake_docker.fail_on = "--workdir /workspace/contracts"

        result = run_enabled(tmp_path, enabled_config(install=False))

        assert result.status == FAILED
        assert "contracts" in result.reason

    def test_scriptless_workspace_cannot_hide_behind_a_passing_root(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"}, name="root")
        write_package(tmp_path / "contracts", {}, name="contracts")

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == SKIPPED
        assert "contracts" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    def test_no_verification_scripts_never_passes(self, tmp_path, fake_docker):
        write_package(tmp_path, {})
        result = run_enabled(tmp_path, enabled_config())
        assert result.status == SKIPPED
        assert result.passed is False

    def test_skipped_verification_cannot_be_masked_by_another_pass(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        write_package(tmp_path / "contracts", {"build": "node -e 'process.exit(0)'"})
        fake_docker.skip_on = "npm run build"

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == SKIPPED
        assert result.passed is False


class TestIsolationInvariants:
    def test_container_creation_enforces_every_security_boundary(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        run_enabled(tmp_path, enabled_config())
        command = fake_docker.create_command

        assert "--pull=never" in command
        assert "--network=none" in command
        assert "--read-only" in command
        assert "--rm" in command
        assert "--cap-drop=ALL" in command
        assert "--security-opt=no-new-privileges:true" in command
        assert "--security-opt=seccomp=builtin" in command
        assert "--cgroupns=private" in command
        assert not any(value == "--pid" or value.startswith("--pid=") for value in command)
        assert "--ipc=private" in command
        assert "--log-driver=none" in command
        assert "--user=65533:65533" in command
        assert "--label=moss.build-gate=true" in command
        assert command[-2:] == ["sleep", str(BUILD_GATE_DEFAULTS["total_timeout"])]
        assert any(value.startswith("--memory=") for value in command)
        assert any(value.startswith("--memory-swap=") for value in command)
        assert any(value.startswith("--cpus=") for value in command)
        assert any(value.startswith("--pids-limit=") for value in command)
        mount = command[command.index("--mount") + 1]
        assert "dst=/input" in mount and "readonly" in mount
        assert str(tmp_path.resolve()) not in mount  # only a sanitized snapshot is mounted
        tmpfs = [command[i + 1] for i, value in enumerate(command) if value == "--tmpfs"]
        assert any(
            value.startswith("/workspace:") and "size=" in value and "nr_inodes=" in value
            for value in tmpfs
        )
        assert any(
            value.startswith("/tmp:") and "size=" in value and "nr_inodes=" in value
            for value in tmpfs
        )
        assert "--privileged" not in command
        assert not any("docker.sock" in value for value in command)
        exec_calls = [call for call, _timeout in fake_docker.calls if call[1] == "exec"]
        assert all(call[call.index("--user") + 1] == "65532:65532" for call in exec_calls)

    def test_snapshot_excludes_secrets_and_original_is_never_writable(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        (tmp_path / ".env").write_text("OPENAI_API_KEY=secret")
        (tmp_path / ".npmrc").write_text("//registry/:_authToken=secret")
        (tmp_path / "private.pem").write_text("secret")
        (tmp_path / "credentials.json").write_text("secret")
        (tmp_path / "app.db").write_text("secret")

        result = run_enabled(tmp_path, enabled_config())

        assert result.passed is True
        assert ".env" not in fake_docker.staged_files
        assert ".npmrc" not in fake_docker.staged_files
        assert "private.pem" not in fake_docker.staged_files
        assert "credentials.json" not in fake_docker.staged_files
        assert "app.db" not in fake_docker.staged_files

    def test_exact_generation_allowlist_excludes_stale_source(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        (tmp_path / "stale-payload.js").write_text("throw new Error('stale')")
        (tmp_path / ".env.example").write_text("TOKEN=placeholder")

        result = run_build_gate(
            str(tmp_path),
            enabled_config(),
            ["package.json", "package-lock.json", ".env.example"],
        )

        assert result.passed is True
        assert "stale-payload.js" not in fake_docker.staged_files
        assert ".env.example" not in fake_docker.staged_files

    def test_container_process_uses_env_i_and_offline_npm(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        run_enabled(tmp_path, enabled_config())

        exec_calls = [command for command, _ in fake_docker.calls if command[1] == "exec"]
        assert exec_calls
        assert all("env" in command and "-i" in command for command in exec_calls)
        assert all("NPM_CONFIG_IGNORE_SCRIPTS=true" in command for command in exec_calls)
        install = next(command for command in exec_calls if "ci" in command)
        assert "--offline" in install
        assert "--ignore-scripts" in install
        assert "--no-audit" in install
        assert "--no-fund" in install
        assert not any(value in install for value in ("--env-file", "-e"))

    def test_host_secrets_are_not_given_to_docker_cli(self, monkeypatch):
        for key in (
            "GITHUB_TOKEN",
            "MOSS_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DOCKER_HOST",
            "DOCKER_CONTEXT",
        ):
            monkeypatch.setenv(key, f"sentinel-{key}")
        captured = {}

        def fake_subprocess_run(command, **kwargs):
            captured.update(kwargs)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(build_gate.subprocess, "run", fake_subprocess_run)
        build_gate._run_cli(["/usr/bin/docker", "version"], 5)

        runtime_env = captured["env"]
        assert all(
            key not in runtime_env
            for key in (
                "GITHUB_TOKEN",
                "MOSS_API_KEY",
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "DOCKER_HOST",
                "DOCKER_CONTEXT",
            )
        )
        assert captured["start_new_session"] is True
        assert "shell" not in captured

    def test_unpinned_image_is_rejected_before_runtime(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        result = run_enabled(tmp_path, enabled_config(container_image="node:22-alpine"))
        assert result.status == SKIPPED
        assert "@sha256" in result.reason
        assert fake_docker.calls == []

    def test_rootless_preflight_is_required_before_create(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        fake_docker.security_options.remove("name=rootless")

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == SKIPPED
        assert "rootless daemon" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    def test_remote_docker_context_is_rejected_before_create(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "tsc"})
        fake_docker.runtime_endpoint = "ssh://sandbox-worker.example"

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == SKIPPED
        assert "remote contexts are forbidden" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    def test_generated_source_without_package_root_is_rejected(self, tmp_path, fake_docker):
        write_package(tmp_path / "src/backend", {"build": "tsc"})
        frontend = tmp_path / "src/frontend/src/page.tsx"
        frontend.parent.mkdir(parents=True)
        frontend.write_text("export default function Page() { return null; }")

        result = run_enabled(
            tmp_path,
            enabled_config(),
            extra_files=["src/frontend/src/page.tsx"],
        )

        assert result.status == FAILED
        assert "no package toolchain root" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    def test_python_source_cannot_hide_behind_passing_frontend(self, tmp_path, fake_docker):
        write_package(tmp_path / "src/frontend", {"build": "tsc"})
        backend = tmp_path / "src/backend/app.py"
        backend.parent.mkdir(parents=True)
        backend.write_text("print('generated')\n")

        result = run_enabled(
            tmp_path,
            enabled_config(),
            extra_files=["src/backend/app.py"],
        )

        assert result.status == FAILED
        assert "no supported sandbox toolchain" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    @pytest.mark.parametrize("cgroup_info", ["1|cgroupfs", "2|cgroupfs", "garbage"])
    def test_cgroup_v2_systemd_is_required(self, tmp_path, fake_docker, cgroup_info):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        fake_docker.cgroup_info = cgroup_info

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == SKIPPED
        assert "cgroup v2" in result.reason
        assert not any(command[1] == "create" for command, _ in fake_docker.calls)

    def test_kernel_visible_limits_are_attested_before_input_copy(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        fake_docker.bad_live_memory = True

        result = run_enabled(tmp_path, enabled_config())

        assert result.status == SKIPPED
        assert "effective memory limit" in result.reason
        exec_calls = [command for command, _ in fake_docker.calls if command[1] == "exec"]
        assert not any("/input/." in command or "npm" in command for command in exec_calls)

    @pytest.mark.parametrize(
        ("field", "value"),
        [("memory", "0m"), ("cpus", 0), ("pids_limit", 0), ("workspace_size", "99g")],
    )
    def test_invalid_resource_limits_fail_closed(self, tmp_path, fake_docker, field, value):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        result = run_enabled(tmp_path, enabled_config(**{field: value}))
        assert result.status == SKIPPED
        assert fake_docker.calls == []

    def test_non_registry_dependency_is_rejected_offline(self, tmp_path, fake_docker):
        write_package(
            tmp_path,
            {"build": "node -e 'process.exit(0)'"},
            dependencies={"payload": "https://attacker.invalid/payload.tgz"},
        )
        result = run_enabled(tmp_path, enabled_config())
        assert result.status == FAILED
        assert "non-registry dependency" in result.reason
        assert fake_docker.calls == []

    def test_missing_lockfile_is_rejected_before_runtime(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        (tmp_path / "package-lock.json").unlink()
        result = run_enabled(tmp_path, enabled_config())
        assert result.status == FAILED
        assert "package-lock.json" in result.reason
        assert fake_docker.calls == []

    def test_symlinked_input_is_rejected_instead_of_following_host_paths(
        self, tmp_path, fake_docker
    ):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        outside = tmp_path.parent / f"{tmp_path.name}-outside-secret"
        outside.write_text("secret")
        (tmp_path / "linked-secret").symlink_to(outside)
        result = run_enabled(tmp_path, enabled_config(), extra_files=["linked-secret"])
        assert result.status == SKIPPED
        assert "unsupported file" in result.reason
        assert fake_docker.calls == []


class TestLifecycleAndFailureHandling:
    def test_generated_output_capture_keeps_only_a_bounded_tail(self):
        result = build_gate._run_cli_bounded(
            [sys.executable, "-c", "import sys; sys.stdout.write('x' * 2000000)"],
            timeout=5,
            output_limit=1024,
        )
        assert result.returncode == 0
        assert len(result.stdout.encode()) == 1024

    def test_invalid_inspect_payload_prevents_start_and_execution(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        fake_docker.invalid_inspect = True
        result = run_enabled(tmp_path, enabled_config())
        assert result.status == SKIPPED
        assert result.passed is False
        assert not any(command[1] == "start" for command, _ in fake_docker.calls)
        assert any(command[1] == "rm" for command, _ in fake_docker.calls)

    @pytest.mark.parametrize("expiry", [1, 4_102_444_800])
    def test_labeled_orphan_is_reaped_before_create(self, tmp_path, fake_docker, expiry):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        fake_docker.stale_container_id = "a" * 64
        fake_docker.stale_expiry = expiry

        result = run_enabled(tmp_path, enabled_config())

        assert result.passed is True
        operations = [command[1] for command, _ in fake_docker.calls]
        stale_rm = next(
            index
            for index, (command, _timeout) in enumerate(fake_docker.calls)
            if command[1] == "rm" and command[-1] == "a" * 64
        )
        assert stale_rm < operations.index("create")

    def test_runtime_that_did_not_enforce_network_none_is_rejected(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        fake_docker.insecure_inspect = True
        result = run_enabled(tmp_path, enabled_config())
        assert result.status == SKIPPED
        assert "network isolation" in result.reason
        assert not any(command[1] == "start" for command, _ in fake_docker.calls)

    def test_timeout_forcibly_removes_exact_container(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'setTimeout(()=>{}, 60000)'"})
        fake_docker.timeout_on = "npm run build"

        result = run_enabled(tmp_path, enabled_config(step_timeout=2))

        assert result.status == FAILED
        create_name = fake_docker.create_command[fake_docker.create_command.index("--name") + 1]
        cleanup = next(command for command, _ in fake_docker.calls if command[1] == "rm")
        assert cleanup[-1] == create_name

    def test_cleanup_failure_overrides_an_apparent_pass(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(0)'"})
        fake_docker.cleanup_fails = True
        result = run_enabled(tmp_path, enabled_config())
        assert result.status == FAILED
        assert "cleanup failed" in result.reason

    def test_real_failure_output_is_truncated_before_storage(self, tmp_path, fake_docker):
        write_package(tmp_path, {"build": "node -e 'process.exit(1)'"})
        fake_docker.fail_on = "npm run build"
        fake_docker.long_failure = True
        result = run_enabled(tmp_path, enabled_config(max_output_chars=4000))
        failed = next(step for step in result.steps if step.status == FAILED)
        assert len(failed.detail) == 4000


class TestSummary:
    def test_summary_names_the_status_and_reason(self):
        result = BuildGateResult(status=FAILED, reason="root: build failed")
        result.steps = [StepResult(name="root: npm install", status=PASSED)]
        line = summarize(result)
        assert "failed" in line
        assert "root: build failed" in line
