from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    """
    Config class for Pydantic fields.
    """
    extra = 'forbid'


class BaseSmartContract(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the smart contract", config=FieldConfig)
    name: str = Field("Default Smart Contract", description="Name of the smart contract", config=FieldConfig)
    description: Optional[str] = Field(None, description="Description of the smart contract", config=FieldConfig)
    contract_address: str = Field("", description="Ethereum contract address", config=FieldConfig)
    blockchain: str = Field("Ethereum", description="Blockchain the smart contract is deployed on", config=FieldConfig)
    created_at: datetime = Field(datetime.now, description="Timestamp of contract creation", config=FieldConfig)
    updated_at: datetime = Field(datetime.now, description="Timestamp of last contract update", config=FieldConfig)


class CreateSmartContract(BaseSmartContract):
    """
    Pydantic model for creating a SmartContract.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "name": "My DeFi Protocol",
                    "description": "A simple lending protocol",
                    "contract_address": "0x...",
                    "blockchain": "Ethereum",
                }
            ]
        }


class UpdateSmartContract(BaseSmartContract):
    """
    Pydantic model for updating a SmartContract.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": 123,
                    "name": "Updated DeFi Protocol",
                    "description": "A more robust lending protocol",
                    "contract_address": "0x...",
                    "blockchain": "Ethereum",
                }
            ]
        }


class ResponseSmartContract(BaseSmartContract):
    """
    Pydantic model for responding with a SmartContract.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": 123,
                    "name": "Updated DeFi Protocol",
                    "description": "A more robust lending protocol",
                    "contract_address": "0x...",
                    "blockchain": "Ethereum",
                }
            ]
        }


class BaseTransaction(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the transaction", config=FieldConfig)
    block_number: int = Field(..., description="Block number on the blockchain where the transaction occurred", config=FieldConfig)
    transaction_hash: str = Field("", description="Ethereum transaction hash", config=FieldConfig)
    from_address: str = Field("", description="Sender's Ethereum address", config=FieldConfig)
    to_address: str = Field("", description="Recipient's Ethereum address", config=FieldConfig)
    value: Optional[float] = Field(None, description="Amount of ETH transferred", config=FieldConfig)
    gas_used: int = Field(0, description="Gas used for the transaction", config=FieldConfig)
    gas_price: Optional[float] = Field(None, description="Gas price in Gwei", config=FieldConfig)
    created_at: datetime = Field(datetime.now, description="Timestamp of transaction creation", config=FieldConfig)
    updated_at: datetime = Field(datetime.now, description="Timestamp of last transaction update", config=FieldConfig)


class CreateTransaction(BaseTransaction):
    """
    Pydantic model for creating a Transaction.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "block_number": 123456789,
                    "transaction_hash": "0x...",
                    "from_address": "0x...",
                    "to_address": "0x...",
                    "value": 1.5,
                    "gas_used": 21000,
                    "gas_price": 1.0,
                }
            ]
        }


class UpdateTransaction(BaseTransaction):
    """
    Pydantic model for updating a Transaction.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": 987,
                    "block_number": 123456790,
                    "transaction_hash": "0x...",
                    "from_address": "0x...",
                    "to_address": "0x...",
                    "value": 2.0,
                    "gas_used": 22000,
                    "gas_price": 1.2,
                }
            ]
        }


class ResponseTransaction(BaseTransaction):
    """
    Pydantic model for responding with a Transaction.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": 987,
                    "block_number": 123456790,
                    "transaction_hash": "0x...",
                    "from_address": "0x...",
                    "to_address": "0x...",
                    "value": 2.0,
                    "gas_used": 22000,
                    "gas_price": 1.2,
                }
            ]
        }


class BaseVulnerabilityPrediction(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the vulnerability prediction", config=FieldConfig)
    smart_contract_id: int = Field(..., description="ID of the smart contract the vulnerability applies to", config=FieldConfig)
    vulnerability_name: str = Field("", description="Name of the vulnerability", config=FieldConfig)
    description: str = Field("", description="Detailed description of the vulnerability", config=FieldConfig)
    severity: str = Field("Medium", description="Severity level of the vulnerability", config=FieldConfig)
    cvss_score: Optional[float] = Field(None, description="CVSS score of the vulnerability", config=FieldConfig)
    created_at: datetime = Field(datetime.now, description="Timestamp of prediction creation", config=FieldConfig)
    updated_at: datetime = Field(datetime.now, description="Timestamp of last prediction update", config=FieldConfig)


class CreateVulnerabilityPrediction(BaseVulnerabilityPrediction):
    """
    Pydantic model for creating a VulnerabilityPrediction.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "smart_contract_id": 123,
                    "vulnerability_name": "Reentrancy",
                    "description": "The smart contract is vulnerable to reentrancy attacks.",
                    "severity": "High",
                    "cvss_score": 8.8,
                }
            ]
        }


class UpdateVulnerabilityPrediction(BaseVulnerabilityPrediction):
    """
    Pydantic model for updating a VulnerabilityPrediction.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": 456,
                    "smart_contract_id": 123,
                    "vulnerability_name": "Fixed Reentrancy",
                    "description": "The reentrancy vulnerability has been fixed.",
                    "severity": "Low",
                    "cvss_score": 0.0,
                }
            ]
        }


class ResponseVulnerabilityPrediction(BaseVulnerabilityPrediction):
    """
    Pydantic model for responding with a VulnerabilityPrediction.
    """
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": 456,
                    "smart_contract_id": 123,
                    "vulnerability_name": "Fixed Reentrancy",
                    "description": "The reentrancy vulnerability has been fixed.",
                    "severity": "Low",
                    "cvss_score": 0.0,
                }
            ]
        }