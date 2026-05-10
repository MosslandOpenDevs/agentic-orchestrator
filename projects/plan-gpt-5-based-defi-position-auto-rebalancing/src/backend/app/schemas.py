from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldValidator(BaseModel):
    """Base class for field validators."""
    value: any
    message: str

    def validate(self, value: any) -> any:
        if value is None:
            return None
        try:
            return value
        except Exception as e:
            raise FieldValidator(value=value, message=str(e))


class Config:
    """Pydantic config class."""
    json_encoders = {
        datetime: lambda v: v.iso8601()
    }


class NFT(BaseModel):
    """NFT - Represents a Mossland NFT."""
    id: str = Field(..., description="Unique NFT identifier", min_length=36)
    name: str = Field(..., description="NFT name")
    metadata: ConfigDict = Field(
        default_factory=ConfigDict,
        description="NFT metadata (JSON)"
    )
    current_holdings: int = Field(
        ..., description="Number of NFTs held"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        schema_extra = {
            "example": {
                "id": "0x1234567890abcdef1234567890abcdef12345678",
                "name": "Mossland 1",
                "metadata": {
                    "description": "A beautiful Mossland",
                    "image_url": "https://example.com/mossland1.png"
                },
                "current_holdings": 1
            }
        }


class Portfolio(BaseModel):
    """Portfolio - Represents a user's NFT portfolio."""
    user_id: str = Field(..., description="User identifier")
    nfts: list[NFT] = Field(
        [],
        description="List of NFTs in the portfolio"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "nfts": [
                    {
                        "id": "0x1234567890abcdef1234567890abcdef12345678",
                        "name": "Mossland 1",
                        "metadata": {
                            "description": "A beautiful Mossland",
                            "image_url": "https://example.com/mossland1.png"
                        },
                        "current_holdings": 1
                    },
                    {
                        "id": "0xabcdef1234567890abcdef1234567890abcdef12345678",
                        "name": "Mossland 2",
                        "metadata": {
                            "description": "Another Mossland",
                            "image_url": "https://example.com/mossland2.png"
                        },
                        "current_holdings": 2
                    }
                ]
            }
        }


class MarketData(BaseModel):
    """MarketData - Real-time market data for NFTs."""
    nft_id: str = Field(..., description="NFT identifier")
    price: float = Field(..., description="Current price")
    volume: int = Field(..., description="Trading volume")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        schema_extra = {
            "example": {
                "nft_id": "0x1234567890abcdef1234567890abcdef12345678",
                "price": 100.0,
                "volume": 1000,
                "timestamp": datetime.now()
            }
        }


class Prediction(BaseModel):
    """Prediction - GPT-5 generated NFT value prediction."""
    nft_id: str = Field(..., description="NFT identifier")
    predicted_value: float = Field(..., description="Predicted value")
    confidence: float = Field(
        ..., description="Prediction confidence level", gt=0, lt=1
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        schema_extra = {
            "example": {
                "nft_id": "0x1234567890abcdef1234567890abcdef12345678",
                "predicted_value": 120.0,
                "confidence": 0.8,
                "timestamp": datetime.now()
            }
        }