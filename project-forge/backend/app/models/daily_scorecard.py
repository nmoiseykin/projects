"""Daily Scorecard strategy models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DailyScorecardScenarioParams(BaseModel):
    """Parameters for a Daily Scorecard scenario."""
    year_start: int = Field(default=2020, ge=2000, le=2100, description="Start year")
    year_end: int = Field(default=2025, ge=2000, le=2100, description="End year")
    calendar_week: int = Field(default=None, ge=1, le=53, description="Calendar week number (1-53). If not provided, uses current week.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "year_start": 2020,
                "year_end": 2025,
                "calendar_week": 44
            }
        }


class DailyScorecardBacktestRequest(BaseModel):
    """Request to create a Daily Scorecard backtest run."""
    scenarios: List[DailyScorecardScenarioParams]
    strategy_text: Optional[str] = None
    mode: Optional[str] = None


class DailyScorecardWeeklyStats(BaseModel):
    """Weekly statistics for the calendar week."""
    total_weeks: int = Field(description="Total number of weeks analyzed")
    bullish_count: int = Field(description="Number of bullish weeks (Friday close > Sunday open)")
    bearish_count: int = Field(description="Number of bearish weeks (Friday close < Sunday open)")
    bullish_percent: float = Field(description="Percentage of bullish weeks")
    bearish_percent: float = Field(description="Percentage of bearish weeks")
    total_weekly_change: float = Field(description="Total weekly change (sum of Friday close - Sunday open across all weeks)")


class DailyScorecardDailyStats(BaseModel):
    """Daily statistics for a specific day of week."""
    day_of_week: int = Field(description="Day of week (0=Sunday, 1=Monday, ..., 6=Saturday)")
    day_name: str = Field(description="Day name (Sunday, Monday, etc.)")
    total_days: int = Field(description="Total number of days analyzed")
    bullish_count: int = Field(description="Number of bullish days (close > open)")
    bearish_count: int = Field(description="Number of bearish days (close < open)")
    bullish_percent: float = Field(description="Percentage of bullish days")
    bearish_percent: float = Field(description="Percentage of bearish days")
    avg_price_range: float = Field(description="Average price range (high - low)")
    avg_bullish_high_time: Optional[str] = Field(default=None, description="Average time (HH:MM:SS) when high occurred on bullish days")
    avg_bullish_low_time: Optional[str] = Field(default=None, description="Average time (HH:MM:SS) when low occurred on bullish days")
    avg_bearish_high_time: Optional[str] = Field(default=None, description="Average time (HH:MM:SS) when high occurred on bearish days")
    avg_bearish_low_time: Optional[str] = Field(default=None, description="Average time (HH:MM:SS) when low occurred on bearish days")


class DailyScorecardResult(BaseModel):
    """Daily Scorecard backtest result."""
    id: str
    scenario_id: str
    calendar_week: int
    year_start: int
    year_end: int
    weekly_stats: DailyScorecardWeeklyStats
    daily_stats: List[DailyScorecardDailyStats]
    created_at: datetime


class DailyScorecardResultsResponse(BaseModel):
    """Response containing Daily Scorecard backtest results."""
    run_id: str
    results: List[DailyScorecardResult]
    total_results: int

