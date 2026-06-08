from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic.validator import validator

class FieldConfig(ConfigDict):
    field_name: str
    default: any
    description: str
    example: any

class BaseNFTPosition(BaseModel):
    nft_id: str = Field(..., description="Unique identifier of the Mossland NFT", example="Mossland-123")
    quantity: int = Field(..., description="Number of NFTs held", example=10)
    protocol_id: str = Field(..., description="ID of the DeFi protocol holding the NFT", example="ProtocolA")

    @validator('quantity')
    def quantity_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("Quantity must be a positive integer")
        return value

class CreateNFTPosition(BaseNFTPosition):
    pass

class UpdateNFTPosition(BaseNFTPosition):
    pass

class ResponseNFTPosition(BaseNFTPosition):
    pass

class BaseRiskProfile(BaseModel):
    risk_tolerance: str = Field(..., description="User's risk tolerance (e.g., Conservative, Moderate, Aggressive)", example="Moderate")

    config = FieldConfig(field_name="risk_tolerance", default="Moderate", description="Default risk tolerance", example="Moderate")

class CreateRiskProfile(BaseRiskProfile):
    pass

class UpdateRiskProfile(BaseRiskProfile):
    pass

class ResponseRiskProfile(BaseRiskProfile):
    pass

class BaseDeFiProtocol(BaseModel):
    protocol_id: str = Field(..., description="Unique identifier of the DeFi protocol", example="ProtocolA")
    name: str = Field(..., description="Name of the DeFi protocol", example="Aave")
    supported_assets: list = Field(..., description="List of supported assets", example=["USDC", "DAI"])

    config = FieldConfig(field_name="protocol_id", default="ProtocolA", description="Default protocol ID", example="ProtocolA")

class CreateDeFiProtocol(BaseDeFiProtocol):
    pass

class UpdateDeFiProtocol(BaseDeFiProtocol):
    pass

class ResponseDeFiProtocol(BaseDeFiProtocol):
    pass

class BaseRebalancingStrategy(BaseModel):
    strategy_id: str = Field(..., description="Unique identifier of the rebalancing strategy", example="StrategyGPT5-1")
    name: str = Field(..., description="Name of the rebalancing strategy", example="GPT-5 Balanced")
    description: Optional[str] = Field(None, description="Description of the strategy", example="A balanced portfolio based on GPT-5 recommendations")
    suggested_allocation: dict = Field(..., description="Suggested asset allocation", example={"USDC": 0.5, "DAI": 0.5})

    config = FieldConfig(field_name="strategy_id", default="StrategyGPT5-1", description="Default strategy ID", example="StrategyGPT5-1")

class CreateRebalancingStrategy(BaseRebalancingStrategy):
    pass

class UpdateRebalancingStrategy(BaseRebalancingStrategy):
    pass

class ResponseRebalancingStrategy(BaseRebalancingStrategy):
    pass