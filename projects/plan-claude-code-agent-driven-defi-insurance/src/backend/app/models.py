from sqlalchemy import Column, Integer, String, UUID, DateTime, Float, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates, relationship
from enum import Enum

from typing import List, Dict, Optional

Base = declarative_base()

class RiskAssessment(Base):
    __tablename__ = 'risk_assessments'

    id = Column(UUID, primary_key=True)
    contractAddress = Column(String)
    vulnerabilities = Column(JSON)
    severity = Column(String)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, contractAddress={self.contractAddress}, vulnerabilities={self.vulnerabilities}, severity={self.severity})>"


class Portfolio(Base):
    __tablename__ = 'portfolios'

    id = Column(UUID, primary_key=True)
    nftHolderId = Column(String, relationship(back_populates="portfolios"))
    assetBalances = Column(JSON)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<Portfolio(id={self.id}, nftHolderId={self.nftHolderId}, assetBalances={self.assetBalances})>"


class DeFiAsset(Base):
    __tablename__ = 'defi_assets'

    id = Column(UUID, primary_key=True)
    address = Column(String)
    quantity = Column(Float)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<DeFiAsset(id={self.id}, address={self.address}, quantity={self.quantity})>"


class NFTHolder(Base):
    __tablename__ = 'nfts_holders'

    id = Column(UUID, primary_key=True)
    nftAddress = Column(String)
    portfolio_id = Column(String, relationship(back_populates="nft_holders"))
    portfolio = relationship(
        "Portfolio",
        back_populates="nft_holders",
        cascade="all",
        passive_with=relationship.select_from(Portfolio)
    )
    
    def __repr__(self):
        return f"<NFTHolder(id={self.id}, nftAddress={self.nftAddress}, portfolio_id={self.portfolio_id})>"