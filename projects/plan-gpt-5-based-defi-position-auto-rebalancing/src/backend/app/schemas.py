from pydantic import BaseModel, Field
from typing import Optional
from pydantic import Field

class FieldValidator(BaseModel):
    pass

class NFTPosition(BaseModel):
    nft_id: str = Field(..., description="Unique identifier of the NFT", min_length=3)
    quantity: int = Field(..., description="Number of NFTs held", gt=0)
    efi_balance: float = Field(..., description="Amount of EFI held associated with this position", gt=0)
    defi_interactions: list[str] = Field(default=[], description="List of DeFi interactions associated with this position")
    
    class Config:
        schema_extra = {
            "example": {
                "nft_id": "0x1234567890abcdef",
                "quantity": 10,
                "efi_balance": 100.50,
                "defi_interactions": ["staking", "lending"]
            }
        }


class RiskProfile(BaseModel):
    risk_tolerance: str = Field(..., description="User's risk tolerance (low, medium, high)", enum=['low', 'medium', 'high'])
    investment_horizon: int = Field(..., description="User's investment horizon in years", gt=0)
    financial_goals: list[str] = Field(default=[], description="User's financial goals")

    class Config:
        schema_extra = {
            "example": {
                "risk_tolerance": "medium",
                "investment_horizon": 5,
                "financial_goals": ["retirement", "wealth accumulation"]
            }
        }


class MarketData(BaseModel):
    asset_id: str = Field(..., description="Unique identifier of the DeFi asset")
    price: float = Field(..., description="Current price of the asset", gt=0)
    volume: float = Field(..., description="Trading volume of the asset", gt=0)
    
    class Config:
        schema_extra = {
            "example": {
                "asset_id": "ETH",
                "price": 3000.75,
                "volume": 100.20
            }
        }

class NFTPositionCreate(BaseModel):
    nft_id: str = Field(..., description="Unique identifier of the NFT", min_length=3)
    quantity: int = Field(..., description="Number of NFTs held", gt=0)
    efi_balance: float = Field(..., description="Amount of EFI held associated with this position", gt=0)
    defi_interactions: list[str] = Field(default=[], description="List of DeFi interactions associated with this position")

    class Config:
        schema_extra = {
            "example": {
                "nft_id": "0x1234567890abcdef",
                "quantity": 5,
                "efi_balance": 50.00,
                "defi_interactions": ["staking"]
            }
        }


class NFTPositionUpdate(BaseModel):
    nft_id: str = Field(..., description="Unique identifier of the NFT", min_length=3)
    quantity: Optional[int] = Field(default=None, description="Number of NFTs held", gt=0)
    efi_balance: Optional[float] = Field(default=None, description="Amount of EFI held associated with this position", gt=0)
    defi_interactions: Optional[list[str]] = Field(default=[], description="List of DeFi interactions associated with this position")

    class Config:
        schema_extra = {
            "example": {
                "nft_id": "0x1234567890abcdef",
                "quantity": 10,
                "efi_balance": 150.00,
                "defi_interactions": ["lending", "yield farming"]
            }
        }


class NFTPositionResponse(BaseModel):
    nft_id: str
    quantity: int
    efi_balance: float
    defi_interactions: list[str]

    class Config:
        schema_extra = {
            "example": {
                "nft_id": "0x1234567890abcdef",
                "quantity": 10,
                "efi_balance": 150.00,
                "defi_interactions": ["lending", "yield farming"]
            }
        }