"""The scheduler no longer mirrors ideas and plans into GitHub issues.

Two source invariants over ``scheduler/*.py``: nothing uses the GitHub issue
client (``github_client`` / ``GitHubClient``), and nothing creates an issue.
The signals job still reaches GitHub through its events adapter; that is a
signal source, not the issue mirror, and it does not use this client.
"""

from pathlib import Path

from agentic_orchestrator.scheduler import tasks as tasks_mod

# The imported package, not a path relative to this file: the scan must read
# the code the other tests run.
SCHEDULER_DIR = Path(tasks_mod.__file__).resolve().parent


def scheduler_sources() -> dict:
    sources = {path.name: path.read_text(encoding="utf-8") for path in SCHEDULER_DIR.glob("*.py")}
    # An empty or misdirected scan passes every "appears nowhere" assertion.
    assert len(sources) >= 5, f"scanned only {sorted(sources)} under {SCHEDULER_DIR}"
    return sources


def uses_issue_client(text: str) -> bool:
    return "github_client" in text or "GitHubClient" in text


class TestTheSchedulerDoesNotMirror:
    def test_nothing_in_the_scheduler_uses_the_issue_client(self):
        # A matcher that matched nothing would pass the emptiness check below.
        assert uses_issue_client("from ..github_client import GitHubClient")

        users = {name for name, text in scheduler_sources().items() if uses_issue_client(text)}

        assert users == set()

    def test_nothing_in_the_scheduler_creates_an_issue(self):
        creators = [name for name, text in scheduler_sources().items() if "create_issue" in text]

        assert creators == []
