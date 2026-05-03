from sqlalchemy import Column, Integer, String, DateTime, Float, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class SmartContract(Base):
    """
    Represents a DeFi protocol smart contract.
    """
    __tablename__ = 'smart_contracts'

    id = Column(UUID, primary_key=True)
    address = Column(String, nullable=False)
    name = Column(String, nullable=False)
    codeHash = Column(String)
    compilerVersion = Column(String)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<SmartContract(id={self.id}, address='{self.address}', name='{self.name}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()


class Transaction(Base):
    """
    Represents a transaction on the Ethereum blockchain.
    """
    __tablename__ = 'transactions'

    id = Column(UUID, primary_key=True)
    hash = Column(String, nullable=False)
    blockNumber = Column(Integer)
    timestamp = Column(DateTime, nullable=False)
    from_ = Column(String, nullable=False)
    to = Column(String, nullable=False)
    value = Column(Integer)
    smart_contract_id = Column(UUID, ForeignKey('smart_contracts.id'))

    def __repr__(self):
        return f"<Transaction(id={self.id}, hash='{self.hash}', blockNumber={self.blockNumber}, from_='{self.from_}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()

    back_populates = back_populates('Transaction', 'smart_contracts')


class VulnerabilityPrediction(Base):
    """
    Represents a predicted vulnerability and its associated details.
    """
    __tablename__ = 'vulnerability_predictions'

    id = Column(UUID, primary_key=True)
    contractAddress = Column(String, nullable=False)
    predictedVulnerability = Column(String, nullable=False)
    confidenceScore = Column(Float)
    severity = Column(String, nullable=False)
    smart_contract_id = Column(UUID, ForeignKey('smart_contracts.id'))

    def __repr__(self):
        return f"<VulnerabilityPrediction(id={self.id}, contractAddress='{self.contractAddress}', predictedVulnerability='{self.predictedVulnerability}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()

    back_populates = back_populates('VulnerabilityPrediction', 'smart_contracts')

from datetime import datetime