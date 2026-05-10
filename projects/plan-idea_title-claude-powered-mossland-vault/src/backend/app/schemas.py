from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class RiskScoreLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class NFTHolder(BaseModel):
    wallet_address: str = Field(..., description="Solana wallet address of the NFT holder", min_length=30, max_length=64)
    nft_id: str = Field(..., description="Unique identifier for the NFT")
    # Add more NFT details as needed

    class Config:
        schema_extra = {
            "example": {
                "wallet_address": "9999999999999999999999999999999