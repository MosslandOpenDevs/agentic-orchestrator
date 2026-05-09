from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional
from datetime import datetime

class FieldValidator:
    @validator('name')
    def name_must_not_be_empty(cls, value):
        if not value:
            raise ValueError('Name cannot be empty')
        return value

class BaseNFT(BaseModel):
    id: str = Field(..., description="Unique identifier for the NFT", config=ConfigDict(frozen=True))
    name: str = Field(..., description="Name of the NFT", FieldValidator())
    description: Optional[str] = None
    image_url: Optional[str] = None
    metadata_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateNFT(BaseNFT):
    pass

class UpdateNFT(BaseNFT):
    pass

class ResponseNFT(BaseNFT):
    pass

class BasePortfolioHolding(BaseModel):
    nft_id: str = Field(..., description="ID of the NFT being held")
    user_id: str = Field(..., description="ID of the user holding the NFT")
    quantity: int = Field(..., description="Number of NFTs held", gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreatePortfolioHolding(BasePortfolioHolding):
    pass

class UpdatePortfolioHolding(BasePortfolioHolding):
    pass

class ResponsePortfolioHolding(BasePortfolioHolding):
    pass

class BaseUser(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="User's username", FieldValidator())
    email: str = Field(..., description="User's email")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CreateUser(BaseUser):
    pass

class UpdateUser(BaseUser):
    pass

class ResponseUser(BaseUser):
    pass

class BaseRiskAssessment(BaseModel):
    id: str = Field(..., description="Unique identifier for the risk assessment")
    nft_id: str = Field(..., description="ID of the NFT being assessed")
    portfolio_id: Optional[str] = None
    risk_score: float = Field(..., description="Risk score of the NFT or portfolio", ge=0, le=100)
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None

class CreateRiskAssessment(BaseRiskAssessment):
    pass

class UpdateRiskAssessment(BaseRiskAssessment):
    pass

class ResponseRiskAssessment(BaseRiskAssessment):
    pass