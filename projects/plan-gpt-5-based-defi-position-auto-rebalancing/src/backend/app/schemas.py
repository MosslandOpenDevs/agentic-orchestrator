from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic.validator import validator

class FieldConfig(ConfigDict):
    """
    Configuration for Pydantic fields.
    """
    yaml_fingerprint: Optional[str] = None
    extra: Optional[bool] = False


class RiskParameter(BaseModel):
    """
    Defines risk parameters for collateral management.
    """
    name: str = Field(..., description="Name of the risk parameter", field_config=FieldConfig)
    value: float = Field(..., description="Value of the risk parameter", field_config=FieldConfig)

    model_config = ConfigDict(example={
        "name": "LiquidityRatio",
        "value": 0.8
    })


class PriceFeedUpdate(BaseModel):
    """
    Records a price feed update from Chainlink.
    """
    symbol: str = Field(..., description="Symbol of the asset", field_config=FieldConfig)
    price: float = Field(..., description="Price of the asset", field_config=FieldConfig)
    oracle_id: str = Field(..., description="ID of the Chainlink oracle", field_config=FieldConfig)
    timestamp: float = Field(..., description="Timestamp of the update", field_config=FieldConfig)

    model_config = ConfigDict(example={
        "symbol": "ETH/USD",
        "price": 2000.0,
        "oracle_id": "chainlink-eth-usd",
        "timestamp": 1678886400.0
    })


class NFTCollateral(BaseModel):
    """
    Represents an NFT used as collateral, including its details and current ratio.
    """
    tokenId: str = Field(..., description="Token ID of the NFT", field_config=FieldConfig)
    nft_address: str = Field(..., description="Address of the NFT", field_config=FieldConfig)
    current_ratio: float = Field(..., description="Current ratio of the NFT", field_config=FieldConfig)
    underlying_asset: str = Field(..., description="Underlying asset of the NFT", field_config=FieldConfig)

    model_config = ConfigDict(example={
        "tokenId": "0x1234567890abcdef",
        "nft_address": "0xfedcba9876543210",
        "current_ratio": 0.95,
        "underlying_asset": "ETH"
    })


class CreateNFTCollateral(BaseModel):
    """
    Create request for NFTCollateral.
    """
    tokenId: str = Field(..., description="Token ID of the NFT", field_config=FieldConfig)
    nft_address: str = Field(..., description="Address of the NFT", field_config=FieldConfig)
    current_ratio: float = Field(..., description="Current ratio of the NFT", field_config=FieldConfig)
    underlying_asset: str = Field(..., description="Underlying asset of the NFT", field_config=FieldConfig)

    model_config = ConfigDict(example={
        "tokenId": "0x1234567890abcdef",
        "nft_address": "0xfedcba9876543210",
        "current_ratio": 0.95,
        "underlying_asset": "ETH"
    })


class UpdateNFTCollateral(BaseModel):
    """
    Update request for NFTCollateral.
    """
    tokenId: str = Field(..., description="Token ID of the NFT", field_config=FieldConfig)
    current_ratio: Optional[float] = Field(None, description="Current ratio of the NFT", field_config=FieldConfig)
    nft_address: Optional[str] = Field(None, description="Address of the NFT", field_config=FieldConfig)
    underlying_asset: Optional[str] = Field(None, description="Underlying asset of the NFT", field_config=FieldConfig)

    model_config = ConfigDict(example={
        "tokenId": "0x1234567890abcdef",
        "current_ratio": 0.98,
        "nft_address": "0xfedcba9876543210",
        "underlying_asset": "BTC"
    })


class ResponseNFTCollateral(BaseModel):
    """
    Response schema for NFTCollateral.
    """
    tokenId: str = Field(..., description="Token ID of the NFT", field_config=FieldConfig)
    nft_address: str = Field(..., description="Address of the NFT", field_config=FieldConfig)
    current_ratio: float = Field(..., description="Current ratio of the NFT", field_config=FieldConfig)
    underlying_asset: str = Field(..., description="Underlying asset of the NFT", field_config=FieldConfig)

    model_config = ConfigDict(example={
        "tokenId": "0x1234567890abcdef",
        "nft_address": "0xfedcba9876543210",
        "current_ratio": 0.95,
        "underlying_asset": "ETH"
    })