from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime

class FieldConfig(ConfigDict):
    schema_extra: dict = Field(
        default={},
        description="Additional schema information"
    )

class BaseSecurityToken(BaseModel):
    id: str = Field(..., description="Unique identifier for the security token",
                     field_validator=FieldValidator.str_id)
    security_ticker: str = Field(..., description="Ticker symbol of the security")
    token_id: str = Field(..., description="Unique token identifier")
    quantity: int = Field(..., description="Quantity of the security token held")
    asset_type: str = Field(..., description="Type of asset (e.g., stock, bond)")
    security_token_type: str = Field(..., description="Type of security token (e.g., ERC-20, BEP-20)")
    created_at: datetime = Field(default=datetime.utcnow, description="Timestamp of token creation")
    updated_at: datetime = Field(default=datetime.utcnow, description="Timestamp of last update")

    class Config:
        schema_extra = FieldConfig()

    def to_dict(self):
        result = super().to_dict()
        result['created_at'] = str(self.created_at)
        result['updated_at'] = str(self.updated_at)
        return result

class CreateSecurityToken(BaseSecurityToken):
    pass

class UpdateSecurityToken(BaseSecurityToken):
    pass

class ResponseSecurityToken(BaseSecurityToken):
    pass

class BasePortfolioPosition(BaseModel):
    id: str = Field(..., description="Unique identifier for the portfolio position",
                     field_validator=FieldValidator.str_id)
    user_id: str = Field(..., description="ID of the user holding the position")
    security_token_id: str = Field(..., description="ID of the security token held in the position")
    quantity: int = Field(..., description="Quantity of the security token held in the position")
    entry_price: float = Field(..., description="Price at which the position was entered")
    entry_date: datetime = Field(default=datetime.utcnow, description="Date when the position was entered")
    profit: float = Field(default=0.0, description="Profit/Loss from the position")
    stop_loss: float = Field(default=None, description="Stop-loss price for the position")
    take_profit: float = Field(default=None, description="Take-profit price for the position")

    class Config:
        schema_extra = FieldConfig()

    def to_dict(self):
        result = super().to_dict()
        result['entry_date'] = str(self.entry_date)
        result['stop_loss'] = str(self.stop_loss) if self.stop_loss is not None else None
        result['take_profit'] = str(self.take_profit) if self.take_profit is not None else None
        return result

class CreatePortfolioPosition(BasePortfolioPosition):
    pass

class UpdatePortfolioPosition(BasePortfolioPosition):
    pass

class ResponsePortfolioPosition(BasePortfolioPosition):
    pass

class BaseRebalancingRecommendation(BaseModel):
    id: str = Field(..., description="Unique identifier for the rebalancing recommendation",
                     field_validator=FieldValidator.str_id)
    user_id: str = Field(..., description="ID of the user receiving the recommendation")
    portfolio_id: str = Field(..., description="ID of the portfolio being rebalanced")
    recommendation_date: datetime = Field(default=datetime.utcnow, description="Date when the recommendation was generated")
    recommendation_type: str = Field(..., description="Type of rebalancing recommendation (e.g., 'aggressive', 'conservative')")
    recommended_assets: list = Field(default=[], description="List of assets recommended for rebalancing")
    recommended_quantities: dict = Field(default={}, description="Quantities of each asset recommended")

    class Config:
        schema_extra = FieldConfig()

    def to_dict(self):
        result = super().to_dict()
        result['recommendation_date'] = str(self.recommendation_date)
        return result

class CreateRebalancingRecommendation(BaseRebalancingRecommendation):
    pass

class UpdateRebalancingRecommendation(BaseRebalancingRecommendation):
    pass

class ResponseRebalancingRecommendation(BaseRebalancingRecommendation):
    pass

class BaseUser(BaseModel):
    id: str = Field(..., description="Unique identifier for the user",
                     field_validator=FieldValidator.str_id)
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    created_at: datetime = Field(default=datetime.utcnow, description="Timestamp of user creation")
    updated_at: datetime = Field(default=datetime.utcnow, description="Timestamp of last update")

    class Config:
        schema_extra = FieldConfig()

    def to_dict(self):
        result = super().to_dict()
        result['created_at'] = str(self.created_at)
        result['updated_at'] = str(self.updated_at)
        return result

class CreateUser(BaseUser):
    pass

class UpdateUser(BaseUser):
    pass

class ResponseUser(BaseUser):
    pass

class FieldValidator:
    @staticmethod
    def str_id(value):
        if not isinstance(value, str):
            raise ValueError("ID must be a string")
        return value