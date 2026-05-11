from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class User(Base):
    """
    Represents a user of the system.
    """
    __tablename__ = 'user'

    id = Column(UUID, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Portfolio(Base):
    """
    Represents a user's NFT portfolio.
    """
    __tablename__ = 'portfolio'

    id = Column(UUID, primary_key=True)
    userId = Column(String, nullable=False)
    portfolioId = Column(String, nullable=False, unique=True)
    createdAt = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    __repr__ = lambda self: f"<Portfolio(id={self.id}, userId='{self.userId}')>"

    back_populates = {'userId': 'user'}


class NFT(Base):
    """
    Represents a Non-Fungible Token.
    """
    __tablename__ = 'nft'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, nullable=False, unique=True)
    name = Column(String)
    symbol = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    __repr__ = lambda self: f"<NFT(id={self.id}, tokenId='{self.tokenId}')>"

    back_populates = {'portfolioId': 'portfolio'}


class TradingSession(Base):
    """
    Represents a single trading operation.
    """
    __tablename__ = 'trading_session'

    id = Column(UUID, primary_key=True)
    sessionId = Column(String, nullable=False, unique=True)
    nftId = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    __repr__ = lambda self: f"<TradingSession(id={self.id}, nftId='{self.nftId}')>"

    back_populates = {'nftId': 'nft'}


if __name__ == '__main__':
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)