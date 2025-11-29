"""SQLAlchemy ORM models."""
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base
import uuid


class BacktestRun(Base):
    """Backtest run model."""
    __tablename__ = "backtest_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False, default="pending")
    total_scenarios = Column(Integer, default=0)
    completed_scenarios = Column(Integer, default=0)
    strategy_type = Column(String(50), nullable=False, default="standard")
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)


class BacktestScenario(Base):
    """Backtest scenario model."""
    __tablename__ = "backtest_scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False)
    params = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    error = Column(Text, nullable=True)
    strategy_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BacktestResult(Base):
    """Backtest result model."""
    __tablename__ = "backtest_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("backtest_scenarios.id", ondelete="CASCADE"), nullable=False)
    grouping = Column(JSON, nullable=True)
    totals = Column(JSON, nullable=True)
    kpis = Column(JSON, nullable=True)
    strategy_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StrategyRequest(Base):
    """Strategy request model - stores the original strategy description."""
    __tablename__ = "strategy_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False, unique=True)
    request_text = Column(Text, nullable=False)  # Original strategy description
    mode = Column(String(20), nullable=False)  # 'ai' or 'grid'
    created_at = Column(DateTime(timezone=True), server_default=func.now())



