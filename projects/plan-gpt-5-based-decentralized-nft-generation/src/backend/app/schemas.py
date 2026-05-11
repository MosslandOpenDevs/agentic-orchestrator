from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional

class BaseNFT(BaseModel):
    id: str = Field(..., description="Unique identifier for the NFT", alias="tokenId")
    name: str = Field(..., description="Name of the NFT")
    description: Optional[str] = Field(None, description="Description of the NFT")
    image_url: str = Field(..., description="URL of the NFT image")
    contract_address: str = Field(..., description="Contract address of the NFT")
    metadata: Optional[dict] = Field(None, description="NFT metadata")
    config = ConfigDict(extra=False)

    @validator('contract_address')
    def contract_address_must_start_with_0x(cls, value):
        if not value.startswith('0x'):
            raise ValueError('Contract address must start with "0x"')
        return value

class CreateNFT(BaseNFT):
    pass

class UpdateNFT(BaseNFT):
    pass

class ResponseNFT(BaseNFT):
    pass

class BasePortfolio(BaseModel):
    id: str = Field(..., description="Unique identifier for the portfolio", alias="portfolioId")
    user_id: str = Field(..., description="ID of the user owning the portfolio")
    name: str = Field(..., description="Name of the portfolio")
    description: Optional[str] = Field(None, description="Description of the portfolio")
    created_at: Optional[str] = Field(None, description="Timestamp of portfolio creation")
    updated_at: Optional[str] = Field(None, description="Timestamp of portfolio update")
    config = ConfigDict(extra=False)

class CreatePortfolio(BasePortfolio):
    pass

class UpdatePortfolio(BasePortfolio):
    pass

class ResponsePortfolio(BasePortfolio):
    pass

class BaseTradingSession(BaseModel):
    id: str = Field(..., description="Unique identifier for the trading session", alias="tradeId")
    portfolio_id: str = Field(..., description="ID of the portfolio involved in the trade")
    nft_id: str = Field(..., description="ID of the NFT involved in the trade")
    quantity: int = Field(..., description="Quantity of the NFT traded")
    price: float = Field(..., description="Price per NFT")
    timestamp: str = Field(..., description="Timestamp of the trade")
    status: str = Field("open", description="Status of the trade (open, completed, cancelled)")
    config = ConfigDict(extra=False)

    @validator('status')
    def status_must_be_one_of_options(cls, value):
        if value not in ["open", "completed", "cancelled"]:
            raise ValueError("Status must be one of: open, completed, cancelled")
        return value

class CreateTradingSession(BaseTradingSession):
    pass

class UpdateTradingSession(BaseTradingSession):
    pass

class ResponseTradingSession(BaseTradingSession):
    pass

class BaseUser(BaseModel):
    id: str = Field(..., description="Unique identifier for the user", alias="userId")
    username: str = Field(..., description="Username of the user")
    email: str = Field(..., description="Email address of the user")
    password: str = Field(..., description="Password of the user")
    created_at: Optional[str] = Field(None, description="Timestamp of user creation")
    updated_at: Optional[str] = Field(None, description="Timestamp of user update")
    config = ConfigDict(extra=False)

    @validator('username')
    def username_must_be_alphanumeric(cls, value):
        if not value.isalnum():
            raise ValueError("Username must be alphanumeric")
        return value

class CreateUser(BaseUser):
    pass

class UpdateUser(BaseUser):
    pass

class ResponseUser(BaseUser):
    pass