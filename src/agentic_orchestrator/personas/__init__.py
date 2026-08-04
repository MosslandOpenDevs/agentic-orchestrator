"""
Personas module for Agentic Orchestrator.

Provides diverse agent personas with different personalities,
roles, and expertise for multi-stage debates.
"""

from .catalog import (
    AgentPersona,
    PersonaCategory,
    get_agent_by_id,
    get_all_agents,
    get_convergence_agents,
    get_divergence_agents,
    get_planning_agents,
)
from .personalities import (
    ActionStyle,
    CommunicationStyle,
    DecisionStyle,
    Personality,
    ThinkingStyle,
)

__all__ = [
    # Personality types
    "ThinkingStyle",
    "DecisionStyle",
    "CommunicationStyle",
    "ActionStyle",
    "Personality",
    # Agent persona
    "AgentPersona",
    "PersonaCategory",
    # Agent getters
    "get_divergence_agents",
    "get_convergence_agents",
    "get_planning_agents",
    "get_all_agents",
    "get_agent_by_id",
]
