"""KPI calculation and analysis."""
from typing import Dict, Any, List
from app.core.logging import logger


def calculate_kpis(
    total_trades: int,
    wins: int,
    losses: int,
    timeouts: int,
    target_pts: float,
    stop_pts: float
) -> Dict[str, Any]:
    """
    Calculate key performance indicators.
    
    Args:
        total_trades: Total number of trades
        wins: Number of winning trades
        losses: Number of losing trades
        timeouts: Number of trades that timed out
        target_pts: Target points
        stop_pts: Stop loss points
        
    Returns:
        Dictionary of KPIs
    """
    if total_trades == 0:
        return {
            "win_rate_percent": 0.0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "timeouts": 0,
            "expectancy_r": 0.0,
            "profit_factor": 0.0
        }
    
    win_rate = (wins / total_trades) * 100.0
    loss_rate = (losses / total_trades)
    
    # Expectancy in R (risk units)
    # Expectancy = (Win% * WinSize) - (Loss% * LossSize)
    # In R terms: (p * target_pts/stop_pts) - ((1-p) * 1)
    # Simplified: (p * R) - (1-p) where R = target_pts/stop_pts
    r_ratio = target_pts / stop_pts if stop_pts > 0 else 0
    expectancy_r = (win_rate / 100.0 * r_ratio) - (loss_rate * 1.0)
    
    # Profit factor = (Wins * Avg Win) / (Losses * Avg Loss)
    # Assuming target_pts for wins and stop_pts for losses
    avg_win = target_pts
    avg_loss = stop_pts
    profit_factor = (wins * avg_win) / (losses * avg_loss) if losses > 0 else float('inf')
    
    return {
        "win_rate_percent": round(win_rate, 2),
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "timeouts": timeouts,
        "expectancy_r": round(expectancy_r, 4),
        "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else None
    }


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate multiple result rows into summary statistics.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Aggregated statistics
    """
    if not results:
        return {
            "total_trades": 0,
            "total_wins": 0,
            "total_losses": 0,
            "total_timeouts": 0,
            "overall_win_rate": 0.0
        }
    
    total_trades = sum(r.get("total_trades", 0) for r in results)
    total_wins = sum(r.get("wins", 0) for r in results)
    total_losses = sum(r.get("losses", 0) for r in results)
    total_timeouts = sum(r.get("timeouts", 0) for r in results)
    
    overall_win_rate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    
    return {
        "total_trades": total_trades,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_timeouts": total_timeouts,
        "overall_win_rate": round(overall_win_rate, 2)
    }


