from sqlalchemy import Column, String, Float, Integer, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from datetime import datetime
import uuid

Base = declarative_base()

class RWAAsset(Base):
    """
    Represents a Real World Asset tokenized on the blockchain.
    """
    __tablename__ = 'rwa_assets'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    blockchain = Column(String, nullable=False)
    created_at = Column(datetime, server_default=datetime.utcnow())
    updated_at = Column(datetime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<RWAAsset(id='{self.id}', name='{self.name}', symbol='{self.symbol}', price={self.price}, blockchain='{self.blockchain}')>"


class Portfolio(Base):
    """
    Represents the Mossland RWA portfolio managed by the agent.
    """
    __tablename__ = 'portfolios'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    riskTolerance = Column(String, nullable=False)
    assetAllocation = Column(JSON, nullable=False)
    created_at = Column(datetime, server_default=datetime.utcnow())
    updated_at = Column(datetime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<Portfolio(id='{self.id}', name='{self.name}', riskTolerance='{self.riskTolerance}', assetAllocation={self.assetAllocation})>"

    rwa_assets = back_populates('rwa_assets', 'rwa_assets')


class GPT5Agent(Base):
    """
    The AI agent powered by GPT-5 responsible for portfolio optimization.
    """
    __tablename__ = 'gpt5_agents'

    id = Column(String, primary_key=True)
    prompt = Column(String, nullable=False)
    created_at = Column(datetime, server_default=datetime.utcnow())
    updated_at = Column(datetime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<GPT5Agent(id='{self.id}', prompt='{self.prompt}')>"


class NFTHolder(Base):
    """
    Mossland NFT holder utilizing the TerraForm agent.
    """
    __tablename__ = 'nfts_holders'

    id = Column(String, primary_key=True)
    nft_id = Column(String, nullable=False)
    wallet_address = Column(String, nullable=False)
    created_at = Column(datetime, server_default=datetime.utcnow())
    updated_at = Column(datetime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<NFTHolder(id='{self.id}', nft_id='{self.nft_id}', wallet_address='{self.wallet_address}')>"


if __name__ == '__main__':
    # Example Usage (Illustrative)
    engine = None # Replace with your database engine setup
    Base.metadata.create_all(engine)

    rwa1 = RWAAsset(id=str(uuid.uuid4()), name="Mossland Plot 1", symbol="MP1", price=1000.00, blockchain="Ethereum")
    portfolio1 = Portfolio(id=str(uuid.uuid4()), name="Mossland Portfolio A", riskTolerance="Moderate", assetAllocation=[(rwa1, 0.5)])
    agent1 = GPT5Agent(id=str(uuid.uuid4()), prompt="Optimize portfolio for long-term growth")
    holder1 = NFTHolder(id=str(uuid.uuid4()), nft_id="NFT123", wallet_address="0x...")

    engine.session.add(rwa1)
    engine.session.add(portfolio1)
    engine.session.add(agent1)
    engine.session.add(holder1)

    engine.session.commit()