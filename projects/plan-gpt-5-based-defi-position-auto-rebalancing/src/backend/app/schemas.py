from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional
import datetime

class FieldValidator(validator.Validator):
    def __init__(self, min_value: int, max_value: int):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: int) -> int:
        if not isinstance(value, int):
            raise ValueError("Value must be an integer.")
        if not self.min_value <= value <= self.max_value:
            raise ValueError(f"Value must be between {self.min_value} and {self.max_value}")
        return value


class ConfigDictExample(ConfigDict):
    example = 10


class NFT(BaseModel):
    id: int = Field(..., description="Unique NFT identifier", example=ConfigDictExample())
    name: str = Field(..., description="NFT name", example="Mossland 1")
    token_id: str = Field(..., description="Token ID", example="0x123...")
    metadata: Optional[dict] = Field(None, description="NFT metadata")
    created_at: datetime.datetime = Field(default=datetime.datetime.utcnow())

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Mossland 1",
                "token_id": "0x123...",
                "metadata": {
                    "image_url": "https://example.com/mossland1.png",
                    "attributes": [{"trait_type": "Rarity", "value": "Rare"}]
                }
            }
        }


class User(BaseModel):
    id: int = Field(..., description="Unique user identifier", example=1)
    username: str = Field(..., description="User username", example="johndoe")
    email: str = Field(..., description="User email", example="john.doe@example.com")
    created_at: datetime.datetime = Field(default=datetime.datetime.utcnow())

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john.doe@example.com"
            }
        }


class Portfolio(BaseModel):
    id: int = Field(..., description="Unique portfolio identifier", example=1)
    user_id: int = Field(..., description="User ID this portfolio belongs to", example=1)
    name: str = Field(..., description="Portfolio name", example="My Mossland Portfolio")
    nft_holdings: List[NFT] = Field([], description="List of NFTs in the portfolio")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "name": "My Mossland Portfolio",
                "nft_holdings": [
                    {
                        "id": 1,
                        "name": "Mossland 1",
                        "token_id": "0x123...",
                        "metadata": {
                            "image_url": "https://example.com/mossland1.png",
                            "attributes": [{"trait_type": "Rarity", "value": "Rare"}]
                        }
                    }
                ]
            }
        }


class MarketData(BaseModel):
    id: int = Field(..., description="Unique market data identifier", example=1)
    nft_id: int = Field(..., description="NFT ID this data relates to", example=1)
    price: float = Field(..., description="Current market price", example=100.0)
    volume: float = Field(..., description="Trading volume", example=10.0)
    timestamp: datetime.datetime = Field(default=datetime.datetime.utcnow())

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "nft_id": 1,
                "price": 100.0,
                "volume": 10.0,
                "timestamp": datetime.datetime.utcnow()
            }
        }


class RebalanceStrategy(BaseModel):
    id: int = Field(..., description="Unique rebalance strategy identifier", example=1)
    portfolio_id: int = Field(..., description="Portfolio ID this strategy applies to", example=1)
    gpt5_output: str = Field(..., description="GPT-5 generated strategy", example="Buy more Mossland 1, sell some Mossland 2")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "portfolio_id": 1,
                "gpt5_output": "Buy more Mossland 1, sell some Mossland 2"
            }
        }