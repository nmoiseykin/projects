"""Script to create database tables."""
import asyncio
from app.core.db import engine, Base
from app.models.orm import BacktestRun, BacktestScenario, BacktestResult, StrategyRequest
from app.core.logging import logger


async def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())


