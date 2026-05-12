from sqlalchemy import Column, String, Float, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from enum import Enum

Base = declarative_base()

class User(Base):
    """
    Represents a user interacting with the Sentinel Shield platform.
    """
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}', role='{self.role}')>"


class SmartContract(Base):
    """
    Represents a smart contract deployed on the Mossland chain.
    """
    __tablename__ = 'smart_contracts'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    contract_address = Column(String, nullable=False)
    code = Column(String, nullable=True)
    vulnerability_score = Column(Float, nullable=True)
    remediation_suggestions = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<SmartContract(id='{self.id}', contract_address='{self.contract_address}', vulnerability_score={self.vulnerability_score})>"

    def __init__(
        self,
        contract_address: str,
        code: str = None,
        vulnerability_score: float = None,
        remediation_suggestions: list = None,
    ):
        super().__init__()
        self.contract_address = contract_address
        self.code = code
        self.vulnerability_score = vulnerability_score
        self.remediation_suggestions = remediation_suggestions if remediation_suggestions is not None else []


class VulnerabilityReport(Base):
    """
    Details a specific vulnerability identified in a smart contract.
    """
    __tablename__ = 'vulnerability_reports'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    smart_contract_id = Column(String, nullable=False)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    remediation_suggestions = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<VulnerabilityReport(id='{self.id}', smart_contract_id='{self.smart_contract_id}', description='{self.description}', severity='{self.severity}')>"

    back_populates = back_populates('SmartContract', 'contract_address')

from datetime import datetime