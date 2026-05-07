from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldValidator(BaseModel):
    """Base class for field validators."""
    value: any
    
    def validate(self, value: any) -> any:
        """Validate the value."""
        try:
            return value
        except Exception as e:
            raise ValueError(f"Validation failed: {e}")


class Config:
    """Pydantic config."""
    arbitrary_types_allowed = True
    json_encoders = {
        datetime: lambda v: v.isoformat()
    }


class BaseNFTPosition(BaseModel):
    """Base schema for NFTPosition."""
    id: int = Field(default=1, description="Unique identifier for the position")
    portfolio_id: int = Field(default=1, description="ID of the portfolio this position belongs to")
    nft_token_id: int = Field(default=1, description="ID of the NFT token")
    quantity: int = Field(default=1, description="Number of tokens held")
    entry_price: float = Field(default=0.0, description="Price at which the token was purchased")
    
    
class CreateNFTPosition(BaseNFTPosition):
    """Create schema for NFTPosition."""
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": 1,
                "nft_token_id": 123,
                "quantity": 10,
                "entry_price": 150.75
            }
        }


class UpdateNFTPosition(BaseNFTPosition):
    """Update schema for NFTPosition."""
    
    class Config:
        schema_extra = {
            "example": {
                "id": 2,
                "quantity": 15,
                "entry_price": 160.50
            }
        }


class ResponseNFTPosition(BaseNFTPosition):
    """Response schema for NFTPosition."""
    
    class Config:
        schema_extra = {
            "example": {
                "id": 2,
                "portfolio_id": 1,
                "nft_token_id": 123,
                "quantity": 15,
                "entry_price": 160.50
            }
        }


class BaseNFTPortfolio(BaseModel):
    """Base schema for NFTPortfolio."""
    id: int = Field(default=1, description="Unique identifier for the portfolio")
    user_id: int = Field(default=1, description="ID of the user who owns the portfolio")
    name: str = Field(default="My Portfolio", description="Name of the portfolio")
    
    
class CreateNFTPortfolio(BaseNFTPortfolio):
    """Create schema for NFTPortfolio."""
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "name": "My Awesome Portfolio"
            }
        }


class UpdateNFTPortfolio(BaseNFTPortfolio):
    """Update schema for NFTPortfolio."""
    
    class Config:
        schema_extra = {
            "example": {
                "id": 2,
                "name": "Updated Portfolio Name"
            }
        }


class ResponseNFTPortfolio(BaseNFTPortfolio):
    """Response schema for NFTPortfolio."""
    
    class Config:
        schema_extra = {
            "example": {
                "id": 2,
                "user_id": 1,
                "name": "Updated Portfolio Name"
            }
        }


class BaseMarketData(BaseModel):
    """Base schema for MarketData."""
    token_id: int = Field(default=1, description="ID of the token")
    timestamp: datetime = Field(default=datetime.now(), description="Timestamp of the data")
    price: float = Field(default=0.0, description="Price of the token")
    volume: float = Field(default=0.0, description="Volume traded")
    
    
class CreateMarketData(BaseMarketData):
    """Create schema for MarketData."""
    
    class Config:
        schema_extra = {
            "example": {
                "token_id": 1,
                "timestamp": datetime(2023, 10, 27, 10, 0, 0),
                "price": 25.50,
                "volume": 100.0
            }
        }


class UpdateMarketData(BaseMarketData):
    """Update schema for MarketData."""
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": datetime(2023, 10, 27, 11, 0, 0),
                "price": 26.00,
                "volume": 120.0
            }
        }


class ResponseMarketData(BaseMarketData):
    """Response schema for MarketData."""
    
    class Config:
        schema_extra = {
            "example": {
                "token_id": 1,
                "timestamp": datetime(2023, 10, 27, 11, 0, 0),
                "price": 26.00,
                "volume": 120.0
            }
        }