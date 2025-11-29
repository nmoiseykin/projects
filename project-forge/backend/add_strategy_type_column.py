"""Add strategy_type column to backtest_runs table if it doesn't exist."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.db import engine
from app.core.logging import logger, setup_logging
from sqlalchemy import text

async def add_strategy_type_column():
    """Add strategy_type column to backtest_runs table."""
    setup_logging()
    
    logger.info("Adding strategy_type column to backtest_runs table...")
    
    try:
        async with engine.begin() as conn:
            # Check if column exists
            check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'backtest_runs' 
            AND column_name = 'strategy_type'
            """
            result = await conn.execute(text(check_sql))
            exists = result.fetchone()
            
            if exists:
                logger.info("Column 'strategy_type' already exists in backtest_runs table")
            else:
                # Add the column
                alter_sql = """
                ALTER TABLE backtest_runs 
                ADD COLUMN strategy_type VARCHAR(50) NOT NULL DEFAULT 'standard'
                """
                await conn.execute(text(alter_sql))
                logger.info("✅ Added 'strategy_type' column to backtest_runs table")
                
                # Also check and add to backtest_scenarios if needed
                check_scenario_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'backtest_scenarios' 
                AND column_name = 'strategy_type'
                """
                result = await conn.execute(text(check_scenario_sql))
                exists = result.fetchone()
                
                if not exists:
                    alter_scenario_sql = """
                    ALTER TABLE backtest_scenarios 
                    ADD COLUMN strategy_type VARCHAR(50)
                    """
                    await conn.execute(text(alter_scenario_sql))
                    logger.info("✅ Added 'strategy_type' column to backtest_scenarios table")
                
                # Also check and add to backtest_results if needed
                check_result_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'backtest_results' 
                AND column_name = 'strategy_type'
                """
                result = await conn.execute(text(check_result_sql))
                exists = result.fetchone()
                
                if not exists:
                    alter_result_sql = """
                    ALTER TABLE backtest_results 
                    ADD COLUMN strategy_type VARCHAR(50)
                    """
                    await conn.execute(text(alter_result_sql))
                    logger.info("✅ Added 'strategy_type' column to backtest_results table")
        
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error adding columns: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(add_strategy_type_column())

