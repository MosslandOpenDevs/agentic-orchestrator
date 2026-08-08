"""Path helpers for values that cross the public API boundary.

Kept dependency-free (stdlib only) so it is safe to import from anywhere,
including the low-level ``db.models`` module, without risking import cycles.
"""

import re
from typing import Optional

# Generated projects live at <repo>/projects/<name>. Everything above that
# segment is where *this deployment* happens to keep its checkout.
_REPO_PROJECT_ROOT = "projects"


def public_project_path(path: Optional[str]) -> Optional[str]:
    """Reduce an on-disk project path to its repo-relative form.

    ``Project.directory_path`` and ``ProjectGenerationResult.project_path``
    hold absolute paths on the app server
    (``/home/<account>/agentic-orchestrator/projects/<name>``), and both are
    serialised straight into responses served from ao.moss.land -- a public
    site in front of a public repository. The prefix names the server's login
    account and directory layout, tells a reader nothing about the project,
    and is exactly the sort of detail the rest of this repo keeps in
    ``CLAUDE.local.md``. So only the portion that also exists in the
    repository is published: ``projects/<name>``.

    The stored value is left alone -- the scaffold, the build gate and git all
    need the real location on disk. Narrowing at serialisation time (rather
    than at write time) means the rows written before this existed are covered
    too, with no migration.
    """
    if not path:
        return path

    segments = [s for s in path.replace("\\", "/").split("/") if s not in ("", ".")]
    if not segments:
        return None

    # Scan from the right: the checkout may itself sit under a directory
    # called "projects", and it is the innermost one that begins the
    # repo-relative portion. A trailing "projects" is the directory itself,
    # not a project inside it, so it does not count as a boundary.
    for i in range(len(segments) - 2, -1, -1):
        if segments[i] == _REPO_PROJECT_ROOT:
            return "/".join(segments[i:])

    # No recognisable boundary (a relocated output_dir, a test fixture): fall
    # back to the leaf, which is the project name and never a host detail.
    return segments[-1]


# An absolute filesystem path: two or more segments from a root. The lookbehind
# keeps URLs intact -- in `http://host:11434/api/generate` the `/api` follows a
# word character and the `//` follows a colon, so neither can start a match.
_ABSOLUTE_PATH = re.compile(r"(?<![\w:/])(?:[A-Za-z]:)?(?:[/\\][\w.@+-]+){2,}")


def redact_paths(message: Optional[str]) -> Optional[str]:
    """Strip absolute filesystem paths out of free text bound for a response.

    Exception messages are the back door that ``public_project_path`` does not
    cover. Every filesystem and subprocess failure inside project generation
    stringifies with the full path attached --
    ``[Errno 2] No such file or directory:
    '/home/<account>/agentic-orchestrator/projects/<name>/src/backend/main.py'``
    -- and ``ProjectGenerationResult.error`` is stored on the job and served by
    ``GET /jobs/{id}``, which is public and unauthenticated. So a failed
    generation published exactly what the redaction of ``directory_path``
    removed.

    Each path is reduced the same way a project path is, so the two agree:
    ``projects/<name>/...`` when the path is inside the generated tree, and an
    elided ``.../<leaf>`` otherwise -- enough to tell *which* file failed
    without saying where the checkout lives.

    Deliberately over-eager: a bare route-like fragment (``/plans/pending``)
    is elided too. Redacting a little more than necessary is the safe error
    here; the messages this guards are diagnostic, not parsed.
    """
    if not message:
        return message

    def _replace(match: "re.Match[str]") -> str:
        reduced = public_project_path(match.group(0))
        if not reduced:
            return "..."
        # A bare leaf means no `projects/` boundary was found; mark the
        # elision so the message does not read as a real relative path.
        return reduced if "/" in reduced else f".../{reduced}"

    return _ABSOLUTE_PATH.sub(_replace, message)
