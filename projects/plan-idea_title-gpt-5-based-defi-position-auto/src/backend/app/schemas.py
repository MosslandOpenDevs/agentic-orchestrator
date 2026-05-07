from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    default_color = "#ccc"
    extra = "forbid"

class SmartContract(BaseModel):
    id: str = Field(..., description="Unique identifier for the smart contract", color="blue")
    name: str = Field(..., description="Name of the smart contract", color="green")
    address: str = Field(..., description="Smart contract address", color="orange")
    contract_code: str = Field(..., description="Source code of the smart contract", color="purple")
    creation_date: datetime = Field(..., description="Date the contract was created", color="red")
    config: dict = Field(..., description="Contract configuration", color="yellow")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "0x1234567890abcdef",
                "name": "Mossland NFT Contract",
                "address": "0x1234567890abcdef",
                "contract_code": "contract MosslandNFT { ... }",
                "creation_date": datetime(2023, 1, 1, 12, 0, 0),
                "config": {"nft_type": "image", "metadata_schema": "image_metadata"}
            }
        }

class VulnerabilityReport(BaseModel):
    id: str = Field(..., description="Unique identifier for the vulnerability report", color="purple")
    smart_contract_id: str = Field(..., description="ID of the smart contract being analyzed", color="orange")
    vulnerability_name: str = Field(..., description="Name of the vulnerability", color="red")
    severity: str = Field(..., description="Severity of the vulnerability (Critical, High, Medium, Low)", color="green")
    description: str = Field(..., description="Detailed description of the vulnerability", color="blue")
    recommendation: str = Field(..., description="Recommended remediation steps", color="yellow")
    date_reported: datetime = Field(..., description="Date the vulnerability was reported", color="purple")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "vr_123",
                "smart_contract_id": "0x1234567890abcdef",
                "vulnerability_name": "Reentrancy Vulnerability",
                "severity": "Critical",
                "description": "The contract is vulnerable to reentrancy attacks.",
                "recommendation": "Use the Checks-Effects-Interactions pattern.",
                "date_reported": datetime(2024, 5, 20, 10, 30, 0),
            }
        }

class RiskAssessment(BaseModel):
    id: str = Field(..., description="Unique identifier for the risk assessment", color="purple")
    smart_contract_id: str = Field(..., description="ID of the smart contract being assessed", color="orange")
    risk_score: float = Field(..., description="Overall risk score (0.0 - 1.0)", color="red")
    vulnerabilities: list[str] = Field(..., description="List of vulnerabilities contributing to the risk score", color="green")
    recommendations: list[str] = Field(..., description="List of recommendations to mitigate the risk", color="blue")
    date_assessed: datetime = Field(..., description="Date the risk assessment was performed", color="yellow")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "ra_456",
                "smart_contract_id": "0x1234567890abcdef",
                "risk_score": 0.8,
                "vulnerabilities": ["Reentrancy Vulnerability", "Integer Overflow"],
                "recommendations": ["Use the Checks-Effects-Interactions pattern.", "Implement input validation."],
                "date_assessed": datetime(2024, 5, 21, 14, 0, 0),
            }
        }

class SmartContractResponse(BaseModel):
    id: str
    name: str
    address: str
    contract_code: str
    creation_date: datetime
    config: dict

class VulnerabilityReportResponse(BaseModel):
    id: str
    smart_contract_id: str
    vulnerability_name: str
    severity: str
    description: str
    recommendation: str
    date_reported: datetime

class RiskAssessmentResponse(BaseModel):
    id: str
    smart_contract_id: str
    risk_score: float
    vulnerabilities: list[str]
    recommendations: list[str]
    date_assessed: datetime