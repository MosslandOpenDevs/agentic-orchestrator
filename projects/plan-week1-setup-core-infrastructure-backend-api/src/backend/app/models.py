from sqlalchemy import Column, String, Float, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from enum import Enum

Base = declarative_base()

class User(Base):
    """
    Represents a user interacting with the platform.
    """
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    createdAt = Column(DateTime, server_default=datetime.datetime.now)
    updated_at = Column(DateTime, server_default=datetime.datetime.now, server_onupdate=datetime.datetime.now)

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', role='{self.role}')>"


class SmartContract(Base):
    """
    Represents a smart contract deployed on the Mossland chain.
    """
    __tablename__ = 'smart_contracts'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    contractAddress = Column(String, nullable=False)
    code = Column(String, nullable=True)
    vulnerabilityScore = Column(Float, nullable=True)
    remediationSuggestions = Column(JSON, nullable=True)
    createdAt = Column(DateTime, server_default=datetime.datetime.now)
    updated_at = Column(DateTime, server_default=datetime.datetime.now, server_onupdate=datetime.datetime.now)

    def __repr__(self):
        return f"<SmartContract(id='{self.id}', contractAddress='{self.contractAddress}')>"


class VulnerabilityReport(Base):
    """
    Details a specific vulnerability found in a smart contract.
    """
    __tablename__ = 'vulnerability_reports'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    contractId = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    remediationSuggestion = Column(String, nullable=True)
    createdAt = Column(DateTime, server_default=datetime.datetime.now)
    updated_at = Column(DateTime, server_default=datetime.datetime.now, server_onupdate=datetime.datetime.now)

    def __repr__(self):
        return f"<VulnerabilityReport(id='{self.id}', contractId='{self.contractId}', description='{self.description}')>"

import datetime

if __name__ == '__main__':
    # Example Usage (not part of the solution, just for testing)
    from sqlalchemy import create_engine
    engine = create_engine('postgresql://user:password@host:port/database')
    Base.metadata.create_all(bind=engine)

    user1 = User(username='testuser', role='Holder')
    user1.id = 'a1b2c3d4-e5f6-7890-1234-567890abcdef'
    user1.updated_at = datetime.datetime.now()

    contract1 = SmartContract(contractAddress='0x123...', code='Some Solidity Code')
    contract1.id = 'f1e2d3c4-b5a6-7890-1234-567890abcdef'
    contract1.updated_at = datetime.datetime.now()

    report1 = VulnerabilityReport(contractId='f1e2d3c4-b5a6-7890-1234-567890abcdef',
                                 description='Critical Vulnerability',
                                 severity='Critical',
                                 remediationSuggestion='Implement proper input validation')
    report1.id = 'c3d4e5f6-b7a8-9012-3456-7890abcdef12'
    report1.updated_at = datetime.datetime.now()

    engine.connect()
    dbsession = engine.session()
    dbsession.add(user1)
    dbsession.add(contract1)
    dbsession.add(report1)
    dbsession.commit()
    dbsession.close()