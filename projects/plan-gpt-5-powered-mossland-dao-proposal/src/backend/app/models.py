from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class NFTCollection(Base):
    """
    Represents a collection of NFTs for risk assessment.
    """
    __tablename__ = 'nft_collection'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    contractAddress = Column(String, nullable=False)
    tokenId = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<NFTCollection(id='{self.id}', name='{self.name}', contractAddress='{self.contractAddress}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, 'id'):
            self.id = str(uuid4())
        if not hasattr(self, 'created_at'):
            self.created_at = datetime.utcnow()
        if not hasattr(self, 'updated_at'):
            self.updated_at = datetime.utcnow()


class NFTTransaction(Base):
    """
    Represents a transaction involving an NFT.
    """
    __tablename__ = 'nft_transaction'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    nftCollectionId = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<NFTTransaction(id='{self.id}', nftCollectionId='{self.nftCollectionId}', timestamp='{self.timestamp}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, 'id'):
            self.id = str(uuid4())
        if not hasattr(self, 'created_at'):
            self.created_at = datetime.utcnow()
        if not hasattr(self, 'updated_at'):
            self.updated_at = datetime.utcnow()

    back_populates = 'NFTCollection'

class RiskAssessment(Base):
    """
    Stores the risk assessment results for a portfolio.
    """
    __tablename__ = 'risk_assessment'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    portfolioId = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    stdDeviation = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<RiskAssessment(id='{self.id}', portfolioId='{self.portfolioId}', timestamp='{self.timestamp}', stdDeviation='{self.stdDeviation}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, 'id'):
            self.id = str(uuid4())
        if not hasattr(self, 'created_at'):
            self.created_at = datetime.utcnow()
        if not hasattr(self, 'updated_at'):
            self.updated_at = datetime.utcnow()


class Portfolio(Base):
    """
    Represents a user's NFT portfolio (used for testing).
    """
    __tablename__ = 'portfolio'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    userId = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<Portfolio(id='{self.id}', userId='{self.userId}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, 'id'):
            self.id = str(uuid4())
        if not hasattr(self, 'created_at'):
            self.created_at = datetime.utcnow()
        if not hasattr(self, 'updated_at'):
            self.updated_at = datetime.utcnow()

# To create the tables:
# Base.metadata.create_all(engine)