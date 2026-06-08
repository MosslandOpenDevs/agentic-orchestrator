from sqlalchemy import Column, Integer, String, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class User(Base):
    """
    Represents a user of the Verdant agent.
    """
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    username = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, onupdate=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class PriceFeed(Base):
    """
    Stores price data for cryptocurrencies.
    """
    __tablename__ = 'price_feeds'

    id = Column(UUID, primary_key=True)
    asset = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<PriceFeed(id={self.id}, asset='{self.asset}', price={self.price}, timestamp={self.timestamp})>"


class NFTCollection(Base):
    """
    Represents a specific Mossland NFT collection.
    """
    __tablename__ = 'nft_collections'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    contractAddress = Column(String, nullable=False)

    def __repr__(self):
        return f"<NFTCollection(id={self.id}, name='{self.name}', contractAddress='{self.contractAddress}')>"


class NFTHolding(Base):
    """
    Represents a user's holding of an NFT from a specific collection.
    """
    __tablename__ = 'nft_holdings'

    id = Column(UUID, primary_key=True)
    nftCollectionId = Column(UUID, ForeignKey('nft_collections.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    lastUpdated = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<NFTHolding(id={self.id}, nftCollectionId={self.nftCollectionId}, quantity={self.quantity})>"

    back_populates = {
        'nftCollectionId': 'nft_collections'
    }


class Portfolio(Base):
    """
    Represents a user's NFT portfolio.
    """
    __tablename__ = 'portfolios'

    id = Column(UUID, primary_key=True)
    userId = Column(UUID, ForeignKey('users.id'), nullable=False)
    createdAt = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, onupdate=True)

    def __repr__(self):
        return f"<Portfolio(id={self.id}, userId={self.userId})>"

    back_populates = {
        'userId': 'users'
    }