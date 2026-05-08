from sqlalchemy import Column, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class NFTTransaction(Base):
    __tablename__ = 'nft_transaction'

    id = Column(UUID, primary_key=True)
    portfolio_id = Column(String, ForeignKey('portfolio.id'))
    nft_collection_id = Column(String, ForeignKey('nft_collection.id'))
    quantity = Column(Integer)
    transaction_timestamp = Column(DateTime)

    def __repr__(self):
        return f"<NFTTransaction(id={self.id}, portfolio_id={self.portfolio_id}, nft_collection_id={self.nft_collection_id}, quantity={self.quantity}, timestamp={self.transaction_timestamp})>"

    back_populates = {'portfolio': 'portfolio'}
    back_populates = {'nft_collection': 'nft_collection'}


class NFTCollection(Base):
    __tablename__ = 'nft_collection'

    id = Column(UUID, primary_key=True)
    name = Column(String)
    contract_address = Column(String)
    token_id = Column(String)

    def __repr__(self):
        return f"<NFTCollection(id={self.id}, name={self.name}, contract_address={self.contract_address}, token_id={self.token_id})>"

class Portfolio(Base):
    __tablename__ = 'portfolio'

    id = Column(UUID, primary_key=True)
    user_id = Column(String)
    total_value = Column(Float)
    created_at = Column(DateTime, server_default=DateTime.now)
    updated_at = Column(DateTime, server_default=DateTime.now, onupdate=DateTime.now)

    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, total_value={self.total_value})>"

class RiskAssessment(Base):
    __tablename__ = 'risk_assessment'

    id = Column(UUID, primary_key=True)
    portfolio_id = Column(String, ForeignKey('portfolio.id'))
    gpt5_output = Column(String)

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, portfolio_id={self.portfolio_id}, gpt5_output={self.gpt5_output})>"

if __name__ == '__main__':
    Base.metadata.create_all(engine)