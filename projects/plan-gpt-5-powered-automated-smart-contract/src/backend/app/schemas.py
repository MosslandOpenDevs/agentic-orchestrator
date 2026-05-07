from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    """
    Custom ConfigDict for Field validators.
    """
    yaml_prefix = ""
    extra = ""


class SmartContract(BaseModel):
    id: str = Field(..., description="Unique identifier for the smart contract", config=FieldConfig())
    name: str = Field(..., description="Name of the smart contract", config=FieldConfig())
    address: str = Field(..., description="Contract address", config=FieldConfig())
    blockchain: str = Field("ethereum", description="Blockchain the contract is deployed on", config=FieldConfig())
    creation_date: datetime = Field(None, description="Date the contract was created", config=FieldConfig())
    metadata: Optional[dict] = Field(None, description="Additional metadata about the contract", config=FieldConfig())

    class Config:
        schema_extra = {
            "example": {
                "id": "0x1234567890abcdef",
                "name": "Mossland NFT 1",
                "address": "0x1234567890abcdef",
                "blockchain": "ethereum",
                "creation_date": datetime(2023, 1, 1, 12, 0, 0),
                "metadata": {"royalty_fee": 0.05}
            }
        }


class VulnerabilityReport(BaseModel):
    id: str = Field(..., description="Unique identifier for the vulnerability report", config=FieldConfig())
    contract_address: str = Field(..., description="Contract address associated with the report", config=FieldConfig())
    vulnerability_name: str = Field(..., description="Name of the vulnerability", config=FieldConfig())
    severity: str = Field("medium", description="Severity of the vulnerability", Field(FieldConfig()))
    description: str = Field(..., description="Detailed description of the vulnerability", config=FieldConfig())
    recommendation: str = Field(..., description="Recommended remediation steps", config=FieldConfig())
    timestamp: datetime = Field(None, description="Timestamp when the report was generated", config=FieldConfig())
    ai_engine_version: str = Field("1.0", description="Version of the AI engine that generated the report", config=FieldConfig())

    class Config:
        schema_extra = {
            "example": {
                "id": "report_1",
                "contract_address": "0x1234567890abcdef",
                "vulnerability_name": "Reentrancy",
                "severity": "high",
                "description": "The contract is vulnerable to reentrancy attacks.",
                "recommendation": "Use the Checks-Effects-Interactions pattern.",
                "timestamp": datetime(2023, 10, 26, 14, 30, 0),
                "ai_engine_version": "1.0"
            }
        }


class RiskAssessment(BaseModel):
    id: str = Field(..., description="Unique identifier for the risk assessment", config=FieldConfig())
    contract_address: str = Field(..., description="Contract address being assessed", config=FieldConfig())
    assessment_date: datetime = Field(None, description="Date the assessment was performed", config=FieldConfig())
    risk_score: float = Field(0.0, description="Overall risk score (0.0 - 1.0)", config=FieldConfig())
    vulnerabilities: list[str] = Field([], description="List of vulnerabilities contributing to the risk", config=FieldConfig())
    recommendations: list[str] = Field([], description="Recommendations for mitigating the risks", config=FieldConfig())
    assessor: str = Field("AI Engine", description="Name of the assessor", config=FieldConfig())

    class Config:
        schema_extra = {
            "example": {
                "id": "assessment_1",
                "contract_address": "0x1234567890abcdef",
                "assessment_date": datetime(2023, 10, 27, 9, 0, 0),
                "risk_score": 0.7,
                "vulnerabilities": ["Reentrancy", "Integer Overflow"],
                "recommendations": ["Use the Checks-Effects-Interactions pattern.", "Implement input validation."],
                "assessor": "AI Engine"
            }
        }