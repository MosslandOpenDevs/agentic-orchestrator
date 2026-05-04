from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic import ValidationError

class FieldValidator(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    value: int = Field(ge=1, le=100)


class Config:
    orm_mode = False


class NFTHolder(BaseModel):
    id: str = Field(..., description="Unique identifier for the NFT holder")
    name: str = Field(..., min_length=3, max_length=50)
    wallet_address: str = Field(..., description="User's wallet address")
    nft_id: str = Field(..., description="ID of the NFT held")
    created_at: int = Field(default=None, description="Timestamp of NFT holder creation")
    updated_at: int = Field(default=None, description="Timestamp of last update")
    
    
class MarketData(BaseModel):
    chainlink_price: float = Field(..., description="Price of Rain stablecoin from Chainlink")
    dune_analytics_volume: float = Field(..., description="24h trading volume on Rain")
    
    
class Portfolio(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    rain_balance: float = Field(..., description="User's Rain stablecoin balance")
    nft_holdings: list[NFTHolder] = Field(default_factory=[], description="List of NFTs held by the user")
    
    
class SmartContract(BaseModel):
    contract_address: str = Field(..., description="Address of the smart contract")
    interaction_type: str = Field(..., description="Type of interaction (e.g., 'mint', 'transfer')")
    timestamp: int = Field(..., description="Timestamp of the interaction")
    input_data: str = Field(..., description="Input data for the smart contract interaction")
    output_data: str = Field(..., description="Output data from the smart contract interaction")


# Example Usage and Validation
if __name__ == '__main__':
    try:
        holder = NFTHolder(id="holder123", name="Alice", wallet_address="0x...", nft_id="mossland1")
        print(holder)
    except ValidationError as e:
        print(e)

    try:
        portfolio = Portfolio(user_id="user456", rain_balance=100.0, nft_holdings=[NFTHolder(id="mossland1", name="Alice", wallet_address="0x...", nft_id="mossland1")])
        print(portfolio)
    except ValidationError as e:
        print(e)