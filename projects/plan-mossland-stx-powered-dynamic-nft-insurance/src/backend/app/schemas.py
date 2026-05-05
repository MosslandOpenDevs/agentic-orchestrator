from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldValidator(BaseModel):
    """Base class for field validators."""
    value: any
    message: str

    class Config:
        extra = False


class PriceFeed(BaseModel):
    """PriceFeed - Stores price data from external sources."""
    symbol: str = Field(..., description="Trading symbol (e.g., NFTLAND)", min_length=5, max_length=10)
    price: float = Field(..., gt=0)
    timestamp: datetime = Field(default=datetime.utcnow())
    source: str = Field(..., description="Source of the price data (e.g., CoinGecko, Chainlink)")
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            symbol=data["symbol"],
            price=data["price"],
            timestamp=data["timestamp"],
            source=data["source"]
        )

    @classmethod
    def from_json(cls, json):
        return cls(
            symbol=json["symbol"],
            price=json["price"],
            timestamp=json["timestamp"],
            source=json["source"]
        )


class User(BaseModel):
    """User - Represents a user within the Mossland ecosystem."""
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    discord_id: Optional[str] = Field(None, description="User's Discord ID")
    created_at: datetime = Field(default=datetime.utcnow())
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user123",
                "username": "mossland_user",
                "email": "user@example.com",
                "discord_id": "1234567890",
            }
        }


class Portfolio(BaseModel):
    """Portfolio - Represents a user's NFT portfolio."""
    user_id: str = Field(..., description="Foreign key referencing the User")
    nft_ids: List[str] = Field(..., description="List of NFT IDs held in the portfolio")
    total_value: float = Field(..., gt=0, description="Total value of the portfolio")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "nft_ids": ["nft1", "nft2"],
                "total_value": 1000.00
            }
        }


class NFTFraction(BaseModel):
    """NFTFraction - Represents a single fractionalized NFT token."""
    id: str = Field(..., description="Unique NFT fraction identifier")
    nft_id: str = Field(..., description="Foreign key referencing the NFT")
    fraction: float = Field(..., gt=0.0, le=1.0, description="Fraction of the NFT owned")
    user_id: Optional[str] = Field(None, description="Foreign key referencing the User who owns the fraction")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "fraction1",
                "nft_id": "nft1",
                "fraction": 0.5
            }
        }


class CreateUserSchema(BaseModel):
    """Create User Schema"""
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    discord_id: Optional[str] = Field(None, description="User's Discord ID")

    class Config:
        schema_extra = {
            "example": {
                "username": "new_user",
                "email": "new@example.com",
                "discord_id": "9876543210"
            }
        }

class CreatePortfolioSchema(BaseModel):
    """Create Portfolio Schema"""
    user_id: str = Field(..., description="Foreign key referencing the User")
    nft_ids: List[str] = Field(..., description="List of NFT IDs held in the portfolio")
    total_value: float = Field(..., gt=0, description="Total value of the portfolio")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "nft_ids": ["nft1", "nft2"],
                "total_value": 1000.00
            }
        }

class UpdatePortfolioSchema(BaseModel):
    """Update Portfolio Schema"""
    nft_ids: Optional[List[str]] = Field(None, description="List of NFT IDs held in the portfolio")
    total_value: Optional[float] = Field(None, description="Total value of the portfolio")

    class Config:
        schema_extra = {
            "example": {
                "nft_ids": ["nft1", "nft3"],
                "total_value": 1200.00
            }
        }

class ResponsePortfolioSchema(BaseModel):
    """Response Portfolio Schema"""
    nft_ids: List[str] = Field(..., description="List of NFT IDs held in the portfolio")
    total_value: float = Field(..., description="Total value of the portfolio")

    class Config:
        schema_extra = {
            "example": {
                "nft_ids": ["nft1", "nft2"],
                "total_value": 1000.00
            }
        }