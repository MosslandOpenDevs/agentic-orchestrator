"""Tests for the backlog workflow module."""
import json
import os
import tempfile
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from agentic_orchestrator.github_client import GitHubClient, GitHubIssue, Labels, GitHubAPIError


class TestLabels:
    """Test Labels constants."""

    def test_type_labels(self):
        """Test type label constants."""
        assert Labels.TYPE_IDEA == "type:idea"
        assert Labels.TYPE_PLAN == "type:plan"

    def test_status_labels(self):
        """Test status label constants."""
        assert Labels.STATUS_BACKLOG == "status:backlog"
        assert Labels.STATUS_PLANNED == "status:planned"
        assert Labels.STATUS_IN_DEV == "status:in-dev"
        assert Labels.STATUS_DONE == "status:done"

    def test_promotion_labels(self):
        """Test promotion label constants."""
        assert Labels.PROMOTE_TO_PLAN == "promote:to-plan"
        assert Labels.PROMOTE_TO_DEV == "promote:to-dev"

    def test_processed_labels(self):
        """Test processed label constants."""
        assert Labels.PROCESSED_TO_PLAN == "processed:to-plan"
        assert Labels.PROCESSED_TO_DEV == "processed:to-dev"

    def test_all_labels_dict(self):
        """Test all labels dictionary."""
        all_labels = Labels.ALL_LABELS
        assert Labels.TYPE_IDEA in all_labels
        assert Labels.PROMOTE_TO_PLAN in all_labels
        assert Labels.GENERATED_BY_ORCHESTRATOR in all_labels
        # Check structure
        assert "color" in all_labels[Labels.TYPE_IDEA]
        assert "description" in all_labels[Labels.TYPE_IDEA]


class TestGitHubIssue:
    """Test GitHubIssue dataclass."""

    def test_issue_creation(self):
        """Test creating a GitHubIssue."""
        issue = GitHubIssue(
            number=1,
            title="Test Issue",
            body="Test body",
            labels=["type:idea", "status:backlog"],
            state="open",
            html_url="https://github.com/test/repo/issues/1",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert issue.number == 1
        assert issue.title == "Test Issue"
        assert "type:idea" in issue.labels

    def test_has_label(self):
        """Test has_label method."""
        issue = GitHubIssue(
            number=1,
            title="Test",
            body="",
            labels=["type:idea", "status:backlog"],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert issue.has_label("type:idea") is True
        assert issue.has_label("type:plan") is False

    def test_has_any_label(self):
        """Test has_any_label method."""
        issue = GitHubIssue(
            number=1,
            title="Test",
            body="",
            labels=["type:idea", "status:backlog"],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert issue.has_any_label(["type:idea", "type:plan"]) is True
        assert issue.has_any_label(["type:plan", "status:done"]) is False

    def test_from_api_response(self):
        """Test creating issue from API response."""
        api_response = {
            "number": 42,
            "title": "API Issue",
            "body": "Body text",
            "labels": [{"name": "type:idea"}, {"name": "status:backlog"}],
            "state": "open",
            "html_url": "https://github.com/test/repo/issues/42",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "user": {"login": "testuser"},
            "assignees": []
        }
        issue = GitHubIssue.from_api_response(api_response)
        assert issue.number == 42
        assert issue.title == "API Issue"
        assert issue.labels == ["type:idea", "status:backlog"]
        assert issue.user == "testuser"


class TestGitHubClient:
    """Test GitHubClient class."""

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            "GITHUB_TOKEN": "test-token",
            "GITHUB_OWNER": "test-owner",
            "GITHUB_REPO": "test-repo"
        }):
            client = GitHubClient()
            assert client.token == "test-token"
            assert client.owner == "test-owner"
            assert client.repo == "test-repo"
            client.close()

    def test_init_with_params(self):
        """Test initialization with parameters."""
        client = GitHubClient(
            token="param-token",
            owner="param-owner",
            repo="param-repo"
        )
        assert client.token == "param-token"
        assert client.owner == "param-owner"
        assert client.repo == "param-repo"
        client.close()

    def test_init_missing_token(self):
        """Test initialization fails without token."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("GITHUB_OWNER", None)
            os.environ.pop("GITHUB_REPO", None)
            with pytest.raises(GitHubAPIError, match="GITHUB_TOKEN"):
                GitHubClient(owner="test", repo="test")

    def test_repo_path(self):
        """Test repo_path property."""
        client = GitHubClient(
            token="test",
            owner="testowner",
            repo="testrepo"
        )
        assert client.repo_path == "testowner/testrepo"
        client.close()

    def test_context_manager(self):
        """Test context manager support."""
        with GitHubClient(token="test", owner="test", repo="test") as client:
            assert client is not None


class TestBacklogOrchestrator:
    """Test BacklogOrchestrator class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test BacklogOrchestrator initialization."""
        from agentic_orchestrator.backlog import BacklogOrchestrator

        orchestrator = BacklogOrchestrator()
        assert orchestrator.github is not None
        assert orchestrator.dry_run is True

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_get_status(self):
        """Test getting backlog status."""
        from agentic_orchestrator.backlog import BacklogOrchestrator

        orchestrator = BacklogOrchestrator()

        with patch.object(orchestrator.github, "find_backlog_ideas", return_value=[]):
            with patch.object(orchestrator.github, "find_backlog_plans", return_value=[]):
                with patch.object(orchestrator.github, "find_ideas_to_promote", return_value=[]):
                    with patch.object(orchestrator.github, "find_plans_to_promote", return_value=[]):
                        status = orchestrator.get_status()

                        assert "backlog" in status
                        assert "pending_promotion" in status
                        assert "issues" in status
                        assert status["backlog"]["ideas"] == 0
                        assert status["pending_promotion"]["ideas_to_plan"] == 0


class TestIdeaGenerator:
    """Test IdeaGenerator class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test IdeaGenerator initialization."""
        from agentic_orchestrator.backlog import IdeaGenerator

        github = GitHubClient(token="test", owner="test", repo="test")
        generator = IdeaGenerator(github=github, dry_run=True)
        assert generator.github is not None
        assert generator.dry_run is True
        github.close()


class TestPlanGenerator:
    """Test PlanGenerator class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test PlanGenerator initialization."""
        from agentic_orchestrator.backlog import PlanGenerator

        github = GitHubClient(token="test", owner="test", repo="test")
        generator = PlanGenerator(github=github, dry_run=True)
        assert generator.github is not None
        assert generator.dry_run is True
        github.close()


class TestDevScaffolder:
    """Test DevScaffolder class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test DevScaffolder initialization."""
        from agentic_orchestrator.backlog import DevScaffolder

        github = GitHubClient(token="test", owner="test", repo="test")
        scaffolder = DevScaffolder(github=github, dry_run=True)
        assert scaffolder.github is not None
        assert scaffolder.dry_run is True
        github.close()
