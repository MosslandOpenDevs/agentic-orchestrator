from sqlalchemy import Column, String, Float, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class SmartContract(Base):
    """
    Represents a smart contract being analyzed for vulnerabilities.
    """
    __tablename__ = 'smart_contracts'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    contractAddress = Column(String, nullable=False)
    code = Column(String, nullable=False)
    riskScore = Column(Float, nullable=False)
    vulnerabilities = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<SmartContract(id='{self.id}', contractAddress='{self.contractAddress}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'contractAddress': self.contractAddress,
            'code': self.code,
            'riskScore': self.riskScore,
            'vulnerabilities': self.vulnerabilities,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class Vulnerability(Base):
    """
    Represents a specific vulnerability identified in a smart contract.
    """
    __tablename__ = 'vulnerabilities'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    contractId = Column(String, ForeignKey('smart_contracts.id'), nullable=False)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    remediationSuggestion = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<Vulnerability(id='{self.id}', contractId='{self.contractId}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'contractId': self.contractId,
            'description': self.description,
            'severity': self.severity,
            'remediationSuggestion': self.remediationSuggestion,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    back_populates = {'contractId': 'smart_contracts'}


class LLMAnalysis(Base):
    """
    Represents the analysis performed by the LLM on a smart contract.
    """
    __tablename__ = 'llm_analyses'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    contractId = Column(String, ForeignKey('smart_contracts.id'), nullable=False)
    analysisResult = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=datetime.utcnow())
    updated_at = Column(DateTime, onupdate=datetime.utcnow())

    def __repr__(self):
        return f"<LLMAnalysis(id='{self.id}', contractId='{self.contractId}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'contractId': self.contractId,
            'analysisResult': self.analysisResult,
            'timestamp': self.timestamp,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    back_populates = {'contractId': 'smart_contracts'}


if __name__ == '__main__':
    # Example usage
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:')  # Use SQLite for testing
    Base.metadata.create_all(engine)

    smart_contract = SmartContract(
        contractAddress='0x...',
        code='// Smart contract code...',
        riskScore=0.8,
        vulnerabilities=[{'description': 'Reentrancy', 'severity': 'High'}]
    )

    vulnerability = Vulnerability(
        contractId=smart_contract.id,
        description='Vulnerable to integer overflow',
        severity='Medium'
    )

    llm_analysis = LLMAnalysis(
        contractId=smart_contract.id,
        analysisResult='LLM analysis completed successfully',
        timestamp=datetime.utcnow()
    )

    engine.add_all([smart_contract, vulnerability, llm_analysis])
    engine.commit()

    print(smart_contract.to_dict())
    print(vulnerability.to_dict())
    print(llm_analysis.to_dict())