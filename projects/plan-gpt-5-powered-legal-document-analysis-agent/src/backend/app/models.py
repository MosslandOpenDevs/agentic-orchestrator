from sqlalchemy import Column, Integer, String, Float, JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates, relationship

Base = declarative_base()

class User(Base):
    """
    Represents a Mossland NFT holder.
    """
    __tablename__ = 'user'

    id = Column(UUID, primary_key=True)
    userId = Column(String, unique=True)
    portfolio = Column(relationship("PortfolioHolding", secondary="portfolio_holding_user", back_populates="user"))

    def __repr__(self):
        return f"<User(userId='{self.userId}')>"


class PortfolioHolding(Base):
    """
    Represents an NFT held within a user's portfolio.
    """
    __tablename__ = 'portfolio_holding'

    id = Column(UUID, primary_key=True)
    userId = Column(String, foreign_key="user.id")
    tokenId = Column(String, foreign_key="nft.id")
    quantity = Column(Integer)
    valuation = Column(Float)

    user = relationship("User", back_populates="portfolio")

    def __repr__(self):
        return f"<PortfolioHolding(userId='{self.userId}', tokenId='{self.tokenId}', quantity={self.quantity})>"


class NFT(Base):
    """
    Represents a Mossland NFT asset.
    """
    __tablename__ = 'nft'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, unique=True)
    metadata = Column(JSON)
    valuation = Column(Float)

    # relationships
    portfolio_holdings = relationship("PortfolioHolding", back_populates="nft")

    def __repr__(self):
        return f"<NFT(tokenId='{self.tokenId}', valuation={self.valuation})>"


class RiskAssessment(Base):
    """
    Represents the risk assessment of an NFT or portfolio.
    """
    __tablename__ = 'risk_assessment'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, foreign_key="nft.id")
    riskScore = Column(Float)
    alertThreshold = Column(Float)

    nft = relationship("NFT", back_populates="risk_assessments")

    def __repr__(self):
        return f"<RiskAssessment(tokenId='{self.tokenId}', riskScore={self.riskScore})>"


class PortfolioHoldingUser(Base):
    __tablename__ = 'portfolio_holding_user'

    portfolio_holding_id = Column(UUID, primary_key=True)
    user_id = Column(UUID, primary_key=True)

    # backrefs to user and portfolio_holding
    user = back_populates('portfolio_holding_user', 'user')
    portfolio_holding = back_populates('portfolio_holding_user', 'portfolio_holding')