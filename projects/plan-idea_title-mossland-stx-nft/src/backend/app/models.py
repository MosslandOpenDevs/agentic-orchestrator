from sqlalchemy import Column, Integer, String, DateTime, UUID, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from datetime import datetime

Base = declarative_base()

class User(Base):
    """
    Represents a user of the platform.
    """
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    address = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(address='{self.address}', username='{self.username}')>"


class Portfolio(Base):
    """
    Represents a user's NFT portfolio.
    """
    __tablename__ = 'portfolios'

    id = Column(UUID, primary_key=True)
    userId = Column(String, nullable=False)
    name = Column(String, nullable=False)
    riskProfile = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Portfolio(userId='{self.userId}', name='{self.name}', riskProfile='{self.riskProfile}')>"

    back_populates = 'Portfolio'  # Back-reference to NFTFraction


class PriceFeed(Base):
    """
    Stores price data from external sources.
    """
    __tablename__ = 'price_feeds'

    id = Column(UUID, primary_key=True)
    asset = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PriceFeed(asset='{self.asset}', price={self.price}, timestamp={self.timestamp})>"


class NFTFraction(Base):
    """
    Represents a single fractionalized NFT token.
    """
    __tablename__ = 'nft_fractions'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, nullable=False)
    totalSupply = Column(Integer, nullable=False)
    owner = Column(String, nullable=False)
    fractionValue = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NFTFraction(tokenId='{self.tokenId}', totalSupply={self.totalSupply}, owner='{self.owner}')>"

    back_populates = 'NFTFraction'  # Back-reference to Portfolio