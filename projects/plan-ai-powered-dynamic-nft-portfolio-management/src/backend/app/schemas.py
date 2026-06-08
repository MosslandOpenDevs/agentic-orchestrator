from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import config

class FieldValidator(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None

class AIModelData(BaseModel):
    timestamp: int = Field(default=None)
    data: dict = Field(default={})
    
    @config.json_encoders.to_json
    def to_json(self):
        return self.dict()

class AIModel(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    version: float = Field(default=1.0)
    data: AIModelData = Field(default=AIModelData())

    class Config:
        schema_extra = {
            "example": {
                "name": "MosslandOptimizerV1",
                "version": 1.5,
                "data": {"timestamp": 1678886400, "data": {"feature1": 0.5, "feature2": 0.8}}
            }
        }

class Position(BaseModel):
    id: int = Field(default=None)
    asset_symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(default=0.0, gt=0)
    entry_price: float = Field(default=0.0, gt=0)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "asset_symbol": "BTC",
                "quantity": 1.5,
                "entry_price": 30000.0
            }
        }

class Portfolio(BaseModel):
    id: int = Field(default=None)
    user_id: int = Field(default=None)
    positions: List[Position] = Field(default=[])
    
    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "user_id": 789,
                "positions": [
                    {
                        "id": 123,
                        "asset_symbol": "BTC",
                        "quantity": 1.5,
                        "entry_price": 30000.0
                    },
                    {
                        "id": 789,
                        "asset_symbol": "ETH",
                        "quantity": 2.0,
                        "entry_price": 1800.0
                    }
                ]
            }
        }

class User(BaseModel):
    id: int = Field(default=None)
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., email=True)
    nft_holdings: List[str] = Field(default=[])
    
    class Config:
        schema_extra = {
            "example": {
                "id": 101,
                "username": "mossland_user",
                "email": "mossland@example.com",
                "nft_holdings": ["mossland_nft_1", "mossland_nft_2"]
            }
        }

class CreateUser(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., email=True)
    nft_holdings: List[str] = Field(default=[])

class CreatePortfolio(BaseModel):
    user_id: int = Field(default=None)
    positions: List[Position] = Field(default=[])

class CreatePosition(BaseModel):
    asset_symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(default=0.0, gt=0)
    entry_price: float = Field(default=0.0, gt=0)

class CreateAIModel(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    version: float = Field(default=1.0)

class UpdateUser(BaseModel):
    id: int = Field(default=None)
    username: Optional[str] = None
    email: Optional[str] = None
    nft_holdings: Optional[List[str]] = None

class UpdatePortfolio(BaseModel):
    id: int = Field(default=None)
    user_id: int = Field(default=None)
    positions: Optional[List[Position]] = None

class UpdatePosition(BaseModel):
    id: int = Field(default=None)
    asset_symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(default=0.0, gt=0)
    entry_price: float = Field(default=0.0, gt=0)

class UpdateAIModel(BaseModel):
    id: int = Field(default=None)
    name: Optional[str] = None
    version: Optional[float] = None

class ResponseUser(BaseModel):
    id: int
    username: str
    email: str
    nft_holdings: List[str]

class ResponsePortfolio(BaseModel):
    id: int
    user_id: int
    positions: List[Position]

class ResponsePosition(BaseModel):
    id: int
    asset_symbol: str
    quantity: float
    entry_price: float

class ResponseAIModel(BaseModel):
    id: int
    name: str
    version: float