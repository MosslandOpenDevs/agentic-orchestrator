from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional

class FieldValidator:
    @validator('value')
    def value_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError('Value must be positive')
        return value

class SecurityToken(BaseModel):
    id: str = Field(..., description="Unique identifier for the security token", example="TOKEN123")
    name: str = Field(..., description="Name of the security token", example="Mossland Gold")
    symbol: str = Field(..., description="Trading symbol for the security token", example="MGS")
    price: float = Field(..., description="Current price of the security token", FieldValidator())
    quantity: int = Field(..., description="Number of tokens held", example=100)
    metadata: Optional[dict] = Field(None, description="Additional metadata about the token")
    config = ConfigDict(extra=None)

    class Create(BaseModel):
        id: str = Field(..., description="Unique identifier for the security token")
        name: str = Field(..., description="Name of the security token")
        symbol: str = Field(..., description="Trading symbol for the security token")
        price: float = Field(..., description="Current price of the security token", FieldValidator())
        quantity: int = Field(..., description="Number of tokens held")
        metadata: Optional[dict] = Field(None, description="Additional metadata about the token")

    class Update(BaseModel):
        id: str = Field(..., description="Unique identifier for the security token")
        name: Optional[str] = Field(None, description="Name of the security token")
        symbol: Optional[str] = Field(None, description="Trading symbol for the security token")
        price: Optional[float] = Field(None, description="Current price of the security token", FieldValidator())
        quantity: Optional[int] = Field(None, description="Number of tokens held")
        metadata: Optional[dict] = Field(None, description="Additional metadata about the token")

    class Response(BaseModel):
        id: str
        name: str
        symbol: str
        price: float
        quantity: int
        metadata: Optional[dict] = Field(None, description="Additional metadata about the token")

class PortfolioPosition(BaseModel):
    id: str = Field(..., description="Unique identifier for the portfolio position", example="POSS123")
    user_id: str = Field(..., description="ID of the user holding the position", example="USER456")
    security_token_id: str = Field(..., description="ID of the security token held", example="TOKEN123")
    quantity: int = Field(..., description="Number of tokens held in the position", FieldValidator())
    entry_price: float = Field(..., description="Price at which the position was entered", example=10.0)
    timestamp: int = Field(..., description="Timestamp of the position entry", example=1678886400)
    config = ConfigDict(extra=None)

    class Create(BaseModel):
        id: str = Field(..., description="Unique identifier for the portfolio position")
        user_id: str = Field(..., description="ID of the user holding the position")
        security_token_id: str = Field(..., description="ID of the security token held")
        quantity: int = Field(..., description="Number of tokens held in the position", FieldValidator())
        entry_price: float = Field(..., description="Price at which the position was entered", FieldValidator())
        timestamp: int = Field(..., description="Timestamp of the position entry")

    class Update(BaseModel):
        id: str = Field(..., description="Unique identifier for the portfolio position")
        user_id: str = Field(..., description="ID of the user holding the position")
        security_token_id: str = Field(..., description="ID of the security token held")
        quantity: Optional[int] = Field(None, description="Number of tokens held in the position", FieldValidator())
        entry_price: Optional[float] = Field(None, description="Price at which the position was entered", FieldValidator())
        timestamp: Optional[int] = Field(None, description="Timestamp of the position entry")

    class Response(BaseModel):
        id: str
        user_id: str
        security_token_id: str
        quantity: int
        entry_price: float
        timestamp: int

class User(BaseModel):
    id: str = Field(..., description="Unique identifier for the user", example="USER456")
    username: str = Field(..., description="Username for the user", example="john.doe")
    email: str = Field(..., description="Email address for the user", example="john.doe@example.com")
    balance: float = Field(..., description="User's balance in the Mossland Lending Protocol", example=1000.0)
    config = ConfigDict(extra=None)

    class Create(BaseModel):
        id: str = Field(..., description="Unique identifier for the user")
        username: str = Field(..., description="Username for the user")
        email: str = Field(..., description="Email address for the user")
        balance: float = Field(..., description="User's balance in the Mossland Lending Protocol", FieldValidator())

    class Update(BaseModel):
        id: str = Field(..., description="Unique identifier for the user")
        username: Optional[str] = Field(None, description="Username for the user")
        email: Optional[str] = Field(None, description="Email address for the user")
        balance: Optional[float] = Field(None, description="User's balance in the Mossland Lending Protocol", FieldValidator())

    class Response(BaseModel):
        id: str
        username: str
        email: str
        balance: float

class RebalancingRecommendation(BaseModel):
    id: str = Field(..., description="Unique identifier for the recommendation", example="REC789")
    user_id: str = Field(..., description="ID of the user the recommendation is for", example="USER456")
    timestamp: int = Field(..., description="Timestamp of when the recommendation was generated", example=1678886400)
    recommended_positions: List[dict] = Field([], description="List of recommended portfolio positions")
    synapse_ai_version: str = Field(..., description="Version of SynapseAI that generated the recommendation", example="1.2.3")
    config = ConfigDict(extra=None)

    class Create(BaseModel):
        id: str = Field(..., description="Unique identifier for the recommendation")
        user_id: str = Field(..., description="ID of the user the recommendation is for")
        timestamp: int = Field(..., description="Timestamp of when the recommendation was generated")
        recommended_positions: List[dict] = Field([], description="List of recommended portfolio positions")
        synapse_ai_version: str = Field(..., description="Version of SynapseAI that generated the recommendation")

    class Update(BaseModel):
        id: str = Field(..., description="Unique identifier for the recommendation")
        user_id: str = Field(..., description="ID of the user the recommendation is for")
        timestamp: Optional[int] = Field(None, description="Timestamp of when the recommendation was generated")
        recommended_positions: Optional[List[dict]] = Field(None, description="List of recommended portfolio positions")
        synapse_ai_version: Optional[str] = Field(None, description="Version of SynapseAI that generated the recommendation")

    class Response(BaseModel):
        id: str
        user_id: str
        timestamp: int
        recommended_positions: List[dict]
        synapse_ai_version: str