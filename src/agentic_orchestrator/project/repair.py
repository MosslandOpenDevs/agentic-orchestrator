"""
Deterministic repair of generated source files.

These are cheap, regex-level fixes for the bug classes we have actually seen in
generator output. They run *before* the (optional) LLM repair pass so the model
is only asked to fix the genuinely hard cases. Every fix here is conservative:
it only changes code that is unambiguously wrong, and only outside of string
literals and comments.

OpenZeppelin policy
-------------------
The small local model emits a mix of OZ v4 and v5 idioms (v4 ``security/``
import paths with a no-arg ``Ownable`` constructor, but sometimes a v5
``Ownable(msg.sender)`` base call, or v5 ``utils/`` import paths). We pin a
single version — **v4.9.x** — because it matches the model's dominant output,
and normalize everything toward it:

- ``utils/ReentrancyGuard.sol`` / ``utils/Pausable.sol`` (v5) -> ``security/``
- a ``Ownable(...)`` base-constructor call (v5) is removed (v4 ``Ownable`` has
  a no-arg constructor)
- any ``.sol`` that imports ``@openzeppelin/contracts`` forces the dependency
  into ``contracts/package.json``
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Callable, List, Sequence, Tuple

from .verifier import SOLIDITY, detect_language

logger = logging.getLogger(__name__)

# Pinned OpenZeppelin major used for generated Hardhat projects. See module docstring.
OZ_PACKAGE = "@openzeppelin/contracts"
OZ_VERSION = "^4.9.6"

_CONTRACTS_PACKAGE_JSON = "contracts/package.json"


@dataclass
class RepairResult:
    """Outcome of repairing a single file."""

    path: str
    content: str
    fixes: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.fixes)


class CodeRepairer:
    """Apply deterministic fixes to generated source files."""

    def repair_file(self, path: str, content: str) -> RepairResult:
        """Return a repaired copy of one file plus a list of applied fixes."""
        language = detect_language(path)
        if language == SOLIDITY:
            new_content, fixes = self._repair_solidity(content)
            return RepairResult(path=path, content=new_content, fixes=fixes)
        # Other languages currently have no safe deterministic fixes; the LLM
        # repair pass handles them when verification fails.
        return RepairResult(path=path, content=content, fixes=[])

    # -- Solidity ----------------------------------------------------------

    def _repair_solidity(self, content: str) -> Tuple[str, List[str]]:
        fixes: List[str] = []
        result = content

        # 1. SPDX license header (solc emits a warning without it).
        if "SPDX-License-Identifier" not in result:
            result = "// SPDX-License-Identifier: MIT\n" + result
            fixes.append("added missing SPDX-License-Identifier header")

        # 2. pragma directive (a hard compile error when absent).
        if "pragma solidity" not in result:
            result = _insert_after_spdx(result, "pragma solidity ^0.8.20;")
            fixes.append("added missing `pragma solidity` directive")

        # `x.length()` is invalid for arrays/bytes (`.length` is a property), but
        # OZ EnumerableSet/EnumerableMap legitimately expose a `.length()` library
        # method. Skip the rewrite entirely when those libraries are in play so we
        # never turn valid code into a member-not-found error.
        if "Enumerable" not in result:
            result, n = _sub_in_code(result, re.compile(r"\.length\s*\(\s*\)"), ".length")
            if n:
                fixes.append(
                    f"replaced {n} likely-invalid `.length()` call(s) with `.length` property"
                )

        # OZ import paths live inside string literals, so the rewrite is anchored
        # to actual `import` directives (keeping whole-line scope) rather than
        # mutating arbitrary string contents elsewhere in the file.
        result, n = _normalize_oz_import_paths(result)
        if n:
            fixes.append(f"normalized {n} OpenZeppelin v5 import path(s) to v4 `security/`")

        # Remove a v5-style `Ownable(<args>)` base-constructor call (v4 Ownable is
        # no-arg). Paren-balanced and anchored to the base-call slot, so it never
        # touches `new Ownable(...)`, casts like `Ownable(x).owner()`, or
        # `is Ownable` inheritance.
        result, n = _transform_in_code(result, _strip_ownable_base_call)
        if n:
            fixes.append(
                f"removed {n} v5-style `Ownable(...)` base call "
                "(pinned OZ v4 uses a no-arg constructor)"
            )

        # `now` was removed in Solidity 0.7. Replace the bare global only.
        result, n = _sub_in_code(result, re.compile(r"(?<![\w.$])now(?![\w(])"), "block.timestamp")
        if n:
            fixes.append(f"replaced {n} removed `now` global with `block.timestamp`")

        return result, fixes


# --- cross-file repair -----------------------------------------------------


def ensure_contract_dependencies(files: Sequence[object]) -> List[str]:
    """Ensure ``contracts/package.json`` declares OpenZeppelin when needed.

    Operates in place on a sequence of objects exposing ``.path`` and mutable
    ``.content`` attributes (both ``TemplateFile`` and ``GeneratedFile`` do).
    Returns a list of human-readable fix descriptions (empty if nothing changed).
    """
    fixes: List[str] = []

    imports_oz = any(
        detect_language(getattr(f, "path", "")) == SOLIDITY
        and OZ_PACKAGE in getattr(f, "content", "")
        for f in files
    )
    if not imports_oz:
        return fixes

    pkg = next(
        (f for f in files if getattr(f, "path", "") == _CONTRACTS_PACKAGE_JSON),
        None,
    )
    if pkg is None:
        # No package.json in the set — the generator is responsible for emitting
        # the Hardhat scaffold; we don't fabricate one here.
        logger.debug(
            "OZ imported but %s absent; skipping dependency injection", _CONTRACTS_PACKAGE_JSON
        )
        return fixes

    try:
        data = json.loads(pkg.content)
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Could not parse %s; skipping OZ dependency injection", _CONTRACTS_PACKAGE_JSON
        )
        return fixes

    deps = data.get("dependencies")
    if not isinstance(deps, dict):
        deps = {}
    if deps.get(OZ_PACKAGE) != OZ_VERSION:
        deps[OZ_PACKAGE] = OZ_VERSION
        data["dependencies"] = deps
        pkg.content = json.dumps(data, indent=2) + "\n"
        fixes.append(f"added `{OZ_PACKAGE}: {OZ_VERSION}` to {_CONTRACTS_PACKAGE_JSON}")

    return fixes


# --- helpers ---------------------------------------------------------------


def _insert_after_spdx(content: str, line: str) -> str:
    """Insert ``line`` right after an SPDX header, else at the top."""
    lines = content.splitlines(keepends=True)
    for idx, raw in enumerate(lines):
        if "SPDX-License-Identifier" in raw:
            tail = raw if raw.endswith("\n") else raw + "\n"
            lines[idx] = tail
            lines.insert(idx + 1, line + "\n")
            return "".join(lines)
    return line + "\n" + content


def _transform_in_code(content: str, fn: Callable[[str], Tuple[str, int]]) -> Tuple[str, int]:
    """Apply ``fn`` to code segments only (never strings/comments).

    ``fn`` takes a code segment and returns ``(new_text, n_changes)``. Returns the
    rejoined content and the total number of changes.
    """
    total = 0
    out: List[str] = []
    for is_code, text in _solidity_segments(content):
        if is_code:
            new_text, n = fn(text)
            total += n
            out.append(new_text)
        else:
            out.append(text)
    return "".join(out), total


def _sub_in_code(content: str, pattern: re.Pattern, repl) -> Tuple[str, int]:
    """Apply ``pattern.sub(repl, ...)`` only to code, not strings/comments."""
    return _transform_in_code(content, lambda text: pattern.subn(repl, text))


_OZ_UTILS_PATH_RE = re.compile(r"@openzeppelin/contracts/utils/(ReentrancyGuard|Pausable)\.sol")


def _normalize_oz_import_paths(content: str) -> Tuple[str, int]:
    """Rewrite OZ v5 ``utils/`` paths to v4 ``security/`` on ``import`` lines only.

    Import paths are string literals, so this runs line-wise (not in code
    segments) but is anchored to ``import`` directives to avoid mutating an
    unrelated string literal elsewhere in the file.
    """
    total = 0
    out: List[str] = []
    for line in content.splitlines(keepends=True):
        if line.lstrip().startswith("import"):
            new_line, n = _OZ_UTILS_PATH_RE.subn(r"@openzeppelin/contracts/security/\1.sol", line)
            total += n
            out.append(new_line)
        else:
            out.append(line)
    return "".join(out), total


def _strip_ownable_base_call(code: str) -> Tuple[str, int]:
    """Remove v5-style ``Ownable(<args>)`` base-constructor calls from code.

    Paren-balanced (handles ``Ownable(_msgSender())``) and anchored to the
    base-call slot: skips ``new Ownable(...)`` instantiations and
    ``Ownable(x).member`` casts, and ignores ``is Ownable`` / identifiers that
    merely end in ``Ownable``.
    """
    needle = "Ownable"
    out: List[str] = []
    i = 0
    n = len(code)
    count = 0

    while i < n:
        idx = code.find(needle, i)
        if idx == -1:
            out.append(code[i:])
            break

        end_name = idx + len(needle)
        # `(` after optional whitespace?
        k = end_name
        while k < n and code[k] in " \t":
            k += 1

        is_call = k < n and code[k] == "("
        # A clean left boundary: start of segment, or a non-identifier char that
        # is not '.' (member access). NB: an empty prev must count as a boundary,
        # so the membership test only applies when there is a preceding char.
        if idx == 0:
            boundary_ok = True
        else:
            prev = code[idx - 1]
            boundary_ok = not (prev.isalnum() or prev in "_$.")
        if not is_call or not boundary_ok:
            out.append(code[i:end_name])
            i = end_name
            continue

        # Scan the balanced parenthesized argument list.
        depth = 0
        p = k
        while p < n:
            if code[p] == "(":
                depth += 1
            elif code[p] == ")":
                depth -= 1
                if depth == 0:
                    break
            p += 1
        if p >= n:  # unbalanced — leave it for the verifier to flag
            out.append(code[i:end_name])
            i = end_name
            continue
        after = p + 1

        # Preceding word (skip whitespace) — exclude `new Ownable(...)`.
        b = idx - 1
        while b >= 0 and code[b] in " \t":
            b -= 1
        we = b
        while b >= 0 and (code[b].isalnum() or code[b] in "_$"):
            b -= 1
        preceding_word = code[b + 1 : we + 1]

        # Following non-space char — `.` means a cast like `Ownable(x).owner()`.
        a = after
        while a < n and code[a] in " \t":
            a += 1
        following = code[a] if a < n else ""

        if preceding_word == "new" or following == ".":
            out.append(code[i:after])
            i = after
            continue

        # Base-constructor call: drop `Ownable(...)`, keep everything before it.
        out.append(code[i:idx])
        i = after
        count += 1

    return "".join(out), count


def _solidity_segments(content: str) -> List[Tuple[bool, str]]:
    """Split Solidity into ``(is_code, text)`` segments.

    Comments (``//`` and ``/* */``) and string/char literals are emitted as
    ``is_code=False`` so regex fixes never corrupt them. Verbatim text is
    preserved so the segments rejoin to the original source.
    """
    segments: List[Tuple[bool, str]] = []
    buf: List[str] = []
    i = 0
    n = len(content)

    def flush_code() -> None:
        if buf:
            segments.append((True, "".join(buf)))
            buf.clear()

    while i < n:
        ch = content[i]
        nxt = content[i + 1] if i + 1 < n else ""

        if ch == "/" and nxt == "/":
            flush_code()
            end = content.find("\n", i)
            end = n if end == -1 else end
            segments.append((False, content[i:end]))
            i = end
            continue

        if ch == "/" and nxt == "*":
            flush_code()
            end = content.find("*/", i + 2)
            end = n if end == -1 else end + 2
            segments.append((False, content[i:end]))
            i = end
            continue

        if ch in ('"', "'"):
            flush_code()
            quote = ch
            j = i + 1
            while j < n:
                if content[j] == "\\":
                    j += 2
                    continue
                if content[j] == quote:
                    j += 1
                    break
                if content[j] == "\n":
                    # Unterminated literal: stop at the line break so the rest of
                    # the file is still treated as code (and fixes still apply).
                    break
                j += 1
            segments.append((False, content[i:j]))
            i = j
            continue

        buf.append(ch)
        i += 1

    flush_code()
    return segments
