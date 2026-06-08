from sqlalchemy import Column, String, Float, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import back_populates

Base = declarative_base()

class User(Base):
    """
    Represents a Mossland NFT holder.
    """
    __tablename__ = 'user'

    id = Column(UUID, primary_key=True)
    nft_id = Column(String, unique=True)
    createdAt = Column(DateTime)

    def __repr__(self):
        return f"<User(id={self.id}, nft_id={self.nft_id})>"


class Portfolio(Base):
    """
    Represents a user's DeFi portfolio.
    """
    __tablename__ = 'portfolio'

    id = Column(UUID, primary_key=True)
    userId = Column(String, index=True)
    risk_profile = Column(String)
    createdAt = Column(DateTime)
    updated_at = Column(DateTime, default=DateTime.utcnow)

    def __repr__(self):
        return f"<Portfolio(id={self.id}, userId={self.userId}, risk_profile={self.risk_profile})>"

    back_populates = {'userId': User}


class Position(Base):
    """
    Represents a single asset holding within a portfolio.
    """
    __tablename__ = 'position'

    id = Column(UUID, primary_key=True)
    portfolioId = Column(String, index=True)
    asset_id = Column(String)
    quantity = Column(Float)
    createdAt = Column(DateTime)
    updated_at = Column(DateTime, default=DateTime.utcnow)

    def __repr__(self):
        return f"<Position(id={self.id}, portfolioId={self.portfolioId}, asset_id={self.asset_id}, quantity={self.quantity})>"

    back_populates = {'portfolioId': Portfolio}


class AIModel(Base):
    """
    Represents the AI model used for portfolio optimization.
    """
    __tablename__ = 'ai_model'

    id = Column(UUID, primary_key=True)
    model_version = Column(String)

    def __repr__(self):
        return f"<AIModel(id={self.id}, model_version={self.model_version})>"

if __name__ == '__main__':
    Base.metadata.create_all(engine)