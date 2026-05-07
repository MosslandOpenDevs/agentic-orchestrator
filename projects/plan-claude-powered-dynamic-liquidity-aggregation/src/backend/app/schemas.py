from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic import ValidationError

class FieldValidator(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    value: int = Field(ge=1, le=100)

    class Config:
        extra = False
        yaml_alias = {"__root__": "dict"}


class NFTHolder(BaseModel):
    id: str = Field(..., description="Unique identifier for the NFT holder")
    name: str = Field(..., min_length=3, max_length=50)
    balance: int = Field(ge=0, le=1000000, description="Total balance of the holder")
    portfolio_id: str = Field(..., description="ID of the associated portfolio")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "holder123",
                "name": "Alice",
                "balance": 50000,
                "portfolio_id": "portfolio456"
            }
        }


class Portfolio(BaseModel):
    id: str = Field(..., description="Unique identifier for the portfolio")
    owner_id: str = Field(..., description="ID of the NFT holder")
    assets: List[str] = Field(..., description="List of NFT IDs in the portfolio")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "portfolio456",
                "owner_id": "holder123",
                "assets": ["nft789", "nft101"]
            }
        }


class MarketData(BaseModel):
    symbol: str = Field(..., description="Trading symbol of the asset")
    price: float = Field(ge=0.01, description="Current price of the asset")
    volume: int = Field(ge=0, description="Trading volume of the asset")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC",
                "price": 30000.00,
                "volume": 1000
            }
        }


class GPT5Response(BaseModel):
    response: str = Field(..., description="The response from the GPT-5 API")
    
    class Config:
        schema_extra = {
            "example": {
                "response": "This is a response from GPT-5."
            }
        }

# Example usage and validation
if __name__ == '__main__':
    try:
        nftholder = NFTHolder(id="holder123", name="Alice", balance=50000, portfolio_id="portfolio456")
        print(nftholder)
    except ValidationError as e:
        print(e)

    try:
        portfolio = Portfolio(id="portfolio456", owner_id="holder123", assets=["nft789", "nft101"])
        print(portfolio)
    except ValidationError as e:
        print(e)

    try:
        market_data = MarketData(symbol="BTC", price=30000.00, volume=1000)
        print(market_data)
    except ValidationError as e:
        print(e)

    try:
        gpt5_response = GPT5Response(response="This is a response from GPT-5.")
        print(gpt5_response)
    except ValidationError as e:
        print(e)