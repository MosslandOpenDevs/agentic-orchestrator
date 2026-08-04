"""
Database module for Agentic Orchestrator.

Provides SQLAlchemy models, connection management, and repositories
for long-term data persistence.
"""

from .connection import Database, db, get_db, init_database

# Aliases for backward compatibility
get_database = get_db
from .models import (
    AgentState,
    APIUsage,
    Base,
    DebateMessage,
    DebateSession,
    Idea,
    Plan,
    Project,
    Signal,
    SystemLog,
    Trend,
)
from .repositories import (
    APIUsageRepository,
    DebateRepository,
    IdeaRepository,
    PlanRepository,
    ProjectRepository,
    SignalRepository,
    SystemLogRepository,
    TrendRepository,
)

__all__ = [
    # Connection
    "Database",
    "db",
    "init_database",
    "get_db",
    "get_database",
    # Models
    "Base",
    "Signal",
    "Trend",
    "Idea",
    "DebateSession",
    "DebateMessage",
    "Plan",
    "Project",
    "APIUsage",
    "SystemLog",
    "AgentState",
    # Repositories
    "SignalRepository",
    "TrendRepository",
    "IdeaRepository",
    "DebateRepository",
    "PlanRepository",
    "ProjectRepository",
    "APIUsageRepository",
    "SystemLogRepository",
]
