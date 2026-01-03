"""
Main Orchestrator class.

Coordinates the execution of stages and manages the overall pipeline.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .state import State, Stage
from .stages.base import StageRegistry, StageResult
from .stages import (  # noqa: F401 - Import to register handlers
    IdeationStage,
    PlanningDraftStage,
    PlanningReviewStage,
    DevelopmentStage,
    QualityStage,
)
from .utils.config import load_config, Config
from .utils.logging import setup_logging, get_logger
from .utils.git import GitHelper
from .utils.files import generate_project_id

logger = get_logger(__name__)


class Orchestrator:
    """
    Main orchestrator that coordinates the autonomous development pipeline.

    The orchestrator:
    1. Manages state persistence
    2. Executes stage handlers in sequence
    3. Handles transitions and iterations
    4. Provides loop mode with guardrails
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        config: Optional[Config] = None,
        dry_run: bool = False,
    ):
        """
        Initialize the orchestrator.

        Args:
            base_path: Base path for all operations.
            config: Configuration instance.
            dry_run: If True, don't make actual changes.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.config = config or load_config(self.base_path / "config.yaml")
        self.dry_run = dry_run or self.config.dry_run
        self._state: Optional[State] = None
        self._git: Optional[GitHelper] = None

        # Setup logging
        setup_logging(
            log_file=self.base_path / "logs" / "orchestrator.log"
        )

    @property
    def state(self) -> State:
        """Get or load the current state."""
        if self._state is None:
            self._state = State.load(self.base_path)
        return self._state

    @property
    def git(self) -> GitHelper:
        """Get Git helper."""
        if self._git is None:
            self._git = GitHelper(self.base_path)
        return self._git

    def save_state(self) -> None:
        """Save the current state."""
        self.state.save(self.base_path)

    def init_project(self, project_id: Optional[str] = None) -> str:
        """
        Initialize a new project.

        Args:
            project_id: Optional custom project ID.

        Returns:
            The project ID.
        """
        if project_id is None:
            project_id = generate_project_id()

        self.state.reset_for_new_project(project_id)
        self.save_state()

        logger.info(f"Initialized new project: {project_id}")
        return project_id

    def step(self) -> StageResult:
        """
        Execute a single step (one stage of the pipeline).

        Returns:
            Result of the stage execution.
        """
        if self.state.is_paused():
            logger.warning(f"Orchestrator is paused: {self.state.errors.paused_reason}")
            return StageResult(
                success=False,
                error=f"Paused: {self.state.errors.paused_reason}",
                message="Orchestrator is paused. Resolve the issue and restart.",
            )

        if self.state.is_complete():
            logger.info("Project is complete")
            return StageResult(
                success=True,
                message="Project is already complete. Run 'ao init' for a new project.",
            )

        current_stage = self.state.stage
        logger.info(f"Executing stage: {current_stage.value}")

        try:
            # Get handler for current stage
            handler = StageRegistry.get_handler(
                current_stage,
                self.state,
                self.base_path,
                self.dry_run,
            )

            # Execute stage
            result = handler.execute()

            # Handle result
            if result.success:
                if result.next_stage:
                    self.state.transition_to(result.next_stage)
                    logger.info(f"Transitioned to: {result.next_stage.value}")
            else:
                if result.error:
                    self.state.set_error(result.error)

            # Save state
            self.save_state()

            return result

        except Exception as e:
            logger.error(f"Stage execution failed: {e}")
            self.state.set_error(str(e))
            self.save_state()

            return StageResult(
                success=False,
                error=str(e),
                message=f"Stage {current_stage.value} failed: {e}",
            )

    def loop(
        self,
        max_steps: Optional[int] = None,
        delay_seconds: Optional[int] = None,
    ) -> list[StageResult]:
        """
        Run in loop mode until completion or limit.

        Args:
            max_steps: Maximum steps to execute.
            delay_seconds: Delay between steps.

        Returns:
            List of all stage results.
        """
        max_steps = max_steps or self.config.loop_max_steps
        delay_seconds = delay_seconds or self.config.loop_delay

        results = []
        step_count = 0

        logger.info(f"Starting loop mode (max_steps={max_steps}, delay={delay_seconds}s)")

        while step_count < max_steps:
            step_count += 1
            logger.info(f"Loop step {step_count}/{max_steps}")

            result = self.step()
            results.append(result)

            # Check if we should stop
            if self.state.is_complete():
                logger.info("Project complete, stopping loop")
                break

            if self.state.is_paused():
                logger.warning("Orchestrator paused, stopping loop")
                break

            if not result.success and not result.should_iterate:
                logger.warning(f"Step failed without iteration flag: {result.error}")
                break

            # Delay before next step
            if step_count < max_steps and delay_seconds > 0:
                logger.debug(f"Waiting {delay_seconds}s before next step")
                time.sleep(delay_seconds)

        logger.info(f"Loop complete after {step_count} steps")
        return results

    def status(self) -> dict:
        """
        Get current orchestrator status.

        Returns:
            Status dictionary.
        """
        return {
            "project_id": self.state.project_id,
            "stage": self.state.stage.value,
            "iteration": {
                "planning": self.state.iteration.planning,
                "dev": self.state.iteration.dev,
            },
            "limits": {
                "planning_max": self.state.limits.planning_max,
                "dev_max": self.state.limits.dev_max,
            },
            "quality": {
                "review_score": self.state.quality.review_score,
                "tests_passed": self.state.quality.tests_passed,
                "required_score": self.state.quality.required_score,
            },
            "timestamps": {
                "created": str(self.state.timestamps.created) if self.state.timestamps.created else None,
                "last_updated": str(self.state.timestamps.last_updated) if self.state.timestamps.last_updated else None,
            },
            "errors": {
                "last_error": self.state.errors.last_error,
                "error_count": self.state.errors.error_count,
                "paused_reason": self.state.errors.paused_reason,
            },
            "flags": {
                "is_paused": self.state.is_paused(),
                "is_complete": self.state.is_complete(),
                "can_continue": self.state.can_continue(),
            },
            "dry_run": self.dry_run,
        }

    def resume(self) -> StageResult:
        """
        Resume from a paused state.

        Clears the pause reason and attempts to continue.

        Returns:
            Result of the resumed step.
        """
        if not self.state.is_paused():
            logger.info("Orchestrator is not paused")
            return self.step()

        logger.info(f"Resuming from paused state: {self.state.errors.paused_reason}")

        # Clear pause reason
        self.state.errors.paused_reason = None

        # If paused for quota, try to recover
        if self.state.stage == Stage.PAUSED_QUOTA:
            # Determine what stage we were in based on artifacts
            # Default to trying planning review again
            self.state.stage = Stage.PLANNING_REVIEW

        self.save_state()
        return self.step()

    def reset(self, keep_project: bool = True) -> None:
        """
        Reset the orchestrator state.

        Args:
            keep_project: If True, keep the current project ID.
        """
        project_id = self.state.project_id if keep_project else None

        if project_id:
            self.state.reset_for_new_project(project_id)
        else:
            self._state = State()
            self.state.timestamps.created = datetime.now()

        self.save_state()
        logger.info(f"Reset orchestrator state (project_id={project_id})")

    def push_changes(self) -> bool:
        """
        Push all committed changes to remote.

        Returns:
            True if push succeeded.
        """
        if self.dry_run:
            logger.info("[DRY RUN] Would push changes")
            return True

        return self.git.push()
