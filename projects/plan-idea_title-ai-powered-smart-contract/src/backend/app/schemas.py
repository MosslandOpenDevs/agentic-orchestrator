from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    """
    Config class for Pydantic fields.
    """
    extra = 'forbid'

class SmartContract(BaseModel):
    id: int = Field(..., description="Unique identifier for the smart contract", config=FieldConfig)
    name: str = Field(..., description="Name of the smart contract", config=FieldConfig)
    address: str = Field(..., description="XMR DEX contract address", config=FieldConfig)
    deployed_at: datetime = Field(..., description="Timestamp of contract deployment", config=FieldConfig)
    code_hash: str = Field(..., description="Hash of the smart contract code", config=FieldConfig)
    version: str = Field(..., description="Version of the smart contract", config=FieldConfig)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "name": "MyAwesomeContract",
                "address": "TXM...",
                "deployed_at": datetime(2023, 1, 1, 12, 0, 0),
                "code_hash": "...",
                "version": "1.0"
            }
        }

class VulnerabilityReport(BaseModel):
    id: int = Field(..., description="Unique identifier for the vulnerability report", config=FieldConfig)
    contract_id: int = Field(..., description="ID of the smart contract the vulnerability is related to", config=FieldConfig)
    reporter: str = Field(..., description="Name of the reporter", config=FieldConfig)
    vulnerability_type: str = Field(..., description="Type of vulnerability", config=FieldConfig)
    description: str = Field(..., description="Detailed description of the vulnerability", config=FieldConfig)
    severity: str = Field(..., description="Severity level of the vulnerability (e.g., Critical, High, Medium, Low)", config=FieldConfig)
    reported_at: datetime = Field(..., description="Timestamp of vulnerability report creation", config=FieldConfig)
    status: str = Field("Open", description="Status of the vulnerability report (e.g., Open, In Progress, Resolved, Closed)", config=FieldConfig)

    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "contract_id": 123,
                "reporter": "Alice",
                "vulnerability_type": "Reentrancy",
                "description": "The contract allows an attacker to drain funds.",
                "severity": "Critical",
                "reported_at": datetime(2024, 5, 10, 10, 30, 0),
                "status": "Open"
            }
        }

class RiskAssessment(BaseModel):
    id: int = Field(..., description="Unique identifier for the risk assessment", config=FieldConfig)
    contract_id: int = Field(..., description="ID of the smart contract being assessed", config=FieldConfig)
    assessor: str = Field(..., description="Name of the assessor", config=FieldConfig)
    assessment_date: datetime = Field(..., description="Date of the risk assessment", config=FieldConfig)
    risk_score: float = Field(..., description="Overall risk score (e.g., 0.0 - 1.0)", config=FieldConfig)
    vulnerabilities: list[int] = Field([], description="List of vulnerability IDs associated with this assessment", config=FieldConfig)
    recommendations: str = Field(..., description="Recommendations for mitigating the risks", config=FieldConfig)

    class Config:
        schema_extra = {
            "example": {
                "id": 789,
                "contract_id": 123,
                "assessor": "Bob",
                "assessment_date": datetime(2024, 5, 15, 14, 0, 0),
                "risk_score": 0.8,
                "vulnerabilities": [456],
                "recommendations": "Implement proper input validation and authorization checks."
            }
        }