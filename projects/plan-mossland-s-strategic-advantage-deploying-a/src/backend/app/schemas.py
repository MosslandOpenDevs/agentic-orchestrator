from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldValidator(BaseModel):
    """
    Base class for field validators.
    """
    pass

class SchemaConfig(ConfigDict):
    """
    Base class for schema configuration.
    """
    yaml = False
    json_encoders = {}

class NFT(BaseModel):
    """
    NFT - Represents a single NFT asset
    """
    id: int = Field(..., description="Unique identifier for the NFT", min=1)
    name: str = Field(..., description="Name of the NFT")
    description: Optional[str] = Field(None, description="Description of the NFT")
    image_url: str = Field(..., description="URL of the NFT image")
    metadata_url: Optional[str] = Field(None, description="URL of the NFT metadata")
    created_at: datetime = Field(datetime.utcnow(), description="Timestamp of NFT creation")
    
    schema_config = SchemaConfig()

    class Config:
        orm_mode = False


class User(BaseModel):
    """
    User - Represents a Mossland NFT holder
    """
    user_id: int = Field(..., description="Unique identifier for the user", min=1)
    username: str = Field(..., description="Username of the user")
    email: str = Field(..., description="Email address of the user")
    nft_id: int = Field(..., description="ID of the NFT held by the user")
    
    schema_config = SchemaConfig()

    class Config:
        orm_mode = False


class YieldFarmPosition(BaseModel):
    """
    YieldFarmPosition - Represents a position within a DeFi protocol for yield farming
    """
    position_id: int = Field(..., description="Unique identifier for the position", min=1)
    user_id: int = Field(..., description="ID of the user holding the position")
    farm_id: int = Field(..., description="ID of the yield farm")
    token_in: str = Field(..., description="Token in the position")
    token_out: str = Field(..., description="Token out of the position")
    amount_in: float = Field(..., description="Amount of token in the position")
    amount_out: float = Field(..., description="Amount of token out of the position")
    position_type: str = Field(..., description="Type of position (e.g., 'LP')", allowed_values=['LP', 'Single'])
    
    schema_config = SchemaConfig()

    class Config:
        orm_mode = False


class PriceFeed(BaseModel):
    """
    PriceFeed - Represents a price feed from an external source
    """
    feed_id: int = Field(..., description="Unique identifier for the price feed", min=1)
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTCUSD')")
    price: float = Field(..., description="Price of the asset")
    last_updated: datetime = Field(datetime.utcnow(), description="Timestamp of the last price update")
    
    schema_config = SchemaConfig()

    class Config:
        orm_mode = False