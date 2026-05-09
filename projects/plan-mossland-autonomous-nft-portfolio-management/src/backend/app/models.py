from sqlalchemy import Column, Integer, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class NFTHolder(Base):
    """
    Represents a Mossland NFT holder within the DeFi ecosystem.
    """
    __tablename__ = 'nfts_holders'

    id = Column(UUID, primary_key=True)
    nftAddress = Column(String, nullable=False)
    createdAt = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<NFTHolder(id={self.id}, nftAddress='{self.nftAddress}')>"

class PortfolioPosition(Base):
    """
    Represents a single asset held within a portfolio.
    """
    __tablename__ = 'portfolio_positions'

    id = Column(UUID, primary_key=True)
    nftHolderId = Column(String, nullable=False)
    assetAddress = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    lastUpdated = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<PortfolioPosition(id={self.id}, nftHolderId='{self.nftHolderId}', assetAddress='{self.assetAddress}')>"

    back_populates = 'NFTHolder'

class RiskParameter(Base):
    """
    Defines the risk profile for a portfolio.
    """
    __tablename__ = 'risk_parameters'

    id = Column(UUID, primary_key=True)
    riskTolerance = Column(Float, nullable=False)
    timeHorizon = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<RiskParameter(id={self.id}, riskTolerance={self.riskTolerance}, timeHorizon={self.timeHorizon})>"

class PerformanceData(Base):
    """
    Stores historical performance data for a portfolio.
    """
    __tablename__ = 'performance_data'

    id = Column(UUID, primary_key=True)
    portfolioPositionId = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)

    def __repr__(self):
        return f"<PerformanceData(id={self.id}, portfolioPositionId='{self.portfolioPositionId}', timestamp={self.timestamp})>"

if __name__ == '__main__':
    # Example usage (not for actual database interaction)
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:')  # Replace with your database URL
    Base.metadata.create_all(bind=engine)

    nfts_holder = NFTHolder(nftAddress='0x123...', createdAt=datetime.datetime.now())
    portfolio_position = PortfolioPosition(nftHolderId=nfts_holder.id, assetAddress='0x456...', quantity=10.0)
    risk_parameter = RiskParameter(riskTolerance=0.5, timeHorizon=5)
    performance_data = PerformanceData(portfolioPositionId=portfolio_position.id, timestamp=datetime.datetime.now(), price=100.0, quantity=1.0)

    engine.connect()
    print(nfts_holder)
    print(portfolio_position)
    print(risk_parameter)
    print(performance_data)
    engine.dispose()