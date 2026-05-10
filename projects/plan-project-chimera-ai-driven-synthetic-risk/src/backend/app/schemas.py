from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    field_name: str
    default: any
    description: str
    annotation: type
    example: any

class SmartContract(BaseModel):
    id: str = Field(..., description="Unique identifier for the smart contract", example="smart_contract_123")
    name: str = Field(..., description="Name of the smart contract", example="MyDEXContract")
    contract_address: str = Field(..., description="WAX blockchain contract address", example="WAX1234567890")
    symbol: str = Field(..., description="Contract symbol", example="MYDEX")
    decimals: int = Field(18, description="Number of decimals", example=18)
    created_at: datetime = Field(datetime.utcnow(), description="Timestamp of contract creation", example=datetime.utcnow())
    updated_at: datetime = Field(datetime.utcnow(), description="Timestamp of last update", example=datetime.utcnow())
    description: Optional[str] = Field(None, description="Description of the contract", example="A decentralized exchange contract")

    class Config:
        schema_extra = {
            "example": {
                "id": "smart_contract_123",
                "name": "MyDEXContract",
                "contract_address": "WAX1234567890",
                "symbol": "MYDEX",
                "decimals": 18,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "description": "A decentralized exchange contract"
            }
        }


class Transaction(BaseModel):
    id: str = Field(..., description="Unique identifier for the transaction", example="transaction_789")
    smart_contract_id: str = Field(..., description="ID of the smart contract involved", example="smart_contract_123")
    transaction_hash: str = Field(..., description="WAX blockchain transaction hash", example="TX1234567890")
    block_height: int = Field(..., description="Block height of the transaction", example=12345)
    timestamp: datetime = Field(datetime.utcnow(), description="Timestamp of the transaction", example=datetime.utcnow())
    value: float = Field(..., description="Amount transferred", example=10.50)
    gas_used: int = Field(0, description="Gas used for the transaction", example=100)

    class Config:
        schema_extra = {
            "example": {
                "smart_contract_id": "smart_contract_123",
                "transaction_hash": "TX1234567890",
                "block_height": 12345,
                "timestamp": datetime.utcnow(),
                "value": 10.50,
                "gas_used": 100
            }
        }


class RiskScore(BaseModel):
    id: str = Field(..., description="Unique identifier for the risk score", example="risk_score_abc")
    smart_contract_id: str = Field(..., description="ID of the smart contract", example="smart_contract_123")
    score: float = Field(..., description="AI-calculated risk score (0-100)", example=75.2)
    confidence: float = Field(..., description="Confidence level of the score (0-100)", example=90.5)
    reasoning: Optional[str] = Field(None, description="Explanation of the risk score", example="High transaction volume and complex code")

    class Config:
        schema_extra = {
            "example": {
                "smart_contract_id": "smart_contract_123",
                "score": 75.2,
                "confidence": 90.5,
                "reasoning": "High transaction volume and complex code"
            }
        }


class User(BaseModel):
    id: str = Field(..., description="Unique identifier for the user", example="user_xyz")
    username: str = Field(..., description="User's username", example="johndoe")
    email: str = Field(..., description="User's email address", example="john.doe@example.com")
    registration_date: datetime = Field(datetime.utcnow(), description="Timestamp of user registration", example=datetime.utcnow())
    balance: float = Field(0.0, description="User's balance", example=100.0)
    is_active: bool = Field(True, description="User account status", example=True)

    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "registration_date": datetime.utcnow(),
                "balance": 100.0,
                "is_active": True
            }
        }