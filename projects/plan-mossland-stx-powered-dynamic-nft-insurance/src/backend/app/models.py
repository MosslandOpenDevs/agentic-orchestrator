from sqlalchemy import Column, Integer, UUID, DateTime, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import back_populates
import uuid

Base = declarative_base()

class User(Base):
    """
    Represents a user within the Mossland ecosystem.
    """
    __tablename__ = 'users'

    id = Column(UUID, default=uuid.uuid4, primary_key=True)
    address = Column(String, nullable=False, unique=True)
    riskProfile = Column(String)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updatedAt = Column(DateTime, server_default=DateTime.utcnow(), onupdate=DateTime.utcnow())

    def __repr__(self):
        return f"<User(id={self.id}, address={self.address})>"


class PriceFeed(Base):
    """
    Stores price data from external sources.
    """
    __tablename__ = 'price_feeds'

    id = Column(UUID, default=uuid.uuid4, primary_key=True)
    assetAddress = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updatedAt = Column(DateTime, server_default=DateTime.utcnow(), onupdate=DateTime.utcnow())

    def __repr__(self):
        return f"<PriceFeed(id={self.id}, assetAddress={self.assetAddress}, price={self.price})>"


class NFTFraction(Base):
    """
    Represents a single fractionalized NFT token.
    """
    __tablename__ = 'nft_fractions'

    id = Column(UUID, default=uuid.uuid4, primary_key=True)
    tokenId = Column(String, nullable=False)
    fractionId = Column(String, nullable=False)
    ownerAddress = Column(String, nullable=False)
    fractionPercentage = Column(Integer, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updatedAt = Column(DateTime, server_default=DateTime.utcnow(), onupdate=DateTime.utcnow())

    def __repr__(self):
        return f"<NFTFraction(id={self.id}, tokenId={self.tokenId}, fractionId={self.fractionId})>"


class Portfolio(Base):
    """
    Represents a user's NFT portfolio.
    """
    __tablename__ = 'portfolios'

    id = Column(UUID, default=uuid.uuid4, primary_key=True)
    userId = Column(String, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updatedAt = Column(DateTime, server_default=DateTime.utcnow(), onupdate=DateTime.utcnow())

    def __repr__(self):
        return f"<Portfolio(id={self.id}, userId={self.userId})>"

    nft_fractions = relationship("NFTFraction", back_populates="portfolio")