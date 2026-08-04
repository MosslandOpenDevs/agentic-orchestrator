"""
Project generation package for Agentic Orchestrator.

Generates project scaffolds from approved Plans using LLM-based code generation.
"""

from .generator import ProjectCodeGenerator
from .parser import APIEndpoint, ParsedPlan, PlanParser, ProjectTask, TechStack
from .scaffold import ProjectScaffold
from .templates import SUPPORTED_STACKS, TemplateManager

__all__ = [
    "PlanParser",
    "ParsedPlan",
    "TechStack",
    "APIEndpoint",
    "ProjectTask",
    "TemplateManager",
    "SUPPORTED_STACKS",
    "ProjectCodeGenerator",
    "ProjectScaffold",
]
