"""Pydantic schemas for backtest API."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Direction(str, Enum):
    """Trade direction."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class ScenarioParams(BaseModel):
    """Parameters for a single backtest scenario."""
    entry_time_start: str = Field(..., description="Start of entry time window (HH:MM:SS)")
    entry_time_end: str = Field(..., description="End of entry time window (HH:MM:SS)")
    trade_end_time: str = Field(default="16:00:00", description="Trade window end time (HH:MM:SS), default 4pm")
    target_pts: float = Field(..., gt=0, description="Target points")
    stop_pts: float = Field(..., gt=0, description="Stop loss points")
    direction: Optional[Direction] = Field(None, description="Direction override (optional)")
    year_start: int = Field(..., ge=2000, le=2100, description="Start year")
    year_end: int = Field(..., ge=2000, le=2100, description="End year")
    # Trend filter parameters
    trend_enabled: Optional[bool] = Field(False, description="Enable trend filtering")
    trend_timeframe: Optional[str] = Field("15m", description="Timeframe for trend calculation (e.g., '15m', '30m', '1h')")
    trend_period: Optional[int] = Field(20, description="Period for moving average (e.g., 20 for 20-period MA)")
    trend_type: Optional[str] = Field("sma", description="Type of moving average: 'sma' or 'ema'")
    trend_strict: Optional[bool] = Field(True, description="If True, only trade in trend direction. If False, allow counter-trend when direction is specified")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entry_time_start": "09:00:00",
                "entry_time_end": "11:00:00",
                "trade_end_time": "16:00:00",
                "target_pts": 60.0,
                "stop_pts": 30.0,
                "direction": "bullish",
                "year_start": 2020,
                "year_end": 2025
            }
        }


class BacktestRequest(BaseModel):
    """Request to create a backtest run."""
    scenarios: List[ScenarioParams] = Field(..., min_items=1)
    strategy_text: Optional[str] = Field(None, description="Original strategy description/request")
    mode: Optional[str] = Field(None, description="Generation mode: 'ai' or 'grid'")


class RunStatus(str, Enum):
    """Backtest run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestRunResponse(BaseModel):
    """Response for backtest run creation."""
    run_id: str
    status: RunStatus
    total_scenarios: int
    created_at: datetime


class BacktestRunStatus(BaseModel):
    """Status of a backtest run."""
    run_id: str
    status: RunStatus
    total_scenarios: int
    completed_scenarios: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    strategy_text: Optional[str] = None
    mode: Optional[str] = None
    strategy_type: Optional[str] = None
    scenario_params: Optional[dict] = None
    overall_win_rate: Optional[float] = None  # Overall win rate percentage across all results


class ResultGrouping(BaseModel):
    """Grouping information for results."""
    year: Optional[int] = None
    direction: Optional[str] = None
    candle_time: Optional[str] = None
    dow: Optional[int] = None  # Day of week (0=Monday, 6=Sunday)


class ResultKPIs(BaseModel):
    """Key performance indicators."""
    win_rate_percent: float
    total_trades: int
    wins: int
    losses: int
    timeouts: int
    expectancy_r: Optional[float] = None
    profit_factor: Optional[float] = None


class BacktestResult(BaseModel):
    """Single backtest result."""
    id: str
    scenario_id: str
    grouping: Dict[str, Any]
    totals: Dict[str, Any]
    kpis: ResultKPIs


class BacktestResultsResponse(BaseModel):
    """Response containing backtest results."""
    run_id: str
    results: List[BacktestResult]
    total: int
    page: int = 1
    page_size: int = 100


class AISuggestRequest(BaseModel):
    """Request for AI scenario suggestions."""
    recent_results: Optional[List[Dict[str, Any]]] = None
    context: Optional[str] = None
    num_scenarios: int = 10


class AISuggestResponse(BaseModel):
    """AI-generated scenario suggestions."""
    scenarios: List[ScenarioParams]
    reasoning: Optional[str] = None


class GridSearchRequest(BaseModel):
    """Request for grid search scenario generation."""
    entry_time_starts: List[str] = Field(..., description="List of entry window start times (HH:MM:SS)")
    entry_time_ends: List[str] = Field(..., description="List of entry window end times (HH:MM:SS)")
    trade_end_times: List[str] = Field(default=["16:00:00"], description="List of trade end times (HH:MM:SS)")
    target_pts_list: List[float] = Field(..., description="List of target point values")
    stop_pts_list: List[float] = Field(..., description="List of stop loss point values")
    directions: List[Optional[str]] = Field(default=[None], description="List of directions (None, 'bullish', 'bearish')")
    year_start: int = Field(..., ge=2000, le=2100, description="Start year")
    year_end: int = Field(..., ge=2000, le=2100, description="End year")
    # Trend filter parameters (optional, applied to all scenarios if enabled)
    trend_enabled: Optional[bool] = Field(False, description="Enable trend filtering for all scenarios")
    trend_timeframe: Optional[str] = Field("15m", description="Timeframe for trend calculation")
    trend_period: Optional[int] = Field(20, description="Period for moving average")
    trend_type: Optional[str] = Field("sma", description="Type: 'sma' or 'ema'")
    trend_strict: Optional[bool] = Field(True, description="Strict mode: only trade with trend")


class GridSearchResponse(BaseModel):
    """Grid search scenario generation response."""
    scenarios: List[ScenarioParams]
    total_combinations: int
    valid_scenarios: int


class AIExplainRequest(BaseModel):
    """Request for AI strategy explanation."""
    results: List[BacktestResult]
    context: Optional[str] = None


class AIExplainResponse(BaseModel):
    """AI-generated strategy explanation."""
    explanation: str  # Markdown format
    summary: Optional[str] = None


class AIAnalyzeRequest(BaseModel):
    """Request for AI strategy analysis."""
    results: List[BacktestResult]
    context: Optional[str] = None


class AIAnalyzeResponse(BaseModel):
    """AI-generated strategy analysis."""
    analysis: str  # Markdown format with viability, testing, trust, recommendations
    summary: Optional[str] = None

