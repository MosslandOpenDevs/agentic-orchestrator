"""
FastAPI main application for Mossland Agentic Orchestrator API.

Endpoints:
- GET /health - System health status
- GET /status - Overall system status
- GET /signals - Recent signals
- GET /debates - Recent debate results
- GET /agents - Agent personas information
"""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="MOSS.AO API",
    description="Mossland Agentic Orchestrator API",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class StatusResponse(BaseModel):
    status: str
    timestamp: str
    components: dict
    stats: dict


class SignalResponse(BaseModel):
    id: str
    source: str
    title: str
    summary: Optional[str]
    score: float
    created_at: str


class DebateResponse(BaseModel):
    id: str
    topic: str
    phase: str
    ideas_count: int
    created_at: str


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    phase: str
    personality: dict


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health status."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="0.4.0",
    )


@app.get("/status", response_model=StatusResponse)
async def system_status():
    """Get overall system status."""
    return StatusResponse(
        status="operational",
        timestamp=datetime.utcnow().isoformat(),
        components={
            "api": {"status": "healthy"},
            "database": {"status": "healthy"},
            "cache": {"status": "healthy"},
            "llm_router": {"status": "healthy"},
        },
        stats={
            "signals_today": 0,
            "debates_today": 0,
            "ideas_generated": 0,
            "agents_active": 34,
        },
    )


@app.get("/signals")
async def get_signals(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    source: Optional[str] = None,
    min_score: Optional[float] = None,
):
    """Get recent signals."""
    # TODO: Implement database query
    return {
        "signals": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@app.get("/debates")
async def get_debates(
    limit: int = Query(default=10, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Get recent debate results."""
    # TODO: Implement database query
    return {
        "debates": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@app.get("/agents")
async def get_agents(phase: Optional[str] = None):
    """Get agent personas information."""
    from ..personas import DIVERGENCE_AGENTS, CONVERGENCE_AGENTS, PLANNING_AGENTS

    agents = []

    if phase is None or phase == "divergence":
        for agent in DIVERGENCE_AGENTS:
            agents.append({
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "phase": "divergence",
                "personality": {
                    "creativity": agent.creativity,
                    "analytical": agent.analytical,
                    "risk_tolerance": agent.risk_tolerance,
                    "collaboration": agent.collaboration,
                },
            })

    if phase is None or phase == "convergence":
        for agent in CONVERGENCE_AGENTS:
            agents.append({
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "phase": "convergence",
                "personality": {
                    "creativity": agent.creativity,
                    "analytical": agent.analytical,
                    "risk_tolerance": agent.risk_tolerance,
                    "collaboration": agent.collaboration,
                },
            })

    if phase is None or phase == "planning":
        for agent in PLANNING_AGENTS:
            agents.append({
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "phase": "planning",
                "personality": {
                    "creativity": agent.creativity,
                    "analytical": agent.analytical,
                    "risk_tolerance": agent.risk_tolerance,
                    "collaboration": agent.collaboration,
                },
            })

    return {
        "agents": agents,
        "total": len(agents),
    }


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "MOSS.AO API",
        "version": "0.4.0",
        "description": "Mossland Agentic Orchestrator API",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "signals": "/signals",
            "debates": "/debates",
            "agents": "/agents",
            "docs": "/docs",
        },
    }
