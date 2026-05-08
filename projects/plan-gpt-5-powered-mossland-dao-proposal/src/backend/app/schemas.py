from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    """
    Configuration for Pydantic fields.
    """
    extra = 'forbid'
    frozen = True


class BaseNFT(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the NFT", config=FieldConfig)
    name: str = Field("Default Name", description="Name of the NFT", config=FieldConfig)
    symbol: Optional[str] = Field(None, description="Symbol of the NFT", config=FieldConfig)
    image_url: str = Field("Default Image URL", description="URL of the NFT image", config=FieldConfig)


class NFTCollection(BaseNFT):
    collection_name: str = Field("Default Collection", description="Name of the NFT collection", config=FieldConfig)
    contract_address: str = Field("Default Contract Address", description="Contract address of the NFT collection", config=FieldConfig)
    token_count: int = Field(0, description="Total number of tokens in the collection", config=FieldConfig)
    created_at: datetime = Field(datetime.now, description="Timestamp of collection creation", config=FieldConfig)

    model_config = ConfigDict(
        extra = 'forbid',
        frozen = True
    )

    @validator('token_count')
    def token_count_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Token count must be a positive integer")
        return v


class CreateNFTCollection(NFTCollection):
    pass


class UpdateNFTCollection(NFTCollection):
    pass


class NFTTransaction(BaseNFT):
    transaction_hash: str = Field("Default Transaction Hash", description="Transaction hash", config=FieldConfig)
    block_number: int = Field(0, description="Block number of the transaction", config=FieldConfig)
    token_id: int = Field(0, description="Token ID in the transaction", config=FieldConfig)
    collection_id: Optional[int] = Field(None, description="ID of the NFT collection", config=FieldConfig)
    price: float = Field(0.0, description="Transaction price", config=FieldConfig)

    model_config = ConfigDict(
        extra = 'forbid',
        frozen = True
    )


class CreateNFTTransaction(NFTTransaction):
    pass


class UpdateNFTTransaction(NFTTransaction):
    pass


class RiskAssessment(BaseNFT):
    score: float = Field(0.0, description="Risk score of the NFT", config=FieldConfig)
    risk_category: str = Field("Low Risk", description="Risk category of the NFT", config=FieldConfig)
    description: Optional[str] = Field(None, description="Description of the risk assessment", config=FieldConfig)

    model_config = ConfigDict(
        extra = 'forbid',
        frozen = True
    )


class CreateRiskAssessment(RiskAssessment):
    pass


class UpdateRiskAssessment(RiskAssessment):
    pass


class Portfolio(BaseNFT):
    portfolio_name: str = Field("Default Portfolio", description="Name of the portfolio", config=FieldConfig)
    nft_holdings: List[int] = Field([], description="List of NFT IDs held in the portfolio", config=FieldConfig)
    created_at: datetime = Field(datetime.now, description="Timestamp of portfolio creation", config=FieldConfig)

    model_config = ConfigDict(
        extra = 'forbid',
        frozen = True
    )

class CreatePortfolio(Portfolio):
    pass


class UpdatePortfolio(Portfolio):
    pass