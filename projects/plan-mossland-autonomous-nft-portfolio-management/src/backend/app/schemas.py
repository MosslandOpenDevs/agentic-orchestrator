from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    """
    Config for Pydantic fields, including default values and validation.
    """
    extra = False
    yaml = False


class RiskParameter(BaseModel):
    """
    Defines the risk profile for a portfolio.
    """
    risk_tolerance: str = Field(
        "moderate",
        FieldConfig(),
        choices=["low", "moderate", "high"],
    )
    max_drawdown: float = Field(
        0.05,
        FieldConfig(),
        ge=0.0,
        le=0.99,
    )
    investment_horizon: str = Field(
        "long-term",
        FieldConfig(),
        choices=["short-term", "medium-term", "long-term"],
    )


class PerformanceData(BaseModel):
    """
    Stores historical performance data for a portfolio.
    """
    start_date: datetime = Field(
        datetime(2023, 1, 1),
        FieldConfig(),
    )
    end_date: datetime = Field(
        datetime.now(),
        FieldConfig(),
    )
    return: float = Field(0.0, FieldConfig(), gt=-1.0)
    volatility: float = Field(0.1, FieldConfig(), gt=0.0)


class PortfolioPosition(BaseModel):
    """
    Represents a single asset held within a portfolio.
    """
    asset_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")
    quantity: int = Field(
        100,
        FieldConfig(),
        ge=0,
    )
    price: float = Field(
        100.0,
        FieldConfig(),
        ge=0.0,
    )
    portfolio_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")


class NFTHolder(BaseModel):
    """
    Represents a Mossland NFT holder within the DeFi ecosystem.
    """
    nft_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")
    wallet_address: str = Field(
        "0x...",
        FieldConfig(),
        regex=r"^(0x[a-zA-Z0-9]+)$",
    )
    name: Optional[str] = Field(None, FieldConfig())
    creation_date: datetime = Field(
        datetime.now(),
        FieldConfig(),
    )


class CreateNFTHolder(BaseModel):
    """
    Create request for NFTHolder
    """
    nft_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")
    wallet_address: str = Field(
        "0x...",
        FieldConfig(),
        regex=r"^(0x[a-zA-Z0-9]+)$",
    )
    name: Optional[str] = Field(None, FieldConfig())


class CreatePortfolioPosition(BaseModel):
    """
    Create request for PortfolioPosition
    """
    asset_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")
    quantity: int = Field(
        100,
        FieldConfig(),
        ge=0,
    )
    price: float = Field(
        100.0,
        FieldConfig(),
        ge=0.0,
    )
    portfolio_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")


class CreateRiskParameter(BaseModel):
    """
    Create request for RiskParameter
    """
    risk_tolerance: str = Field(
        "moderate",
        FieldConfig(),
        choices=["low", "moderate", "high"],
    )
    max_drawdown: float = Field(
        0.05,
        FieldConfig(),
        ge=0.0,
        le=0.99,
    )
    investment_horizon: str = Field(
        "long-term",
        FieldConfig(),
        choices=["short-term", "medium-term", "long-term"],
    )


class CreatePerformanceData(BaseModel):
    """
    Create request for PerformanceData
    """
    start_date: datetime = Field(
        datetime(2023, 1, 1),
        FieldConfig(),
    )
    end_date: datetime = Field(
        datetime.now(),
        FieldConfig(),
    )
    return: float = Field(0.0, FieldConfig(), gt=-1.0)
    volatility: float = Field(0.1, FieldConfig(), gt=0.0)


class UpdateNFTHolder(BaseModel):
    """
    Update request for NFTHolder
    """
    nft_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")
    wallet_address: str = Field(
        "0x...",
        FieldConfig(),
        regex=r"^(0x[a-zA-Z0-9]+)$",
    )
    name: Optional[str] = Field(None, FieldConfig())


class UpdatePortfolioPosition(BaseModel):
    """
    Update request for PortfolioPosition
    """
    asset_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")
    quantity: int = Field(
        100,
        FieldConfig(),
        ge=0,
    )
    price: float = Field(
        100.0,
        FieldConfig(),
        ge=0.0,
    )
    portfolio_id: str = Field(..., FieldConfig(), regex="^[a-zA-Z0-9-]+")


class UpdateRiskParameter(BaseModel):
    """
    Update request for RiskParameter
    """
    risk_tolerance: str = Field(
        "moderate",
        FieldConfig(),
        choices=["low", "moderate", "high"],
    )
    max_drawdown: float = Field(
        0.05,
        FieldConfig(),
        ge=0.0,
        le=0.99,
    )
    investment_horizon: str = Field(
        "long-term",
        FieldConfig(),
        choices=["short-term", "medium-term", "long-term"],
    )


class UpdatePerformanceData(BaseModel):
    """
    Update request for PerformanceData
    """
    start_date: datetime = Field(
        datetime(2023, 1, 1),
        FieldConfig(),
    )
    end_date: datetime = Field(
        datetime.now(),
        FieldConfig(),
    )
    return: float = Field(0.0, FieldConfig(), gt=-1.0)
    volatility: float = Field(0.1, FieldConfig(), gt=0.0)


class ResponseNFTHolder(BaseModel):
    """
    Response schema for NFTHolder
    """
    nft_id: str
    wallet_address: str
    name: Optional[str]
    creation_date: datetime


class ResponsePortfolioPosition(BaseModel):
    """
    Response schema for PortfolioPosition
    """
    asset_id: str
    quantity: int
    price: float
    portfolio_id: str


class ResponseRiskParameter(BaseModel):
    """
    Response schema for RiskParameter
    """
    risk_tolerance: str
    max_drawdown: float
    investment_horizon: str


class ResponsePerformanceData(BaseModel):
    """
    Response schema for PerformanceData
    """
    start_date: datetime
    end_date: datetime
    return: float
    volatility: float