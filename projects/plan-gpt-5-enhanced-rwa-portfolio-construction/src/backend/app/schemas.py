from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    yaml_fingerprint: Optional[str] = None

class RWAPortfolioBase(BaseModel):
    id: Optional[int] = Field(None, FieldConfig(yaml_fingerprint="RWAPortfolioBase"))
    name: str
    description: str
    created_at: datetime = Field(default=datetime.utcnow, FieldConfig(yaml_fingerprint="RWAPortfolioBase"))
    updated_at: datetime = Field(default=datetime.utcnow, FieldConfig(yaml_fingerprint="RWAPortfolioBase"))

class RWAPortfolioCreate(RWAPortfolioBase):
    pass

class RWAPortfolioUpdate(RWAPortfolioBase):
    pass

class RWAPortfolioResponse(RWAPortfolioBase):
    pass


class RWAAssetBase(BaseModel):
    id: Optional[int] = Field(None, FieldConfig(yaml_fingerprint="RWAAssetBase"))
    portfolio_id: int
    token_name: str
    token_symbol: str
    token_decimals: int = Field(0, FieldConfig(yaml_fingerprint="RWAAssetBase"))
    created_at: datetime = Field(default=datetime.utcnow, FieldConfig(yaml_fingerprint="RWAAssetBase"))
    updated_at: datetime = Field(default=datetime.utcnow, FieldConfig(yaml_fingerprint="RWAAssetBase"))

class RWAAssetCreate(RWAAssetBase):
    pass

class RWAAssetUpdate(RWAAssetBase):
    pass

class RWAAssetResponse(RWAAssetBase):
    pass


class GPT5AgentBase(BaseModel):
    id: Optional[int] = Field(None, FieldConfig(yaml_fingerprint="GPT5AgentBase"))
    name: str
    model_name: str = Field("GPT-5", FieldConfig(yaml_fingerprint="GPT5AgentBase"))
    created_at: datetime = Field(default=datetime.utcnow, FieldConfig(yaml_fingerprint="GPT5AgentBase"))
    updated_at: datetime = Field(default=datetime.utcnow, FieldConfig(yaml_fingerprint="GPT5AgentBase"))

class GPT5AgentCreate(GPT5AgentBase):
    pass

class GPT5AgentUpdate(GPT5AgentBase):
    pass

class GPT5AgentResponse(GPT5AgentBase):
    pass