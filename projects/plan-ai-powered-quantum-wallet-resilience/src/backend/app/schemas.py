from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic import ValidationError

class FieldValidator(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    value: str = Field(..., min_length=1, max_length=255)


class SmartContract(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the smart contract")
    name: str = Field(..., min_length=3, max_length=100)
    code: str = Field(..., description="The smart contract code")
    version: str = Field(..., min_length=1, max_length=50)
    blockchain: str = Field(..., min_length=3, max_length=50)
    schema_version: str = Field(..., min_length=1, max_length=50)
    config = ConfigDict(example={'description': 'A smart contract for decentralized finance'})

    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "name": "MyDApp",
                "code": "contract MyDApp { ... }",
                "version": "1.0",
                "blockchain": "Ethereum",
                "schema_version": "1.2",
            }
        }


class Vulnerability(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the vulnerability")
    smart_contract_id: int = Field(..., description="ID of the smart contract this vulnerability belongs to")
    name: str = Field(..., min_length=3, max_length=100)
    severity: str = Field(..., enum=["Critical", "High", "Medium", "Low"], description="Severity level of the vulnerability")
    description: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=255)
    cvss_score: Optional[float] = Field(None, description="CVSS score of the vulnerability")
    field_validator = FieldValidator()

    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "smart_contract_id": 123,
                "name": "SQL Injection",
                "severity": "Critical",
                "description": "Vulnerable to SQL injection attacks.",
                "location": "contract.js",
                "cvss_score": 9.8,
                "field_validator": {"name": "SQL Injection", "value": "vulnerable code"}
            }
        }


class LLMAnalysis(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the LLM analysis")
    smart_contract_id: int = Field(..., description="ID of the smart contract analyzed")
    analysis_date: str = Field(..., format="%Y-%m-%d %H:%M:%S")
    llm_model: str = Field(..., min_length=3, max_length=100)
    analysis_result: str = Field(..., min_length=1, max_length=255)
    confidence_score: Optional[float] = Field(None, description="Confidence score of the analysis")
    field_validator = FieldValidator()

    class Config:
        schema_extra = {
            "example": {
                "id": 789,
                "smart_contract_id": 123,
                "analysis_date": "2023-10-27 10:00:00",
                "llm_model": "GPT-4",
                "analysis_result": "High risk of reentrancy vulnerability.",
                "confidence_score": 0.95,
                "field_validator": {"name": "Reentrancy", "value": "vulnerable code"}
            }
        }


class SmartContractResponse(BaseModel):
    id: int
    name: str
    code: str
    version: str
    blockchain: str
    schema_version: str

    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "name": "MyDApp",
                "code": "contract MyDApp { ... }",
                "version": "1.0",
                "blockchain": "Ethereum",
                "schema_version": "1.2",
            }
        }

class VulnerabilityResponse(BaseModel):
    id: int
    smart_contract_id: int
    name: str
    severity: str
    description: str
    location: str
    cvss_score: Optional[float]
    field_validator: dict

    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "smart_contract_id": 123,
                "name": "SQL Injection",
                "severity": "Critical",
                "description": "Vulnerable to SQL injection attacks.",
                "location": "contract.js",
                "cvss_score": 9.8,
                "field_validator": {"name": "SQL Injection", "value": "vulnerable code"}
            }
        }

class LLMAnalysisResponse(BaseModel):
    id: int
    smart_contract_id: int
    analysis_date: str
    llm_model: str
    analysis_result: str
    confidence_score: Optional[float]
    field_validator: dict

    class Config:
        schema_extra = {
            "example": {
                "id": 789,
                "smart_contract_id": 123,
                "analysis_date": "2023-10-27 10:00:00",
                "llm_model": "GPT-4",
                "analysis_result": "High risk of reentrancy vulnerability.",
                "confidence_score": 0.95,
                "field_validator": {"name": "Reentrancy", "value": "vulnerable code"}
            }
        }