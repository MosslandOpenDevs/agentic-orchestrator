from sqlalchemy import Column, Integer, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from datetime import datetime

Base = declarative_base()

class RWAPortfolio(Base):
    __tablename__ = 'rwa_portfolios'

    id = Column(UUID, primary_key=True)
    nftHolderId = Column(String, nullable=True)
    riskTolerance = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RWAPortfolio(id={self.id}, nftHolderId={self.nftHolderId}, riskTolerance={self.riskTolerance})>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID()
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
        if 'updatedAt' not in kwargs:
            self.updatedAt = datetime.utcnow()


class RWAAsset(Base):
    __tablename__ = 'rwa_assets'

    id = Column(UUID, primary_key=True)
    assetName = Column(String, nullable=False)
    assetPrice = Column(Float, nullable=False)
    assetQuantity = Column(Float, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RWAAsset(id={self.id}, assetName={self.assetName}, assetPrice={self.assetPrice}, assetQuantity={self.assetQuantity})>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID()
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
        if 'updatedAt' not in kwargs:
            self.updatedAt = datetime.utcnow()

    portfolio = Column(UUID, ForeignKey('rwa_portfolios.id'), nullable=False)

    def __repr__(self):
        return f"<RWAAsset(id={self.id}, assetName={self.assetName}, assetPrice={self.assetPrice}, assetQuantity={self.assetQuantity}, portfolio_id={self.portfolio})>"


class GPT5Agent(Base):
    __tablename__ = 'gpt5_agents'

    id = Column(UUID, primary_key=True)
    lastRunTime = Column(DateTime, nullable=True)
    prompt = Column(String, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GPT5Agent(id={self.id}, lastRunTime={self.lastRunTime}, prompt={self.prompt})>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID()
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
        if 'updatedAt' not in kwargs:
            self.updatedAt = datetime.utcnow()

    portfolios = Column(UUID, ForeignKey('rwa_portfolios.id'),  nullable=True,  chaingate=True)

    def __repr__(self):
        return f"<GPT5Agent(id={self.id}, lastRunTime={self.lastRunTime}, prompt={self.prompt}, portfolios={self.portfolios})>"