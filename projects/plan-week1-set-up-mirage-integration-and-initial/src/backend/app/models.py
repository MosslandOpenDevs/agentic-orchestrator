from sqlalchemy import Column, String, DateTime, JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import back_populates

Base = declarative_base()

class DAOStrategy(Base):
    """
    Represents a specific DAO governance strategy being simulated.
    """
    __tablename__ = 'dao_strategies'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=True)
    updated_at = Column(DateTime, server_default=True)

    def __repr__(self):
        return f"<DAOStrategy(id={self.id}, name='{self.name}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()


class SimulationResult(Base):
    """
    Stores the outcome of a simulation run for a given DAO strategy.
    """
    __tablename__ = 'simulation_results'

    id = Column(UUID, primary_key=True)
    strategyId = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    outcome = Column(JSON, nullable=False)

    def __repr__(self):
        return f"<SimulationResult(id={self.id}, strategyId='{self.strategyId}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()

    back_populates = back_populates('DAOStrategy', 'strategyId')


class AgentState(Base):
    """
    Stores the state of the agent (e.g., current parameters, last simulation result).
    """
    __tablename__ = 'agent_states'

    id = Column(UUID, primary_key=True)
    strategyId = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    lastSimulationResultId = Column(String, nullable=True)

    def __repr__(self):
        return f"<AgentState(id={self.id}, strategyId='{self.strategyId}')>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = UUID.generate()
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()

    back_populates = back_populates('DAOStrategy', 'strategyId')