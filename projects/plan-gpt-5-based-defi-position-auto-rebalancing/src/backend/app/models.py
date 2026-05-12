from sqlalchemy import Column, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates, relationship

Base = declarative_base()

class RiskParameter(Base):
    __tablename__ = 'risk_parameters'

    id = Column(UUID, primary_key=True)
    asset = Column(String, nullable=False)
    thresholdLow = Column(Float, nullable=False)
    thresholdHigh = Column(Float, nullable=False)
    action = Column(String, nullable=False)
    createdAt = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True, server_expression=True, onupdate=True)

    def __repr__(self):
        return f"<RiskParameter(id={self.id}, asset='{self.asset}', thresholdLow={self.thresholdLow}, thresholdHigh={self.thresholdHigh}, action='{self.action}')>"


class NFTCollateral(Base):
    __tablename__ = 'nft_collaterals'

    id = Column(UUID, primary_key=True)
    tokenId = Column(String, nullable=False)
    asset = Column(String, nullable=False)
    currentRatio = Column(Float, nullable=False)
    createdAt = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True, server_expression=True, onupdate=True)

    def __repr__(self):
        return f"<NFTCollateral(id={self.id}, tokenId='{self.tokenId}', asset='{self.asset}', currentRatio={self.currentRatio})>"

    PriceFeedUpdates = relationship("PriceFeedUpdate", back_populates="nft_collateral")


class PriceFeedUpdate(Base):
    __tablename__ = 'price_feed_updates'

    id = Column(UUID, primary_key=True)
    asset = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True, server_expression=True, onupdate=True)

    def __repr__(self):
        return f"<PriceFeedUpdate(id={self.id}, asset='{self.asset}', price={self.price}, timestamp={self.timestamp})>"

    nft_collateral = relationship("NFTCollateral", back_populates="price_feed_updates")

if __name__ == '__main__':
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)