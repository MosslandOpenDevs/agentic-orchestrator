from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestException
from typing import List
import logging
import os
import asyncio
from datetime import datetime

app = FastAPI(
    title="DAO Simulation Agent",
    description="A data-driven DAO simulation agent leveraging Claude and Mirage.",
    version="0.1",
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["Access-Control-Allow-Origin"],
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment Variable Configuration
API_KEY = os.environ.get("OPENAI_API_KEY", "default_openai_key")
MIRAGE_URL = os.environ.get("MIRAGE_URL", "default_mirage_url")
DUNE_API_KEY = os.environ.get("DUNE_API_KEY", "default_dune_key")


# Health Check Endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# Dummy Data - Replace with actual Mirage integration
class AgentState:
    def __init__(self):
        self.dao_parameters = {}
        self.simulation_results = {}

    async def generate_scenario(self, prompt: str) -> str:
        # Simulate Claude call
        await asyncio.sleep(1)
        return f"Scenario generated from: {prompt}"

    async def store_state(self, key: str, value: any):
        self.dao_parameters[key] = value
        logger.info(f"Stored state: {key} = {value}")

    async def retrieve_state(self, key: str) -> any:
        if key in self.dao_parameters:
            return self.dao_parameters[key]
        else:
            return None


# Dependency Injection - Example
def get_agent_state():
    return AgentState()


# API Endpoints
@app.post("/agent/scenario", response_model=dict)
async def agent_scenario(
    agent_state: AgentState = Depends(get_agent_state),
    prompt: str,
):
    try:
        scenario = await agent_state.generate_scenario(prompt)
        await agent_state.store_state("scenario", scenario)
        return {"message": "Scenario generated successfully", "scenario": scenario}
    except Exception as e:
        logger.exception("Error generating scenario")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate scenario: {str(e)}",
        )


@app.get("/agent/state", response_model=dict)
async def get_agent_state_data(
    agent_state: AgentState = Depends(get_agent_state),
):
    state_data = {}
    for key, value in agent_state.dao_parameters.items():
        state_data[key] = value
    return {"state": state_data}


@app.get("/agent/state/{key}", response_model=dict)
async def get_agent_state_by_key(
    key: str, agent_state: AgentState = Depends(get_agent_state)
):
    value = await agent_state.retrieve_state(key)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State key '{key}' not found",
        )
    return {"key": key, "value": value}


@app.get("/shutdown")
async def shutdown():
    logger.info("Shutting down the application...")
    await asyncio.sleep(2)
    return {"message": "Application shutdown initiated"}