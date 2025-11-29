"""iFVG Reversal strategy models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class IFVGScenarioParams(BaseModel):
    """Parameters for a single iFVG backtest scenario."""
    fvg_timeframe: str = Field(default="5m", description="Timeframe for FVG detection (e.g., '5m', '15m', '30m', '1h')")
    entry_timeframe: str = Field(default="1m", description="Timeframe for entry execution (e.g., '1m', '5m')")
    wait_candles: int = Field(default=24, ge=1, description="Number of FVG timeframe candles to wait for inversion")
    use_adaptive_rr: bool = Field(default=True, description="Use adaptive RR based on FVG size (True) or fixed RR (False)")
    target_pts: Optional[float] = Field(default=None, gt=0, description="Fixed target points (if use_adaptive_rr=False)")
    stop_pts: Optional[float] = Field(default=None, gt=0, description="Fixed stop loss points (if use_adaptive_rr=False)")
    extra_margin_pts: float = Field(default=5.0, ge=0, description="Extra margin points beyond FVG boundary for adaptive SL")
    rr_multiple: float = Field(default=2.0, gt=0, description="Risk-reward multiple for adaptive TP calculation")
    cutoff_time: str = Field(default="16:00:00", description="Session cutoff time (HH:MM:SS) in NY timezone")
    # Date range parameters (optional - if not provided, use year_start/year_end)
    year_start: Optional[int] = Field(default=None, ge=2000, le=2100, description="Start year (required if date_start not provided)")
    year_end: Optional[int] = Field(default=None, ge=2000, le=2100, description="End year (required if date_end not provided)")
    date_start: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD) - optional, overrides year_start if provided")
    date_end: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD) - optional, overrides year_end if provided")
    # Time filter parameters (optional - if not provided, allow all times)
    time_start: Optional[str] = Field(default=None, description="Start time filter (HH:MM:SS) in NY timezone - optional")
    time_end: Optional[str] = Field(default=None, description="End time filter (HH:MM:SS) in NY timezone - optional")
    # Liquidity filter parameters
    liquidity_enabled: bool = Field(default=False, description="Enable liquidity filter (only trade FVGs at swing highs/lows)")
    liquidity_timeframe: Optional[str] = Field(default=None, description="Timeframe for swing high/low detection (15m, 30m, 1h, 4h, 1d)")
    swing_lookback: int = Field(default=5, ge=1, le=50, description="Number of candles to look back/forward for swing detection")
    tolerance_pts: float = Field(default=5.0, ge=0, description="Price tolerance in points for matching FVG to swing level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fvg_timeframe": "5m",
                "entry_timeframe": "1m",
                "wait_candles": 24,
                "use_adaptive_rr": True,
                "extra_margin_pts": 5.0,
                "rr_multiple": 2.0,
                "cutoff_time": "16:00:00",
                "year_start": 2020,
                "year_end": 2025,
                "liquidity_enabled": False,
                "liquidity_timeframe": None,
                "swing_lookback": 5,
                "tolerance_pts": 5.0
            }
        }


class IFVGBacktestRequest(BaseModel):
    """Request to create an iFVG backtest run."""
    scenarios: List[IFVGScenarioParams]
    strategy_text: Optional[str] = None
    mode: Optional[str] = None


class IFVGResultKPIs(BaseModel):
    """iFVG-specific KPIs."""
    total_trades: int
    wins: int
    losses: int
    timeouts: int
    win_rate_percent: float
    avg_fvg_size: Optional[float] = None
    avg_tp_pts: Optional[float] = None
    avg_sl_pts: Optional[float] = None
    expectancy_r: Optional[float] = None
    profit_factor: Optional[float] = None


class IFVGResult(BaseModel):
    """iFVG backtest result."""
    id: str
    scenario_id: str
    grouping: Optional[dict] = None
    totals: Optional[dict] = None
    kpis: IFVGResultKPIs
    created_at: datetime


class IFVGResultsResponse(BaseModel):
    """Response containing iFVG backtest results."""
    run_id: str
    results: List[IFVGResult]
    total_results: int

