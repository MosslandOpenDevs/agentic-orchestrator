from sqlalchemy import Column, Integer, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class NFTHolder(Base):
    __tablename__ = 'nfts_holder'

    id = Column(UUID, primary_key=True)
    walletAddress = Column(String, nullable=False, doc="Solana wallet address of the NFT holder")
    nftToken = Column(String, nullable=False, doc="Token address of the NFT held")
    ownershipCount = Column(Integer, nullable=False, doc="Number of NFTs held by the holder")
    created_at = Column(DateTime, server_default=DateTime.utcnow, doc="Timestamp of creation")
    updated_at = Column(DateTime, onupdate=DateTime.utcnow, doc="Timestamp of last update")

    def __repr__(self):
        return f"<NFTHolder(id={self.id}, walletAddress='{self.walletAddress}', nftToken='{self.nftToken}', ownershipCount={self.ownershipCount})>"

    def __str__(self):
        return __repr__()


class RiskScore(Base):
    __tablename__ = 'risk_score'

    id = Column(UUID, primary_key=True)
    walletAddress = Column(String, nullable=False, doc="Solana wallet address associated with the score")
    score = Column(Float, nullable=False, doc="The calculated risk score")
    timestamp = Column(DateTime, nullable=False, doc="Timestamp of the risk score calculation")
    created_at = Column(DateTime, server_default=DateTime.utcnow, doc="Timestamp of creation")
    updated_at = Column(DateTime, onupdate=DateTime.utcnow, doc="Timestamp of last update")

    def __repr__(self):
        return f"<RiskScore(id={self.id}, walletAddress='{self.walletAddress}', score={self.score}, timestamp={self.timestamp})>"

    def __str__(self):
        return __repr__()


class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(UUID, primary_key=True)
    assetAddress = Column(String, nullable=False, doc="Solana asset address")
    price = Column(Float, nullable=False, doc="Current market price")
    volatility = Column(Float, nullable=False, doc="Volatility metric")
    created_at = Column(DateTime, server_default=DateTime.utcnow, doc="Timestamp of creation")
    updated_at = Column(DateTime, onupdate=DateTime.utcnow, doc="Timestamp of last update")

    def __repr__(self):
        return f"<MarketData(id={self.id}, assetAddress='{self.assetAddress}', price={self.price}, volatility={self.volatility})>"

    def __str__(self):
        return __repr__()


class ClaudeAgentPrompt(Base):
    __tablename__ = 'claude_agent_prompt'

    id = Column(UUID, primary_key=True)
    promptText = Column(String, nullable=False, doc="The text of the prompt")
    promptVersion = Column(String, nullable=False, doc="Version of the prompt")
    created_at = Column(DateTime, server_default=DateTime.utcnow, doc="Timestamp of creation")
    updated_at = Column(DateTime, onupdate=DateTime.utcnow, doc="Timestamp of last update")

    def __repr__(self):
        return f"<ClaudeAgentPrompt(id={self.id}, promptText='{self.promptText}', promptVersion='{self.promptVersion}')>"

    def __str__(self):
        return __repr__()