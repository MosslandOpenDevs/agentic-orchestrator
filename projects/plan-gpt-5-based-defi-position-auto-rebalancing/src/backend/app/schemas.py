from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic.validator import validator

class FieldConfig(ConfigDict):
    """
    Configuration for Pydantic fields.
    """
    extra = False
    yaml = False

class BaseNFTPosition(BaseModel):
    """
    Base schema for NFTPosition entities.
    """
    nft_id: str = Field(..., description="Unique identifier for the NFT", config=FieldConfig)
    holdings: Optional[dict] = Field(None, description="NFT holdings details")
    decentralized_finance_allocations: Optional[dict] = Field(None, description="DeFi protocol allocations")


class CreateNFTPosition(BaseNFTPosition):
    """
    Create schema for NFTPosition entities.
    """
    pass


class UpdateNFTPosition(BaseNFTPosition):
    """
    Update schema for NFTPosition entities.
    """
    pass


class ResponseNFTPosition(BaseNFTPosition):
    """
    Response schema for NFTPosition entities.
    """
    pass


class RiskProfile(BaseModel):
    """
    Base schema for RiskProfile entities.
    """
    risk_tolerance: str = Field(..., description="User's risk tolerance level (e.g., Conservative, Moderate, Aggressive)", config=FieldConfig)
    investment_horizon: Optional[int] = Field(None, description="User's investment horizon in years", config=FieldConfig)


class CreateRiskProfile(RiskProfile):
    """
    Create schema for RiskProfile entities.
    """
    pass


class UpdateRiskProfile(RiskProfile):
    """
    Update schema for RiskProfile entities.
    """
    pass


class ResponseRiskProfile(RiskProfile):
    """
    Response schema for RiskProfile entities.
    """
    pass


class MarketData(BaseModel):
    """
    Base schema for MarketData entities.
    """
    asset_id: str = Field(..., description="Unique identifier for the DeFi asset", config=FieldConfig)
    price: float = Field(..., description="Current price of the asset", config=FieldConfig)
    volume: Optional[float] = Field(None, description="Trading volume of the asset", config=FieldConfig)


class CreateMarketData(MarketData):
    """
    Create schema for MarketData entities.
    """
    pass


class UpdateMarketData(MarketData):
    """
    Update schema for MarketData entities.
    """
    pass


class ResponseMarketData(MarketData):
    """
    Response schema for MarketData entities.
    """
    pass