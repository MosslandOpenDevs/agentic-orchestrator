from sqlalchemy import Column, Integer, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates, relationship

Base = declarative_base()

class NFTPosition(Base):
    """
    Represents a user's position within the Mossland NFT ecosystem,
    detailing holdings and DeFi interactions.
    """
    __tablename__ = 'nft_position'

    id = Column(UUID, primary_key=True)
    nftId = Column(String, nullable=False)
    userAddress = Column(String, nullable=False)
    defiProtocol = Column(String)
    assetToken = Column(String)
    quantity = Column(Integer, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updated_at = Column(DateTime, server_default=DateTime.utcnow(), onupdate=True)

    __repr__ = lambda self: f"NFTPosition(id={self.id}, nftId={self.nftId}, userAddress={self.userAddress})"

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
    __tablename__ = 'risk_profile'

    id = Column(UUID, primary_key=True)
    userId = Column(String, nullable=False)
    riskLevel = Column(String, nullable=False)
    volatilityThreshold = Column(Float, nullable=False)
    lossTolerance = Column(Float, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updated_at = Column(DateTime, server_default=DateTime.utcnow(), onupdate=True)

    __repr__ = lambda self: f"RiskProfile(id={self.id}, userId={self.userId}, riskLevel={self.riskLevel})"

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
    Stores real-time price data for DeFi assets.
    """
    __tablename__ = 'market_data'

    id = Column(UUID, primary_key=True)
    assetToken = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, server_default=DateTime.utcnow())
    updated_at = Column(DateTime, server_default=DateTime.utcnow(), onupdate=True)

    __repr__ = lambda self: f"MarketData(id={self.id}, assetToken={self.assetToken}, price={self.price})"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID()
        if 'createdAt' not in kwargs:
            self.createdAt = DateTime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = DateTime.utcnow()


if __name__ == '__main__':
    Base.metadata.create_all(engine)