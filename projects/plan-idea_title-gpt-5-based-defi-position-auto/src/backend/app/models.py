from sqlalchemy import Column, Integer, String, DateTime, JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates, relationship

Base = declarative_base()

class Asset(Base):
    __tablename__ = 'asset'

    id = Column(UUID, primary_key=True)
    symbol = Column(String, unique=True)
    name = Column(String)

    def __repr__(self):
        return f"<Asset(id={self.id}, symbol={self.symbol}, name={self.name})>"


class RebalancingRecommendation(Base):
    __tablename__ = 'rebalancing_recommendation'

    id = Column(UUID, primary_key=True)
    portfolio_id = Column(String, index=True)
    recommendation = Column(String)
    timestamp = Column(DateTime)

    def __repr__(self):
        return f"<RebalancingRecommendation(id={self.id}, portfolio_id={self.portfolio_id}, recommendation={self.recommendation}, timestamp={self.timestamp})>"


class Portfolio(Base):
    __tablename__ = 'portfolio'

    id = Column(UUID, primary_key=True)
    nft_holder_id = Column(String, index=True)
    asset_balances = Column(JSON)

    def __repr__(self):
        return f"<Portfolio(id={self.id}, nft_holder_id={self.nft_holder_id}, asset_balances={self.asset_balances})>"


class NFTHolder(Base):
    __tablename__ = 'nft_holder'

    id = Column(UUID, primary_key=True)
    nft_address = Column(String)
    preferences = Column(JSON)

    def __repr__(self):
        return f"<NFTHolder(id={self.id}, nft_address={self.nft_address}, preferences={self.preferences})>"

    # Relationships
    # NFTHolder owns Portfolio
    portfolios = relationship("Portfolio", back_populates="nft_holder")