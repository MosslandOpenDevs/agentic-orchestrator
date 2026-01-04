"""
Development stage handler.

Implements the planned features using Claude Code.
"""

import re
from datetime import datetime
from pathlib import Path

from ..providers.claude import ClaudeProvider, create_claude_provider
from ..state import Stage, State
from ..utils.files import ensure_dir
from ..utils.logging import get_logger
from .base import BaseStage, StageRegistry, StageResult

logger = get_logger(__name__)


class DevelopmentStage(BaseStage):
    """
    Development stage: Implement planned features.

    This stage:
    1. Reads planning documents
    2. Uses Claude Code to implement features task by task
    3. Commits changes incrementally
    4. Tracks progress in development log
    """

    stage_name = "dev"
    stage_type = Stage.DEV

    def __init__(
        self,
        state: State,
        base_path: Path | None = None,
        dry_run: bool = False,
    ):
        super().__init__(state, base_path, dry_run)
        self._claude: ClaudeProvider | None = None

    @property
    def claude(self) -> ClaudeProvider:
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    @property
    def implementation_dir(self) -> Path:
        """Get the implementation directory."""
        impl_dir = self.stage_dir
        ensure_dir(impl_dir)
        return impl_dir

    def execute(self) -> StageResult:
        """Execute development stage."""
        logger.info(f"Starting development (iteration {self.state.iteration.dev + 1})")

        # Increment dev iteration
        self.state.increment_dev()

        try:
            # Load planning documents
            tasks = self.read_artifact("PLANNING_DRAFT", "TASKS.md")
            architecture = self.read_artifact("PLANNING_DRAFT", "ARCHITECTURE.md")
            prd = self.read_artifact("PLANNING_DRAFT", "PRD.md")

            if not all([tasks, architecture]):
                return StageResult(
                    success=False,
                    error="Missing planning documents",
                    message="Cannot proceed without Tasks and Architecture documents",
                )

            # Parse tasks
            task_list = self._parse_tasks(tasks)
            logger.info(f"Found {len(task_list)} tasks to implement")

            # Check for existing progress
            progress = self._load_progress()
            completed_tasks = progress.get("completed", [])

            artifacts = []
            implemented = []

            for i, task in enumerate(task_list):
                task_id = task.get("id", f"task_{i+1}")

                if task_id in completed_tasks:
                    logger.info(f"Skipping completed task: {task_id}")
                    continue

                logger.info(f"Implementing task {i+1}/{len(task_list)}: {task_id}")

                try:
                    # Implement task
                    result = self._implement_task(task, architecture, prd)

                    # Save implementation log
                    log_file = self.save_artifact(
                        f"impl_{task_id}.md",
                        result["log"],
                        title=f"Implementation: {task.get('name', task_id)}",
                        metadata={
                            "task_id": task_id,
                            "status": "completed",
                        },
                    )
                    artifacts.append(str(log_file))
                    implemented.append(task_id)

                    # Update progress
                    completed_tasks.append(task_id)
                    self._save_progress({"completed": completed_tasks})

                    # Commit this task
                    self.commit_changes(
                        f"Implement {task.get('name', task_id)}",
                        result.get("summary", ""),
                    )

                except Exception as e:
                    logger.error(f"Failed to implement {task_id}: {e}")
                    # Log the failure but continue with other tasks
                    error_file = self.save_artifact(
                        f"error_{task_id}.md",
                        f"# Implementation Error\n\n**Task**: {task_id}\n\n**Error**:\n```\n{e}\n```",
                        title=f"Error: {task_id}",
                        metadata={"task_id": task_id, "status": "error"},
                    )
                    artifacts.append(str(error_file))

            # Create implementation summary
            summary = self._create_summary(task_list, implemented, completed_tasks)
            summary_file = self.save_artifact(
                f"summary_iteration_{self.state.iteration.dev}.md",
                summary,
                title="Development Summary",
            )
            artifacts.append(str(summary_file))

            # Commit summary
            self.commit_changes(
                f"Development iteration {self.state.iteration.dev} complete",
                f"Implemented {len(implemented)} tasks",
            )

            # Check if all tasks are done
            all_done = len(completed_tasks) >= len(task_list)

            if all_done:
                return StageResult(
                    success=True,
                    next_stage=Stage.QA,
                    message=f"All {len(task_list)} tasks implemented",
                    artifacts=artifacts,
                )
            else:
                # Check iteration limit
                if self.state.iteration.dev >= self.state.limits.dev_max:
                    logger.warning("Max dev iterations reached, proceeding to QA")
                    return StageResult(
                        success=True,
                        next_stage=Stage.QA,
                        message=f"Max iterations reached, {len(completed_tasks)}/{len(task_list)} tasks done",
                        artifacts=artifacts,
                    )
                else:
                    return StageResult(
                        success=True,
                        next_stage=Stage.DEV,  # Continue development
                        message=f"Progress: {len(completed_tasks)}/{len(task_list)} tasks",
                        artifacts=artifacts,
                        should_iterate=True,
                    )

        except Exception as e:
            logger.error(f"Development failed: {e}")
            self.state.set_error(str(e))
            return StageResult(
                success=False,
                error=str(e),
                message=f"Development failed: {e}",
            )

    def _parse_tasks(self, tasks_md: str) -> list[dict]:
        """Parse tasks from markdown."""
        task_list = []

        # Pattern to match task items
        # - [ ] **Task 1.1**: Description (Effort: S/M/L)
        pattern = r"-\s*\[[ x]\]\s*\*?\*?([^:*]+)\*?\*?:\s*(.+?)(?:\(Effort:\s*([SML])\))?$"

        for match in re.finditer(pattern, tasks_md, re.MULTILINE):
            task_id = match.group(1).strip()
            description = match.group(2).strip()
            effort = match.group(3) or "M"

            task_list.append(
                {
                    "id": task_id.replace(" ", "_").lower(),
                    "name": task_id,
                    "description": description,
                    "effort": effort,
                }
            )

        # If no tasks found with pattern, try simpler extraction
        if not task_list:
            # Look for any checkbox items
            simple_pattern = r"-\s*\[[ x]\]\s*(.+)$"
            for i, match in enumerate(re.finditer(simple_pattern, tasks_md, re.MULTILINE)):
                task_text = match.group(1).strip()
                task_list.append(
                    {
                        "id": f"task_{i+1}",
                        "name": f"Task {i+1}",
                        "description": task_text,
                        "effort": "M",
                    }
                )

        return task_list

    def _implement_task(self, task: dict, architecture: str, prd: str) -> dict:
        """Implement a single task using Claude."""
        prompt = f"""Implement the following task for a Mossland Web3 micro-service project.

## Task
**ID**: {task['id']}
**Name**: {task['name']}
**Description**: {task['description']}
**Effort**: {task['effort']}

## Architecture Context
{architecture[:2000]}  # Truncate for context limit

## Requirements Context
{prd[:1000]}  # Truncate for context limit

## Instructions

1. Create the necessary files and code for this task
2. Follow the architecture and requirements
3. Write clean, well-documented code
4. Include basic error handling
5. Add comments explaining key logic

If this is a setup task, create the necessary project structure.
If this is a feature task, implement the feature.
If this is a testing task, create test files.

Provide your implementation and a summary of what was created."""

        if self.dry_run:
            response = f"[DRY RUN] Would implement: {task['name']}"
        else:
            # Use Claude's chat method for generation
            response = self.claude.chat(
                user_message=prompt,
                system_message="""You are an expert software developer implementing a Web3 micro-service.
Write production-quality code following best practices.
Be concise but complete. Focus on working code.""",
            )

        # Parse response for summary
        summary_match = re.search(
            r"(?:Summary|What was created):?\s*(.+?)(?:\n\n|$)", response, re.IGNORECASE | re.DOTALL
        )
        summary = summary_match.group(1).strip() if summary_match else f"Implemented {task['name']}"

        return {
            "log": f"# Implementation: {task['name']}\n\n{response}",
            "summary": summary[:200],
        }

    def _load_progress(self) -> dict:
        """Load development progress."""
        progress_file = self.implementation_dir / "progress.json"
        if progress_file.exists():
            import json

            with open(progress_file) as f:
                return json.load(f)
        return {"completed": []}

    def _save_progress(self, progress: dict):
        """Save development progress."""
        import json

        progress_file = self.implementation_dir / "progress.json"
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=2)

    def _create_summary(self, all_tasks: list, implemented: list, completed: list) -> str:
        """Create implementation summary."""
        total = len(all_tasks)
        done = len(completed)

        content = f"""# Development Summary

## Progress

- **Total Tasks**: {total}
- **Completed**: {done}
- **Remaining**: {total - done}
- **This Iteration**: {len(implemented)}

## Task Status

| Task | Status |
|------|--------|
"""
        for task in all_tasks:
            status = "Completed" if task["id"] in completed else "Pending"
            if task["id"] in implemented:
                status = "Completed (this iteration)"
            content += f"| {task['name']} | {status} |\n"

        content += """
## Implemented This Iteration

"""
        for task_id in implemented:
            content += f"- {task_id}\n"

        content += f"""
## Next Steps

{"All tasks complete. Proceed to QA." if done >= total else f"Continue implementation. {total - done} tasks remaining."}

---

*Generated at {datetime.now().isoformat()}*
"""
        return content


# Register handler
StageRegistry.register(Stage.DEV, DevelopmentStage)
