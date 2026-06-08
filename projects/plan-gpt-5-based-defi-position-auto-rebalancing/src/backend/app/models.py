from sqlalchemy import Column, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates, relationship

Base = declarative_base()

class NFTPosition(Base):
    """
    Represents a user's position within the Mossland NFT ecosystem,
    detailing holdings and DeFi protocol allocations.
    """
    __tablename__ = 'nft_positions'

    id = Column(UUID, primary_key=True)
    nftId = Column(String, nullable=False)
    userAddress = Column(String, nullable=False)
    protocol = Column(String, nullable=False)
    asset = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updated_at = Column(DateTime, onupdate=True)

    __repr__ = lambda self: f"NFTPosition(id={self.id}, nftId={self.nftId}, userAddress={self.userAddress}, protocol={self.protocol}, asset={self.asset}, amount={self.amount})"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID()
        if 'createdAt' not in kwargs:
            self.createdAt = DateTime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = DateTime.utcnow()


class RiskProfile(Base):
    """
    Defines the user's risk tolerance for DeFi portfolio management.
    """
    __tablename__ = 'risk_profiles'

    id = Column(UUID, primary_key=True)
    userId = Column(String, nullable=False)
    riskTolerance = Column(String, nullable=False)
    volatilityThreshold = Column(Float, nullable=False)
    maxLossPercentage = Column(Float, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updated_at = Column(DateTime, onupdate=True)

    __repr__ = lambda self: f"RiskProfile(id={self.id}, userId={self.userId}, riskTolerance={self.riskTolerance}, volatilityThreshold={self.volatilityThreshold}, maxLossPercentage={self.maxLossPercentage})"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID()
        if 'createdAt' not in kwargs:
            self.createdAt = DateTime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = DateTime.utcnow()


class MarketData(Base):
    """
    Stores real-time market data for DeFi assets.
    """
    __tablename__ = 'market_data'

    id = Column(UUID, primary_key=True)
    asset = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    volatility = Column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=DateTime.utcnow())
    updated_at = Column(DateTime, onupdate=True)

    __repr__ = lambda self: f"MarketData(id={self.id}, asset={self.asset}, price={self.price}, volatility={self.volatility}, timestamp={self.timestamp})"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID()
        if 'timestamp' not in kwargs:
            self.timestamp = DateTime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = DateTime.utcnow()


if __name__ == '__main__':
    Base.metadata.create_all(engine)