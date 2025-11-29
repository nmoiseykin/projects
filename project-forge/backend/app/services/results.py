"""Results persistence helpers."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.models.orm import BacktestResult as ORMResult
from app.core.logging import logger


async def save_results(
    session: AsyncSession,
    scenario_id: UUID,
    results: List[Dict[str, Any]],
    strategy_type: Optional[str] = None
) -> List[ORMResult]:
    """
    Save backtest results to database using batch insert for performance.
    
    Args:
        session: Database session
        scenario_id: Scenario ID
        results: List of result dictionaries
        strategy_type: Strategy type (e.g., 'ifvg', 'standard')
        
    Returns:
        List of saved ORM result objects
    """
    if not results:
        return []
    
    # Get strategy_type from scenario if not provided
    if strategy_type is None:
        from app.models.orm import BacktestScenario
        stmt = select(BacktestScenario).where(BacktestScenario.id == scenario_id)
        result = await session.execute(stmt)
        scenario = result.scalar_one_or_none()
        if scenario:
            strategy_type = scenario.strategy_type
    
    # Create ORM objects for batch insert
    orm_results = [
        ORMResult(
            scenario_id=scenario_id,
            grouping=result.get("grouping"),
            totals=result.get("totals"),
            kpis=result.get("kpis"),
            strategy_type=strategy_type
        )
        for result in results
    ]
    
    # Use add_all for batch insert (more efficient than individual adds)
    session.add_all(orm_results)
    await session.flush()  # Flush to get IDs without committing
    
    # Refresh objects to ensure they're fully loaded
    for orm_result in orm_results:
        await session.refresh(orm_result)
    
    await session.commit()
    logger.info(f"Saved {len(orm_results)} results for scenario {scenario_id} (batch insert)")
    return orm_results


async def get_results_by_scenario(
    session: AsyncSession,
    scenario_id: UUID
) -> List[ORMResult]:
    """
    Get all results for a scenario.
    
    Args:
        session: Database session
        scenario_id: Scenario ID
        
    Returns:
        List of result objects
    """
    stmt = select(ORMResult).where(ORMResult.scenario_id == scenario_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_results_by_run(
    session: AsyncSession,
    run_id: UUID,
    page: int = 1,
    page_size: int = 100,
    strategy_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all results for a run (paginated).
    
    Args:
        session: Database session
        run_id: Run ID
        page: Page number (1-indexed)
        page_size: Results per page
        strategy_type: Optional strategy type to filter results
        
    Returns:
        Tuple of (results list, total count)
    """
    from app.models.orm import BacktestScenario, BacktestRun
    
    # Get the run to check strategy_type
    stmt_run = select(BacktestRun).where(BacktestRun.id == run_id)
    run_result = await session.execute(stmt_run)
    run = run_result.scalar_one_or_none()
    
    if not run:
        return []
    
    # Get scenario IDs for this run
    stmt_scenarios = select(BacktestScenario.id).where(BacktestScenario.run_id == run_id)
    scenario_ids = await session.execute(stmt_scenarios)
    scenario_id_list = [row[0] for row in scenario_ids]
    
    if not scenario_id_list:
        return []
    
    # Get results, optionally filtered by strategy_type
    stmt = select(ORMResult).where(ORMResult.scenario_id.in_(scenario_id_list))
    
    # Filter by strategy_type if provided or if run has a strategy_type
    if strategy_type or run.strategy_type:
        target_strategy_type = strategy_type or run.strategy_type
        stmt = stmt.where(
            (ORMResult.strategy_type == target_strategy_type) | 
            (ORMResult.strategy_type.is_(None))
        )
    
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    results = list(result.scalars().all())
    
    # Convert to dictionaries for API response
    results_dict = []
    for result in results:
        results_dict.append({
            "id": str(result.id),
            "scenario_id": str(result.scenario_id),
            "grouping": result.grouping,
            "totals": result.totals,
            "kpis": result.kpis,
            "strategy_type": result.strategy_type,
            "created_at": result.created_at
        })
    
    return results_dict

