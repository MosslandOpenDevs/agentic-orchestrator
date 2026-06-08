from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4

Base = declarative_base()

class User(Base):
    """
    Represents a Mossland NFT holder.
    """
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    nft_id = Column(String, unique=True)
    createdAt = Column(DateTime, server_default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id='{self.id}', nft_id='{self.nft_id}')>"

class Portfolio(Base):
    """
    Represents a user's DeFi portfolio.
    """
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    userId = Column(String, nullable=False, index=True)
    risk_profile = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<Portfolio(id='{self.id}', userId='{self.userId}', risk_profile='{self.risk_profile}')>"

    
class Position(Base):
    """
    Represents a single asset holding within a portfolio.
    """
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    portfolioId = Column(String, nullable=False, index=True)
    asset_id = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<Position(id='{self.id}', portfolioId='{self.portfolioId}', asset_id='{self.asset_id}', quantity={self.quantity}, price={self.price})>"

    
class AIModelData(Base):
    """
    Stores data used for training and updating the AI model.
    """
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, server_default=datetime.utcnow)
    asset_data = Column(JSON, nullable=False)
    
    def __repr__(self):
        return f"<AIModelData(id='{self.id}', timestamp='{self.timestamp}', asset_data={self.asset_data})>"

    
class AIModel(Base):
    """
    The AI model used for portfolio optimization.
    """
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    model_version = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<AIModel(id='{self.id}', model_version='{self.model_version}')>"
from datetime import datetime