from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import validator

class FieldValidator:
    @validator('name')
    def name_must_be_non_empty(cls, value):
        if not value:
            raise ValueError('Name cannot be empty')
        return value

class GPTResponse(BaseModel):
    """
    Stores the output from the GPT-5 API.
    """
    id: str = Field(..., description="Unique identifier for the GPT response")
    text: str = Field(..., description="The generated text")
    model: str = Field("gpt-5", description="The GPT model used")
    usage: float = Field(0.0, description="Usage of the model")
    
    @validator('usage')
    def usage_must_be_non_negative(cls, value):
        if value < 0:
            raise ValueError('Usage must be non-negative')
        return value

    example = {
        "id": "gpt-response-123",
        "text": "This is a generated response.",
        "model": "gpt-5",
        "usage": 0.5
    }


class Asset(BaseModel):
    """
    Represents a cryptocurrency asset within the vault.
    """
    id: str = Field(..., description="Unique identifier for the asset")
    name: str = Field(..., description="Name of the asset", validator=FieldValidator.name_must_be_non_empty)
    symbol: str = Field(..., description="Symbol of the asset")
    quantity: float = Field(..., description="Quantity of the asset in the vault")
    price: float = Field(..., description="Price of the asset")
    
    example = {
        "id": "asset-123",
        "name": "Bitcoin",
        "symbol": "BTC",
        "quantity": 1.5,
        "price": 65000.0
    }


class Vault(BaseModel):
    """
    Represents a user's automated Principal Token portfolio.
    """
    id: str = Field(..., description="Unique identifier for the vault")
    user_id: str = Field(..., description="User ID associated with the vault")
    assets: List[Asset] = Field([], description="List of assets in the vault")
    
    example = {
        "id": "vault-123",
        "user_id": "user-456",
        "assets": [
            {"id": "asset-123", "name": "Bitcoin", "symbol": "BTC", "quantity": 1.5, "price": 65000.0},
            {"id": "asset-456", "name": "Ethereum", "symbol": "ETH", "quantity": 2.0, "price": 3500.0}
        ]
    }


class User(BaseModel):
    """
    Represents a Mossland NFT holder or DeFi investor.
    """
    id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="User's username")
    nft_id: Optional[str] = Field(None, description="NFT ID associated with the user")
    balance: float = Field(0.0, description="User's balance")
    
    example = {
        "id": "user-456",
        "username": "mossland_user",
        "nft_id": "nft-789",
        "balance": 1000.0
    }


class CreateVault(BaseModel):
    """
    Create Vault Request
    """
    user_id: str = Field(..., description="User ID")
    assets: List[dict] = Field([], description="List of assets to add to the vault")

    example = {
        "user_id": "user-456",
        "assets": [
            {"id": "asset-789", "name": "Solana", "symbol": "SOL", "quantity": 0.5, "price": 150.0},
            {"id": "asset-101", "name": "Cardano", "symbol": "ADA", "quantity": 1.0, "price": 0.7}
        ]
    }

class UpdateVault(BaseModel):
    """
    Update Vault Request
    """
    assets: List[dict] = Field([], description="List of assets to update in the vault")

    example = {
        "assets": [
            {"id": "asset-123", "quantity": 2.0, "price": 66000.0},
            {"id": "asset-456", "quantity": 2.5, "price": 3600.0}
        ]
    }

class ResponseVault(BaseModel):
    """
    Response Vault
    """
    id: str = Field("vault-123", description="Unique identifier for the vault")
    user_id: str = Field("user-456", description="User ID associated with the vault")
    assets: List[Asset] = Field([], description="List of assets in the vault")