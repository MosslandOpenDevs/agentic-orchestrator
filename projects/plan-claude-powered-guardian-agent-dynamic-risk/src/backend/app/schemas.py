from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic.validator import validator

class FieldConfig(ConfigDict):
    """
    Custom ConfigDict for Field validation.
    """
    yaml_prefix = ''
    extra = False

class Portfolio(BaseModel):
    id: int = Field(..., description="Unique identifier for the portfolio", config=FieldConfig())
    name: str = Field(..., description="Name of the portfolio", config=FieldConfig())
    user_id: int = Field(..., description="ID of the user owning the portfolio", config=FieldConfig())
    assets: list = Field([], description="List of assets in the portfolio", config=FieldConfig())
    total_value: float = Field(0.0, description="Total value of the portfolio", config=FieldConfig())
    created_at: str = Field(..., description="Timestamp of portfolio creation", config=FieldConfig())
    updated_at: str = Field(..., description="Timestamp of portfolio last update", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PortfolioCreate(BaseModel):
    id: int = Field(..., description="Unique identifier for the portfolio", config=FieldConfig())
    name: str = Field(..., description="Name of the portfolio", config=FieldConfig())
    user_id: int = Field(..., description="ID of the user owning the portfolio", config=FieldConfig())
    assets: list = Field([], description="List of assets in the portfolio", config=FieldConfig())
    total_value: float = Field(0.0, description="Total value of the portfolio", config=FieldConfig())
    created_at: str = Field(..., description="Timestamp of portfolio creation", config=FieldConfig())
    updated_at: str = Field(..., description="Timestamp of portfolio last update", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PortfolioUpdate(BaseModel):
    id: int = Field(..., description="Unique identifier for the portfolio", config=FieldConfig())
    name: Optional[str] = Field(None, description="Name of the portfolio", config=FieldConfig())
    user_id: int = Field(..., description="ID of the user owning the portfolio", config=FieldConfig())
    assets: Optional[list] = Field(None, description="List of assets in the portfolio", config=FieldConfig())
    total_value: Optional[float] = Field(None, description="Total value of the portfolio", config=FieldConfig())
    created_at: str = Field(..., description="Timestamp of portfolio creation", config=FieldConfig())
    updated_at: str = Field(..., description="Timestamp of portfolio last update", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PortfolioResponse(BaseModel):
    id: int
    name: str
    user_id: int
    assets: list
    total_value: float
    created_at: str
    updated_at: str

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RiskProfile(BaseModel):
    id: int = Field(..., description="Unique identifier for the risk profile", config=FieldConfig())
    risk_tolerance: str = Field("moderate", description="Risk tolerance level (low, moderate, high)", config=FieldConfig())
    investment_horizon: int = Field(..., description="Investment horizon in years", config=FieldConfig())
    time_horizon_description: Optional[str] = Field(None, description="Description of the time horizon", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RiskProfileCreate(BaseModel):
    id: int = Field(..., description="Unique identifier for the risk profile", config=FieldConfig())
    risk_tolerance: str = Field("moderate", description="Risk tolerance level (low, moderate, high)", config=FieldConfig())
    investment_horizon: int = Field(..., description="Investment horizon in years", config=FieldConfig())
    time_horizon_description: Optional[str] = Field(None, description="Description of the time horizon", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RiskProfileUpdate(BaseModel):
    id: int = Field(..., description="Unique identifier for the risk profile", config=FieldConfig())
    risk_tolerance: Optional[str] = Field(None, description="Risk tolerance level (low, moderate, high)", config=FieldConfig())
    investment_horizon: int = Field(..., description="Investment horizon in years", config=FieldConfig())
    time_horizon_description: Optional[str] = Field(None, description="Description of the time horizon", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RiskProfileResponse(BaseModel):
    id: int
    risk_tolerance: str
    investment_horizon: int
    time_horizon_description: Optional[str]

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Strategy(BaseModel):
    id: int = Field(..., description="Unique identifier for the strategy", config=FieldConfig())
    name: str = Field(..., description="Name of the strategy", config=FieldConfig())
    portfolio_id: int = Field(..., description="ID of the portfolio the strategy belongs to", config=FieldConfig())
    gpt5_output: str = Field(..., description="GPT-5 generated strategy output", config=FieldConfig())
    created_at: str = Field(..., description="Timestamp of strategy creation", config=FieldConfig())
    updated_at: str = Field(..., description="Timestamp of strategy last update", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StrategyCreate(BaseModel):
    id: int = Field(..., description="Unique identifier for the strategy", config=FieldConfig())
    name: str = Field(..., description="Name of the strategy", config=FieldConfig())
    portfolio_id: int = Field(..., description="ID of the portfolio the strategy belongs to", config=FieldConfig())
    gpt5_output: str = Field(..., description="GPT-5 generated strategy output", config=FieldConfig())
    created_at: str = Field(..., description="Timestamp of strategy creation", config=FieldConfig())
    updated_at: str = Field(..., description="Timestamp of strategy last update", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StrategyUpdate(BaseModel):
    id: int = Field(..., description="Unique identifier for the strategy", config=FieldConfig())
    name: Optional[str] = Field(None, description="Name of the strategy", config=FieldConfig())
    portfolio_id: int = Field(..., description="ID of the portfolio the strategy belongs to", config=FieldConfig())
    gpt5_output: Optional[str] = Field(None, description="GPT-5 generated strategy output", config=FieldConfig())
    created_at: str = Field(..., description="Timestamp of strategy creation", config=FieldConfig())
    updated_at: str = Field(..., description="Timestamp of strategy last update", config=FieldConfig())

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StrategyResponse(BaseModel):
    id: int
    name: str
    portfolio_id: int
    gpt5_output: str
    created_at: str
    updated_at: str

    class Config:
        orm_mode = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }