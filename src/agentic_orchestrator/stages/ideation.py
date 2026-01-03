"""
Ideation stage handler.

Generates micro Web3 service ideas for the Mossland ecosystem.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import BaseStage, StageResult, StageRegistry
from ..state import State, Stage
from ..providers.claude import create_claude_provider
from ..utils.logging import get_logger
from ..utils.files import generate_project_id

logger = get_logger(__name__)


class IdeationStage(BaseStage):
    """
    Ideation stage: Generate project ideas.

    This stage:
    1. Uses Claude to generate micro Web3 service ideas
    2. Evaluates ideas for feasibility and Mossland ecosystem fit
    3. Selects the best idea and creates initial documentation
    4. Transitions to PLANNING_DRAFT stage
    """

    stage_name = "ideation"
    stage_type = Stage.IDEATION

    def __init__(
        self,
        state: State,
        base_path: Optional[Path] = None,
        dry_run: bool = False,
    ):
        super().__init__(state, base_path, dry_run)
        self._claude = None

    @property
    def claude(self):
        """Get Claude provider."""
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    def execute(self) -> StageResult:
        """Execute ideation stage."""
        logger.info("Starting ideation stage")

        # If no project ID, this is a fresh start
        if not self.state.project_id:
            project_id = generate_project_id()
            self.state.reset_for_new_project(project_id)
            logger.info(f"Created new project: {project_id}")

        try:
            # Load prompt
            try:
                prompt = self.load_prompts("ideation.md")
            except FileNotFoundError:
                prompt = self._get_default_prompt()

            # Generate ideas
            logger.info("Generating project ideas...")
            ideas_content = self.claude.chat(
                user_message=prompt,
                system_message=self._get_system_message(),
            )

            # Save ideas document
            ideas_file = self.save_artifact(
                "ideas.md",
                ideas_content,
                title="Project Ideas",
                metadata={
                    "ideas_count": 3,
                    "focus": "Mossland Web3 micro-services",
                },
            )
            logger.info(f"Saved ideas: {ideas_file}")

            # Select best idea and create summary
            selection_prompt = self._get_selection_prompt(ideas_content)
            selected_idea = self.claude.chat(
                user_message=selection_prompt,
                system_message="You are a project evaluator. Select the best idea and explain why.",
            )

            # Save selected idea
            selected_file = self.save_artifact(
                "selected_idea.md",
                selected_idea,
                title="Selected Project Idea",
                metadata={"status": "selected"},
            )
            logger.info(f"Saved selected idea: {selected_file}")

            # Commit changes
            self.commit_changes(
                f"Generate project ideas for {self.project_id}",
                f"Created {len([ideas_file, selected_file])} ideation documents",
            )

            return StageResult(
                success=True,
                next_stage=Stage.PLANNING_DRAFT,
                message=f"Generated and selected project idea for {self.project_id}",
                artifacts=[str(ideas_file), str(selected_file)],
            )

        except Exception as e:
            logger.error(f"Ideation failed: {e}")
            self.state.set_error(str(e))
            return StageResult(
                success=False,
                error=str(e),
                message=f"Ideation failed: {e}",
            )

    def _get_system_message(self) -> str:
        """Get system message for ideation."""
        return """You are a creative Web3 product strategist for the Mossland ecosystem.

Mossland is a blockchain-based metaverse project that:
- Has its own token (MOC - Mossland Coin)
- Focuses on connecting real-world locations with virtual spaces
- Operates NFT-based digital assets
- Provides AR/VR experiences

Your role is to generate innovative micro-service ideas that:
1. Benefit the Mossland ecosystem
2. Are technically feasible as small, focused projects
3. Can be implemented and tested in a reasonable timeframe
4. Leverage Web3 technologies (blockchain, tokens, NFTs, smart contracts)
5. Have clear value propositions

Be specific and practical in your ideas."""

    def _get_default_prompt(self) -> str:
        """Get default ideation prompt."""
        return """Generate 3 innovative micro Web3 service ideas for the Mossland ecosystem.

For each idea, provide:

## Idea [N]: [Name]

### Overview
Brief description of the service (2-3 sentences)

### Problem Statement
What problem does this solve for Mossland users?

### Proposed Solution
How does this service address the problem?

### Key Features
- Feature 1
- Feature 2
- Feature 3

### Technical Approach
- Technology stack
- Integration points with Mossland
- Smart contract requirements (if any)

### Value Proposition
- For Mossland ecosystem
- For end users
- For MOC token utility

### Feasibility Assessment
- Implementation complexity (Low/Medium/High)
- Time estimate category (1-2 weeks / 2-4 weeks / 1-2 months)
- Key risks or challenges

---

Focus on ideas that are:
- Small enough to implement as a single focused project
- Novel and valuable to the Mossland ecosystem
- Technically sound with Web3 technologies
- Testable with clear success criteria"""

    def _get_selection_prompt(self, ideas_content: str) -> str:
        """Get prompt for selecting the best idea."""
        return f"""Based on these project ideas, select the BEST one to implement:

{ideas_content}

Evaluate each idea on:
1. **Impact**: How much value does it add to Mossland?
2. **Feasibility**: Can it realistically be built?
3. **Innovation**: Is it novel and interesting?
4. **Testability**: Can success be measured?

Provide your selection in this format:

## Selected Idea

**Name**: [The selected idea name]

**Reason for Selection**:
[2-3 paragraphs explaining why this idea is the best choice]

**Key Success Metrics**:
- Metric 1
- Metric 2
- Metric 3

**Initial Scope Recommendation**:
[Suggestions for MVP scope]

**Potential Challenges**:
- Challenge 1 and mitigation
- Challenge 2 and mitigation

## Next Steps

1. [First planning step]
2. [Second planning step]
3. [Third planning step]"""


# Register the handler
StageRegistry.register(Stage.IDEATION, IdeationStage)
