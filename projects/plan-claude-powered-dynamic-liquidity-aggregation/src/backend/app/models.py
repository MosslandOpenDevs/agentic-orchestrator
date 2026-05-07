from sqlalchemy import Column, String, Float, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class NFTHolder(Base):
    """
    Represents a user holding NFTs on the Billions Network.
    """
    __tablename__ = 'nfts_holder'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    network = Column(String)
    walletAddress = Column(String)
    riskProfile = Column(String)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NFTHolder(id='{self.id}', network='{self.network}', walletAddress='{self.walletAddress}', riskProfile='{self.riskProfile}')>"


class Portfolio(Base):
    """
    Represents an NFT holder's portfolio of assets.
    """
    __tablename__ = 'portfolios'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    nftHolderId = Column(String, ForeignKey('nfts_holder.id'))
    totalValue = Column(Float)
    assetAllocation = Column(JSON)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Portfolio(id='{self.id}', nftHolderId='{self.nftHolderId}', totalValue={self.totalValue}, assetAllocation={self.assetAllocation})>"

    back_populates = 'NFTHolder'


class MarketData(Base):
    """
    Represents real-time market data for assets.
    """
    __tablename__ = 'market_data'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    assetSymbol = Column(String)
    price = Column(Float)
    volume = Column(Float)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MarketData(id='{self.id}', assetSymbol='{self.assetSymbol}', price={self.price}, volume={self.volume})>"


class GPT5Response(Base):
    """
    Stores the output from the GPT-5 API.
    """
    __tablename__ = 'gpt5_responses'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    portfolioId = Column(String, ForeignKey('portfolios.id'))
    prompt = Column(String)
    response = Column(String)
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GPT5Response(id='{self.id}', portfolioId='{self.portfolioId}', prompt='{self.prompt}', response='{self.response}')>"

    back_populates = 'Portfolio'


if __name__ == '__main__':
    Base.metadata.create_all(engine)