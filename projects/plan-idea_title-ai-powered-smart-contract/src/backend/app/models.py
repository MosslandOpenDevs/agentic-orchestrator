from sqlalchemy import Column, String, Float, Integer, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class SmartContract(Base):
    """
    Represents a smart contract deployed on the XMR DEX.
    """
    __tablename__ = 'smart_contracts'

    id = Column(UUID, primary_key=True)
    address = Column(String, nullable=False, doc="Contract address")
    name = Column(String, nullable=False, doc="Contract name")
    abi = Column(String, nullable=False, doc="Contract ABI")
    createdAt = Column(DateTime, nullable=False, doc="Contract creation timestamp")

    def __repr__(self):
        return f"<SmartContract(id={self.id}, address='{self.address}', name='{self.name}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()


class VulnerabilityReport(Base):
    """
    Records a detected vulnerability in a smart contract.
    """
    __tablename__ = 'vulnerability_reports'

    id = Column(UUID, primary_key=True)
    contractAddress = Column(String, nullable=False, doc="Address of the vulnerable contract")
    vulnerabilityType = Column(String, nullable=False, doc="Type of vulnerability (e.g., Reentrancy, Overflow)")
    severity = Column(String, nullable=False, doc="Severity level (e.g., Critical, High, Medium, Low)")
    description = Column(String, nullable=False, doc="Detailed description of the vulnerability")
    createdAt = Column(DateTime, nullable=False, doc="Report creation timestamp")

    def __repr__(self):
        return f"<VulnerabilityReport(id={self.id}, contractAddress='{self.contractAddress}', vulnerabilityType='{self.vulnerabilityType}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()

    back_populates = {'vulnerability_reports': SmartContract}


class RiskAssessment(Base):
    """
    Represents a dynamic risk assessment of a smart contract.
    """
    __tablename__ = 'risk_assessments'

    id = Column(UUID, primary_key=True)
    contractAddress = Column(String, nullable=False, doc="Address of the assessed contract")
    riskScore = Column(Float, nullable=False, doc="Overall risk score")
    vulnerabilityCount = Column(Integer, nullable=False, doc="Number of vulnerabilities detected")
    lastUpdated = Column(DateTime, nullable=False, doc="Timestamp of the last risk assessment update")

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, contractAddress='{self.contractAddress}', riskScore={self.riskScore})>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()

from datetime import datetime

if __name__ == '__main__':
    # Example Usage (for testing)
    from sqlalchemy import create_engine, text
    engine = create_engine('sqlite:///:memory:')  # Use SQLite for testing
    Base.metadata.create_all(bind=engine)

    smart_contract1 = SmartContract(address='0x123...', name='ContractA', abi='...')
    vulnerability_report1 = VulnerabilityReport(contractAddress='0x123...', vulnerabilityType='Reentrancy', severity='Critical', description='...')
    risk_assessment1 = RiskAssessment(contractAddress='0x123...', riskScore=0.8, vulnerabilityCount=2)

    engine.connect()
    smart_contract1.id = UUID.generate()
    vulnerability_report1.id = UUID.generate()
    risk_assessment1.id = UUID.generate()

    engine.add(smart_contract1)
    engine.add(vulnerability_report1)
    engine.add(risk_assessment1)

    engine.commit()
    engine.close()