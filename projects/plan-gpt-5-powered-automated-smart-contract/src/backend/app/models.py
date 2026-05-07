from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class SmartContract(Base):
    __tablename__ = 'smart_contracts'

    id = Column(UUID, primary_key=True, default=uuid4)
    contractAddress = Column(String, nullable=False)
    contractName = Column(String, nullable=False)
    creationTimestamp = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<SmartContract(id={self.id}, contractAddress='{self.contractAddress}', contractName='{self.contractName}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = uuid4()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()


class VulnerabilityReport(Base):
    __tablename__ = 'vulnerability_reports'

    id = Column(UUID, primary_key=True, default=uuid4)
    reportId = Column(String, nullable=False)
    contractAddress = Column(String, nullable=False)
    vulnerabilityType = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    confidenceScore = Column(Float, nullable=False)
    createdAt = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<VulnerabilityReport(id={self.id}, reportId='{self.reportId}', contractAddress='{self.contractAddress}', vulnerabilityType='{self.vulnerabilityType}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = uuid4()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()
        
    back_populates('smart_contracts')

class RiskAssessment(Base):
    __tablename__ = 'risk_assessments'

    id = Column(UUID, primary_key=True, default=uuid4)
    assessmentId = Column(String, nullable=False)
    contractAddress = Column(String, nullable=False)
    riskScore = Column(Float, nullable=False)
    riskFactors = Column(String, nullable=False)
    createdAt = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, assessmentId='{self.assessmentId}', contractAddress='{self.contractAddress}', riskScore={self.riskScore})>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = uuid4()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()
        
    back_populates('smart_contracts')


# Example usage (not part of the model definition)
# if __name__ == '__main__':
#     Base.metadata.create_all(engine)
#     smart_contract = SmartContract(contractAddress="0x...", contractName="MyContract")
#     vulnerability_report = VulnerabilityReport(contractAddress=smart_contract.contractAddress, vulnerabilityType="Reentrancy", severity="Critical")
#     vulnerability_report.smart_contracts = [smart_contract]
#     risk_assessment = RiskAssessment(contractAddress=smart_contract.contractAddress, riskScore=0.8)
#     risk_assessment.smart_contracts = [smart_contract]