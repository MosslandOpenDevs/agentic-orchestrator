"""
Quality Assurance stage handler.

Runs tests, performs code review, and validates the implementation.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..providers.base import QuotaExhaustedError
from ..providers.gemini import create_gemini_provider
from ..providers.openai import create_openai_provider
from ..state import Stage, State
from ..utils.files import create_alert_file
from ..utils.logging import get_logger
from .base import BaseStage, StageRegistry, StageResult

logger = get_logger(__name__)


class QualityStage(BaseStage):
    """
    Quality Assurance stage: Validate the implementation.

    This stage:
    1. Runs automated tests (if available)
    2. Performs code review with external models
    3. Checks for security issues
    4. Creates QA report
    5. Determines if ready for DONE or needs more development
    """

    stage_name = "qa"
    stage_type = Stage.QA

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
        """Execute QA stage."""
        logger.info("Starting QA stage")

        try:
            artifacts = []
            qa_results = {}

            # 1. Run automated tests
            test_results = self._run_tests()
            qa_results["tests"] = test_results

            test_report = self.save_artifact(
                "test_results.md",
                test_results["report"],
                title="Test Results",
                metadata={"passed": test_results["passed"]},
            )
            artifacts.append(str(test_report))

            # 2. Code review
            code_review = self._perform_code_review()
            qa_results["review"] = code_review

            review_report = self.save_artifact(
                "code_review.md",
                code_review["report"],
                title="Code Review",
                metadata={
                    "score": code_review["score"],
                    "issues_count": code_review["issues_count"],
                },
            )
            artifacts.append(str(review_report))

            # 3. Security check
            security_results = self._security_check()
            qa_results["security"] = security_results

            security_report = self.save_artifact(
                "security_check.md",
                security_results["report"],
                title="Security Check",
                metadata={"issues_count": security_results["issues_count"]},
            )
            artifacts.append(str(security_report))

            # 4. Create overall QA report
            overall = self._create_overall_report(qa_results)

            qa_report = self.save_artifact(
                "qa_report.md",
                overall["report"],
                title="QA Report",
                metadata={
                    "passed": overall["passed"],
                    "score": overall["score"],
                },
            )
            artifacts.append(str(qa_report))

            # Update state
            self.state.quality.tests_passed = test_results["passed"]
            self.state.quality.review_score = code_review["score"]

            # Commit
            self.commit_changes(
                f"QA complete - {'PASSED' if overall['passed'] else 'NEEDS WORK'}",
                f"Score: {overall['score']}/10, Tests: {'PASS' if test_results['passed'] else 'FAIL'}",
            )

            # Determine next step
            if overall["passed"]:
                return StageResult(
                    success=True,
                    next_stage=Stage.DONE,
                    message=f"QA passed with score {overall['score']}/10",
                    artifacts=artifacts,
                )
            else:
                # Check if we should iterate
                if self.state.iteration.dev < self.state.limits.dev_max:
                    return StageResult(
                        success=True,
                        next_stage=Stage.DEV,
                        message=f"QA score {overall['score']}/10 below threshold, needs revision",
                        artifacts=artifacts,
                        should_iterate=True,
                    )
                else:
                    # Max iterations, complete anyway
                    logger.warning("Max iterations reached, marking as done despite QA issues")
                    return StageResult(
                        success=True,
                        next_stage=Stage.DONE,
                        message=f"Max iterations reached, completing with score {overall['score']}/10",
                        artifacts=artifacts,
                    )

        except QuotaExhaustedError as e:
            self.state.pause_for_quota(f"QA quota exhausted: {e}")
            return StageResult(
                success=False,
                error=str(e),
                message="QA paused due to API quota exhaustion",
            )
        except Exception as e:
            logger.error(f"QA failed: {e}")
            self.state.set_error(str(e))
            return StageResult(
                success=False,
                error=str(e),
                message=f"QA failed: {e}",
            )

    def _run_tests(self) -> dict[str, Any]:
        """Run automated tests."""
        logger.info("Running automated tests...")

        # Look for test files in implementation directory
        impl_dir = self.base_path / "projects" / self.project_id / "03_implementation"

        if not impl_dir.exists():
            return {
                "passed": True,  # No tests = pass by default
                "report": "# Test Results\n\nNo implementation directory found. Skipping tests.\n",
                "details": "No tests to run",
            }

        # Check for Python tests
        test_files = list(impl_dir.rglob("test_*.py")) + list(impl_dir.rglob("*_test.py"))

        if not test_files:
            return {
                "passed": True,
                "report": "# Test Results\n\nNo test files found. Consider adding tests.\n",
                "details": "No test files detected",
            }

        # Try to run pytest
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(impl_dir), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.base_path,
            )

            passed = result.returncode == 0
            output = result.stdout + result.stderr

            report = f"""# Test Results

## Summary
- **Status**: {"PASSED" if passed else "FAILED"}
- **Exit Code**: {result.returncode}

## Test Output
```
{output[:5000]}
```

## Test Files Found
"""
            for tf in test_files:
                report += f"- {tf.relative_to(self.base_path)}\n"

            return {
                "passed": passed,
                "report": report,
                "details": output,
            }

        except FileNotFoundError:
            return {
                "passed": True,
                "report": "# Test Results\n\npytest not available. Skipping automated tests.\n",
                "details": "pytest not installed",
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "report": "# Test Results\n\nTests timed out after 5 minutes.\n",
                "details": "timeout",
            }
        except Exception as e:
            return {
                "passed": False,
                "report": f"# Test Results\n\nError running tests: {e}\n",
                "details": str(e),
            }

    def _perform_code_review(self) -> dict[str, Any]:
        """Perform code review using external models."""
        logger.info("Performing code review...")

        # Gather implementation files
        impl_dir = self.base_path / "projects" / self.project_id / "03_implementation"
        code_files = []

        if impl_dir.exists():
            for ext in ["*.py", "*.js", "*.ts", "*.sol", "*.md"]:
                code_files.extend(impl_dir.rglob(ext))

        if not code_files:
            return {
                "score": 7.0,
                "report": "# Code Review\n\nNo code files found to review.\n",
                "issues_count": 0,
            }

        # Build code context
        code_context = "# Code to Review\n\n"
        for cf in code_files[:10]:  # Limit to 10 files
            try:
                content = cf.read_text()[:2000]  # Truncate large files
                code_context += f"## {cf.name}\n```\n{content}\n```\n\n"
            except Exception:
                continue

        # Get review
        reviews = []

        try:
            if self.openai.is_available():
                review = self._get_code_review(self.openai, code_context, "OpenAI")
                reviews.append(("openai", review))
        except QuotaExhaustedError as e:
            self._handle_quota_error("openai", e)

        try:
            if self.gemini.is_available():
                review = self._get_code_review(self.gemini, code_context, "Gemini")
                reviews.append(("gemini", review))
        except QuotaExhaustedError as e:
            self._handle_quota_error("gemini", e)

        if not reviews:
            return {
                "score": 7.0,
                "report": "# Code Review\n\nNo external reviewers available. Passing with default score.\n",
                "issues_count": 0,
            }

        # Combine reviews
        combined = self._combine_reviews(reviews)
        return combined

    def _get_code_review(self, provider, code_context: str, name: str) -> str:
        """Get code review from a provider."""
        prompt = f"""Review the following code for a Mossland Web3 micro-service project.

{code_context}

Provide a structured code review:

# Code Review by {name}

## Overall Quality Score: X/10

## Strengths
- Strength 1
- Strength 2

## Issues Found

### Critical Issues
1. Issue and fix

### Major Issues
1. Issue and fix

### Minor Issues
1. Issue and fix

## Security Concerns
1. Concern and mitigation

## Recommendations
1. Recommendation

## Summary
Brief overall assessment

```json
{{
  "score": X,
  "critical_issues": N,
  "major_issues": N,
  "minor_issues": N
}}
```"""

        return provider.chat(
            prompt,
            system_message="You are an expert code reviewer. Be thorough but fair.",
        )

    def _combine_reviews(self, reviews: list) -> dict[str, Any]:
        """Combine multiple code reviews."""
        scores = []
        total_issues = 0

        report = "# Code Review Summary\n\n"

        for provider, review in reviews:
            # Extract score
            score_match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", review)
            score = float(score_match.group(1)) if score_match else 5.0
            scores.append(score)

            # Count issues
            issues = len(re.findall(r"^\d+\.", review, re.MULTILINE))
            total_issues += issues

            report += f"## Review by {provider}\n\n"
            report += review + "\n\n---\n\n"

        avg_score = sum(scores) / len(scores) if scores else 5.0

        report = (
            f"""# Combined Code Review

**Average Score**: {avg_score:.1f}/10
**Total Issues Found**: {total_issues}

---

"""
            + report
        )

        return {
            "score": round(avg_score, 1),
            "report": report,
            "issues_count": total_issues,
        }

    def _security_check(self) -> dict[str, Any]:
        """Perform basic security checks."""
        logger.info("Performing security check...")

        impl_dir = self.base_path / "projects" / self.project_id / "03_implementation"
        issues = []

        if not impl_dir.exists():
            return {
                "report": "# Security Check\n\nNo implementation to check.\n",
                "issues_count": 0,
            }

        # Check for common security issues
        for code_file in impl_dir.rglob("*"):
            if code_file.is_file() and code_file.suffix in [".py", ".js", ".ts", ".sol"]:
                try:
                    content = code_file.read_text()

                    # Check for hardcoded secrets
                    secret_patterns = [
                        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Possible hardcoded API key"),
                        (r'password\s*=\s*["\'][^"\']+["\']', "Possible hardcoded password"),
                        (r'secret\s*=\s*["\'][^"\']+["\']', "Possible hardcoded secret"),
                        (
                            r'private[_-]?key\s*=\s*["\'][^"\']+["\']',
                            "Possible hardcoded private key",
                        ),
                    ]

                    for pattern, message in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(
                                {
                                    "file": str(code_file.relative_to(self.base_path)),
                                    "type": "hardcoded_secret",
                                    "message": message,
                                    "severity": "HIGH",
                                }
                            )

                    # Check for SQL injection (basic)
                    if re.search(r"execute\s*\([^)]*%s", content) or re.search(
                        r'f["\'].*{.*}.*SELECT', content, re.IGNORECASE
                    ):
                        issues.append(
                            {
                                "file": str(code_file.relative_to(self.base_path)),
                                "type": "sql_injection",
                                "message": "Possible SQL injection vulnerability",
                                "severity": "HIGH",
                            }
                        )

                    # Check for eval usage
                    if re.search(r"\beval\s*\(", content):
                        issues.append(
                            {
                                "file": str(code_file.relative_to(self.base_path)),
                                "type": "dangerous_eval",
                                "message": "Use of eval() is dangerous",
                                "severity": "MEDIUM",
                            }
                        )

                except Exception:
                    continue

        # Generate report
        report = "# Security Check\n\n"

        if issues:
            report += f"**Issues Found**: {len(issues)}\n\n"
            report += "| File | Type | Severity | Message |\n"
            report += "|------|------|----------|--------|\n"

            for issue in issues:
                report += f"| {issue['file']} | {issue['type']} | {issue['severity']} | {issue['message']} |\n"

            report += "\n## Details\n\n"
            for i, issue in enumerate(issues, 1):
                report += f"### Issue {i}: {issue['type']}\n"
                report += f"- **File**: {issue['file']}\n"
                report += f"- **Severity**: {issue['severity']}\n"
                report += f"- **Message**: {issue['message']}\n\n"
        else:
            report += "No security issues detected.\n"

        return {
            "report": report,
            "issues_count": len(issues),
            "issues": issues,
        }

    def _create_overall_report(self, qa_results: dict[str, Any]) -> dict[str, Any]:
        """Create overall QA report."""
        tests_passed = qa_results["tests"]["passed"]
        review_score = qa_results["review"]["score"]
        security_issues = qa_results["security"]["issues_count"]

        # Calculate overall score
        score = review_score
        if not tests_passed:
            score = max(1, score - 2)
        if security_issues > 0:
            score = max(1, score - (security_issues * 0.5))

        passed = (
            tests_passed and score >= self.state.quality.required_score and security_issues == 0
        )

        report = f"""# Overall QA Report

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Tests | {"PASS" if tests_passed else "FAIL"} | {qa_results["tests"].get("details", "N/A")[:50]} |
| Code Review | {review_score}/10 | {qa_results["review"]["issues_count"]} issues |
| Security | {"PASS" if security_issues == 0 else "FAIL"} | {security_issues} issues |

## Overall Score: {score:.1f}/10

## Verdict: {"APPROVED" if passed else "NEEDS REVISION"}

## Next Steps

"""
        if passed:
            report += "- All checks passed. Ready for release.\n"
        else:
            if not tests_passed:
                report += "- Fix failing tests\n"
            if review_score < self.state.quality.required_score:
                report += "- Address code review issues\n"
            if security_issues > 0:
                report += "- Fix security vulnerabilities\n"

        report += f"""
---

*Report generated at {datetime.now().isoformat()}*
*Required score: {self.state.quality.required_score}/10*
"""

        return {
            "passed": passed,
            "score": round(score, 1),
            "report": report,
        }

    def _handle_quota_error(self, provider: str, error: QuotaExhaustedError):
        """Handle quota exhaustion."""
        logger.warning(f"{provider} quota exhausted during QA: {error}")
        create_alert_file(
            alert_type="quota",
            provider=provider,
            model=error.model,
            stage=self.stage_type.value,
            error=str(error),
            resolution=f"""QA was interrupted due to {provider} quota exhaustion.

To resolve:
1. Check your {provider.upper()} billing/quota
2. Wait for quota reset or upgrade plan
3. Restart QA with: ao step""",
            base_path=self.base_path,
            project_id=self.project_id,
        )


# Register handler
StageRegistry.register(Stage.QA, QualityStage)


class DoneStage(BaseStage):
    """
    Done stage: Finalize the project.

    This stage creates final documentation and marks the project complete.
    """

    stage_name = "done"
    stage_type = Stage.DONE

    def execute(self) -> StageResult:
        """Execute done stage."""
        logger.info("Project complete, creating final documentation")

        try:
            # Create completion report
            report = self._create_completion_report()

            report_file = self.save_artifact(
                "COMPLETION_REPORT.md",
                report,
                title="Project Completion Report",
            )

            self.commit_changes(
                f"Project {self.project_id} completed",
                "Final documentation and completion report",
            )

            return StageResult(
                success=True,
                next_stage=None,  # No next stage
                message=f"Project {self.project_id} successfully completed",
                artifacts=[str(report_file)],
            )

        except Exception as e:
            logger.error(f"Completion stage failed: {e}")
            return StageResult(
                success=False,
                error=str(e),
                message=f"Completion failed: {e}",
            )

    def _create_completion_report(self) -> str:
        """Create final project completion report."""
        # Gather all artifacts
        project_dir = self.base_path / "projects" / self.project_id

        report = f"""# Project Completion Report

## Project: {self.project_id}

## Completion Date
{datetime.now().isoformat()}

## Summary

This project has successfully completed all stages of the Agentic Orchestrator pipeline.

## Stages Completed

| Stage | Status | Artifacts |
|-------|--------|-----------|
"""
        stages = ["01_ideation", "02_planning", "03_implementation", "04_quality"]

        for stage in stages:
            stage_dir = project_dir / stage
            if stage_dir.exists():
                artifacts = list(stage_dir.glob("*.md"))
                report += f"| {stage} | Complete | {len(artifacts)} documents |\n"
            else:
                report += f"| {stage} | N/A | - |\n"

        report += f"""
## Quality Metrics

- **Review Score**: {self.state.quality.review_score or 'N/A'}/10
- **Tests Passed**: {self.state.quality.tests_passed or 'N/A'}
- **Iterations**: Planning={self.state.iteration.planning}, Dev={self.state.iteration.dev}

## Project Artifacts

"""
        for stage in stages:
            stage_dir = project_dir / stage
            if stage_dir.exists():
                report += f"### {stage}\n"
                for f in stage_dir.glob("*.md"):
                    report += f"- {f.name}\n"
                report += "\n"

        report += """
## Next Steps

1. Review all generated documentation
2. Deploy the implementation
3. Monitor and gather feedback
4. Start next project cycle with `ao init`

---

*Generated by Mossland Agentic Orchestrator*
"""
        return report


# Register handler
StageRegistry.register(Stage.DONE, DoneStage)
