from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List

class FieldConfig(ConfigDict):
    schema_extra: dict = Field(default={})

class RWAAsset(BaseModel):
    id: str = Field(..., description="Unique identifier for the RWA asset", FieldConfig)
    name: str = Field(..., description="Name of the RWA asset", FieldConfig)
    asset_type: str = Field(..., description="Type of the RWA asset (e.g., Real Estate, Commodities)", FieldConfig)
    value: float = Field(..., description="Value of the RWA asset in USD", FieldConfig)
    blockchain_address: str = Field(..., description="Blockchain address associated with the asset", FieldConfig)
    quantity: int = Field(..., description="Quantity of the asset represented", FieldConfig)
    
    class Config:
        schema_extra: dict = Field(default={})


class Portfolio(BaseModel):
    id: str = Field(..., description="Unique identifier for the portfolio", FieldConfig)
    name: str = Field(..., description="Name of the portfolio", FieldConfig)
    agent_id: str = Field(..., description="ID of the GPT-5 Agent managing the portfolio", FieldConfig)
    assets: List[str] = Field(..., description="List of RWA asset IDs in the portfolio", FieldConfig)
    total_value: float = Field(..., description="Total value of the portfolio in USD", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})


class GPT5Agent(BaseModel):
    id: str = Field(..., description="Unique identifier for the GPT-5 Agent", FieldConfig)
    name: str = Field(..., description="Name of the GPT-5 Agent", FieldConfig)
    model_version: str = Field(..., description="Version of the GPT-5 model", FieldConfig)
    last_update: str = Field(..., description="Timestamp of the last agent update", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})


class NFTHolder(BaseModel):
    id: str = Field(..., description="Unique identifier for the NFT holder", FieldConfig)
    nft_id: str = Field(..., description="ID of the NFT held by the holder", FieldConfig)
    agent_id: str = Field(..., description="ID of the TerraForm agent managing the holder", FieldConfig)
    portfolio_id: Optional[str] = Field(None, description="ID of the portfolio the NFT holder belongs to", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})


# Create Schemas
class RWAAssetCreate(BaseModel):
    name: str = Field(..., description="Name of the RWA asset", FieldConfig)
    asset_type: str = Field(..., description="Type of the RWA asset (e.g., Real Estate, Commodities)", FieldConfig)
    value: float = Field(..., description="Value of the RWA asset in USD", FieldConfig)
    blockchain_address: str = Field(..., description="Blockchain address associated with the asset", FieldConfig)
    quantity: int = Field(..., description="Quantity of the asset represented", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class PortfolioCreate(BaseModel):
    agent_id: str = Field(..., description="ID of the GPT-5 Agent managing the portfolio", FieldConfig)
    assets: List[str] = Field(..., description="List of RWA asset IDs in the portfolio", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class GPT5AgentCreate(BaseModel):
    name: str = Field(..., description="Name of the GPT-5 Agent", FieldConfig)
    model_version: str = Field(..., description="Version of the GPT-5 model", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class NFTHolderCreate(BaseModel):
    nft_id: str = Field(..., description="ID of the NFT held by the holder", FieldConfig)
    agent_id: str = Field(..., description="ID of the TerraForm agent managing the holder", FieldConfig)
    portfolio_id: Optional[str] = Field(None, description="ID of the portfolio the NFT holder belongs to", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

# Update Schemas
class RWAAssetUpdate(BaseModel):
    value: Optional[float] = Field(None, description="Value of the RWA asset in USD", FieldConfig)
    
    class Config:
        schema_extra: dict = Field(default={})

class PortfolioUpdate(BaseModel):
    agent_id: Optional[str] = Field(None, description="ID of the GPT-5 Agent managing the portfolio", FieldConfig)
    assets: Optional[List[str]] = Field(None, description="List of RWA asset IDs in the portfolio", FieldConfig)
    total_value: Optional[float] = Field(None, description="Total value of the portfolio in USD", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class GPT5AgentUpdate(BaseModel):
    model_version: Optional[str] = Field(None, description="Version of the GPT-5 model", FieldConfig)
    last_update: Optional[str] = Field(None, description="Timestamp of the last agent update", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class NFTHolderUpdate(BaseModel):
    portfolio_id: Optional[str] = Field(None, description="ID of the portfolio the NFT holder belongs to", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

# Response Schemas
class RWAAssetResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the RWA asset", FieldConfig)
    name: str = Field(..., description="Name of the RWA asset", FieldConfig)
    asset_type: str = Field(..., description="Type of the RWA asset (e.g., Real Estate, Commodities)", FieldConfig)
    value: float = Field(..., description="Value of the RWA asset in USD", FieldConfig)
    blockchain_address: str = Field(..., description="Blockchain address associated with the asset", FieldConfig)
    quantity: int = Field(..., description="Quantity of the asset represented", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class PortfolioResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the portfolio", FieldConfig)
    name: str = Field(..., description="Name of the portfolio", FieldConfig)
    agent_id: str = Field(..., description="ID of the GPT-5 Agent managing the portfolio", FieldConfig)
    assets: List[str] = Field(..., description="List of RWA asset IDs in the portfolio", FieldConfig)
    total_value: float = Field(..., description="Total value of the portfolio in USD", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class GPT5AgentResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the GPT-5 Agent", FieldConfig)
    name: str = Field(..., description="Name of the GPT-5 Agent", FieldConfig)
    model_version: str = Field(..., description="Version of the GPT-5 model", FieldConfig)
    last_update: str = Field(..., description="Timestamp of the last agent update", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})

class NFTHolderResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the NFT holder", FieldConfig)
    nft_id: str = Field(..., description="ID of the NFT held by the holder", FieldConfig)
    agent_id: str = Field(..., description="ID of the TerraForm agent managing the holder", FieldConfig)
    portfolio_id: Optional[str] = Field(None, description="ID of the portfolio the NFT holder belongs to", FieldConfig)

    class Config:
        schema_extra: dict = Field(default={})