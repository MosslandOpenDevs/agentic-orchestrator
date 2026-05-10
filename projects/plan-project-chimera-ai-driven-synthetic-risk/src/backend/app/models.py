from sqlalchemy import Column, Integer, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class SmartContract(Base):
    """
    Represents a smart contract deployed on the WAX blockchain.
    """
    __tablename__ = 'smart_contracts'

    id = Column(UUID, primary_key=True)
    contract_address = Column(String, nullable=False)
    code_hash = Column(String)
    created_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<SmartContract(id={self.id}, contract_address='{self.contract_address}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = UUID.generate()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class Transaction(Base):
    """
    Represents a transaction interacting with a smart contract.
    """
    __tablename__ = 'transactions'

    id = Column(UUID, primary_key=True)
    transaction_hash = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    contract_address = Column(String, nullable=False)
    block_number = Column(Integer)

    def __repr__(self):
        return f"<Transaction(id={self.id}, transaction_hash='{self.transaction_hash}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = UUID.generate()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class RiskScore(Base):
    """
    Represents the AI-calculated risk score for a smart contract.
    """
    __tablename__ = 'risk_scores'

    id = Column(UUID, primary_key=True)
    contract_address = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<RiskScore(id={self.id}, contract_address='{self.contract_address}', score={self.score})>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = UUID.generate()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class User(Base):
    """
    Represents a user of the DEX platform.
    """
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    username = Column(String, nullable=False)
    daily_active_users = Column(Integer)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = UUID.generate()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()