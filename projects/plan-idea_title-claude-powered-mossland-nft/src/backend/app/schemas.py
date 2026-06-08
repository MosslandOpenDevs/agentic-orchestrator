from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic.validator import validator

class FieldConfig(ConfigDict):
    field_name: str
    default: any
    description: str
    example: any

# Base schema for all entities
class BaseEntity(BaseModel):
    id: str
    created_at: str
    updated_at: str
    
    class Config:
        schema_extra = FieldConfig(
            field_name="id",
            default="placeholder",
            description="Unique identifier for the entity",
            example="12345"
        )
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# NFTCollection
class NFTCollection(BaseEntity):
    name: str
    symbol: str
    description: Optional[str] = None
    image_url: str
    
    class Config:
        schema_extra = FieldConfig(
            field_name="name",
            default="placeholder",
            description="Name of the NFT collection",
            example="Mossland"
        )
        schema_extra = FieldConfig(
            field_name="symbol",
            default="placeholder",
            description="Symbol of the NFT collection",
            example="MSL"
        )

# NFTHolding
class NFTHolding(BaseEntity):
    nft_id: str
    collection_id: str
    quantity: int = Field(gt=0, description="Number of NFTs held")
    
    class Config:
        schema_extra = FieldConfig(
            field_name="nft_id",
            default="placeholder",
            description="ID of the NFT",
            example="nft123"
        )
        schema_extra = FieldConfig(
            field_name="collection_id",
            default="placeholder",
            description="ID of the NFT collection",
            example="collection1"
        )
        schema_extra = FieldConfig(
            field_name="quantity",
            default=1,
            description="Number of NFTs held",
            example=1
        )

# Portfolio
class Portfolio(BaseEntity):
    user_id: str
    holdings: List[NFTHolding]
    
    class Config:
        schema_extra = FieldConfig(
            field_name="user_id",
            default="placeholder",
            description="ID of the user",
            example="user1"
        )

# PriceFeed
class PriceFeed(BaseEntity):
    currency: str
    price: float
    
    class Config:
        schema_extra = FieldConfig(
            field_name="currency",
            default="placeholder",
            description="Cryptocurrency currency",
            example="BTC"
        )
        schema_extra = FieldConfig(
            field_name="price",
            default=0.0,
            description="Price of the cryptocurrency",
            example=65000.0
        )

# User
class User(BaseEntity):
    username: str
    email: str
    
    class Config:
        schema_extra = FieldConfig(
            field_name="username",
            default="placeholder",
            description="Username of the user",
            example="verdant_agent"
        )
        schema_extra = FieldConfig(
            field_name="email",
            default="placeholder",
            description="Email of the user",
            example="verdant@example.com"
        )