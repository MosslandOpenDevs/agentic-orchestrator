"""
Planning stage handlers.

Handles PLANNING_DRAFT and PLANNING_REVIEW stages.
"""

import json
import re
from pathlib import Path
from typing import Any

from ..providers.base import QuotaExhaustedError
from ..providers.claude import create_claude_provider
from ..providers.gemini import create_gemini_provider
from ..providers.openai import create_openai_provider
from ..state import Stage, State
from ..utils.files import create_alert_file
from ..utils.logging import get_logger
from .base import BaseStage, StageRegistry, StageResult

logger = get_logger(__name__)


class PlanningDraftStage(BaseStage):
    """
    Planning Draft stage: Create detailed project documents.

    This stage creates:
    - PRD (Product Requirements Document)
    - Architecture document
    - Task breakdown
    - Acceptance criteria
    """

    stage_name = "planning"
    stage_type = Stage.PLANNING_DRAFT

    def __init__(
        self,
        state: State,
        base_path: Path | None = None,
        dry_run: bool = False,
    ):
        super().__init__(state, base_path, dry_run)
        self._claude = None

    @property
    def claude(self):
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    def execute(self) -> StageResult:
        """Execute planning draft stage."""
        logger.info(f"Starting planning draft (iteration {self.state.iteration.planning + 1})")

        # Increment planning iteration
        self.state.increment_planning()

        try:
            # Load selected idea
            selected_idea = self.read_artifact("IDEATION", "selected_idea.md")
            if not selected_idea:
                return StageResult(
                    success=False,
                    error="No selected idea found",
                    message="Cannot proceed without selected idea from ideation stage",
                )

            # Generate planning documents
            artifacts = []

            # 1. PRD
            prd_content = self._generate_prd(selected_idea)
            prd_file = self.save_artifact(
                "PRD.md", prd_content, title="Product Requirements Document"
            )
            artifacts.append(str(prd_file))
            logger.info("Generated PRD")

            # 2. Architecture
            arch_content = self._generate_architecture(selected_idea, prd_content)
            arch_file = self.save_artifact(
                "ARCHITECTURE.md", arch_content, title="Architecture Document"
            )
            artifacts.append(str(arch_file))
            logger.info("Generated Architecture document")

            # 3. Tasks
            tasks_content = self._generate_tasks(prd_content, arch_content)
            tasks_file = self.save_artifact("TASKS.md", tasks_content, title="Task Breakdown")
            artifacts.append(str(tasks_file))
            logger.info("Generated Tasks breakdown")

            # 4. Acceptance Criteria
            acceptance_content = self._generate_acceptance_criteria(prd_content)
            acceptance_file = self.save_artifact(
                "ACCEPTANCE_CRITERIA.md", acceptance_content, title="Acceptance Criteria"
            )
            artifacts.append(str(acceptance_file))
            logger.info("Generated Acceptance Criteria")

            # Commit
            self.commit_changes(
                f"Draft planning documents (iteration {self.state.iteration.planning})",
                "Created PRD, Architecture, Tasks, and Acceptance Criteria",
            )

            return StageResult(
                success=True,
                next_stage=Stage.PLANNING_REVIEW,
                message=f"Created {len(artifacts)} planning documents",
                artifacts=artifacts,
            )

        except Exception as e:
            logger.error(f"Planning draft failed: {e}")
            self.state.set_error(str(e))
            return StageResult(
                success=False,
                error=str(e),
                message=f"Planning draft failed: {e}",
            )

    def _generate_prd(self, selected_idea: str) -> str:
        """Generate Product Requirements Document."""
        prompt = f"""Based on the following selected project idea, create a detailed Product Requirements Document (PRD).

SELECTED IDEA:
{selected_idea}

Create a comprehensive PRD with these sections:

# Product Requirements Document

## 1. Executive Summary
Brief overview of the product

## 2. Problem Statement
Detailed problem description

## 3. Goals and Objectives
- Primary goals
- Secondary goals
- Success metrics

## 4. Target Users
- User personas
- User needs
- User journey

## 5. Functional Requirements
### 5.1 Core Features
- Feature descriptions
- User stories (As a... I want... So that...)

### 5.2 Feature Priority (MoSCoW)
- Must Have
- Should Have
- Could Have
- Won't Have (this version)

## 6. Non-Functional Requirements
- Performance
- Security
- Scalability
- Reliability

## 7. Constraints and Assumptions
- Technical constraints
- Business constraints
- Assumptions

## 8. Dependencies
- External services
- Mossland ecosystem integrations

## 9. Timeline (Phases)
- Phase 1: MVP
- Phase 2: Enhancement
- Phase 3: Scale

## 10. Risks
- Risk identification
- Mitigation strategies

Be specific and practical. Focus on a minimal viable scope."""

        return self.claude.chat(prompt, system_message="You are an expert product manager.")

    def _generate_architecture(self, selected_idea: str, prd: str) -> str:
        """Generate Architecture Document."""
        prompt = f"""Based on the following PRD, create a technical architecture document.

PRD:
{prd}

Create an Architecture Document with these sections:

# Architecture Document

## 1. System Overview
High-level system description and diagram (in text/ASCII)

## 2. Architecture Principles
- Design principles followed
- Key decisions and rationale

## 3. Component Architecture
### 3.1 Frontend
- Technology choices
- Component structure

### 3.2 Backend
- Technology choices
- Service structure

### 3.3 Smart Contracts (if applicable)
- Contract architecture
- Key functions

### 3.4 Database
- Data model
- Storage decisions

## 4. Integration Architecture
- External APIs
- Mossland ecosystem integration
- Third-party services

## 5. Security Architecture
- Authentication/Authorization
- Data protection
- Smart contract security

## 6. Deployment Architecture
- Infrastructure
- CI/CD approach
- Environment strategy

## 7. Technology Stack
| Layer | Technology | Justification |
|-------|------------|---------------|
| ... | ... | ... |

## 8. API Design
Key endpoints and contracts

## 9. Data Flow
How data moves through the system

## 10. Scalability Considerations
How the system can scale

Be practical and implementation-focused. Keep the scope minimal for an MVP."""

        return self.claude.chat(prompt, system_message="You are an expert software architect.")

    def _generate_tasks(self, prd: str, architecture: str) -> str:
        """Generate Task Breakdown."""
        prompt = f"""Based on the following PRD and Architecture, create a detailed task breakdown.

PRD:
{prd}

ARCHITECTURE:
{architecture}

Create a Task Breakdown with:

# Task Breakdown

## Overview
Summary of the work to be done

## Task List

### Phase 1: Setup
- [ ] Task 1.1: Description (Effort: S/M/L)
  - Subtask details
  - Acceptance criteria
- [ ] Task 1.2: ...

### Phase 2: Core Development
- [ ] Task 2.1: ...

### Phase 3: Integration
- [ ] Task 3.1: ...

### Phase 4: Testing
- [ ] Task 4.1: ...

### Phase 5: Deployment
- [ ] Task 5.1: ...

## Dependencies Graph
Which tasks depend on which

## Critical Path
The sequence of tasks that determines minimum project duration

## Risk Tasks
Tasks with higher uncertainty

Format each task as:
- [ ] **Task ID**: Task Name (Effort: S/M/L)
  - Description
  - Inputs required
  - Outputs/deliverables
  - Definition of done

Focus on MVP scope. Keep tasks small and actionable."""

        return self.claude.chat(prompt, system_message="You are an expert project planner.")

    def _generate_acceptance_criteria(self, prd: str) -> str:
        """Generate Acceptance Criteria."""
        prompt = f"""Based on the following PRD, create detailed acceptance criteria.

PRD:
{prd}

Create Acceptance Criteria document:

# Acceptance Criteria

## Feature Acceptance Criteria

For each major feature, provide:

### Feature: [Feature Name]

**User Story**: As a [user], I want [action] so that [benefit]

**Acceptance Criteria** (Gherkin format):
```gherkin
Given [context]
When [action]
Then [expected outcome]
```

**Test Scenarios**:
1. Happy path scenario
2. Edge case scenario
3. Error scenario

---

## Quality Acceptance Criteria

### Functional Requirements
- [ ] Criterion 1
- [ ] Criterion 2

### Performance Requirements
- [ ] Response time < X seconds
- [ ] Can handle Y concurrent users

### Security Requirements
- [ ] Authentication works correctly
- [ ] Authorization enforced

### Usability Requirements
- [ ] Accessible UI
- [ ] Clear error messages

## Definition of Done

A feature is considered DONE when:
- [ ] Code is written and reviewed
- [ ] Unit tests pass (coverage > X%)
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Security review passed
- [ ] Performance acceptable

Be specific and measurable. Focus on testable criteria."""

        return self.claude.chat(prompt, system_message="You are an expert QA engineer.")


class PlanningReviewStage(BaseStage):
    """
    Planning Review stage: External review of planning documents.

    Uses OpenAI/Gemini for independent review to catch issues
    before development begins. May iterate back to PLANNING_DRAFT.
    """

    stage_name = "review"
    stage_type = Stage.PLANNING_REVIEW

    def __init__(
        self,
        state: State,
        base_path: Path | None = None,
        dry_run: bool = False,
    ):
        super().__init__(state, base_path, dry_run)
        self._openai = None
        self._gemini = None

    @property
    def openai(self):
        if self._openai is None:
            self._openai = create_openai_provider(dry_run=self.dry_run)
        return self._openai

    @property
    def gemini(self):
        if self._gemini is None:
            self._gemini = create_gemini_provider(dry_run=self.dry_run)
        return self._gemini

    def execute(self) -> StageResult:
        """Execute planning review stage."""
        logger.info("Starting planning review")

        try:
            # Load planning documents
            prd = self.read_artifact("PLANNING_DRAFT", "PRD.md")
            architecture = self.read_artifact("PLANNING_DRAFT", "ARCHITECTURE.md")
            tasks = self.read_artifact("PLANNING_DRAFT", "TASKS.md")
            acceptance = self.read_artifact("PLANNING_DRAFT", "ACCEPTANCE_CRITERIA.md")

            if not all([prd, architecture, tasks, acceptance]):
                return StageResult(
                    success=False,
                    error="Missing planning documents",
                    message="Cannot review without complete planning documents",
                )

            planning_docs = f"""
# PRD
{prd}

# ARCHITECTURE
{architecture}

# TASKS
{tasks}

# ACCEPTANCE CRITERIA
{acceptance}
"""

            artifacts = []
            reviews = []

            # Try OpenAI review
            try:
                if self.openai.is_available():
                    logger.info("Getting OpenAI review...")
                    openai_review = self._get_review(self.openai, planning_docs, "OpenAI GPT")
                    review_file = self.save_artifact(
                        f"review_openai_{self.state.iteration.planning}.md",
                        openai_review,
                        title="Planning Review - OpenAI",
                        metadata={"reviewer": "openai"},
                    )
                    artifacts.append(str(review_file))
                    reviews.append(("openai", openai_review))
                    logger.info("OpenAI review complete")
            except QuotaExhaustedError as e:
                self._handle_quota_error("openai", e)

            # Try Gemini review
            try:
                if self.gemini.is_available():
                    logger.info("Getting Gemini review...")
                    gemini_review = self._get_review(self.gemini, planning_docs, "Google Gemini")
                    review_file = self.save_artifact(
                        f"review_gemini_{self.state.iteration.planning}.md",
                        gemini_review,
                        title="Planning Review - Gemini",
                        metadata={"reviewer": "gemini"},
                    )
                    artifacts.append(str(review_file))
                    reviews.append(("gemini", gemini_review))
                    logger.info("Gemini review complete")
            except QuotaExhaustedError as e:
                self._handle_quota_error("gemini", e)

            # If no reviews possible, proceed anyway
            if not reviews:
                logger.warning("No external reviews available, proceeding to development")
                self.state.quality.review_score = 7.0  # Default passing score
                return StageResult(
                    success=True,
                    next_stage=Stage.DEV,
                    message="No external reviews available, proceeding with default approval",
                )

            # Parse reviews and calculate score
            review_analysis = self._analyze_reviews(reviews)

            # Save analysis
            analysis_file = self.save_artifact(
                f"review_analysis_{self.state.iteration.planning}.md",
                review_analysis["content"],
                title="Review Analysis",
                metadata={
                    "score": review_analysis["score"],
                    "passed": review_analysis["passed"],
                },
            )
            artifacts.append(str(analysis_file))

            # Update state
            self.state.quality.review_score = review_analysis["score"]
            self.state.quality.review_approvals = sum(
                1 for r in reviews if self._extract_score(r[1]) >= 7.0
            )

            # Commit
            self.commit_changes(
                f"Planning review (iteration {self.state.iteration.planning})",
                f"Score: {review_analysis['score']}/10, Passed: {review_analysis['passed']}",
            )

            # Determine next step
            if review_analysis["passed"]:
                return StageResult(
                    success=True,
                    next_stage=Stage.DEV,
                    message=f"Planning approved with score {review_analysis['score']}/10",
                    artifacts=artifacts,
                )
            else:
                # Check iteration limit
                if self.state.iteration.planning >= self.state.limits.planning_max:
                    logger.warning("Max planning iterations reached, proceeding anyway")
                    return StageResult(
                        success=True,
                        next_stage=Stage.DEV,
                        message=f"Max iterations reached, proceeding with score {review_analysis['score']}/10",
                        artifacts=artifacts,
                    )
                else:
                    return StageResult(
                        success=True,
                        next_stage=Stage.PLANNING_DRAFT,
                        message=f"Review score {review_analysis['score']}/10, requires revision",
                        artifacts=artifacts,
                        should_iterate=True,
                    )

        except QuotaExhaustedError as e:
            # All reviewers have quota issues
            self.state.pause_for_quota(f"Review quota exhausted: {e}")
            return StageResult(
                success=False,
                error=str(e),
                message="Cannot continue: API quota exhausted",
            )
        except Exception as e:
            logger.error(f"Planning review failed: {e}")
            self.state.set_error(str(e))
            return StageResult(
                success=False,
                error=str(e),
                message=f"Planning review failed: {e}",
            )

    def _get_review(self, provider, planning_docs: str, reviewer_name: str) -> str:
        """Get a review from a provider."""
        prompt = f"""Review the following planning documents for a Mossland Web3 micro-service project.

{planning_docs}

Provide a structured review with:

# Planning Review by {reviewer_name}

## Overall Assessment
Brief summary of the planning quality

## Score
Provide a score from 1-10 based on:
- Completeness (is everything needed there?)
- Clarity (is it understandable?)
- Feasibility (is it achievable?)
- Technical soundness (is the architecture solid?)

**OVERALL SCORE: X/10**

## Critical Issues (Must Fix)
Issues that must be addressed before development:
1. Issue and recommendation
2. ...

## Recommendations (Should Fix)
Improvements that would help:
1. Recommendation
2. ...

## Risks Identified
1. Risk and mitigation suggestion
2. ...

## Test Scenarios to Consider
1. Scenario
2. ...

## Verdict
APPROVED / NEEDS_REVISION

## Summary JSON
```json
{{
  "score": X,
  "verdict": "APPROVED/NEEDS_REVISION",
  "critical_issues_count": N,
  "recommendations_count": N
}}
```

Be thorough but practical. Focus on catching real issues that could cause problems in development."""

        return provider.chat(
            prompt,
            system_message="You are an expert technical reviewer. Be thorough and objective.",
        )

    def _extract_score(self, review: str) -> float:
        """Extract score from review text."""
        # Try to find JSON summary
        json_match = re.search(r"```json\s*({.*?})\s*```", review, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return float(data.get("score", 0))
            except (json.JSONDecodeError, ValueError):
                pass

        # Try to find "OVERALL SCORE: X/10" pattern
        score_match = re.search(r"OVERALL SCORE:\s*(\d+(?:\.\d+)?)\s*/\s*10", review, re.IGNORECASE)
        if score_match:
            return float(score_match.group(1))

        # Try to find just "X/10" pattern
        score_match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", review)
        if score_match:
            return float(score_match.group(1))

        return 5.0  # Default middle score if not found

    def _analyze_reviews(self, reviews: list) -> dict[str, Any]:
        """Analyze all reviews and determine overall result."""
        scores = []
        verdicts = []

        for _provider, review in reviews:
            score = self._extract_score(review)
            scores.append(score)

            verdict = "NEEDS_REVISION"
            if "APPROVED" in review.upper() and "NEEDS_REVISION" not in review.upper():
                verdict = "APPROVED"
            elif score >= 7.0:
                verdict = "APPROVED"
            verdicts.append(verdict)

        avg_score = sum(scores) / len(scores) if scores else 0
        passed = avg_score >= self.state.quality.required_score

        content = """# Review Analysis

## Summary

| Reviewer | Score | Verdict |
|----------|-------|---------|
"""
        for i, (provider, _) in enumerate(reviews):
            content += f"| {provider} | {scores[i]}/10 | {verdicts[i]} |\n"

        content += f"""
**Average Score**: {avg_score:.1f}/10
**Required Score**: {self.state.quality.required_score}/10
**Result**: {"PASSED" if passed else "NEEDS REVISION"}

## Consolidated Feedback

Review the individual review documents for detailed feedback.

## Next Steps

{"Proceed to development phase." if passed else "Address critical issues and revise planning documents."}
"""

        return {
            "score": round(avg_score, 1),
            "passed": passed,
            "content": content,
        }

    def _handle_quota_error(self, provider: str, error: QuotaExhaustedError):
        """Handle quota exhaustion for a provider."""
        logger.warning(f"{provider} quota exhausted: {error}")
        create_alert_file(
            alert_type="quota",
            provider=provider,
            model=error.model,
            stage=self.stage_type.value,
            error=str(error),
            resolution=f"""To resolve this issue:
1. Check your {provider.upper()} API key is valid
2. Verify your billing/quota status at the {provider} console
3. Wait for quota reset or upgrade your plan
4. Update API key if needed in .env file
5. Restart with: ao step""",
            base_path=self.base_path,
            project_id=self.project_id,
        )


# Register handlers
StageRegistry.register(Stage.PLANNING_DRAFT, PlanningDraftStage)
StageRegistry.register(Stage.PLANNING_REVIEW, PlanningReviewStage)
