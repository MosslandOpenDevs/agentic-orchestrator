from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional
import datetime

class FieldValidator:
    @validator('nft_id')
    def nft_id_must_be_string(cls, value):
        if not isinstance(value, str):
            raise ValueError("nft_id must be a string")
        return value

    @validator('portfolio_id')
    def portfolio_id_must_be_string(cls, value):
        if not isinstance(value, str):
            raise ValueError("portfolio_id must be a string")
        return value

    @validator('user_id')
    def user_id_must_be_string(cls, value):
        if not isinstance(value, str):
            raise ValueError("user_id must be a string")
        return value

    @validator('market_data_id')
    def market_data_id_must_be_string(cls, value):
        if not isinstance(value, str):
            raise ValueError("market_data_id must be a string")
        return value

    @validator('risk_threshold_id')
    def risk_threshold_id_must_be_string(cls, value):
        if not isinstance(value, str):
            raise ValueError("risk_threshold_id must be a string")
        return value


class RiskThreshold(BaseModel):
    risk_threshold_id: str = Field(..., description="Unique identifier for the risk threshold", validator=FieldValidator.risk_threshold_id_must_be_string)
    name: str = Field("Conservative", description="Name of the risk threshold", example="Conservative")
    level: int = Field(1, description="Risk level (1-5)", ge=1, le=5, example=1)
    description: Optional[str] = None, description="Description of the risk threshold"

    class Config:
        schema_extra = {
            "example": {
                "risk_threshold_id": "risk_threshold_1",
                "name": "Moderate",
                "level": 3,
                "description": "A moderate risk threshold for users who are willing to take some risk."
            }
        }


class MarketData(BaseModel):
    market_data_id: str = Field(..., description="Unique identifier for the market data", validator=FieldValidator.market_data_id_must_be_string)
    nft_id: str = Field("mossland_1", description="ID of the NFT", example="mossland_1")
    price: float = Field(100.0, description="Current price of the NFT", gt=0, example=100.0)
    volume: int = Field(10, description="Trading volume", ge=0, example=10)
    timestamp: datetime.datetime = Field(datetime.datetime.now(), description="Timestamp of the data", example=datetime.datetime.now())

    class Config:
        schema_extra = {
            "example": {
                "market_data_id": "market_data_1",
                "nft_id": "mossland_1",
                "price": 110.0,
                "volume": 15,
                "timestamp": datetime.datetime.now()
            }
        }


class PortfolioHolding(BaseModel):
    portfolio_id: str = Field(..., description="Unique identifier for the portfolio", validator=FieldValidator.portfolio_id_must_be_string)
    nft_id: str = Field(..., description="ID of the NFT", validator=FieldValidator.nft_id_must_be_string)
    quantity: int = Field(1, description="Quantity of the NFT held", ge=0, example=1)
    purchase_price: float = Field(100.0, description="Price at which the NFT was purchased", gt=0, example=100.0)
    timestamp: datetime.datetime = Field(datetime.datetime.now(), description="Timestamp of the purchase", example=datetime.datetime.now())

    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "portfolio_1",
                "nft_id": "mossland_1",
                "quantity": 2,
                "purchase_price": 95.0,
                "timestamp": datetime.datetime.now()
            }
        }


class User(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user", validator=FieldValidator.user_id_must_be_string)
    username: str = Field("john.doe", description="Username of the user", example="john.doe")
    email: str = Field("john.doe@example.com", description="Email address of the user", example="john.doe@example.com")
    risk_threshold_id: str = Field("risk_threshold_1", description="ID of the user's risk threshold", validator=FieldValidator.risk_threshold_id_must_be_string)

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_1",
                "username": "jane.doe",
                "email": "jane.doe@example.com",
                "risk_threshold_id": "risk_threshold_1"
            }
        }


class NFT(BaseModel):
    nft_id: str = Field(..., description="Unique identifier for the NFT", validator=FieldValidator.nft_id_must_be_string)
    name: str = Field("Mossland 1", description="Name of the NFT", example="Mossland 1")
    description: Optional[str] = None, description="Description of the NFT"
    image_url: Optional[str] = None, description="URL of the NFT image"

    class Config:
        schema_extra = {
            "example": {
                "nft_id": "nft_1",
                "name": "Mossland 1",
                "description": "A beautiful Mossland NFT",
                "image_url": "https://example.com/mossland_1.png"
            }
        }


class CreateRiskThreshold(BaseModel):
    risk_threshold_id: str = Field(..., description="Unique identifier for the risk threshold", validator=FieldValidator.risk_threshold_id_must_be_string)
    name: str = Field("Conservative", description="Name of the risk threshold", example="Conservative")
    level: int = Field(1, description="Risk level (1-5)", ge=1, le=5, example=1)
    description: Optional[str] = None, description="Description of the risk threshold"

    class Config:
        schema_extra = {
            "example": {
                "risk_threshold_id": "risk_threshold_1",
                "name": "Moderate",
                "level": 3,
                "description": "A moderate risk threshold for users who are willing to take some risk."
            }
        }


class CreateMarketData(BaseModel):
    market_data_id: str = Field(..., description="Unique identifier for the market data", validator=FieldValidator.market_data_id_must_be_string)
    nft_id: str = Field("mossland_1", description="ID of the NFT", example="mossland_1")
    price: float = Field(100.0, description="Current price of the NFT", gt=0, example=100.0)
    volume: int = Field(10, description="Trading volume", ge=0, example=10)
    timestamp: datetime.datetime = Field(datetime.datetime.now(), description="Timestamp of the data", example=datetime.datetime.now())

    class Config:
        schema_extra = {
            "example": {
                "market_data_id": "market_data_1",
                "nft_id": "mossland_1",
                "price": 110.0,
                "volume": 15,
                "timestamp": datetime.datetime.now()
            }
        }


class CreatePortfolioHolding(BaseModel):
    portfolio_id: str = Field(..., description="Unique identifier for the portfolio", validator=FieldValidator.portfolio_id_must_be_string)
    nft_id: str = Field(..., description="ID of the NFT", validator=FieldValidator.nft_id_must_be_string)
    quantity: int = Field(1, description="Quantity of the NFT held", ge=0, example=1)
    purchase_price: float = Field(100.0, description="Price at which the NFT was purchased", gt=0, example=100.0)
    timestamp: datetime.datetime = Field(datetime.datetime.now(), description="Timestamp of the purchase", example=datetime.datetime.now())

    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "portfolio_1",
                "nft_id": "mossland_1",
                "quantity": 2,
                "purchase_price": 95.0,
                "timestamp": datetime.datetime.now()
            }
        }


class CreateUser(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user", validator=FieldValidator.user_id_must_be_string)
    username: str = Field("john.doe", description="Username of the user", example="john.doe")
    email: str = Field("john.doe@example.com", description="Email address of the user", example="john.doe@example.com")
    risk_threshold_id: str = Field("risk_threshold_1", description="ID of the user's risk threshold", validator=FieldValidator.risk_threshold_id_must_be_string)

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_1",
                "username": "jane.doe",
                "email": "jane.doe@example.com",
                "risk_threshold_id": "risk_threshold_1"
            }
        }


class CreateNFT(BaseModel):
    nft_id: str = Field(..., description="Unique identifier for the NFT", validator=FieldValidator.nft_id_must_be_string)
    name: str = Field("Mossland 1", description="Name of the NFT", example="Mossland 1")
    description: Optional[str] = None, description="Description of the NFT"
    image_url: Optional[str] = None, description="URL of the NFT image"

    class Config:
        schema_extra = {
            "example": {
                "nft_id": "nft_1",
                "name": "Mossland 1",
                "description": "A beautiful Mossland NFT",