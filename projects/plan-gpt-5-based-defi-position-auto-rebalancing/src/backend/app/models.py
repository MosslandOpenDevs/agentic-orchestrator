from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class NFT(Base):
    """
    Represents a Mossland NFT, including its metadata and current holdings.
    """
    __tablename__ = 'nft'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, unique=True, nullable=False)
    owner = Column(String, nullable=False)
    metadata = Column(JSON, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=DateTime.now)
    updated_at = Column(DateTime, server_default=DateTime.now, server_expression=True)

    def __repr__(self):
        return f"<NFT(tokenId='{self.tokenId}', owner='{self.owner}')>"

    __table_args__ = (
        {'schema': 'public'}
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Portfolio(Base):
    """
    Represents a user's NFT portfolio managed by the system.
    """
    __tablename__ = 'portfolio'

    id = Column(UUID, primary_key=True)
    portfolioId = Column(String, unique=True, nullable=False)
    userId = Column(String, nullable=False)
    holdings = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=DateTime.now)
    updated_at = Column(DateTime, server_default=DateTime.now, server_expression=True)

    def __repr__(self):
        return f"<Portfolio(portfolioId='{self.portfolioId}', userId='{self.userId}')>"

    __table_args__ = (
        {'schema': 'public'}
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MarketData(Base):
    """
    Real-time market data for NFTs.
    """
    __tablename__ = 'market_data'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=DateTime.now)
    updated_at = Column(DateTime, server_default=DateTime.now, server_expression=True)

    def __repr__(self):
        return f"<MarketData(tokenId='{self.tokenId}', price={self.price})>"

    __table_args__ = (
        {'schema': 'public'}
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Prediction(Base):
    """
    GPT-5 generated NFT value prediction.
    """
    __tablename__ = 'prediction'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, nullable=False)
    predictedValue = Column(Float, nullable=False)
    confidenceInterval = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=DateTime.now)
    updated_at = Column(DateTime, server_default=DateTime.now, server_expression=True)

    def __repr__(self):
        return f"<Prediction(tokenId='{self.tokenId}', predictedValue={self.predictedValue})>"

    __table_args__ = (
        {'schema': 'public'}
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)