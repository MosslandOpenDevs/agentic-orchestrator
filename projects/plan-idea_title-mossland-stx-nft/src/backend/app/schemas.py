from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldValidator(BaseModel):
    """Base class for field validators."""
    value: any
    
    def validate(self, value: any) -> any:
        """Validates the value against the defined rules."""
        try:
            return value
        except Exception as e:
            raise ValueError(f"Validation failed: {e}")


class Config:
    """Pydantic Config class."""
    allow_population_by_field_name = True
    extra = "forbid"


class PriceFeed(BaseModel):
    """Price Feed Entity."""
    id: int = Field(..., description="Unique identifier for the price feed", example=1)
    symbol: str = Field(..., description="Trading symbol (e.g., ETH)", example="ETH")
    price: float = Field(..., description="Price of the asset", example=1000.00)
    timestamp: datetime = Field(..., description="Timestamp of the price data", example=datetime.now())
    source: str = Field(..., description="Source of the price data", example="CoinGecko")
    
    config = Config()


class User(BaseModel):
    """User Entity."""
    id: int = Field(..., description="Unique identifier for the user", example=1)
    username: str = Field(..., description="User's username", min_length=3, max_length=50, example="john_doe")
    email: str = Field(..., description="User's email address", format="email", example="john.doe@example.com")
    
    config = Config()


class Portfolio(BaseModel):
    """Portfolio Entity."""
    user_id: int = Field(..., description="Foreign key referencing the User", example=1)
    nft_ids: List[int] = Field(..., description="List of NFT IDs in the portfolio", example=[1, 2, 3])
    total_value: float = Field(..., description="Total value of the portfolio", example=10000.00)
    
    config = Config()


class NFTFraction(BaseModel):
    """NFTFraction Entity."""
    id: int = Field(..., description="Unique identifier for the NFT fraction", example=1)
    nft_id: int = Field(..., description="Foreign key referencing the NFT", example=1)
    fraction_amount: float = Field(..., description="Fraction of the NFT owned", example=0.01)
    
    config = Config()


class CreateUser(BaseModel):
    """Create User Request Schema."""
    username: str = Field(..., description="User's username", min_length=3, max_length=50)
    email: str = Field(..., description="User's email address", format="email")

    class Config(Config):
        extra = "forbid"


class UpdateUser(BaseModel):
    """Update User Request Schema."""
    username: Optional[str] = Field(..., description="User's username", min_length=3, max_length=50)
    email: Optional[str] = Field(..., description="User's email address", format="email")

    class Config(Config):
        extra = "forbid"


class ResponsePortfolio(BaseModel):
    """Response Portfolio Schema."""
    portfolio_id: int = Field(..., description="Unique identifier for the portfolio", example=1)
    user_id: int = Field(..., description="Foreign key referencing the User", example=1)
    nft_ids: List[int] = Field(..., description="List of NFT IDs in the portfolio", example=[1, 2, 3])
    total_value: float = Field(..., description="Total value of the portfolio", example=10000.00)

    class Config(Config):
        extra = "forbid"


class ResponseNFTFraction(BaseModel):
    """Response NFTFraction Schema."""
    id: int = Field(..., description="Unique identifier for the NFT fraction", example=1)
    nft_id: int = Field(..., description="Foreign key referencing the NFT", example=1)
    fraction_amount: float = Field(..., description="Fraction of the NFT owned", example=0.01)

    class Config(Config):
        extra = "forbid"