"""
FastAPI backend for Mossland Agentic Orchestrator.

Provides REST API endpoints for:
- System health and status
- Signal data access
- Debate results
- Agent information
"""

from .main import app

__all__ = ["app"]
