"""Fail-closed build gate for generated projects.

Generated source is untrusted model output derived from public inputs.  It must
never be imported, built, or tested in the orchestrator process.  When this
gate is enabled it uses one disposable, network-isolated Docker container and
only a clean build/typecheck/test pass earns ``ready``.  A missing runtime,
image, cache, or security control is SKIPPED/FAILED and therefore maps to
``ready_with_warnings``; there is deliberately no host-toolchain fallback.

The sandbox invariants are code, not operator-tunable suggestions:

* no network, host environment, Docker socket, or writable host project mount;
* a numeric non-root user, no Linux capabilities, no-new-privileges, private
  PID/IPC/cgroup namespaces, and a read-only root filesystem;
* a sanitized read-only input snapshot and bounded tmpfs workspace;
* memory, swap, CPU, PID, file-size, file-descriptor, and wall-clock limits;
* a digest-pinned, pre-pulled image (``--pull=never``);
* exact random container names and unconditional ``docker rm -f`` cleanup.

Dependency installation is also offline and ignores lifecycle scripts.  A
fresh generated project therefore needs a trusted immutable npm cache baked
into the pinned sandbox image before this gate can be enabled usefully.  A
cache miss fails closed rather than relaxing the network policy.
"""

import fcntl
import json
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)

_PINNED_NODE_IMAGE = (
    "node:22-alpine@sha256:c610fcdfb1d5b4740dd70c284ed3cb16bb857e0f7166196e36a5501df7a3aa32"
)
_DIGEST_IMAGE_RE = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
_SIZE_RE = re.compile(r"^(\d+)([kmgt]?)b?$", re.IGNORECASE)
_SANDBOX_UID = 65532
_SANDBOX_GID = 65532
_SANDBOX_USER = f"{_SANDBOX_UID}:{_SANDBOX_GID}"
_SUPERVISOR_UID = 65533
_SUPERVISOR_GID = 65533
_SUPERVISOR_USER = f"{_SUPERVISOR_UID}:{_SUPERVISOR_GID}"
_CONTAINER_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
_CONTAINER_ENV = (
    f"PATH={_CONTAINER_PATH}",
    "HOME=/tmp",
    "TMPDIR=/tmp",
    "CI=1",
    "NO_COLOR=1",
    "NPM_CONFIG_OFFLINE=true",
    "NPM_CONFIG_IGNORE_SCRIPTS=true",
    "NPM_CONFIG_USERCONFIG=/dev/null",
    "NPM_CONFIG_CACHE=/tmp/npm-cache",
)

# These values are emitted by the deterministic project generator/templates,
# not accepted from model output.  `npm run` is retained only to locate the
# offline-installed toolchain; ignore-scripts prevents pre/post hook execution.
_TRUSTED_VERIFICATION_SCRIPTS = {
    "build": frozenset(
        {
            "next build",
            "tsc",
            "tsc && vite build",
            "vue-tsc && vite build",
        }
    ),
    "typecheck": frozenset({"tsc --noEmit", "vue-tsc --noEmit"}),
    "test": frozenset({"hardhat test", "jest"}),
}
_GENERATED_NODE_CODE_SUFFIXES = frozenset(
    {".cjs", ".js", ".jsx", ".mjs", ".sol", ".ts", ".tsx", ".vue"}
)
_UNSUPPORTED_GENERATED_CODE_SUFFIXES = frozenset(
    {
        ".bash",
        ".c",
        ".cc",
        ".cpp",
        ".go",
        ".h",
        ".hpp",
        ".java",
        ".kt",
        ".kts",
        ".move",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".swift",
    }
)

BUILD_GATE_DEFAULTS = {
    # A malformed/missing config must never turn generated-code execution on.
    "enabled": False,
    "install": True,
    "install_timeout": 300,
    "step_timeout": 300,
    "setup_timeout": 60,
    "total_timeout": 1800,
    "max_output_chars": 4000,
    "container_runtime": "docker",
    "container_image": _PINNED_NODE_IMAGE,
    "memory": "2g",
    "cpus": 1.0,
    "pids_limit": 128,
    "workspace_size": "2g",
    "tmp_size": "256m",
    "max_source_files": 5000,
    "max_source_bytes": 64 * 1024 * 1024,
}

PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"
_BUILD_GATE_SLOT = threading.BoundedSemaphore(value=1)


def _worker_lock_path() -> Path:
    """Return one stable per-user lease path shared by API and scheduler workers."""
    uid = os.geteuid()
    runtime_dir = Path(f"/run/user/{uid}")
    if runtime_dir.is_dir():
        try:
            metadata = runtime_dir.stat()
            if metadata.st_uid == uid and not metadata.st_mode & 0o022:
                return runtime_dir / "agentic-orchestrator-build-gate.lock"
        except OSError:
            pass
    return Path("/tmp") / f"agentic-orchestrator-build-gate-{uid}.lock"


def _acquire_worker_lease() -> int:
    """Take a non-blocking cross-process lease without following lock symlinks."""
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise _SandboxUnavailableError("safe cross-process sandbox lease is unsupported")
    flags |= nofollow
    try:
        descriptor = os.open(_worker_lock_path(), flags, 0o600)
    except OSError as exc:
        raise _SandboxUnavailableError("could not open cross-process sandbox lease") from exc
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or metadata.st_nlink != 1
        ):
            raise _SandboxUnavailableError("cross-process sandbox lease is unsafe")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise _SandboxUnavailableError(
                "sandbox worker busy; concurrent execution refused"
            ) from exc
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _release_worker_lease(descriptor: int) -> None:
    try:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


@dataclass
class StepResult:
    name: str
    status: str
    command: str = ""
    detail: str = ""
    duration_seconds: float = 0.0
    # Install/setup is not evidence that generated code works.
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
    """Outcome of the whole gate.  Only ``PASSED`` earns ``ready``."""

    status: str = SKIPPED
    reason: str = ""
    steps: List[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == PASSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass(frozen=True)
class _SandboxLimits:
    setup_timeout: int
    total_timeout: int
    install_timeout: int
    step_timeout: int
    max_output: int
    memory_bytes: int
    cpus: float
    pids_limit: int
    workspace_bytes: int
    tmp_bytes: int
    max_source_files: int
    max_source_bytes: int


class _SandboxUnavailableError(RuntimeError):
    """The required isolation could not be established."""


def _parse_size(value: Any, *, minimum: int, maximum: int, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a byte size")
    if isinstance(value, int):
        size = value
    elif isinstance(value, str):
        match = _SIZE_RE.fullmatch(value.strip())
        if not match:
            raise ValueError(f"{field_name} must look like 256m or 2g")
        number = int(match.group(1))
        multiplier = {
            "": 1,
            "k": 1024,
            "m": 1024**2,
            "g": 1024**3,
            "t": 1024**4,
        }[match.group(2).lower()]
        size = number * multiplier
    else:
        raise ValueError(f"{field_name} must be a byte size")
    if not minimum <= size <= maximum:
        raise ValueError(f"{field_name} is outside the enforced safe range")
    return size


def _positive_int(settings: dict, name: str, *, minimum: int, maximum: int) -> int:
    value = settings.get(name)
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} is outside the enforced safe range")
    return parsed


def _validate_settings(settings: dict) -> _SandboxLimits:
    if settings.get("container_runtime") != "docker":
        raise ValueError("container_runtime must be docker")
    image = settings.get("container_image")
    if not isinstance(image, str) or not _DIGEST_IMAGE_RE.fullmatch(image):
        raise ValueError("container_image must be pinned with @sha256:<64 hex chars>")
    if not isinstance(settings.get("install"), bool):
        raise ValueError("install must be a boolean")

    try:
        cpus = float(settings.get("cpus"))
    except (TypeError, ValueError) as exc:
        raise ValueError("cpus must be numeric") from exc
    if not 0.1 <= cpus <= 4.0:
        raise ValueError("cpus is outside the enforced safe range")

    return _SandboxLimits(
        setup_timeout=_positive_int(settings, "setup_timeout", minimum=5, maximum=300),
        total_timeout=_positive_int(settings, "total_timeout", minimum=30, maximum=3600),
        install_timeout=_positive_int(settings, "install_timeout", minimum=1, maximum=1800),
        step_timeout=_positive_int(settings, "step_timeout", minimum=1, maximum=1800),
        max_output=_positive_int(settings, "max_output_chars", minimum=256, maximum=100_000),
        memory_bytes=_parse_size(
            settings.get("memory"),
            minimum=128 * 1024**2,
            maximum=4 * 1024**3,
            field_name="memory",
        ),
        cpus=cpus,
        pids_limit=_positive_int(settings, "pids_limit", minimum=16, maximum=512),
        workspace_bytes=_parse_size(
            settings.get("workspace_size"),
            minimum=128 * 1024**2,
            maximum=4 * 1024**3,
            field_name="workspace_size",
        ),
        tmp_bytes=_parse_size(
            settings.get("tmp_size"),
            minimum=16 * 1024**2,
            maximum=512 * 1024**2,
            field_name="tmp_size",
        ),
        max_source_files=_positive_int(settings, "max_source_files", minimum=1, maximum=20_000),
        max_source_bytes=_positive_int(
            settings,
            "max_source_bytes",
            minimum=1024,
            maximum=256 * 1024**2,
        ),
    )


def _host_runtime_env() -> Dict[str, str]:
    """Minimal environment for the trusted Docker CLI, never the container."""
    allowed = (
        "PATH",
        "HOME",
        "XDG_RUNTIME_DIR",
        "TMPDIR",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
    )
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env.setdefault("PATH", os.defpath)
    env["LANG"] = "C"
    env["LC_ALL"] = "C"
    return env


def _run_cli(command: List[str], timeout: int) -> subprocess.CompletedProcess[str]:
    """Run only the trusted container CLI with a secret-free host environment."""
    return subprocess.run(
        command,
        cwd="/",
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=_host_runtime_env(),
        start_new_session=True,
    )


def _verify_runtime_security(runtime: str, timeout: int) -> None:
    """Require a rootless, cgroup-v2 Docker worker with built-in seccomp."""

    try:
        endpoint_proc = _run_cli(
            [
                runtime,
                "context",
                "inspect",
                "--format",
                "{{json .Endpoints.docker.Host}}",
            ],
            timeout,
        )
        endpoint = json.loads((endpoint_proc.stdout or "").strip())
    except Exception as exc:
        raise _SandboxUnavailableError("Docker endpoint preflight unavailable") from exc
    if endpoint_proc.returncode != 0 or not isinstance(endpoint, str):
        raise _SandboxUnavailableError("Docker endpoint preflight returned invalid data")
    if (
        not endpoint.startswith("unix://")
        or not Path(endpoint.removeprefix("unix://")).is_absolute()
    ):
        raise _SandboxUnavailableError(
            "sandbox requires a local Unix Docker endpoint; remote contexts are forbidden"
        )

    def query(format_string: str, label: str) -> str:
        try:
            proc = _run_cli([runtime, "info", "--format", format_string], timeout)
        except Exception as exc:
            raise _SandboxUnavailableError(f"Docker {label} preflight unavailable") from exc
        if proc.returncode != 0:
            raise _SandboxUnavailableError(f"Docker {label} preflight failed")
        return (proc.stdout or "").strip()

    try:
        options = json.loads(query("{{json .SecurityOptions}}", "security"))
    except (json.JSONDecodeError, TypeError) as exc:
        raise _SandboxUnavailableError("Docker security preflight returned invalid data") from exc
    if not isinstance(options, list) or not all(isinstance(item, str) for item in options):
        raise _SandboxUnavailableError("Docker security preflight returned invalid options")

    normalized = {item.strip().lower() for item in options}
    required = {
        "rootless daemon": "name=rootless" in normalized,
        "built-in seccomp": "name=seccomp,profile=builtin" in normalized,
        "private cgroup namespaces": "name=cgroupns" in normalized,
    }
    missing = [name for name, present in required.items() if not present]
    if missing:
        raise _SandboxUnavailableError("Docker worker missing: " + ", ".join(sorted(missing)))

    cgroup = query("{{.CgroupVersion}}|{{.CgroupDriver}}", "cgroup")
    if cgroup != "2|systemd":
        raise _SandboxUnavailableError("Docker worker must use cgroup v2 with the systemd driver")


def _cleanup_orphaned_sandboxes(runtime: str, timeout: int) -> None:
    """Remove labeled leftovers while the caller holds the exclusive host lease."""
    deadline = time.monotonic() + timeout

    def remaining() -> int:
        value = deadline - time.monotonic()
        if value <= 0:
            raise _SandboxUnavailableError("sandbox janitor timed out")
        return max(1, int(value + 0.999))

    try:
        listed = _run_cli(
            [
                runtime,
                "ps",
                "--all",
                "--quiet",
                "--no-trunc",
                "--filter",
                "label=moss.build-gate=true",
            ],
            remaining(),
        )
    except Exception as exc:
        raise _SandboxUnavailableError("sandbox janitor unavailable") from exc
    if listed.returncode != 0:
        raise _SandboxUnavailableError("sandbox janitor listing failed")

    identifiers = [line.strip() for line in (listed.stdout or "").splitlines() if line.strip()]
    if len(identifiers) > 64 or any(
        not re.fullmatch(r"[0-9a-f]{64}", identifier) for identifier in identifiers
    ):
        raise _SandboxUnavailableError("sandbox janitor received unsafe container IDs")

    for identifier in identifiers:
        try:
            inspected = _run_cli([runtime, "inspect", identifier], remaining())
        except Exception as exc:
            raise _SandboxUnavailableError("sandbox janitor inspect unavailable") from exc
        if inspected.returncode != 0:
            if "no such" in _bounded_output(inspected, 300).lower():
                continue
            raise _SandboxUnavailableError("sandbox janitor inspect failed")
        try:
            payload = json.loads(inspected.stdout)[0]
            labels = payload["Config"]["Labels"] or {}
            name = str(payload.get("Name") or "").lstrip("/")
            expiry = int(labels["moss.build-gate.expires"])
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise _SandboxUnavailableError("sandbox janitor found invalid labels") from exc
        if labels.get("moss.build-gate") != "true" or not name.startswith("moss-build-gate-"):
            raise _SandboxUnavailableError("sandbox janitor refused an ambiguous target")
        # A live orchestrator process would still own the cross-process flock,
        # so every matching container found under our exclusive lease is an
        # orphan even when its in-container TTL has not elapsed yet.
        if expiry <= 0:
            raise _SandboxUnavailableError("sandbox janitor found invalid expiry")
        try:
            removed = _run_cli([runtime, "rm", "--force", "--volumes", identifier], remaining())
        except Exception as exc:
            raise _SandboxUnavailableError("sandbox janitor cleanup unavailable") from exc
        if removed.returncode != 0 and "no such" not in _bounded_output(removed, 300).lower():
            raise _SandboxUnavailableError("sandbox janitor cleanup failed")


def _run_cli_bounded(
    command: List[str], timeout: int, output_limit: int
) -> subprocess.CompletedProcess[str]:
    """Run a Docker exec while retaining only a bounded tail of its output."""
    proc = subprocess.Popen(
        command,
        cwd="/",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_host_runtime_env(),
        start_new_session=True,
    )
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    selector = selectors.DefaultSelector()
    assert proc.stdout is not None
    assert proc.stderr is not None
    selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
    selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
    deadline = time.monotonic() + timeout

    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, timeout)
            for key, _mask in selector.select(timeout=min(remaining, 0.5)):
                chunk = os.read(key.fileobj.fileno(), 64 * 1024)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                buffer = streams[key.data]
                buffer.extend(chunk)
                if len(buffer) > output_limit:
                    del buffer[: len(buffer) - output_limit]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, timeout)
        returncode = proc.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        proc.wait()
        raise
    finally:
        selector.close()
        for pipe in (proc.stdout, proc.stderr):
            if pipe and not pipe.closed:
                pipe.close()

    return subprocess.CompletedProcess(
        command,
        returncode,
        stdout=bytes(streams["stdout"]).decode("utf-8", errors="replace"),
        stderr=bytes(streams["stderr"]).decode("utf-8", errors="replace"),
    )


def _bounded_output(proc: subprocess.CompletedProcess[str], maximum: int) -> str:
    output = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()
    return output[-maximum:]


def _run_sandbox_step(
    command: List[str],
    *,
    name: str,
    logical_command: str,
    timeout: int,
    max_output: int,
    verifies: bool,
) -> StepResult:
    started = time.monotonic()
    try:
        proc = _run_cli_bounded(command, timeout, max_output)
    except subprocess.TimeoutExpired:
        return StepResult(
            name=name,
            status=FAILED,
            command=logical_command,
            detail=f"timed out after {timeout}s",
            duration_seconds=time.monotonic() - started,
            verifies=verifies,
        )
    except Exception as exc:
        return StepResult(
            name=name,
            status=SKIPPED,
            command=logical_command,
            detail=str(exc)[:200],
            duration_seconds=time.monotonic() - started,
            verifies=verifies,
        )

    duration = time.monotonic() - started
    if proc.returncode == 0:
        return StepResult(
            name=name,
            status=PASSED,
            command=logical_command,
            duration_seconds=duration,
            verifies=verifies,
        )
    return StepResult(
        name=name,
        status=FAILED,
        command=logical_command,
        detail=_bounded_output(proc, max_output),
        duration_seconds=duration,
        verifies=verifies,
    )


_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".next",
        ".cache",
        ".aws",
        ".docker",
        ".pytest_cache",
        ".ssh",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "secrets",
    }
)
_SECRET_NAMES = frozenset(
    {
        ".git-credentials",
        ".netrc",
        ".npmrc",
        ".pypirc",
        ".yarnrc",
        ".yarnrc.yml",
        "auth.json",
        "credentials",
        "credentials.json",
        "secrets.json",
        "service-account.json",
        "service_account.json",
        "serviceaccountkey.json",
    }
)
_SECRET_SUFFIXES = (
    ".db",
    ".jks",
    ".key",
    ".keystore",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
)


def _ignore_source_name(name: str, *, is_dir: bool) -> bool:
    lowered = name.lower()
    if is_dir and lowered in _IGNORED_DIRS:
        return True
    if lowered.startswith(".env") or lowered in _SECRET_NAMES:
        return True
    ssh_private_names = {"id_" + algorithm for algorithm in ("rsa", "ed25519")}
    if lowered in ssh_private_names or lowered.endswith(_SECRET_SUFFIXES):
        return True
    return False


def _scan_source(path: Path, limits: _SandboxLimits) -> None:
    """Reject links/special files and bound the snapshot before copying it."""
    count = 0
    total = 0
    for current, dirnames, filenames in os.walk(path, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for name in dirnames:
            if _ignore_source_name(name, is_dir=True):
                continue
            candidate = current_path / name
            mode = candidate.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise ValueError(f"sandbox input contains unsupported path: {name}")
            kept_dirs.append(name)
        dirnames[:] = kept_dirs

        for name in filenames:
            if _ignore_source_name(name, is_dir=False):
                continue
            candidate = current_path / name
            info = candidate.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise ValueError(f"sandbox input contains unsupported file: {name}")
            count += 1
            total += info.st_size
            if count > limits.max_source_files or total > limits.max_source_bytes:
                raise ValueError("sandbox input exceeds source size limits")


def _make_snapshot_read_only(path: Path) -> None:
    for current, dirnames, filenames in os.walk(path, topdown=False):
        current_path = Path(current)
        for name in filenames:
            candidate = current_path / name
            mode = candidate.stat().st_mode
            candidate.chmod(0o555 if mode & 0o111 else 0o444)
        for name in dirnames:
            (current_path / name).chmod(0o555)
        current_path.chmod(0o555)


def _stage_project(
    path: Path,
    destination: Path,
    limits: _SandboxLimits,
    allowed_files: Iterable[str],
) -> Path:
    """Copy only files emitted by this generation, never a reused directory."""
    staged = destination / "input"
    staged.mkdir()
    count = 0
    total = 0
    seen: set[Path] = set()

    for raw in allowed_files:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("generated-file allowlist contains an invalid path")
        relative = Path(raw)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise ValueError("generated-file allowlist contains an unsafe path")
        if relative in seen:
            continue
        seen.add(relative)
        if any(
            _ignore_source_name(part, is_dir=index < len(relative.parts) - 1)
            for index, part in enumerate(relative.parts)
        ):
            # Generated `.env.example` files are useful deliverables but never
            # required to compile. Keep every env/key-shaped path outside the
            # sandbox even when the model emitted it in this generation.
            continue

        source = path / relative
        current = path
        for index, part in enumerate(relative.parts):
            current /= part
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(f"sandbox input contains unsupported file: {relative.name}")
            if index < len(relative.parts) - 1 and not stat.S_ISDIR(info.st_mode):
                raise ValueError(f"sandbox input has an invalid parent: {relative.name}")
        info = source.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"sandbox input contains unsupported file: {relative.name}")

        count += 1
        total += info.st_size
        if count > limits.max_source_files or total > limits.max_source_bytes:
            raise ValueError("sandbox input exceeds source size limits")

        target = staged / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # O_NOFOLLOW closes the final-component race. The post-copy lstat scan
        # below protects the mounted tree as a second independent check.
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(source, flags)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_size != info.st_size:
                raise ValueError(f"sandbox input changed while staging: {relative.name}")
            with (
                os.fdopen(descriptor, "rb", closefd=False) as source_file,
                target.open("xb") as target_file,
            ):
                remaining = opened.st_size
                while remaining:
                    chunk = source_file.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        raise ValueError(f"sandbox input changed while staging: {relative.name}")
                    target_file.write(chunk)
                    remaining -= len(chunk)
                if source_file.read(1):
                    raise ValueError(f"sandbox input grew while staging: {relative.name}")
        finally:
            os.close(descriptor)

    _scan_source(staged, limits)
    _make_snapshot_read_only(staged)
    return staged


def _read_manifest(package_json: Path) -> Dict[str, Any]:
    try:
        data = json.loads(package_json.read_text())
    except Exception as exc:
        raise ValueError(f"invalid package.json: {package_json.name}") from exc
    if not isinstance(data, dict):
        raise ValueError("package.json must contain an object")
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        dependencies = data.get(section) or {}
        if not isinstance(dependencies, dict):
            raise ValueError(f"package.json {section} must be an object")
        for package, spec in dependencies.items():
            if not isinstance(package, str) or not isinstance(spec, str):
                raise ValueError(f"package.json {section} contains a non-string dependency")
            lowered = spec.strip().lower()
            unsafe_prefixes = (
                "file:",
                "link:",
                "workspace:",
                "git:",
                "git+",
                "github:",
                "http:",
                "https:",
                "ssh:",
            )
            if lowered.startswith(unsafe_prefixes) or lowered.startswith(("/", "./", "../", "~")):
                raise ValueError(f"non-registry dependency rejected: {package}")
    return data


def _validate_lockfile(lockfile: Path) -> None:
    try:
        data = json.loads(lockfile.read_text())
    except Exception as exc:
        raise ValueError("offline install requires a valid package-lock.json") from exc
    if not isinstance(data, dict) or data.get("lockfileVersion") not in {2, 3}:
        raise ValueError("offline install requires package-lock.json lockfileVersion 2 or 3")
    packages = data.get("packages")
    if not isinstance(packages, dict):
        raise ValueError("package-lock.json must contain a packages map")
    for location, metadata in packages.items():
        if not isinstance(location, str) or not isinstance(metadata, dict):
            raise ValueError("package-lock.json contains an invalid package entry")
        if not location or location == "":
            continue
        if metadata.get("link") is True:
            raise ValueError("package-lock.json local links are not allowed")
        resolved = metadata.get("resolved")
        if resolved is not None and (
            not isinstance(resolved, str) or not resolved.startswith("https://registry.npmjs.org/")
        ):
            raise ValueError("package-lock.json contains a non-registry artifact")
        if resolved is not None and not isinstance(metadata.get("integrity"), str):
            raise ValueError("package-lock.json registry artifacts must have integrity hashes")


def _npm_scripts(manifest: Dict[str, Any]) -> Dict[str, str]:
    scripts = manifest.get("scripts") or {}
    if not isinstance(scripts, dict):
        return {}
    return {
        key: value
        for key, value in scripts.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def _trusted_verification_scripts(manifest: Dict[str, Any]) -> Dict[str, str]:
    """Return only generator-owned checks; reject self-authored no-op scripts."""
    scripts = _npm_scripts(manifest)
    selected: Dict[str, str] = {}
    for name, allowed_commands in _TRUSTED_VERIFICATION_SCRIPTS.items():
        if name not in scripts:
            continue
        command = scripts[name].strip()
        if command not in allowed_commands:
            raise ValueError(f"untrusted npm {name} script rejected")
        selected[name] = command

        # Defense in depth: npm config disables lifecycle hooks, and manifests
        # carrying hooks around the one explicit verification command are also
        # refused rather than relying on npm-version-specific behavior.
        for hook in (f"pre{name}", f"post{name}"):
            if hook in scripts:
                raise ValueError(f"npm lifecycle hook rejected: {hook}")
    return selected


def _node_roots(project_path: Path) -> List[Path]:
    """Return every generated package root; staging already bounds the tree."""
    return [candidate.parent for candidate in sorted(project_path.rglob("package.json"))]


def _validate_source_coverage(project_path: Path, roots: List[Path]) -> None:
    """Refuse source files that no discovered Node toolchain can possibly see."""
    uncovered = []
    unsupported = []
    for candidate in project_path.rglob("*"):
        if not candidate.is_file():
            continue
        suffix = candidate.suffix.lower()
        if suffix in _UNSUPPORTED_GENERATED_CODE_SUFFIXES:
            unsupported.append(candidate.relative_to(project_path).as_posix())
            if len(unsupported) >= 5:
                break
            continue
        if suffix not in _GENERATED_NODE_CODE_SUFFIXES:
            continue
        if not any(root == candidate.parent or root in candidate.parents for root in roots):
            uncovered.append(candidate.relative_to(project_path).as_posix())
            if len(uncovered) >= 5:
                break
    if unsupported:
        raise ValueError(
            "generated source has no supported sandbox toolchain: " + ", ".join(unsupported)
        )
    if uncovered:
        raise ValueError("generated source has no package toolchain root: " + ", ".join(uncovered))


class _DockerSandbox:
    """One disposable, inspected container with a bounded tmpfs workspace."""

    def __init__(
        self,
        runtime: str,
        source: Path,
        image: str,
        limits: _SandboxLimits,
    ):
        self.runtime = runtime
        self.source = source.resolve()
        self.image = image
        self.limits = limits
        self.name = f"moss-build-gate-{uuid.uuid4().hex[:16]}"
        self.deadline = time.monotonic() + limits.total_timeout
        self.cleanup_needed = False

    def _remaining_timeout(self, requested: int) -> int:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise _SandboxUnavailableError("sandbox total deadline exceeded")
        return max(1, min(requested, int(remaining + 0.999)))

    def _create_command(self) -> List[str]:
        return [
            self.runtime,
            "create",
            "--name",
            self.name,
            "--label=moss.build-gate=true",
            f"--label=moss.build-gate.expires={int(time.time()) + self.limits.total_timeout}",
            "--rm",
            "--pull=never",
            "--network=none",
            "--read-only",
            f"--user={_SUPERVISOR_USER}",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            "--security-opt=seccomp=builtin",
            "--cgroupns=private",
            "--ipc=private",
            f"--memory={self.limits.memory_bytes}",
            f"--memory-swap={self.limits.memory_bytes}",
            f"--cpus={self.limits.cpus:g}",
            f"--pids-limit={self.limits.pids_limit}",
            "--ulimit=nofile=1024:1024",
            "--ulimit=fsize=268435456:268435456",
            "--shm-size=67108864",
            "--stop-timeout=5",
            "--no-healthcheck",
            "--log-driver=none",
            "--hostname=moss-build-sandbox",
            "--mount",
            f"type=bind,src={self.source},dst=/input,readonly",
            "--tmpfs",
            (
                "/workspace:rw,exec,nosuid,nodev,"
                f"size={self.limits.workspace_bytes},mode=0700,"
                f"uid={_SANDBOX_UID},gid={_SANDBOX_GID},nr_inodes=200000"
            ),
            "--tmpfs",
            (
                "/tmp:rw,noexec,nosuid,nodev,"
                f"size={self.limits.tmp_bytes},mode=0700,"
                f"uid={_SANDBOX_UID},gid={_SANDBOX_GID},nr_inodes=20000"
            ),
            "--entrypoint=env",
            self.image,
            "-i",
            *_CONTAINER_ENV,
            "sleep",
            str(self.limits.total_timeout),
        ]

    def _control(self, command: List[str], action: str) -> subprocess.CompletedProcess[str]:
        try:
            proc = _run_cli(command, self._remaining_timeout(self.limits.setup_timeout))
        except subprocess.TimeoutExpired as exc:
            raise _SandboxUnavailableError(f"sandbox {action} timed out") from exc
        except Exception as exc:
            raise _SandboxUnavailableError(
                f"sandbox {action} unavailable: {str(exc)[:120]}"
            ) from exc
        if proc.returncode != 0:
            detail = _bounded_output(proc, 300).replace(str(self.source), "<sandbox-input>")
            raise _SandboxUnavailableError(f"sandbox {action} failed: {detail or proc.returncode}")
        return proc

    def _validate_inspect(self, payload: str) -> None:
        try:
            inspected = json.loads(payload)[0]
            host = inspected["HostConfig"]
            config = inspected["Config"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise _SandboxUnavailableError("sandbox inspect returned an invalid payload") from exc

        required = {
            "network isolation": host.get("NetworkMode") == "none",
            "read-only root": host.get("ReadonlyRootfs") is True,
            "non-privileged": host.get("Privileged") is False,
            "auto-remove": host.get("AutoRemove") is True,
            # Docker encodes its private PID namespace as an empty PidMode.
            # Unlike IPC/cgroup modes, `--pid=private` is invalid Docker CLI.
            "private PID namespace": not host.get("PidMode"),
            "private IPC namespace": host.get("IpcMode") == "private",
            "private cgroup namespace": host.get("CgroupnsMode") == "private",
            "memory limit": host.get("Memory") == self.limits.memory_bytes,
            "swap limit": host.get("MemorySwap") == self.limits.memory_bytes,
            "CPU limit": host.get("NanoCpus") == int(self.limits.cpus * 1_000_000_000),
            "PID limit": host.get("PidsLimit") == self.limits.pids_limit,
            "numeric non-root supervisor": config.get("User") == _SUPERVISOR_USER,
            "all capabilities dropped": "ALL" in (host.get("CapDrop") or []),
            "no added capabilities": not (host.get("CapAdd") or []),
            "no-new-privileges": any(
                value.startswith("no-new-privileges") for value in (host.get("SecurityOpt") or [])
            ),
            "built-in seccomp": "seccomp=builtin" in (host.get("SecurityOpt") or []),
            "no devices": not (host.get("Devices") or []),
            "no device requests": not (host.get("DeviceRequests") or []),
            "logging disabled": (host.get("LogConfig") or {}).get("Type") == "none",
            "bounded shared memory": host.get("ShmSize") == 64 * 1024**2,
            "no image-declared volumes": not (config.get("Volumes") or {}),
            "no restart": (host.get("RestartPolicy") or {}).get("Name", "no") == "no",
            "no published ports": not (host.get("PortBindings") or {})
            and host.get("PublishAllPorts") is not True,
            "sandbox label": (config.get("Labels") or {}).get("moss.build-gate") == "true",
        }

        ulimits = {
            item.get("Name"): (item.get("Soft"), item.get("Hard"))
            for item in (host.get("Ulimits") or [])
            if isinstance(item, dict)
        }
        required["file descriptor limit"] = ulimits.get("nofile") == (1024, 1024)
        required["file size limit"] = ulimits.get("fsize") == (268435456, 268435456)

        mounts = host.get("Mounts") or []
        required["single read-only input mount"] = (
            len(mounts) == 1
            and mounts[0].get("Type") == "bind"
            and Path(mounts[0].get("Source", "")).resolve() == self.source
            and mounts[0].get("Target") == "/input"
            and mounts[0].get("ReadOnly") is True
        )
        tmpfs = host.get("Tmpfs") or {}
        required["only bounded tmpfs mounts"] = set(tmpfs) == {"/workspace", "/tmp"}

        def tmpfs_matches(target: str, size: int, inode_limit: int, *, executable: bool) -> bool:
            raw = tmpfs.get(target)
            if not isinstance(raw, str):
                return False
            flags: set[str] = set()
            values: Dict[str, str] = {}
            for option in raw.split(","):
                if "=" in option:
                    key, value = option.split("=", 1)
                    values[key] = value
                else:
                    flags.add(option)
            return (
                {"rw", "nosuid", "nodev"}.issubset(flags)
                and (("exec" in flags) if executable else ("noexec" in flags))
                and values.get("size") == str(size)
                and values.get("mode") in {"0700", "700"}
                and values.get("uid") == str(_SANDBOX_UID)
                and values.get("gid") == str(_SANDBOX_GID)
                and values.get("nr_inodes") == str(inode_limit)
            )

        required["bounded workspace tmpfs"] = tmpfs_matches(
            "/workspace", self.limits.workspace_bytes, 200000, executable=True
        )
        required["bounded tmp tmpfs"] = tmpfs_matches(
            "/tmp", self.limits.tmp_bytes, 20000, executable=False
        )

        for mount in inspected.get("Mounts") or []:
            destination = mount.get("Destination") or mount.get("Target")
            if destination not in {"/input", "/workspace", "/tmp"}:
                required["no unexpected live mounts"] = False
                break

        missing = [name for name, present in required.items() if not present]
        if missing:
            raise _SandboxUnavailableError(
                "sandbox runtime did not enforce: " + ", ".join(sorted(missing))
            )

    def _read_live(self, path: str) -> str:
        proc = self._control(self._exec_command("/", ["cat", path]), f"read {path}")
        return (proc.stdout or "").strip()

    def _validate_effective_isolation(self) -> None:
        """Check kernel-visible controls before copying or running generated bytes."""
        status = {}
        for line in self._read_live("/proc/self/status").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                status[key] = value.strip()

        memory = self._read_live("/sys/fs/cgroup/memory.max")
        swap = self._read_live("/sys/fs/cgroup/memory.swap.max")
        pids = self._read_live("/sys/fs/cgroup/pids.max")
        cpu = self._read_live("/sys/fs/cgroup/cpu.max").split()
        cpu_limited = False
        if len(cpu) == 2 and cpu[0] != "max":
            try:
                cpu_limited = abs(int(cpu[0]) / int(cpu[1]) - self.limits.cpus) < 1e-6
            except (ValueError, ZeroDivisionError):
                cpu_limited = False

        required = {
            "effective seccomp": status.get("Seccomp") == "2",
            "effective no-new-privileges": status.get("NoNewPrivs") == "1",
            "zero effective capabilities": bool(status.get("CapEff"))
            and set(status["CapEff"]) == {"0"},
            "numeric non-root execution UID": status.get("Uid", "").split()
            == [str(_SANDBOX_UID)] * 4,
            "numeric non-root execution GID": status.get("Gid", "").split()
            == [str(_SANDBOX_GID)] * 4,
            "effective memory limit": memory == str(self.limits.memory_bytes),
            "effective zero swap": swap == "0",
            "effective PID limit": pids == str(self.limits.pids_limit),
            "effective CPU limit": cpu_limited,
        }
        missing = [name for name, present in required.items() if not present]
        if missing:
            raise _SandboxUnavailableError(
                "sandbox kernel did not enforce: " + ", ".join(sorted(missing))
            )

    def _exec_command(self, workdir: str, command: List[str]) -> List[str]:
        return [
            self.runtime,
            "exec",
            "--user",
            _SANDBOX_USER,
            "--workdir",
            workdir,
            self.name,
            "env",
            "-i",
            *_CONTAINER_ENV,
            *command,
        ]

    def prepare(self) -> None:
        self.cleanup_needed = True
        self._control(self._create_command(), "create")
        inspect = self._control([self.runtime, "inspect", self.name], "inspect")
        self._validate_inspect(inspect.stdout)
        self._control([self.runtime, "start", self.name], "start")
        live_inspect = self._control([self.runtime, "inspect", self.name], "live inspect")
        self._validate_inspect(live_inspect.stdout)
        self._validate_effective_isolation()
        copy = _run_sandbox_step(
            self._exec_command("/workspace", ["cp", "-R", "/input/.", "/workspace/"]),
            name="sandbox: copy input",
            logical_command="copy sanitized input",
            timeout=self._remaining_timeout(self.limits.setup_timeout),
            max_output=self.limits.max_output,
            verifies=False,
        )
        if copy.status != PASSED:
            raise _SandboxUnavailableError(f"sandbox input copy {copy.status}: {copy.detail}")
        make_writable = _run_sandbox_step(
            self._exec_command("/workspace", ["chmod", "-R", "u+rwX", "/workspace"]),
            name="sandbox: prepare workspace",
            logical_command="make sandbox workspace writable",
            timeout=self._remaining_timeout(self.limits.setup_timeout),
            max_output=self.limits.max_output,
            verifies=False,
        )
        if make_writable.status != PASSED:
            raise _SandboxUnavailableError(
                f"sandbox workspace preparation {make_writable.status}: {make_writable.detail}"
            )
        cache = _run_sandbox_step(
            self._exec_command(
                "/workspace",
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p /tmp/npm-cache && "
                        "if [ -d /opt/moss/npm-cache ]; then "
                        "cp -R /opt/moss/npm-cache/. /tmp/npm-cache/; fi"
                    ),
                ],
            ),
            name="sandbox: prepare offline cache",
            logical_command="copy trusted offline npm cache",
            timeout=self._remaining_timeout(self.limits.setup_timeout),
            max_output=self.limits.max_output,
            verifies=False,
        )
        if cache.status != PASSED:
            raise _SandboxUnavailableError(
                f"sandbox cache preparation {cache.status}: {cache.detail}"
            )

    def run_npm(
        self,
        workdir: str,
        args: List[str],
        *,
        name: str,
        timeout: int,
        max_output: int,
        verifies: bool,
    ) -> StepResult:
        logical = "npm " + " ".join(args)
        try:
            effective_timeout = self._remaining_timeout(timeout)
        except _SandboxUnavailableError as exc:
            return StepResult(
                name=name,
                status=FAILED,
                command=logical,
                detail=str(exc),
                verifies=verifies,
            )
        return _run_sandbox_step(
            self._exec_command(workdir, ["npm", *args]),
            name=name,
            logical_command=logical,
            timeout=effective_timeout,
            max_output=max_output,
            verifies=verifies,
        )

    def cleanup(self) -> bool:
        if not self.cleanup_needed:
            return True
        try:
            proc = _run_cli(
                [self.runtime, "rm", "--force", "--volumes", self.name],
                min(self.limits.setup_timeout, 30),
            )
        except Exception:
            return False
        if proc.returncode == 0:
            return True
        detail = _bounded_output(proc, 300).lower()
        return "no such container" in detail


def _container_workdir(root: Path, staged: Path) -> str:
    relative = root.relative_to(staged).as_posix()
    return "/workspace" if relative == "." else f"/workspace/{relative}"


def _run_build_gate_once(
    project_path: str,
    config: Optional[dict] = None,
    allowed_files: Optional[Iterable[str]] = None,
) -> BuildGateResult:
    """Run generated npm checks only inside a verified disposable sandbox."""
    settings = {**BUILD_GATE_DEFAULTS, **(config or {})}
    result = BuildGateResult()

    if settings.get("enabled", False) is not True:
        result.reason = "build gate disabled in config"
        return result

    if allowed_files is None:
        result.reason = "generated-file allowlist missing; reused project trees are forbidden"
        return result

    try:
        limits = _validate_settings(settings)
    except ValueError as exc:
        result.reason = f"invalid build gate config: {exc}"
        return result

    path = Path(project_path)
    if path.is_symlink() or not path.is_dir():
        result.reason = "project path not found or unsafe"
        return result
    path = path.resolve()

    runtime = shutil.which(str(settings["container_runtime"]))
    if not runtime:
        result.reason = "container runtime unavailable; host fallback is forbidden"
        return result
    runtime = str(Path(runtime).resolve())

    try:
        with tempfile.TemporaryDirectory(prefix="moss-build-gate-") as temporary:
            staged = _stage_project(path, Path(temporary), limits, allowed_files)
            roots = _node_roots(staged)
            if not roots:
                result.reason = "no package.json found — nothing this gate knows how to build"
                return result
            if len(roots) > 16:
                result.status = FAILED
                result.reason = "too many Node workspaces for one sandbox gate"
                return result

            manifests: Dict[Path, Dict[str, Any]] = {}
            verification_scripts: Dict[Path, Dict[str, str]] = {}
            unverified_roots: List[str] = []
            try:
                _validate_source_coverage(staged, roots)
                for root in roots:
                    manifests[root] = _read_manifest(root / "package.json")
                    if settings.get("install") is True:
                        _validate_lockfile(root / "package-lock.json")
                    scripts = _trusted_verification_scripts(manifests[root])
                    verification_scripts[root] = scripts
                    if not scripts:
                        label = root.relative_to(staged).as_posix() or "."
                        unverified_roots.append(label)
            except ValueError as exc:
                result.status = FAILED
                result.reason = str(exc)
                return result
            if unverified_roots:
                result.reason = "workspace(s) have no build/typecheck/test script: " + ", ".join(
                    unverified_roots
                )
                return result

            try:
                _verify_runtime_security(runtime, limits.setup_timeout)
                _cleanup_orphaned_sandboxes(runtime, limits.setup_timeout)
            except _SandboxUnavailableError as exc:
                result.reason = str(exc)
                return result

            sandbox = _DockerSandbox(runtime, staged, str(settings["container_image"]), limits)
            try:
                sandbox.prepare()

                # Complete all setup before any generated script executes.  Both
                # setup and execution stay offline; lifecycle scripts are disabled.
                if settings.get("install") is True:
                    for root in roots:
                        label = root.relative_to(staged).as_posix() or "."
                        step = sandbox.run_npm(
                            _container_workdir(root, staged),
                            [
                                "ci",
                                "--offline",
                                "--ignore-scripts",
                                "--no-audit",
                                "--no-fund",
                            ],
                            name=f"{label}: npm ci",
                            timeout=limits.install_timeout,
                            max_output=limits.max_output,
                            verifies=False,
                        )
                        result.steps.append(step)
                        if step.status != PASSED:
                            result.status = FAILED if step.status == FAILED else SKIPPED
                            result.reason = f"{label}: offline install {step.status}"
                            return result

                for root in roots:
                    label = root.relative_to(staged).as_posix() or "."
                    scripts = verification_scripts[root]
                    for script in ("build", "typecheck", "test"):
                        if script not in scripts:
                            continue
                        args = ["run", script, "--if-present"]
                        if script == "test" and "vitest" in scripts.get("test", ""):
                            args += ["--", "--watch=false"]
                        step = sandbox.run_npm(
                            _container_workdir(root, staged),
                            args,
                            name=f"{label}: npm run {script}",
                            timeout=limits.step_timeout,
                            max_output=limits.max_output,
                            verifies=True,
                        )
                        result.steps.append(step)
                        if step.status != PASSED:
                            result.status = FAILED if step.status == FAILED else SKIPPED
                            result.reason = f"{label}: {script} {step.status}"
                            return result

                verified = [step for step in result.steps if step.verifies]
                if not verified:
                    result.reason = "no build/typecheck/test script to run — nothing was verified"
                    return result
                if any(step.status != PASSED for step in verified):
                    result.status = FAILED
                    result.reason = "one or more verification steps did not pass"
                    return result

                result.status = PASSED
                result.reason = f"{len(verified)} sandboxed check(s) passed"
                return result
            except _SandboxUnavailableError as exc:
                result.status = SKIPPED
                result.reason = str(exc)[:500]
                return result
            finally:
                if not sandbox.cleanup():
                    result.status = FAILED
                    result.reason = "sandbox cleanup failed; manual container cleanup required"
    except (OSError, ValueError) as exc:
        result.status = SKIPPED
        result.reason = f"could not create safe sandbox input: {str(exc)[:300]}"
    return result


def run_build_gate(
    project_path: str,
    config: Optional[dict] = None,
    allowed_files: Optional[Iterable[str]] = None,
) -> BuildGateResult:
    """Serialize resource-heavy sandboxes and fail closed under contention."""
    if config is not None and not isinstance(config, dict):
        return BuildGateResult(reason="invalid build gate config: expected a mapping")
    settings = {**BUILD_GATE_DEFAULTS, **(config or {})}
    if settings.get("enabled") is not True:
        return _run_build_gate_once(project_path, config, allowed_files)
    if not _BUILD_GATE_SLOT.acquire(blocking=False):
        return BuildGateResult(reason="sandbox worker busy; concurrent execution refused")
    lease: Optional[int] = None
    try:
        try:
            lease = _acquire_worker_lease()
        except _SandboxUnavailableError as exc:
            return BuildGateResult(reason=str(exc))
        return _run_build_gate_once(project_path, config, allowed_files)
    finally:
        if lease is not None:
            _release_worker_lease(lease)
        _BUILD_GATE_SLOT.release()


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
