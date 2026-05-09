from sqlalchemy import Column, Integer, String, Float, UUID, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from datetime import datetime

Base = declarative_base()

class RiskThreshold(Base):
    __tablename__ = 'risk_thresholds'

    id = Column(UUID, primary_key=True)
    thresholdId = Column(String, unique=True)
    riskLevel = Column(String)
    percentage = Column(Float)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RiskThreshold(id={self.id}, thresholdId={self.thresholdId}, riskLevel={self.riskLevel}, percentage={self.percentage})>"


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    userId = Column(String, unique=True)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, userId={self.userId})>"


class PortfolioHolding(Base):
    __tablename__ = 'portfolio_holdings'

    id = Column(UUID, primary_key=True)
    userId = Column(String, back_populates='portfolio_holdings')
    nftId = Column(String, back_populates='portfolio_holdings')
    quantity = Column(Integer)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PortfolioHolding(id={self.id}, userId={self.userId}, nftId={self.nftId}, quantity={self.quantity})>"


class NFT(Base):
    __tablename__ = 'nfts'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, unique=True)
    metadata = Column(String, nullable=True)
    valuation = Column(Float)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NFT(id={self.id}, tokenId={self.tokenId}, valuation={self.valuation})>"


class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, unique=True)
    price = Column(Float)
    volume = Column(Float)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MarketData(id={self.id}, tokenId={self.tokenId}, price={self.price}, volume={self.volume})>"