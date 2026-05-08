from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional

class FieldValidator:
    @validator('value')
    def check_value(cls, value):
        if value is None:
            return None
        return value

class DAOStrategy(BaseModel):
    id: int = Field(..., description="Unique identifier for the DAO strategy", example=1)
    name: str = Field(..., description="Name of the DAO strategy", example="Token Voting")
    parameters: dict = Field(..., description="Parameters specific to the strategy", example={"voting_power": 100})
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Token Voting",
                "parameters": {"voting_power": 100}
            }
        }


class SimulationResult(BaseModel):
    id: int = Field(..., description="Unique identifier for the simulation result", example=1)
    dao_strategy_id: int = Field(..., description="ID of the DAO strategy this result belongs to", example=1)
    timestamp: str = Field(..., description="Timestamp of the simulation run", example="2023-10-27T10:00:00Z")
    outcome: dict = Field(..., description="Outcome of the simulation", example={"total_votes": 500, "approved": True})
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "dao_strategy_id": 1,
                "timestamp": "2023-10-27T10:00:00Z",
                "outcome": {"total_votes": 500, "approved": True}
            }
        }

class AgentState(BaseModel):
    id: int = Field(..., description="Unique identifier for the agent", example=1)
    name: str = Field(..., description="Name of the agent", example="AgentA")
    dao_strategy_id: int = Field(..., description="ID of the DAO strategy the agent is using", example=1)
    simulation_results: List[SimulationResult] = Field(..., description="List of simulation results for this agent", example=[SimulationResult(id=1, dao_strategy_id=1, timestamp="2023-10-27T10:00:00Z", outcome={"total_votes": 500, "approved": True}), SimulationResult(id=2, dao_strategy_id=1, timestamp="2023-10-27T10:01:00Z", outcome={"total_votes": 600, "approved": True})])
    parameters: dict = Field(..., description="Current parameters of the agent", example={"voting_power": 100})
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "AgentA",
                "dao_strategy_id": 1,
                "simulation_results": [
                    SimulationResult(id=1, dao_strategy_id=1, timestamp="2023-10-27T10:00:00Z", outcome={"total_votes": 500, "approved": True}),
                    SimulationResult(id=2, dao_strategy_id=1, timestamp="2023-10-27T10:01:00Z", outcome={"total_votes": 600, "approved": True})
                ],
                "parameters": {"voting_power": 100}
            }
        }

class DAOStrategyResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for the DAO strategy", example=1)
    name: str = Field(..., description="Name of the DAO strategy", example="Token Voting")
    parameters: dict = Field(..., description="Parameters specific to the strategy", example={"voting_power": 100})
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Token Voting",
                "parameters": {"voting_power": 100}
            }
        }

class SimulationResultResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for the simulation result", example=1)
    dao_strategy_id: int = Field(..., description="ID of the DAO strategy this result belongs to", example=1)
    timestamp: str = Field(..., description="Timestamp of the simulation run", example="2023-10-27T10:00:00Z")
    outcome: dict = Field(..., description="Outcome of the simulation", example={"total_votes": 500, "approved": True})
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "dao_strategy_id": 1,
                "timestamp": "2023-10-27T10:00:00Z",
                "outcome": {"total_votes": 500, "approved": True}
            }
        }

class AgentStateResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for the agent", example=1)
    name: str = Field(..., description="Name of the agent", example="AgentA")
    dao_strategy_id: int = Field(..., description="ID of the DAO strategy the agent is using", example=1)
    simulation_results: List[SimulationResult] = Field(..., description="List of simulation results for this agent", example=[SimulationResult(id=1, dao_strategy_id=1, timestamp="2023-10-27T10:00:00Z", outcome={"total_votes": 500, "approved": True}), SimulationResult(id=2, dao_strategy_id=1, timestamp="2023-10-27T10:01:00Z", outcome={"total_votes": 600, "approved": True})])
    parameters: dict = Field(..., description="Current parameters of the agent", example={"voting_power": 100})
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "AgentA",
                "dao_strategy_id": 1,
                "simulation_results": [
                    SimulationResult(id=1, dao_strategy_id=1, timestamp="2023-10-27T10:00:00Z", outcome={"total_votes": 500, "approved": True}),
                    SimulationResult(id=2, dao_strategy_id=1, timestamp="2023-10-27T10:01:00Z", outcome={"total_votes": 600, "approved": True})
                ],
                "parameters": {"voting_power": 100}
            }
        }