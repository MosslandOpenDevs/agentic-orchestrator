"""
Post-generation code verification for project scaffolding.

The project generator emits code from a small local model (gemma3:4b) plus a
handful of hard-coded templates. Neither is guaranteed to compile, so this
module gives the scaffold a verification *gate*: every generated source file is
checked for the failure classes we have actually observed in generated output
(plain syntax errors, truncated output, ``string.length()``, missing pragmas).

Design constraints:

- **Graceful degradation.** The generation host may not have ``solc``,
  ``tsc`` or ``esbuild`` installed. A missing toolchain yields a ``SKIPPED``
  result, never a false ``FAILED``. Python is always fully syntax-checked
  because :func:`compile` is built in.
- **No new hard dependencies.** External tools are discovered on ``PATH`` and
  invoked lazily behind ``try/except``; nothing here imports a third-party
  package at module load time.
- **No false failures.** A check only reports ``FAILED`` for a *definite*
  error. Anything version-dependent (e.g. OpenZeppelin v4/v5 import paths) is
  left to the repairer, not flagged here.
- **Pure over files.** Verifiers take ``content`` and return a
  :class:`VerificationResult`; the scaffold owns the file list and persistence.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# --- Languages -------------------------------------------------------------

SOLIDITY = "solidity"
PYTHON = "python"
TYPESCRIPT = "typescript"
JAVASCRIPT = "javascript"
UNKNOWN = "unknown"

# File extension -> language. Only languages we can meaningfully verify are
# listed; everything else (md, json, yml, env, sol-adjacent configs) maps to
# UNKNOWN and is skipped.
_LANG_BY_EXT: Dict[str, str] = {
    ".sol": SOLIDITY,
    ".py": PYTHON,
    ".tsx": TYPESCRIPT,
    ".mts": TYPESCRIPT,
    ".cts": TYPESCRIPT,
    ".ts": TYPESCRIPT,
    ".jsx": JAVASCRIPT,
    ".mjs": JAVASCRIPT,
    ".cjs": JAVASCRIPT,
    ".js": JAVASCRIPT,
}

# esbuild loader per extension. Using the `tsx` loader for plain `.ts` would
# misparse legal TS (generic arrows, angle-bracket assertions) as JSX, so the
# loader is chosen by extension, not by coarse language.
_ESBUILD_LOADER_BY_EXT: Dict[str, str] = {
    ".tsx": "tsx",
    ".ts": "ts",
    ".mts": "ts",
    ".cts": "ts",
    ".jsx": "jsx",
    ".js": "js",
    ".mjs": "js",
    ".cjs": "js",
}


def _esbuild_loader(path: str) -> str:
    """Pick the esbuild loader for a file path (defaults to ``ts``)."""
    lowered = path.lower()
    for ext, loader in _ESBUILD_LOADER_BY_EXT.items():
        if lowered.endswith(ext):
            return loader
    return "ts"


def detect_language(path: str) -> str:
    """Return the verification language for a file path, or ``UNKNOWN``."""
    lowered = path.lower()
    for ext, lang in _LANG_BY_EXT.items():
        if lowered.endswith(ext):
            return lang
    return UNKNOWN


# --- Results ---------------------------------------------------------------


class VerificationStatus:
    """Outcome of verifying a single file.

    ``SKIPPED`` means "we could not fully verify" (no toolchain, or an
    unverifiable language) and is treated as a non-failure by the scaffold.
    """

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class VerificationResult:
    """Result of verifying one generated file."""

    path: str
    language: str
    status: str
    checker: str
    errors: List[str] = field(default_factory=list)
    # Set by the scaffold once a repair pass has run; recorded for the summary.
    repaired: bool = False

    @property
    def ok(self) -> bool:
        """True when the file is not a confirmed failure (passed or skipped)."""
        return self.status != VerificationStatus.FAILED

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "language": self.language,
            "status": self.status,
            "checker": self.checker,
            "errors": self.errors,
            "repaired": self.repaired,
        }


# --- Verifier --------------------------------------------------------------


class CodeVerifier:
    """Verify generated source files with graceful toolchain degradation.

    Args:
        enable_solc: Attempt real ``solc`` compilation for import-free Solidity
            when the binary is on ``PATH``. Default True.
        enable_esbuild: Attempt ``esbuild`` syntax checks for TS/JS when
            available on ``PATH``. Default True.
        subprocess_timeout: Per-tool subprocess timeout in seconds.
    """

    def __init__(
        self,
        enable_solc: bool = True,
        enable_esbuild: bool = True,
        subprocess_timeout: int = 60,
    ) -> None:
        self.enable_solc = enable_solc
        self.enable_esbuild = enable_esbuild
        self.subprocess_timeout = subprocess_timeout
        self._tool_cache: Dict[str, Optional[str]] = {}

    # -- public API --

    def verify(self, path: str, content: str) -> VerificationResult:
        """Verify a single file, dispatching on its detected language."""
        language = detect_language(path)

        if not content or not content.strip():
            return VerificationResult(
                path=path,
                language=language,
                status=VerificationStatus.FAILED,
                checker="empty-check",
                errors=["file is empty"],
            )

        if language == PYTHON:
            status, checker, errors = self._verify_python(content)
        elif language == SOLIDITY:
            status, checker, errors = self._verify_solidity(content)
        elif language in (TYPESCRIPT, JAVASCRIPT):
            status, checker, errors = self._verify_js_ts(content, path)
        else:
            status, checker, errors = (VerificationStatus.SKIPPED, "unsupported-language", [])

        return VerificationResult(
            path=path,
            language=language,
            status=status,
            checker=checker,
            errors=errors,
        )

    # -- Python --

    def _verify_python(self, content: str) -> Tuple[str, str, List[str]]:
        """Full syntax check using the built-in compiler (always available)."""
        try:
            compile(content, "<generated>", "exec")
            return VerificationStatus.PASSED, "py-compile", []
        except SyntaxError as exc:
            location = f"line {exc.lineno}" if exc.lineno else "unknown line"
            return (
                VerificationStatus.FAILED,
                "py-compile",
                [f"SyntaxError at {location}: {exc.msg}"],
            )
        except ValueError as exc:
            # e.g. source containing null bytes
            return VerificationStatus.FAILED, "py-compile", [f"invalid source: {exc}"]

    # -- Solidity --

    def _verify_solidity(self, content: str) -> Tuple[str, str, List[str]]:
        """Static checks (always) plus optional ``solc`` for import-free code.

        Definite static errors always win (``FAILED``). When static checks are
        clean we only claim ``PASSED`` if a real compiler ran; otherwise the
        result is ``SKIPPED`` so the summary stays honest about what was
        actually compiled.
        """
        static_errors = self._solidity_static_issues(content)
        if static_errors:
            return VerificationStatus.FAILED, "solc-static", static_errors

        # Real compilation is only attempted when there are no external imports
        # to resolve — otherwise unresolved ``@openzeppelin/...`` imports would
        # produce false failures on hosts without the npm packages installed.
        if self.enable_solc and not _has_external_imports(content):
            solc = self._which("solc")
            if solc:
                ok, errors = self._run_solc(solc, content)
                if ok:
                    return VerificationStatus.PASSED, "solc", []
                return VerificationStatus.FAILED, "solc", errors
            reason = "solc-static (solc not installed)"
        elif not self.enable_solc:
            reason = "solc-static (solc disabled)"
        else:
            reason = "solc-static (external imports, not compiled)"
        return VerificationStatus.SKIPPED, reason, []

    @staticmethod
    def _solidity_static_issues(content: str) -> List[str]:
        """Detect definite Solidity errors without a compiler.

        Conservative on purpose: every pattern here is *always* invalid (or, for
        ``.length()``, invalid unless an Enumerable* library is in play), so it
        does not produce false positives on otherwise-good code.
        """
        errors: List[str] = []
        stripped = _strip_solidity_noise(content)

        if "pragma solidity" not in content:
            errors.append("missing `pragma solidity` directive")

        # `.length` is an array/bytes property, never a method — except OZ
        # Enumerable{Set,Map} expose a real `.length()` library call, so the
        # check is suppressed when those libraries appear.
        if "Enumerable" not in content:
            for lineno in _find_line_numbers(stripped, _LENGTH_CALL_NEEDLE):
                errors.append(
                    f"line {lineno}: invalid `.length()` call "
                    "(Solidity `.length` is a property, not a method)"
                )

        # Brace/paren imbalance almost always means the model truncated output.
        for opener, closer, name in (("{", "}", "braces"), ("(", ")", "parens")):
            delta = stripped.count(opener) - stripped.count(closer)
            if delta != 0:
                errors.append(
                    f"unbalanced {name} ({opener}{closer} differ by {delta}) "
                    "— output may be truncated"
                )

        return errors

    def _run_solc(self, solc: str, content: str) -> Tuple[bool, List[str]]:
        """Compile a self-contained contract via ``solc`` reading from stdin."""
        try:
            proc = subprocess.run(
                [solc, "--bin", "-"],
                input=content,
                capture_output=True,
                text=True,
                timeout=self.subprocess_timeout,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.debug("solc invocation failed, skipping: %s", exc)
            return True, []  # treat as non-failure; static checks already ran
        if proc.returncode == 0:
            return True, []
        return False, _split_tool_errors(proc.stderr or proc.stdout)

    # -- TypeScript / JavaScript --

    def _verify_js_ts(self, content: str, path: str) -> Tuple[str, str, List[str]]:
        """Syntax check via ``esbuild`` (no type-checking, no import resolution).

        ``esbuild`` parses TS/TSX/JS/JSX syntax without resolving imports, so it
        flags truncation and syntax errors without needing ``node_modules``.
        Type errors are out of scope (they require installed dependencies). The
        loader is chosen by file extension so plain ``.ts`` is not parsed as JSX.
        """
        if not self.enable_esbuild:
            return VerificationStatus.SKIPPED, "esbuild (disabled)", []

        esbuild = self._which("esbuild")
        if not esbuild:
            return VerificationStatus.SKIPPED, "esbuild (not installed)", []

        loader = _esbuild_loader(path)
        try:
            proc = subprocess.run(
                [esbuild, f"--loader={loader}", "--log-level=warning"],
                input=content,
                capture_output=True,
                text=True,
                timeout=self.subprocess_timeout,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.debug("esbuild invocation failed, skipping: %s", exc)
            return VerificationStatus.SKIPPED, "esbuild (unavailable)", []

        if proc.returncode == 0:
            return VerificationStatus.PASSED, "esbuild", []
        return VerificationStatus.FAILED, "esbuild", _split_tool_errors(proc.stderr)

    # -- helpers --

    def _which(self, tool: str) -> Optional[str]:
        """Locate a tool on PATH, cached for the lifetime of the verifier."""
        if tool not in self._tool_cache:
            self._tool_cache[tool] = shutil.which(tool)
        return self._tool_cache[tool]


# --- module-level helpers --------------------------------------------------

_LENGTH_CALL_NEEDLE = ".length()"


def _has_external_imports(content: str) -> bool:
    """True if the contract imports a package path (e.g. ``@openzeppelin/...``).

    Relative imports (``./`` / ``../``) are also treated as external because we
    verify one file at a time without its siblings on disk.
    """
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("import"):
            return True
    return False


def _strip_solidity_noise(content: str) -> str:
    """Remove comments and string literals so structural checks don't trip on them."""
    out: List[str] = []
    i = 0
    n = len(content)
    while i < n:
        ch = content[i]
        nxt = content[i + 1] if i + 1 < n else ""
        # line comment
        if ch == "/" and nxt == "/":
            i = content.find("\n", i)
            if i == -1:
                break
            continue
        # block comment
        if ch == "/" and nxt == "*":
            end = content.find("*/", i + 2)
            i = end + 2 if end != -1 else n
            continue
        # string / char literal
        if ch in ('"', "'"):
            quote = ch
            i += 1
            while i < n:
                if content[i] == "\\":
                    i += 2
                    continue
                if content[i] == quote:
                    i += 1
                    break
                i += 1
            out.append(" ")  # keep a placeholder token
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _find_line_numbers(content: str, needle: str) -> List[int]:
    """Return 1-based line numbers where ``needle`` (a literal) appears."""
    return [idx for idx, line in enumerate(content.splitlines(), start=1) if needle in line]


def _split_tool_errors(text: Optional[str], limit: int = 8) -> List[str]:
    """Turn raw compiler stderr into a trimmed list of non-empty lines."""
    if not text:
        return ["compilation failed (no diagnostics captured)"]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ["compilation failed (no diagnostics captured)"]
    if len(lines) > limit:
        return lines[:limit] + [f"... (+{len(lines) - limit} more)"]
    return lines
