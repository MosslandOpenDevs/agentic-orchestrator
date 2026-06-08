from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import validator

class FieldValidator:
    @validator('name')
    def name_must_not_be_empty(cls, value):
        if not value:
            raise ValueError('Name cannot be empty')
        return value

class AIModel(BaseModel):
    id: int = Field(..., description="Unique identifier for the AI model", example=1)
    name: str = Field('', description="Name of the AI model", FieldValidator())
    version: str = Field('1.0', description="Version of the AI model", example="1.0")
    parameters: dict = Field({}, description="Model parameters", example={'learning_rate': 0.01})
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Mossland Optimizer",
                "version": "1.0",
                "parameters": {"learning_rate": 0.01}
            }
        }


class User(BaseModel):
    id: int = Field(..., description="Unique identifier for the user", example=1)
    username: str = Field('', description="User's username", FieldValidator())
    email: str = Field('', description="User's email address", example="user@example.com")
    nft_address: str = Field('', description="User's Mossland NFT address", example="0x...")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "username": "mossland_user",
                "email": "user@example.com",
                "nft_address": "0x..."
            }
        }


class Portfolio(BaseModel):
    id: int = Field(..., description="Unique identifier for the portfolio", example=1)
    user_id: int = Field(..., description="Foreign key referencing the User", FieldValidator())
    name: str = Field('', description="Name of the portfolio", example="My DeFi Portfolio")
    total_value: float = Field(0.0, description="Total value of the portfolio", example=1000.0)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "name": "My DeFi Portfolio",
                "total_value": 1000.0
            }
        }


class Position(BaseModel):
    id: int = Field(..., description="Unique identifier for the position", example=1)
    portfolio_id: int = Field(..., description="Foreign key referencing the Portfolio", FieldValidator())
    asset_symbol: str = Field('', description="Symbol of the asset", example="BTC")
    quantity: float = Field(0.0, description="Quantity of the asset held", example=0.5)
    price: float = Field(0.0, description="Current price of the asset", example=30000.0)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "portfolio_id": 1,
                "asset_symbol": "BTC",
                "quantity": 0.5,
                "price": 30000.0
            }
        }

class CreateUser(BaseModel):
    username: str = Field('', description="User's username", FieldValidator())
    email: str = Field('', description="User's email address", example="user@example.com")
    nft_address: str = Field('', description="User's Mossland NFT address", example="0x...")

class CreatePortfolio(BaseModel):
    user_id: int = Field(..., description="Foreign key referencing the User", FieldValidator())
    name: str = Field('', description="Name of the portfolio", example="My DeFi Portfolio")
    total_value: float = Field(0.0, description="Total value of the portfolio", example=1000.0)

class CreatePosition(BaseModel):
    portfolio_id: int = Field(..., description="Foreign key referencing the Portfolio", FieldValidator())
    asset_symbol: str = Field('', description="Symbol of the asset", example="BTC")
    quantity: float = Field(0.0, description="Quantity of the asset held", example=0.5)
    price: float = Field(0.0, description="Current price of the asset", example=30000.0)

class UpdateUser(BaseModel):
    id: int = Field(..., description="Unique identifier for the user", example=1)
    username: Optional[str] = Field('', description="User's username", FieldValidator())
    email: Optional[str] = Field('', description="User's email address", example="user@example.com")
    nft_address: Optional[str] = Field('', description="User's Mossland NFT address", example="0x...")

class UpdatePortfolio(BaseModel):
    id: int = Field(..., description="Unique identifier for the portfolio", example=1)
    user_id: int = Field(..., description="Foreign key referencing the User", FieldValidator())
    name: Optional[str] = Field('', description="Name of the portfolio", example="My DeFi Portfolio")
    total_value: Optional[float] = Field(0.0, description="Total value of the portfolio", example=1000.0)

class UpdatePosition(BaseModel):
    id: int = Field(..., description="Unique identifier for the position", example=1)
    portfolio_id: int = Field(..., description="Foreign key referencing the Portfolio", FieldValidator())
    asset_symbol: Optional[str] = Field('', description="Symbol of the asset", example="BTC")
    quantity: Optional[float] = Field(0.0, description="Quantity of the asset held", example=0.5)
    price: Optional[float] = Field(0.0, description="Current price of the asset", example=30000.0)

class ResponseUser(BaseModel):
    id: int
    username: str
    email: str
    nft_address: str

class ResponsePortfolio(BaseModel):
    id: int
    user_id: int
    name: str
    total_value: float

class ResponsePosition(BaseModel):
    id: int
    portfolio_id: int
    asset_symbol: str
    quantity: float
    price: float