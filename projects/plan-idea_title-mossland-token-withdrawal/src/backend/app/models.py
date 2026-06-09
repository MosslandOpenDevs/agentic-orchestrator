from sqlalchemy import Column, Integer, String, DateTime, UUID, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from enum import Enum

from typing import Optional

Base = declarative_base()

class StatusEnum(Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class NFTWithdrawalTransaction(Base):
    """
    Represents a single NFT withdrawal transaction from the Mossland blockchain.
    """
    __tablename__ = 'nft_withdrawal_transactions'

    id = Column(UUID, primary_key=True)
    nftAddress = Column(String, nullable=False)
    senderAddress = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String, Enum(StatusEnum), nullable=False)

    def __repr__(self):
        return f"<NFTWithdrawalTransaction(id={self.id}, nftAddress='{self.nftAddress}', senderAddress='{self.senderAddress}', timestamp={self.timestamp}, status='{self.status}')>"

class SmartContract(Base):
    """
    Represents the Mossland NFT smart contract.
    """
    __tablename__ = 'smart_contracts'

    contractAddress = Column(String, primary_key=True)
    contractName = Column(String, nullable=False)

    def __repr__(self):
        return f"<SmartContract(contractAddress='{self.contractAddress}', contractName='{self.contractName}')>"

class ClaudeOpusResponse(Base):
    """
    Represents the response from the Claude Opus API.
    """
    __tablename__ = 'claude_opus_responses'

    responseCode = Column(Integer, nullable=False)
    responseText = Column(String, nullable=False)

    def __repr__(self):
        return f"<ClaudeOpusResponse(responseCode={self.responseCode}, responseText='{self.responseText}')>"


if __name__ == '__main__':
    from sqlalchemy import create_engine, text
    engine = create_engine('postgresql://user:password@host:port/database')
    Base.metadata.create_all(bind=engine)

    # Example usage:
    # transaction = NFTWithdrawalTransaction(
    #     nftAddress="0x...",
    #     senderAddress="0x...",
    #     timestamp=datetime.datetime.now(),
    #     status=StatusEnum.pending
    # )
    # session.add(transaction)
    # session.commit()