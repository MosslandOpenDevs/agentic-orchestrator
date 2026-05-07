from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates, relationship

Base = declarative_base()

class NFT(Base):
    """
    Represents a single NFT asset.
    """
    __tablename__ = 'nft'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    floorPrice = Column(Float, nullable=True)
    createdAt = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<NFT(tokenId='{self.tokenId}', name='{self.name}')>"

    @relationship(Policy.id, back_populates="nft_holdings")
    def user(self):
        return self.user

class User(Base):
    """
    Represents a Mossland NFT holder.
    """
    __tablename__ = 'user'

    id = Column(UUID, primary_key=True)
    userId = Column(String, unique=True, nullable=False)
    riskTolerance = Column(String, nullable=True)
    nftHoldings = Column(String, nullable=True)

    def __repr__(self):
        return f"<User(userId='{self.userId}')>"

    @relationship(NFT.id, back_populates="owner")
    def nft_holdings(self):
        return self.nft_holdings

class YieldFarmPosition(Base):
    """
    Represents a position within a DeFi protocol for yield farming.
    """
    __tablename__ = 'yield_farm_position'

    id = Column(UUID, primary_key=True)
    positionId = Column(String, unique=True, nullable=False)
    nftId = Column(String, nullable=False)
    protocol = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    yieldRate = Column(Float, nullable=False)

    def __repr__(self):
        return f"<YieldFarmPosition(positionId='{self.positionId}', nftId='{self.nftId}')>"

    @relationship(NFT.id, back_populates="yield_farm_positions")
    def nft(self):
        return self.nft

class PriceFeed(Base):
    """
    Represents a price feed from an external source.
    """
    __tablename__ = 'price_feed'

    id = Column(UUID, primary_key=True)
    feedId = Column(String, unique=True, nullable=False)
    asset = Column(String, nullable=False)
    price = Column(Float, nullable=False)

    def __repr__(self):
        return f"<PriceFeed(feedId='{self.feedId}', asset='{self.asset}')>"

    # No relationships

class Policy(Base):
    __tablename__ = 'policy'

    id = Column(UUID, primary_key=True)
    nft_id = Column(String, nullable=False)
    owner = relationship("NFT", back_populates="user")
    nft_holdings = relationship(
        "User", back_populates="nft_holdings", collection=None
    )
    yield_farm_positions = relationship(
        "YieldFarmPosition", back_populates="nft"
    )