from sqlalchemy import Column, Integer, String, Float, DateTime, UUID, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from uuid import uuid4

Base = declarative_base()

class RiskScore(Base):
    __tablename__ = 'risk_score'

    id = Column(String, primary_key=True)
    stablecoinId = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<RiskScore(id='{self.id}', score={self.score}, timestamp={self.timestamp})>"


class Stablecoin(Base):
    __tablename__ = 'stablecoin'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    totalSupply = Column(Integer, nullable=False)
    decimals = Column(Integer, nullable=False)
    riskScoreId = Column(String, ForeignKey('risk_score.id'))
    riskScore = Column(Float, ForeignKey('risk_score.score'), nullable=True)
    
    transactions = relationship("Transaction", back_populates="stablecoin")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Stablecoin(id='{self.id}', name='{self.name}', totalSupply={self.totalSupply}, decimals={self.decimals})>"


class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    sender = Column(String, nullable=False)
    receiver = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    blockNumber = Column(Integer, nullable=False)
    stablecoinId = Column(String, ForeignKey('stablecoin.id'))
    stablecoin = relationship("Stablecoin", back_populates="transactions")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction(id='{self.id}', timestamp={self.timestamp}, sender='{self.sender}', receiver='{self.receiver}', amount={self.amount})>"


class Validator(Base):
    __tablename__ = 'validator'

    id = Column(String, primary_key=True)
    address = Column(String, nullable=False)
    reputationScore = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Validator(id='{self.id}', address='{self.address}', reputationScore={self.reputationScore})>"


if __name__ == '__main__':
    # Example Usage (not for direct execution in a database)
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:')  # Use SQLite for testing
    Base.metadata.create_all(bind=engine)

    stablecoin1 = Stablecoin(name='USDC', totalSupply=1000000000, decimals=6)
    transaction1 = Transaction(sender='0x123...', receiver='0x456...', amount=1000, blockNumber=123)
    transaction1.stablecoin = stablecoin1
    stablecoin1.transactions.append(transaction1)

    risk_score1 = RiskScore(stablecoinId=stablecoin1.id, score=0.8, timestamp=datetime.utcnow())

    engine.connect()
    stablecoin1.riskScore = risk_score1.score
    stablecoin1.riskScoreId = risk_score1.id
    
    transaction1.stablecoinId = stablecoin1.id
    
    engine.session.add(stablecoin1)
    engine.session.add(transaction1)
    engine.session.commit()
    engine.disconnect()