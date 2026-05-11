from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Represents a Mossland NFT holder or DeFi investor."""
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    nft_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __repr__ = lambda self: f"User(id='{self.id}', nft_id='{self.nft_id}')"


class Vault(Base):
    """Represents a user's automated Principal Token portfolio."""
    __tablename__ = 'vaults'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False)
    pt_balance = Column(Float, nullable=False)
    risk_profile = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __repr__ = lambda self: f"Vault(id='{self.id}', user_id='{self.user_id}', pt_balance={self.pt_balance})"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'user_id' not in kwargs:
            raise ValueError("user_id must be provided")
        if 'pt_balance' not in kwargs:
            raise ValueError("pt_balance must be provided")


class Asset(Base):
    """Represents a cryptocurrency asset within the vault."""
    __tablename__ = 'assets'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __repr__ = lambda self: f"Asset(id='{self.id}', name='{self.name}', symbol='{self.symbol}', price={self.price}, quantity={self.quantity})"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'name' not in kwargs:
            raise ValueError("name must be provided")
        if 'symbol' not in kwargs:
            raise ValueError("symbol must be provided")
        if 'price' not in kwargs:
            raise ValueError("price must be provided")
        if 'quantity' not in kwargs:
            raise ValueError("quantity must be provided")


class GPTResponse(Base):
    """Stores the output from the GPT-5 API."""
    __tablename__ = 'gpt_responses'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False)
    recommendation = Column(String, nullable=False)
    risk_assessment = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __repr__ = lambda self: f"GPTResponse(id='{self.id}', timestamp='{self.timestamp}', recommendation='{self.recommendation}', confidence_score={self.confidence_score})"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'timestamp' not in kwargs:
            raise ValueError("timestamp must be provided")
        if 'recommendation' not in kwargs:
            raise ValueError("recommendation must be provided")
        if 'confidence_score' not in kwargs:
            raise ValueError("confidence_score must be provided")


if __name__ == '__main__':
    Base.metadata.create_all(engine)

    # Example usage
    user1 = User(nft_id="nft123")
    vault1 = Vault(user_id="user1", pt_balance=100.0, risk_profile="Moderate")
    asset1 = Asset(name="PT", symbol="PT", price=10.0, quantity=50.0)
    gpt_response = GPTResponse(timestamp=datetime.utcnow(), recommendation="Buy PT", confidence_score=0.8)

    print(user1)
    print(vault1)
    print(asset1)
    print(gpt_response)