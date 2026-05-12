from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional

class FieldValidator:
    @validator('value')
    def check_value(cls, value):
        if value is None:
            return None
        return value

class SmartContract(BaseModel):
    id: str = Field(..., description="Unique identifier for the smart contract", config=ConfigDict(frozen=True))
    name: str = Field(..., description="Name of the smart contract")
    address: str = Field(..., description="Contract address on the Mossland chain")
    contract_code: str = Field(..., description="The smart contract's code")
    created_at: int = Field(..., description="Timestamp of contract creation")
    updated_at: Optional[int] = Field(None, description="Timestamp of last update")
    version: str = Field(..., description="Contract version")

    class Config:
        schema_extra = {
            "example": {
                "id": "0x1234567890abcdef",
                "name": "MyContract",
                "address": "0x1234567890abcdef",
                "contract_code": "contract MyContract { ... }",
                "created_at": 1678886400,
                "updated_at": 1678972800,
                "version": "1.0"
            }
        }


class VulnerabilityReport(BaseModel):
    id: str = Field(..., description="Unique identifier for the vulnerability report", config=ConfigDict(frozen=True))
    contract_id: str = Field(..., description="ID of the smart contract this report relates to")
    reporter_id: str = Field(..., description="ID of the user who reported the vulnerability")
    vulnerability_type: str = Field(..., description="Type of vulnerability found")
    description: str = Field(..., description="Detailed description of the vulnerability")
    severity: str = Field(
        FieldValidator,
        description="Severity level of the vulnerability (e.g., Critical, High, Medium, Low)",
    )
    cvss_score: Optional[float] = Field(None, description="CVSS score of the vulnerability")
    timestamp: int = Field(..., description="Timestamp of vulnerability report creation")

    class Config:
        schema_extra = {
            "example": {
                "id": "0xfedcba9876543210",
                "contract_id": "0x1234567890abcdef",
                "reporter_id": "0x9876543210fedcba",
                "vulnerability_type": "SQL Injection",
                "description": "Vulnerable to SQL injection due to unsanitized user input.",
                "severity": "Critical",
                "cvss_score": 9.8,
                "timestamp": 1678972800
            }
        }


class User(BaseModel):
    id: str = Field(..., description="Unique identifier for the user", config=ConfigDict(frozen=True))
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    is_active: bool = Field(True, description="Whether the user account is active")

    class Config:
        schema_extra = {
            "example": {
                "id": "0xabcdef1234567890",
                "username": "john.doe",
                "email": "john.doe@example.com",
                "is_active": True
            }
        }

class SmartContractCreate(BaseModel):
    name: str = Field(..., description="Name of the smart contract")
    address: str = Field(..., description="Contract address on the Mossland chain")
    contract_code: str = Field(..., description="The smart contract's code")
    version: str = Field(..., description="Contract version")

class SmartContractUpdate(BaseModel):
    id: str = Field(..., description="Unique identifier for the smart contract")
    name: Optional[str] = Field(None, description="Name of the smart contract")
    address: Optional[str] = Field(None, description="Contract address on the Mossland chain")
    contract_code: Optional[str] = Field(None, description="The smart contract's code")
    updated_at: Optional[int] = Field(None, description="Timestamp of last update")
    version: Optional[str] = Field(None, description="Contract version")

class VulnerabilityReportCreate(BaseModel):
    contract_id: str = Field(..., description="ID of the smart contract this report relates to")
    reporter_id: str = Field(..., description="ID of the user who reported the vulnerability")
    vulnerability_type: str = Field(..., description="Type of vulnerability found")
    description: str = Field(..., description="Detailed description of the vulnerability")

class VulnerabilityReportUpdate(BaseModel):
    id: str = Field(..., description="Unique identifier for the vulnerability report")
    contract_id: str = Field(..., description="ID of the smart contract this report relates to")
    reporter_id: str = Field(..., description="ID of the user who reported the vulnerability")
    vulnerability_type: str = Field(..., description="Type of vulnerability found")
    description: str = Field(..., description="Detailed description of the vulnerability")
    severity: str = Field(..., description="Severity level of the vulnerability (e.g., Critical, High, Medium, Low)")
    cvss_score: Optional[float] = Field(None, description="CVSS score of the vulnerability")

class UserCreate(BaseModel):
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")

class UserUpdate(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    username: Optional[str] = Field(None, description="User's username")
    email: Optional[str] = Field(None, description="User's email address")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")