from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from enum import Enum

class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class NFTHolder(BaseModel):
    id: str = Field(..., description="Unique identifier for the NFT holder", min_length=36)
    name: str = Field(..., description="Holder's name")
    wallet_address: str = Field(..., description="Holder's wallet address")
    creation_date: str = Field(..., description="Date the holder joined the system")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "0x1234567890abcdef1234567890abcdef12345678",
                "name": "Alice Smith",
                "wallet_address": "0xAbCdEfGhIjKlMnOpQrStUvWxYz",
                "creation_date": "2023-10-26T10:00:00Z"
            }
        }

class DeFiAsset(BaseModel):
    id: str = Field(..., description="Unique identifier for the DeFi asset", min_length=36)
    name: str = Field(..., description="Name of the DeFi asset")
    symbol: str = Field(..., description="Asset symbol")
    quantity: float = Field(..., description="Quantity of the asset held", gt=0)
    decimals: int = Field(..., description="Number of decimals for the asset", ge=0)
    contract_address: str = Field(..., description="Contract address of the asset")

    class Config:
        schema_extra = {
            "example": {
                "id": "0x2345678901abcd2345678901abcd2345678",
                "name": "Wrapped Bitcoin",
                "symbol": "WBTC",
                "quantity": 10.5,
                "decimals": 8,
                "contract_address": "0x..."
            }
        }

class RiskAssessment(BaseModel):
    id: str = Field(..., description="Unique identifier for the risk assessment", min_length=36)
    contract_address: str = Field(..., description="Contract address being assessed")
    vulnerability_type: str = Field(..., description="Type of vulnerability identified")
    severity: RiskSeverity = Field(..., description="Severity of the vulnerability", enum_values=RiskSeverity.__members__)
    description: str = Field(..., description="Detailed description of the vulnerability")
    recommendations: str = Field(..., description="Recommendations for remediation")

    class Config:
        schema_extra = {
            "example": {
                "id": "0x3456789012bcdef3456789012bcdef345678",
                "contract_address": "0x...",
                "vulnerability_type": "Reentrancy",
                "severity": "high",
                "description": "The contract is vulnerable to reentrancy attacks.",
                "recommendations": "Implement checks-effects-interactions pattern."
            }
        }

class Portfolio(BaseModel):
    id: str = Field(..., description="Unique identifier for the portfolio", min_length=36)
    nft_holder_id: str = Field(..., description="ID of the NFT holder owning the portfolio")
    name: str = Field(..., description="Name of the portfolio")
    assets: List[DeFiAsset] = Field(..., description="List of DeFi assets in the portfolio")

    class Config:
        schema_extra = {
            "example": {
                "id": "0x4567890123def4567890123def4567890",
                "nft_holder_id": "0x1234567890abcdef1234567890abcdef12345678",
                "name": "My DeFi Portfolio",
                "assets": [
                    {
                        "id": "0x2345678901abcd2345678901abcd2345678",
                        "name": "Wrapped Bitcoin",
                        "symbol": "WBTC",
                        "quantity": 10.5,
                        "decimals": 8,
                        "contract_address": "0x..."
                    },
                    {
                        "id": "0x5678901234ef5678901234ef56789012",
                        "name": "Ethereum",
                        "symbol": "ETH",
                        "quantity": 5.2,
                        "decimals": 18,
                        "contract_address": "0x..."
                    }
                ]
            }
        }