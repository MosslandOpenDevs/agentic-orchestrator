"""
Multi-stage debate.

Persona agents debate a topic in three phases — Divergence → Convergence →
Planning — routed through ``HybridLLMRouter``.

Usage:
    from agentic_orchestrator.debate import run_multi_stage_debate

    result = await run_multi_stage_debate(router, topic, context)
"""

from .multi_stage import (
    Idea,
    MultiStageDebate,
    MultiStageDebateResult,
    run_multi_stage_debate,
)
from .protocol import (
    DebateMessage,
    DebatePhase,
    DebateProtocol,
    DebateProtocolConfig,
    DebateRound,
    MessageType,
    PhaseResult,
)

__all__ = [
    # Protocol
    "DebatePhase",
    "DebateProtocol",
    "DebateProtocolConfig",
    "DebateMessage",
    "DebateRound",
    "PhaseResult",
    "MessageType",
    # Multi-stage debate
    "Idea",
    "MultiStageDebate",
    "MultiStageDebateResult",
    "run_multi_stage_debate",
]
