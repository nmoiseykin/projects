"""Initialize database tables."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.db import engine, Base
from app.models.orm import BacktestRun, BacktestScenario, BacktestResult, StrategyRequest
from app.core.logging import logger, setup_logging
from app.core.config import settings


async def init_database():
    """Create all database tables if they don't exist."""
    setup_logging()
    
    logger.info("Initializing database...")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully!")
        logger.info("   Created tables:")
        logger.info("   - backtest_runs")
        logger.info("   - backtest_scenarios")
        logger.info("   - backtest_results")
        logger.info("   - strategy_requests")
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database())


