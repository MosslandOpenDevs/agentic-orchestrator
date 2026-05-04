from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class NFTHolder(Base):
    """
    Represents a Mossland NFT holder within the Rain ecosystem.
    """
    __tablename__ = 'nfts_holder'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    nftAddress = Column(String, nullable=False)
    rainBalance = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NFTHolder(id='{self.id}', nftAddress='{self.nftAddress}', rainBalance={self.rainBalance})>"


class MarketData(Base):
    """
    Stores data from external APIs like Chainlink and Dune Analytics.
    """
    __tablename__ = 'market_data'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False)
    assetPrice = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MarketData(id='{self.id}', timestamp={self.timestamp}, assetPrice={self.assetPrice}, volume={self.volume})>"


class Portfolio(Base):
    """
    Represents a user's portfolio of NFTs and Rain stablecoin.
    """
    __tablename__ = 'portfolios'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    nftHolderId = Column(String, nullable=False, index=True)
    rainBalance = Column(Float, nullable=False)
    nftAssetAllocation = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Portfolio(id='{self.id}', nftHolderId='{self.nftHolderId}', rainBalance={self.rainBalance}, nftAssetAllocation={self.nftAssetAllocation})>"


class SmartContract(Base):
    """
    Represents a smart contract interaction.
    """
    __tablename__ = 'smart_contracts'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    contractAddress = Column(String, nullable=False)
    functionName = Column(String, nullable=False)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SmartContract(id='{self.id}', contractAddress='{self.contractAddress}', functionName='{self.functionName}', parameters={self.parameters})>"