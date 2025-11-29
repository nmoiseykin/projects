"""AI API routes."""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from app.core.config import settings
from app.models.backtest import (
    AISuggestRequest,
    AISuggestResponse,
    AIExplainRequest,
    AIExplainResponse,
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    GridSearchRequest,
    GridSearchResponse
)
from app.services.ai import ai_service
from app.services.scenarios import generate_grid_scenarios
from app.core.logging import logger

router = APIRouter(prefix="/ai", tags=["ai"])


def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    """Verify API key."""
    if settings.API_KEY:
        if not x_api_key or x_api_key != settings.API_KEY:
            logger.warning(f"Invalid API key attempt. Expected: {settings.API_KEY[:10]}..., Got: {x_api_key[:10] if x_api_key else 'None'}...")
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.post("/suggest", response_model=AISuggestResponse)
async def suggest_scenarios(
    request: AISuggestRequest,
    _: bool = Depends(verify_api_key)
):
    """Generate AI-suggested scenarios."""
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured")
        raise HTTPException(
            status_code=503, 
            detail="AI service not configured. Please set OPENAI_API_KEY in .env file"
        )
    
    try:
        scenarios = await ai_service.suggest_scenarios(
            recent_results=request.recent_results,
            context=request.context,
            num_scenarios=request.num_scenarios
        )
        
        if not scenarios:
            logger.warning("AI service returned empty scenarios list")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate scenarios. Check OpenAI API key and try again."
            )
        
        return AISuggestResponse(
            scenarios=scenarios,
            reasoning="AI-generated scenarios based on recent results"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in suggest_scenarios endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating scenarios: {str(e)}"
        )


@router.post("/explain", response_model=AIExplainResponse)
async def explain_strategy(
    request: AIExplainRequest,
    _: bool = Depends(verify_api_key)
):
    """Generate AI strategy explanation."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    explanation = await ai_service.explain_strategy(
        results=request.results,
        context=request.context
    )
    
    return AIExplainResponse(
        explanation=explanation,
        summary="AI-generated strategy analysis"
    )


@router.post("/analyze", response_model=AIAnalyzeResponse)
async def analyze_strategy(
    request: AIAnalyzeRequest,
    _: bool = Depends(verify_api_key)
):
    """Analyze strategy viability, testing adequacy, trustworthiness, and provide recommendations."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    analysis = await ai_service.analyze_strategy(
        results=request.results,
        context=request.context
    )
    
    return AIAnalyzeResponse(
        analysis=analysis,
        summary="AI-generated strategy analysis"
    )


@router.post("/grid", response_model=GridSearchResponse)
async def generate_grid(
    request: GridSearchRequest,
    _: bool = Depends(verify_api_key)
):
    """Generate all possible scenario combinations (grid search)."""
    try:
        # Calculate total possible combinations
        # Handle entry time pairs (discrete points if lists are identical, otherwise windows)
        if len(request.entry_time_starts) == len(request.entry_time_ends) and request.entry_time_starts == request.entry_time_ends:
            # Discrete entry points (paired by index)
            entry_time_combinations = len(request.entry_time_starts)
        else:
            # Entry windows (all combinations)
            entry_time_combinations = len(request.entry_time_starts) * len(request.entry_time_ends)
        
        # Handle TP/SL pairs (matching if same length, otherwise all combinations)
        if len(request.target_pts_list) == len(request.stop_pts_list):
            tp_sl_combinations = len(request.target_pts_list)
        else:
            tp_sl_combinations = len(request.target_pts_list) * len(request.stop_pts_list)
        
        total_combinations = (
            entry_time_combinations *
            len(request.trade_end_times) *
            tp_sl_combinations *
            len(request.directions)
        )
        
        logger.info(f"Generating grid search with {total_combinations} possible combinations")
        
        scenarios = generate_grid_scenarios(
            entry_time_starts=request.entry_time_starts,
            entry_time_ends=request.entry_time_ends,
            trade_end_times=request.trade_end_times,
            target_pts_list=request.target_pts_list,
            stop_pts_list=request.stop_pts_list,
            directions=request.directions,
            year_start=request.year_start,
            year_end=request.year_end,
            # Pass trend parameters
            trend_enabled=request.trend_enabled or False,
            trend_timeframe=request.trend_timeframe or "15m",
            trend_period=request.trend_period or 20,
            trend_type=request.trend_type or "sma",
            trend_strict=request.trend_strict if request.trend_enabled else True
        )
        
        logger.info(f"Generated {len(scenarios)} valid scenarios from {total_combinations} combinations")
        
        return GridSearchResponse(
            scenarios=scenarios,
            total_combinations=total_combinations,
            valid_scenarios=len(scenarios)
        )
        
    except Exception as e:
        logger.error(f"Error generating grid scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating grid scenarios: {str(e)}"
        )

