from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class MarketData(Base):
    """
    Represents real-time and historical market data for Billions Network token and related assets.
    """
    __tablename__ = 'market_data'

    id = Column(String, primary_key=True)
    asset = Column(String)
    timestamp = Column(DateTime)
    price = Column(Float)
    volume = Column(Float)
    change = Column(Float)
    createdAt = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, server_default=datetime.utcnow(), server_onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<MarketData(id={self.id}, asset={self.asset}, timestamp={self.timestamp}, price={self.price})>"


class NFTPortfolio(Base):
    """
    Represents a user's NFT portfolio on the Billions Network.
    """
    __tablename__ = 'nft_portfolios'

    id = Column(String, primary_key=True)
    userId = Column(String)
    nftPositions = Column(JSON)
    riskProfile = Column(String)
    createdAt = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, server_default=datetime.utcnow(), server_onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<NFTPortfolio(id={self.id}, userId={self.userId}, nftPositions={self.nftPositions}, riskProfile={self.riskProfile})>"


class NFTPosition(Base):
    """
    Represents a single NFT position within an NFTPortfolio.
    """
    __tablename__ = 'nft_positions'

    id = Column(String, primary_key=True)
    nftAsset = Column(String)
    quantity = Column(Integer)
    entryPrice = Column(Float)
    currentPrice = Column(Float)
    portfolioId = Column(String, ForeignKey('nft_portfolios.id'))
    createdAt = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, server_default=datetime.utcnow(), server_onupdate=datetime.utcnow())

    __repr__ = back_populates('id', NFTPortfolio)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'portfolio' is None:
            raise ValueError("portfolio must be provided")