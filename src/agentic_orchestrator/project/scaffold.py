"""
Project scaffold orchestrator.

Orchestrates the complete project generation pipeline:
1. Load Plan from database
2. Parse Plan content
3. Detect tech stack
4. Generate template files
5. Generate LLM-enhanced code
6. Create project directory structure
7. Update project status in database
8. Auto-commit and push to GitHub
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..timeutil import utcnow
from .generator import GeneratedFile, ProjectCodeGenerator
from .parser import ParsedPlan, PlanParser
from .repair import CodeRepairer, ensure_contract_dependencies
from .templates import TemplateFile, TemplateManager, slugify_project_name
from .verifier import UNKNOWN, CodeVerifier, VerificationStatus, detect_language

logger = logging.getLogger(__name__)


@dataclass
class ProjectGenerationResult:
    """Result of project generation."""

    success: bool
    project_id: Optional[str] = None
    project_path: Optional[str] = None
    plan_id: str = ""
    tech_stack: Dict[str, Any] = field(default_factory=dict)
    files_generated: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "plan_id": self.plan_id,
            "tech_stack": self.tech_stack,
            "files_generated": self.files_generated,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


class ProjectScaffold:
    """
    Orchestrates project generation from Plans.

    Usage:
        scaffold = ProjectScaffold(router=llm_router)
        result = await scaffold.generate_project(plan_id="abc123")

        if result.success:
            print(f"Project created at: {result.project_path}")
    """

    def __init__(
        self,
        router=None,
        projects_dir: str = "projects",
        db_session=None,
    ):
        """
        Initialize the scaffold.

        Args:
            router: HybridLLMRouter for LLM-based generation
            projects_dir: Base directory for generated projects
            db_session: SQLAlchemy session (optional)
        """
        self.router = router
        self.projects_dir = Path(projects_dir)
        self.db_session = db_session

        self.parser = PlanParser(router=router)
        self.templates = TemplateManager(projects_dir=projects_dir)
        self.generator = ProjectCodeGenerator(router=router)

        # Ensure projects directory exists
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    async def generate_project(
        self,
        plan_id: str,
        force_regenerate: bool = False,
    ) -> ProjectGenerationResult:
        """
        Generate a project from a Plan.

        Args:
            plan_id: ID of the Plan to generate from
            force_regenerate: If True, regenerate even if project exists

        Returns:
            ProjectGenerationResult with status and details
        """
        start_time = utcnow()

        try:
            # Load plan from database
            plan = await self._load_plan(plan_id)
            if not plan:
                return ProjectGenerationResult(
                    success=False,
                    plan_id=plan_id,
                    error=f"Plan not found: {plan_id}",
                )

            # Check if project already exists
            existing_project = await self._get_existing_project(plan_id)
            if existing_project and not force_regenerate:
                return ProjectGenerationResult(
                    success=True,
                    project_id=existing_project.get("id"),
                    project_path=existing_project.get("directory_path"),
                    plan_id=plan_id,
                    tech_stack=existing_project.get("tech_stack", {}),
                    error="Project already exists. Use force_regenerate=True to regenerate.",
                )

            # Parse plan content with deep extraction
            logger.info(f"Parsing plan: {plan_id}")
            plan_content = plan.get("final_plan") or plan.get("prd_content") or ""
            plan_title = plan.get("title") or "Untitled Project"

            if self.router:
                # Use deep parsing for comprehensive extraction
                logger.info("Using deep LLM parsing for high-quality code generation")
                parsed_plan = await self.parser.parse_deep_with_llm(plan_content, plan_title)
            else:
                parsed_plan = self.parser.parse(plan_content, plan_title)

            logger.info(
                f"Parsed: {len(parsed_plan.entities)} entities, "
                f"{len(parsed_plan.api_endpoints)} endpoints, "
                f"{len(parsed_plan.ui_components)} UI components"
            )

            # Generate project name
            project_name = self._generate_project_name(parsed_plan.title)
            logger.info(f"Generating project: {project_name}")

            # Create project in database (status: generating)
            project_id = await self._create_project_record(
                plan_id=plan_id,
                name=project_name,
                tech_stack=parsed_plan.tech_stack.to_dict(),
                status="generating",
            )

            # Generate full production-quality project code
            logger.info("Generating production-quality project code...")
            logger.info(f"Tech stack: {parsed_plan.tech_stack.to_dict()}")

            if self.router:
                # Use full project generation for high-quality code
                generated_files = await self.generator.generate_full_project(
                    parsed_plan, project_name
                )
                all_files = [TemplateFile(path=f.path, content=f.content) for f in generated_files]
                logger.info(f"Generated {len(all_files)} production-quality files")
            else:
                # Fallback: Use template files + basic LLM generation
                template_files = self.templates.get_template_files(
                    frontend=parsed_plan.tech_stack.frontend,
                    backend=parsed_plan.tech_stack.backend,
                    database=parsed_plan.tech_stack.database,
                    blockchain=parsed_plan.tech_stack.blockchain,
                )
                llm_files = await self._generate_llm_files(parsed_plan, project_name)
                all_files = template_files + [
                    TemplateFile(path=f.path, content=f.content) for f in llm_files
                ]
                logger.info(f"Generated {len(all_files)} files (fallback mode)")

            # Verify and repair generated source before writing to disk. Never
            # blocks: failures are repaired where possible and recorded.
            verification = await self._verify_and_repair(all_files)

            # Add PLAN.md (copy of original plan)
            all_files.append(
                TemplateFile(
                    path="PLAN.md",
                    content=plan_content or "# Plan\n\nOriginal plan content not available.",
                )
            )

            # Add .moss-project.json with metadata
            all_files.append(
                TemplateFile(
                    path=".moss-project.json",
                    content=json.dumps(
                        {
                            "version": "1.0.0",
                            "generator": "moss-ao",
                            "createdAt": utcnow().isoformat(),
                            "planId": plan_id,
                            "projectId": project_id,
                            "techStack": parsed_plan.tech_stack.to_dict(),
                            "features": parsed_plan.features[:10],
                            "verification": verification,
                        },
                        indent=2,
                    ),
                )
            )

            # Create project directory and files
            project_path = self.templates.create_project_structure(
                project_name=project_name,
                files=all_files,
            )

            logger.info(f"Project created at: {project_path}")

            # Update project status in database. Unresolved verification
            # failures surface as `ready_with_warnings` rather than blocking.
            final_status = "ready_with_warnings" if verification.get("unresolved") else "ready"
            await self._update_project_status(
                project_id=project_id,
                status=final_status,
                directory_path=str(project_path),
                files_generated=len(all_files),
                verification=verification,
            )

            # Auto-commit and push to GitHub
            git_success = await self._git_commit_and_push(str(project_path), project_name)
            if git_success:
                logger.info(f"Project auto-pushed to GitHub: {project_name}")
            else:
                logger.warning(
                    f"Git push failed for project: {project_name} (project still created locally)"
                )

            duration = (utcnow() - start_time).total_seconds()

            return ProjectGenerationResult(
                success=True,
                project_id=project_id,
                project_path=str(project_path),
                plan_id=plan_id,
                tech_stack=parsed_plan.tech_stack.to_dict(),
                files_generated=len(all_files),
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error(f"Project generation failed: {e}", exc_info=True)
            duration = (utcnow() - start_time).total_seconds()

            # Update project status to error if we created a record
            if "project_id" in locals():
                await self._update_project_status(
                    project_id=project_id,
                    status="error",
                )

            return ProjectGenerationResult(
                success=False,
                plan_id=plan_id,
                error=str(e),
                duration_seconds=duration,
            )

    async def _load_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Load plan from database."""
        if not self.db_session:
            logger.warning("No database session, cannot load plan")
            return None

        try:
            from ..db.models import Plan

            plan = self.db_session.query(Plan).filter(Plan.id == plan_id).first()
            if plan:
                return {
                    "id": plan.id,
                    "title": plan.title,
                    "final_plan": plan.final_plan,
                    "prd_content": plan.prd_content,
                    "architecture_content": plan.architecture_content,
                    "status": plan.status,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to load plan: {e}")
            return None

    async def _get_existing_project(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Check if a project already exists for this plan."""
        if not self.db_session:
            return None

        try:
            from ..db.models import Project

            project = self.db_session.query(Project).filter(Project.plan_id == plan_id).first()
            if project:
                return {
                    "id": project.id,
                    "directory_path": project.directory_path,
                    "tech_stack": project.tech_stack,
                    "status": project.status,
                }
            return None
        except Exception as e:
            logger.debug(f"No existing project found: {e}")
            return None

    async def _create_project_record(
        self,
        plan_id: str,
        name: str,
        tech_stack: Dict[str, Any],
        status: str = "generating",
    ) -> str:
        """Create project record in database.

        Checks for existing projects with same plan_id to prevent duplicates.
        """
        import uuid

        project_id = str(uuid.uuid4())[:8]

        if not self.db_session:
            return project_id

        try:
            from ..db.models import COMPLETED_PROJECT_STATUSES, Project

            # Check for existing project with same plan_id (prevent duplicates).
            # Includes ready_with_warnings so a warned project is not duplicated.
            existing = (
                self.db_session.query(Project)
                .filter(
                    Project.plan_id == plan_id,
                    Project.status.in_(["generating", *COMPLETED_PROJECT_STATUSES]),
                )
                .first()
            )
            if existing:
                logger.warning(
                    f"Project already exists for plan {plan_id}: {existing.id} (status: {existing.status})"
                )
                return existing.id

            project = Project(
                id=project_id,
                plan_id=plan_id,
                name=name,
                tech_stack=tech_stack,
                status=status,
            )
            self.db_session.add(project)
            self.db_session.flush()
            return project_id
        except Exception as e:
            logger.error(f"Failed to create project record: {e}")
            return project_id

    async def _update_project_status(
        self,
        project_id: str,
        status: str,
        directory_path: Optional[str] = None,
        files_generated: Optional[int] = None,
        verification: Optional[Dict[str, Any]] = None,
    ):
        """Update project status in database."""
        if not self.db_session:
            return

        try:
            from ..db.models import Project

            project = self.db_session.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = status
                if directory_path:
                    project.directory_path = directory_path
                if files_generated is not None:
                    project.files_generated = files_generated
                if verification is not None:
                    project.extra_metadata = {
                        **(project.extra_metadata or {}),
                        "verification": verification,
                    }
                    project.generation_log = _summarize_verification(verification)
                if status in ("ready", "ready_with_warnings"):
                    project.completed_at = utcnow()
                self.db_session.flush()
        except Exception as e:
            logger.error(f"Failed to update project status: {e}")

    async def _verify_and_repair(self, files: List[TemplateFile]) -> Dict[str, Any]:
        """Verify every generated source file and repair failures in place.

        Pipeline per code file:
          1. deterministic repair (cheap, always safe)
          2. verify
          3. on failure (and if a router is available) one LLM repair attempt,
             re-run deterministic repair on the model's output, then re-verify;
             the LLM version is only accepted if it resolves the failure.

        This never raises and never blocks generation — it mutates ``files`` and
        returns a JSON-serializable summary for persistence.
        """
        verifier = CodeVerifier()
        repairer = CodeRepairer()

        # Cross-file pass first: make sure contracts/package.json declares OZ.
        dependency_fixes = ensure_contract_dependencies(files)

        results = []
        deterministic_repairs = 0
        llm_repairs = 0

        for f in files:
            language = detect_language(f.path)
            if language == UNKNOWN:
                continue

            try:
                det = repairer.repair_file(f.path, f.content)
                content = det.content
                if det.changed:
                    deterministic_repairs += 1

                result = verifier.verify(f.path, content)
                llm_applied = False

                if result.status == VerificationStatus.FAILED and self.router:
                    llm_out = await self.generator.repair_code(content, language, result.errors)
                    if llm_out:
                        candidate = repairer.repair_file(f.path, llm_out).content
                        recheck = verifier.verify(f.path, candidate)
                        if recheck.ok:  # only accept a fix that actually helps
                            content = candidate
                            result = recheck
                            llm_applied = True
                            llm_repairs += 1

                f.content = content
                result.repaired = det.changed or llm_applied
                results.append(result)
            except Exception as e:  # defensive: verification must never block
                logger.error(f"Verification/repair errored for {f.path}: {e}")

        summary = _build_verification_summary(
            results, deterministic_repairs, llm_repairs, dependency_fixes
        )
        logger.info(
            "Verification: %s passed, %s failed, %s skipped "
            "(deterministic repairs: %s, LLM repairs: %s)",
            summary["passed"],
            summary["failed"],
            summary["skipped"],
            summary["deterministic_repairs"],
            summary["llm_repairs"],
        )
        return summary

    async def _generate_llm_files(
        self,
        parsed_plan: ParsedPlan,
        project_name: str,
    ) -> List[GeneratedFile]:
        """Generate LLM-enhanced files."""
        files = []

        # Generate README.md
        logger.info("Generating README.md...")
        readme = await self.generator.generate_readme(parsed_plan, project_name)
        files.append(
            GeneratedFile(
                path="README.md",
                content=readme,
                description="Project README",
            )
        )

        # Generate architecture documentation
        logger.info("Generating architecture documentation...")
        architecture = await self.generator.generate_architecture_doc(parsed_plan, project_name)
        files.append(
            GeneratedFile(
                path="docs/ARCHITECTURE.md",
                content=architecture,
                description="Architecture documentation",
            )
        )

        # Generate API routes if endpoints are defined
        if parsed_plan.api_endpoints:
            logger.info("Generating API routes...")
            route_files = await self.generator.generate_api_routes(parsed_plan)
            files.extend(route_files)

        # Generate data models if backend is defined
        if parsed_plan.tech_stack.backend:
            logger.info("Generating data models...")
            model_files = await self.generator.generate_data_models(parsed_plan)
            files.extend(model_files)

        return files

    def _generate_project_name(self, title: str) -> str:
        """Generate a safe project directory name from title."""
        normalized = "-".join((title or "").split())
        return slugify_project_name(normalized)

    async def _git_commit_and_push(self, project_path: str, project_name: str) -> bool:
        """
        Commit and push the generated project to GitHub.

        Args:
            project_path: Full path to the project directory
            project_name: Name of the project

        Returns:
            True if successful, False otherwise
        """
        try:
            # Defense-in-depth: project_name is already slugified, but verify
            # before passing it into a subprocess argument.
            if project_name != slugify_project_name(project_name):
                logger.error("Refusing git operations: unsafe project name %r", project_name)
                return False

            # Get the repository root (parent of projects/ directory)
            repo_root = Path(project_path).parent.parent

            # Stage the project directory
            add_result = subprocess.run(
                ["git", "add", f"projects/{project_name}/"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if add_result.returncode != 0:
                logger.error(f"Git add failed: {add_result.stderr}")
                return False

            # Create commit message
            commit_message = f"feat: generate production-quality code for {project_name}"

            # Commit the changes
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if commit_result.returncode != 0:
                # Check if there's nothing to commit
                if "nothing to commit" in commit_result.stdout.lower():
                    logger.info("No changes to commit (project already committed)")
                    return True
                logger.error(f"Git commit failed: {commit_result.stderr}")
                return False

            logger.info(f"Committed project: {project_name}")

            # Push to remote
            push_result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if push_result.returncode != 0:
                logger.error(f"Git push failed: {push_result.stderr}")
                return False

            logger.info(f"Pushed project to GitHub: {project_name}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Git operation timed out")
            return False
        except Exception as e:
            logger.error(f"Git commit/push failed: {e}")
            return False


def _build_verification_summary(
    results: List[Any],
    deterministic_repairs: int,
    llm_repairs: int,
    dependency_fixes: List[str],
) -> Dict[str, Any]:
    """Aggregate per-file verification results into a serializable summary."""
    passed = sum(1 for r in results if r.status == VerificationStatus.PASSED)
    failed = sum(1 for r in results if r.status == VerificationStatus.FAILED)
    skipped = sum(1 for r in results if r.status == VerificationStatus.SKIPPED)
    unresolved = [r.path for r in results if r.status == VerificationStatus.FAILED]

    # Keep the per-file detail compact: only record files that are not a clean
    # first-pass PASS (i.e. failures, repairs, or skipped-without-compiler).
    files = [r.to_dict() for r in results if r.status != VerificationStatus.PASSED or r.repaired]

    return {
        "checked": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "deterministic_repairs": deterministic_repairs,
        "llm_repairs": llm_repairs,
        "dependency_fixes": dependency_fixes,
        "unresolved": unresolved,
        "files": files,
    }


def _summarize_verification(verification: Dict[str, Any]) -> str:
    """Render a one-line human-readable summary for the project generation log."""
    parts = [
        f"{verification.get('passed', 0)} passed",
        f"{verification.get('failed', 0)} failed",
        f"{verification.get('skipped', 0)} skipped",
        f"{verification.get('deterministic_repairs', 0)} auto-repaired",
        f"{verification.get('llm_repairs', 0)} LLM-repaired",
    ]
    line = "Verification: " + ", ".join(parts)
    unresolved = verification.get("unresolved") or []
    if unresolved:
        line += f". Unresolved: {', '.join(unresolved[:10])}"
        if len(unresolved) > 10:
            line += f" (+{len(unresolved) - 10} more)"
    return line


async def generate_project_from_plan(
    plan_id: str,
    router=None,
    db_session=None,
    force_regenerate: bool = False,
) -> ProjectGenerationResult:
    """
    Convenience function to generate a project from a plan.

    Args:
        plan_id: ID of the Plan
        router: HybridLLMRouter (optional)
        db_session: SQLAlchemy session (optional)
        force_regenerate: Force regeneration if project exists

    Returns:
        ProjectGenerationResult
    """
    scaffold = ProjectScaffold(
        router=router,
        db_session=db_session,
    )
    return await scaffold.generate_project(
        plan_id=plan_id,
        force_regenerate=force_regenerate,
    )
