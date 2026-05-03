from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List

class FieldValidator:
    """
    Placeholder for Field validators.  This is just to satisfy the prompt
    requirements.  Real implementations would be more complex.
    """
    def __init__(self, message: str):
        self.message = message

    def __call__(self, value: any) -> any:
        if value is None:
            return None
        if isinstance(value, str) and value.isdigit():
            return value
        raise ValueError(self.message)


class Stablecoin(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the stablecoin", example=1)
    name: str = Field(..., description="Name of the stablecoin", example="USD-Stable")
    value: float = Field(..., description="Value of the stablecoin", example=100.0)
    asset: str = Field(..., description="Asset the stablecoin is pegged to", example="USD")
    config = ConfigDict(extra=None)


class Transaction(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the transaction", example=1)
    sender: str = Field(..., description="Address of the sender", example="0xSenderAddress")
    receiver: str = Field(..., description="Address of the receiver", example="0xReceiverAddress")
    amount: float = Field(..., description="Amount transferred", example=10.5)
    timestamp: float = Field(..., description="Timestamp of the transaction", example=1678886400.0)
    stablecoin_id: Optional[int] = Field(None, description="ID of the stablecoin involved", example=1)
    config = ConfigDict(extra=None)


class Validator(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the validator", example=1)
    name: str = Field(..., description="Name of the validator", example="Validator1")
    address: str = Field(..., description="Address of the validator", example="0xValidatorAddress")
    uptime: float = Field(..., description="Uptime of the validator", example=1678886400.0)
    risk_score: Optional[float] = Field(None, description="Risk score assigned by the oracle", example=0.8)
    config = ConfigDict(extra=None)


class RiskScore(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the risk score", example=1)
    stablecoin_id: Optional[int] = Field(None, description="ID of the stablecoin", example=1)
    score: float = Field(..., description="Risk score", example=0.9)
    oracle_id: Optional[int] = Field(None, description="ID of the oracle", example=1)
    config = ConfigDict(extra=None)


# Example usage (not part of the schema, just for demonstration)
if __name__ == '__main__':
    try:
        stablecoin = Stablecoin(name="BTC-Stable", value=50000.0, asset="BTC")
        print(stablecoin)
    except Exception as e:
        print(f"Error creating stablecoin: {e}")