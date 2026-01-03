"""
Base stage handler for the orchestrator pipeline.

Defines the interface that all stage handlers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any

from ..state import State, Stage
from ..providers.base import BaseProvider
from ..utils.logging import get_logger
from ..utils.files import write_markdown, get_stage_dir, ensure_dir
from ..utils.git import GitHelper

logger = get_logger(__name__)


@dataclass
class StageResult:
    """Result of a stage execution."""

    success: bool
    next_stage: Optional[Stage] = None
    message: str = ""
    artifacts: List[str] = None  # List of created file paths
    should_iterate: bool = False
    error: Optional[str] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class BaseStage(ABC):
    """
    Abstract base class for stage handlers.

    Each stage in the pipeline has a corresponding handler that:
    1. Reads the current state
    2. Performs the stage's work
    3. Produces artifacts (markdown files, code, etc.)
    4. Returns the result indicating next steps
    """

    stage_name: str = "base"
    stage_type: Stage = Stage.IDEATION

    def __init__(
        self,
        state: State,
        base_path: Optional[Path] = None,
        dry_run: bool = False,
    ):
        """
        Initialize stage handler.

        Args:
            state: Current orchestrator state.
            base_path: Base path for file operations.
            dry_run: If True, don't make actual changes.
        """
        self.state = state
        self.base_path = base_path or Path.cwd()
        self.dry_run = dry_run
        self._git: Optional[GitHelper] = None

    @property
    def git(self) -> GitHelper:
        """Get Git helper instance."""
        if self._git is None:
            self._git = GitHelper(self.base_path)
        return self._git

    @property
    def project_id(self) -> str:
        """Get current project ID."""
        if not self.state.project_id:
            raise ValueError("No active project")
        return self.state.project_id

    @property
    def stage_dir(self) -> Path:
        """Get the output directory for this stage."""
        return get_stage_dir(
            self.project_id,
            self.stage_type.value,
            self.base_path,
        )

    @abstractmethod
    def execute(self) -> StageResult:
        """
        Execute the stage's main logic.

        Returns:
            StageResult indicating success/failure and next steps.
        """
        pass

    def save_artifact(
        self,
        filename: str,
        content: str,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Path:
        """
        Save a markdown artifact for this stage.

        Args:
            filename: Name of the file (without path).
            content: Markdown content.
            title: Optional document title.
            metadata: Optional YAML frontmatter metadata.

        Returns:
            Path to the saved file.
        """
        # Add standard metadata
        full_metadata = {
            "stage": self.stage_type.value,
            "project_id": self.project_id,
            "generated_at": datetime.now().isoformat(),
            "iteration": {
                "planning": self.state.iteration.planning,
                "dev": self.state.iteration.dev,
            },
        }
        if metadata:
            full_metadata.update(metadata)

        filepath = self.stage_dir / filename
        return write_markdown(filepath, content, title=title, metadata=full_metadata)

    def commit_changes(self, message: str, details: Optional[str] = None) -> bool:
        """
        Commit changes for this stage.

        Args:
            message: Commit message (brief).
            details: Additional details for commit body.

        Returns:
            True if commit was made.
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would commit: {message}")
            return False

        if not self.git.has_changes():
            logger.info("No changes to commit")
            return False

        # Build prefix from stage
        prefix = f"[{self.stage_name}]"

        commit_info = self.git.commit(
            f"{prefix} {message}",
            stage=self.stage_type.value,
            project_id=self.project_id,
            planning_iter=self.state.iteration.planning,
            dev_iter=self.state.iteration.dev,
        )

        if commit_info:
            logger.info(f"Committed: {commit_info.short_hash} - {message}")
            return True

        return False

    def load_prompts(self, prompt_file: str) -> str:
        """
        Load a prompt template.

        Args:
            prompt_file: Prompt filename (relative to prompts/).

        Returns:
            Prompt content.
        """
        prompt_paths = [
            self.base_path / ".agent" / "prompts" / prompt_file,
            self.base_path / "prompts" / prompt_file,
        ]

        for path in prompt_paths:
            if path.exists():
                return path.read_text()

        raise FileNotFoundError(f"Prompt not found: {prompt_file}")

    def get_previous_artifacts(self, stage: str) -> List[Path]:
        """
        Get artifacts from a previous stage.

        Args:
            stage: Stage name to get artifacts from.

        Returns:
            List of artifact file paths.
        """
        stage_dir = get_stage_dir(self.project_id, stage, self.base_path)
        if not stage_dir.exists():
            return []
        return list(stage_dir.glob("*.md"))

    def read_artifact(self, stage: str, filename: str) -> Optional[str]:
        """
        Read an artifact from a stage.

        Args:
            stage: Stage name.
            filename: Artifact filename.

        Returns:
            File content or None if not found.
        """
        stage_dir = get_stage_dir(self.project_id, stage, self.base_path)
        filepath = stage_dir / filename
        if filepath.exists():
            return filepath.read_text()
        return None


class StageRegistry:
    """Registry of stage handlers."""

    _handlers: dict = {}

    @classmethod
    def register(cls, stage: Stage, handler_class: type):
        """Register a handler for a stage."""
        cls._handlers[stage] = handler_class

    @classmethod
    def get_handler(
        cls,
        stage: Stage,
        state: State,
        base_path: Optional[Path] = None,
        dry_run: bool = False,
    ) -> BaseStage:
        """
        Get a handler instance for a stage.

        Args:
            stage: The stage to handle.
            state: Current state.
            base_path: Base path.
            dry_run: Dry run mode.

        Returns:
            Configured stage handler.

        Raises:
            ValueError: If no handler registered for stage.
        """
        if stage not in cls._handlers:
            raise ValueError(f"No handler registered for stage: {stage}")

        handler_class = cls._handlers[stage]
        return handler_class(state=state, base_path=base_path, dry_run=dry_run)

    @classmethod
    def get_all_stages(cls) -> List[Stage]:
        """Get all registered stages in order."""
        stage_order = [
            Stage.IDEATION,
            Stage.PLANNING_DRAFT,
            Stage.PLANNING_REVIEW,
            Stage.DEV,
            Stage.QA,
            Stage.DONE,
        ]
        return [s for s in stage_order if s in cls._handlers]
