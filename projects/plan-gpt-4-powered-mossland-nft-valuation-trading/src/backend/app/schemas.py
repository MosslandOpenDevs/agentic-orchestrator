from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldValidator(BaseModel):
    """Base class for field validators."""
    value: any
    message: str

    class Config:
        orm_mode = False

class User(BaseModel):
    id: int = Field(default=None, description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    email: str = Field(..., regex="^[^@]+@[^@]+\.[^@]+$", description="User's email address")
    discord_id: Optional[int] = Field(default=None, description="User's Discord ID")
    created_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of user creation")
    updated_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of last update")
    
    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    email: str = Field(..., regex="^[^@]+@[^@]+\.[^@]+$", description="User's email address")
    discord_id: Optional[int] = Field(default=None, description="User's Discord ID")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="User's username")
    email: Optional[str] = Field(default=None, regex="^[^@]+@[^@]+\.[^@]+$", description="User's email address")
    discord_id: Optional[int] = Field(default=None, description="User's Discord ID")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp of user creation")
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp of last update")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    discord_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Portfolio(BaseModel):
    id: int = Field(default=None, description="Unique portfolio identifier")
    user_id: int = Field(..., description="Foreign key referencing the User")
    name: str = Field(..., min_length=3, max_length=100, description="Portfolio name")
    created_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of portfolio creation")
    updated_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of last update")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PortfolioCreate(BaseModel):
    user_id: int = Field(..., description="Foreign key referencing the User")
    name: str = Field(..., min_length=3, max_length=100, description="Portfolio name")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=100, description="Portfolio name")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp of portfolio creation")
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp of last update")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PortfolioResponse(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Position(BaseModel):
    id: int = Field(default=None, description="Unique position identifier")
    portfolio_id: int = Field(..., description="Foreign key referencing the Portfolio")
    asset_id: int = Field(..., description="Foreign key referencing the Asset")
    quantity: float = Field(..., gt=0, description="Quantity of the asset held")
    price: float = Field(..., gt=0, description="Price of the asset")
    created_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of position creation")
    updated_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of last update")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PositionCreate(BaseModel):
    portfolio_id: int = Field(..., description="Foreign key referencing the Portfolio")
    asset_id: int = Field(..., description="Foreign key referencing the Asset")
    quantity: float = Field(..., gt=0, description="Quantity of the asset held")
    price: float = Field(..., gt=0, description="Price of the asset")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PositionUpdate(BaseModel):
    quantity: Optional[float] = Field(default=None, gt=0, description="Quantity of the asset held")
    price: Optional[float] = Field(default=None, gt=0, description="Price of the asset")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp of position creation")
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp of last update")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PositionResponse(BaseModel):
    id: int
    portfolio_id: int
    asset_id: int
    quantity: float
    price: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AIModel(BaseModel):
    id: int = Field(default=None, description="Unique AI model identifier")
    name: str = Field(..., min_length=3, max_length=100, description="AI model name")
    algorithm: str = Field(..., description="AI model algorithm")
    parameters: dict = Field(default={}, description="AI model parameters")
    created_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of AI model creation")
    updated_at: datetime = Field(default=datetime.utcnow(), description="Timestamp of last update")

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }