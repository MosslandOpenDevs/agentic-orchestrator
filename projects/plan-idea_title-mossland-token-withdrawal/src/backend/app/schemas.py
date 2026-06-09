from pydantic import BaseModel, Field
from typing import Optional
from typing import Dict

class FieldValidator:
    """
    Placeholder for Field validators.
    In a real application, this would contain actual validation logic.
    """
    def __init__(self, message: str):
        self.message = message

    def __call__(self, value: any) -> bool:
        # Placeholder validation - always returns True
        return True

class ClaudeOpusResponse(BaseModel):
    """
    Represents the response from the Claude Opus API.
    """
    response_id: str = Field(..., description="Unique identifier for the response", min_length=36)
    status_code: int = Field(200, description="HTTP status code of the response", ge=1, le=599)
    data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return ClaudeOpusResponse(**data)

    config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            dict: lambda v: v
        }
    }


class SmartContract(BaseModel):
    """
    Represents the Mossland NFT smart contract.
    """
    contract_address: str = Field(..., description="The contract address", min_length=42)
    chain_id: int = Field(1, description="The chain ID", ge=1, le=10000)
    name: str = Field(..., description="The contract name", min_length=1)
    symbol: str = Field(..., description="The contract symbol", min_length=1)
    decimals: int = Field(18, description="The number of decimals", ge=1, le=255)

    @classmethod
    def from_dict(cls, data: Dict):
        return SmartContract(**data)

    config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            dict: lambda v: v
        }
    }


class NFTWithdrawalTransaction(BaseModel):
    """
    Represents a single NFT withdrawal transaction from the Mossland blockchain.
    """
    transaction_hash: str = Field(..., description="The transaction hash", min_length=66)
    nft_id: str = Field(..., description="The NFT ID", min_length=36)
    contract_address: str = Field(..., description="The contract address", min_length=42)
    chain_id: int = Field(1, description="The chain ID", ge=1, le=10000)
    value: float = Field(0.0, description="The value of the NFT", gt=-1000000.0, lt=1000000.0)
    timestamp: float = Field(None, description="The timestamp of the transaction in seconds", ge=0)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return NFTWithdrawalTransaction(**data)

    config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            dict: lambda v: v
        }
    }

class WithdrawalResponse(BaseModel):
    """
    Represents the response for NFT withdrawal transactions.
    """
    transaction_hash: str = Field(..., description="The transaction hash", min_length=66)
    status: str = Field("success", description="The status of the transaction", enum=["success", "failed"])
    error_message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict):
        return WithdrawalResponse(**data)

    config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            dict: lambda v: v
        }
    }

class CreateWithdrawalRequest(BaseModel):
    """
    Request schema for creating a new withdrawal transaction.
    """
    nft_id: str = Field(..., description="The NFT ID", min_length=36)
    contract_address: str = Field(..., description="The contract address", min_length=42)
    value: float = Field(0.0, description="The value of the NFT", gt=-1000000.0, lt=1000000.0)

class UpdateWithdrawalRequest(BaseModel):
    """
    Request schema for updating a withdrawal transaction.
    """
    transaction_hash: str = Field(..., description="The transaction hash", min_length=66)
    value: Optional[float] = None
    status: Optional[str] = None