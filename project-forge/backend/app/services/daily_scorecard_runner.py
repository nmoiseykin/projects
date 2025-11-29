"""Daily Scorecard strategy runner."""
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.models.orm import BacktestScenario
from app.core.logging import logger


def get_calendar_week(date: datetime) -> int:
    """Get ISO calendar week number (1-53)."""
    return date.isocalendar()[1]


def get_week_start_end(year: int, week: int) -> tuple[datetime, datetime]:
    """
    Get the start (Sunday 00:00) and end (Friday 23:59:59) of a calendar week.
    Uses ISO week definition but adjusts to trading week (Sunday-Friday).
    """
    # Use a more reliable method: find the Monday of ISO week N
    # ISO week 1 is the first week with a Thursday in it
    # We'll find the Monday of week N by starting from Jan 4 (which is always in week 1)
    
    # Jan 4 is always in ISO week 1 of its year
    jan_4 = datetime(year, 1, 4)
    jan_4_iso = jan_4.isocalendar()
    jan_4_weekday = jan_4_iso[2]  # 1=Monday, 7=Sunday
    
    # Calculate days to get to Monday of week 1
    # Monday is weekday 1, so if Jan 4 is Monday, we're already there
    # Otherwise, go back to the Monday of that week
    days_to_monday_week1 = (1 - jan_4_weekday) % 7
    if jan_4_weekday > 1:
        days_to_monday_week1 = days_to_monday_week1 - 7
    
    # Monday of week 1
    monday_week1 = jan_4 + timedelta(days=days_to_monday_week1)
    
    # Monday of target week (week N)
    weeks_from_week1 = week - 1
    target_monday = monday_week1 + timedelta(weeks=weeks_from_week1)
    
    # Adjust to Sunday (trading week start) - Sunday is the day before Monday
    sunday = target_monday - timedelta(days=1)
    
    # Friday is 5 days after Sunday
    friday = sunday + timedelta(days=5)
    
    # Set times: Sunday 00:00:00, Friday 23:59:59
    week_start = sunday.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = friday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return week_start, week_end


async def run_daily_scorecard_scenario(
    session: AsyncSession,
    scenario: BacktestScenario,
    grouping_type: str = "hierarchical"
) -> List[Dict[str, Any]]:
    """
    Run a Daily Scorecard scenario.
    
    Calculates weekly and daily statistics for a specific calendar week
    across multiple years.
    
    Returns:
        List of result dictionaries with weekly and daily stats
    """
    params = scenario.params
    year_start = params.get('year_start', 2020)
    year_end = params.get('year_end', 2025)
    calendar_week = params.get('calendar_week')
    
    # If calendar_week not provided, use current week
    if calendar_week is None:
        now = datetime.now()
        calendar_week = get_calendar_week(now)
        logger.info(f"No calendar week specified, using current week: {calendar_week}")
    
    logger.info(f"Running Daily Scorecard: years {year_start}-{year_end}, calendar week {calendar_week}")
    
    # Fetch candle data only for the specific calendar week across all years
    # Use date ranges instead of EXTRACT(WEEK) for better index usage
    # We'll use 5m timeframe for granularity, but aggregate to daily/weekly
    all_rows = []
    for year in range(year_start, year_end + 1):
        week_start, week_end = get_week_start_end(year, calendar_week)
        logger.info(f"Fetching data for year {year}, week {calendar_week}: {week_start.date()} to {week_end.date()}")
        
        sql = """
        SELECT
          (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
          open_price,
          high_price,
          low_price,
          close_price
        FROM market.ohlcv_data
        WHERE timeframe = '5m'
          AND (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' >= :week_start
          AND (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' <= :week_end
        ORDER BY ts_ny
        """
        
        try:
            result = await session.execute(text(sql), {
                "week_start": week_start,
                "week_end": week_end
            })
            year_rows = result.fetchall()
            logger.info(f"Fetched {len(year_rows)} candles for year {year}, week {calendar_week}")
            all_rows.extend(year_rows)
        except Exception as e:
            logger.error(f"Error fetching data for year {year}, week {calendar_week}: {e}", exc_info=True)
            # Continue with other years even if one fails
            continue
    
    rows = all_rows
    logger.info(f"Total fetched {len(rows)} candles for calendar week {calendar_week} across all years")
    
    if len(rows) == 0:
        logger.warning(f"No data found for years {year_start}-{year_end}")
        return []
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'ts_ny': row.ts_ny,
            'open_price': float(row.open_price),
            'high_price': float(row.high_price),
            'low_price': float(row.low_price),
            'close_price': float(row.close_price)
        }
        for row in rows
    ])
    
    # Add date columns
    df['date'] = pd.to_datetime(df['ts_ny']).dt.date
    df['year'] = pd.to_datetime(df['ts_ny']).dt.year
    df['day_of_week'] = pd.to_datetime(df['ts_ny']).dt.dayofweek  # 0=Monday, 6=Sunday
    
    # No need to filter by week_number since SQL already filtered
    df_week = df.copy()
    
    if len(df_week) == 0:
        logger.warning(f"No data found for calendar week {calendar_week}")
        return []
    
    # Calculate weekly statistics
    weekly_data = []
    for year in range(year_start, year_end + 1):
        year_data = df_week[df_week['year'] == year].copy()
        if len(year_data) == 0:
            continue
        
        # Get Sunday open (first candle of Sunday in that week)
        # ISO week starts Monday, but we want Sunday
        # Find the first Sunday of the week
        week_start, week_end = get_week_start_end(year, calendar_week)
        
        # Filter data for this specific week
        year_week_data = year_data[
            (pd.to_datetime(year_data['ts_ny']) >= week_start) &
            (pd.to_datetime(year_data['ts_ny']) <= week_end)
        ].copy()
        
        if len(year_week_data) == 0:
            continue
        
        # Get Sunday open (first candle on or after week_start)
        sunday_candles = year_week_data[
            pd.to_datetime(year_week_data['ts_ny']).dt.date == week_start.date()
        ]
        if len(sunday_candles) == 0:
            # If no Sunday data, use first candle of the week
            sunday_open = year_week_data.iloc[0]['open_price']
        else:
            sunday_open = sunday_candles.iloc[0]['open_price']
        
        # Get Friday close (last candle on Friday)
        friday_candles = year_week_data[
            pd.to_datetime(year_week_data['ts_ny']).dt.date == week_end.date()
        ]
        if len(friday_candles) == 0:
            # If no Friday data, use last candle of the week
            friday_close = year_week_data.iloc[-1]['close_price']
        else:
            friday_close = friday_candles.iloc[-1]['close_price']
        
        # Weekly high and low
        week_high = year_week_data['high_price'].max()
        week_low = year_week_data['low_price'].min()
        week_range = week_high - week_low
        
        # Determine if bullish (Friday close > Sunday open)
        is_bullish = friday_close > sunday_open
        
        weekly_data.append({
            'year': year,
            'sunday_open': sunday_open,
            'friday_close': friday_close,
            'week_high': week_high,
            'week_low': week_low,
            'week_range': week_range,
            'is_bullish': is_bullish,
            'is_bearish': not is_bullish
        })
    
    # Calculate daily statistics
    daily_data_by_dow = {}  # day_of_week -> list of day stats
    
    for year in range(year_start, year_end + 1):
        year_data = df_week[df_week['year'] == year].copy()
        if len(year_data) == 0:
            continue
        
        week_start, week_end = get_week_start_end(year, calendar_week)
        year_week_data = year_data[
            (pd.to_datetime(year_data['ts_ny']) >= week_start) &
            (pd.to_datetime(year_data['ts_ny']) <= week_end)
        ].copy()
        
        if len(year_week_data) == 0:
            continue
        
        # Group by day of week (0=Monday, 6=Sunday)
        # Adjust: Sunday=0, Monday=1, ..., Saturday=6 (trading week perspective)
        for date_val in year_week_data['date'].unique():
            day_data = year_week_data[year_week_data['date'] == date_val].copy()
            if len(day_data) == 0:
                continue
            
            # Get day of week (0=Monday in pandas, but we want 0=Sunday for trading week)
            first_ts = pd.to_datetime(day_data.iloc[0]['ts_ny'])
            # Convert: pandas Monday=0 to our Sunday=0
            dow = (first_ts.weekday() + 1) % 7  # Sunday=0, Monday=1, ..., Saturday=6
            
            day_open = day_data.iloc[0]['open_price']
            day_close = day_data.iloc[-1]['close_price']
            day_high = day_data['high_price'].max()
            day_low = day_data['low_price'].min()
            day_range = day_high - day_low
            
            # Find the timestamp when high and low occurred
            high_idx = day_data['high_price'].idxmax()
            low_idx = day_data['low_price'].idxmin()
            high_ts = pd.to_datetime(day_data.loc[high_idx, 'ts_ny'])
            low_ts = pd.to_datetime(day_data.loc[low_idx, 'ts_ny'])
            
            # Extract time of day (seconds since midnight)
            high_time_seconds = high_ts.hour * 3600 + high_ts.minute * 60 + high_ts.second
            low_time_seconds = low_ts.hour * 3600 + low_ts.minute * 60 + low_ts.second
            
            is_bullish = day_close > day_open
            
            if dow not in daily_data_by_dow:
                daily_data_by_dow[dow] = []
            
            daily_data_by_dow[dow].append({
                'year': year,
                'day_open': day_open,
                'day_close': day_close,
                'day_high': day_high,
                'day_low': day_low,
                'day_range': day_range,
                'is_bullish': is_bullish,
                'is_bearish': not is_bullish,
                'high_time_seconds': high_time_seconds,
                'low_time_seconds': low_time_seconds
            })
    
    # Aggregate weekly stats
    total_weeks = len(weekly_data)
    bullish_count = sum(1 for w in weekly_data if w['is_bullish'])
    bearish_count = sum(1 for w in weekly_data if w['is_bearish'])
    bullish_percent = (bullish_count / total_weeks * 100) if total_weeks > 0 else 0.0
    bearish_percent = (bearish_count / total_weeks * 100) if total_weeks > 0 else 0.0
    # Calculate total weekly change (Friday close - Sunday open) summed across all weeks
    total_weekly_change = sum(w['friday_close'] - w['sunday_open'] for w in weekly_data)
    
    # Aggregate daily stats by day of week
    daily_stats_list = []
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    for dow in sorted(daily_data_by_dow.keys()):
        day_data = daily_data_by_dow[dow]
        total_days = len(day_data)
        
        if total_days == 0:
            continue
        
        bullish_days = [d for d in day_data if d['is_bullish']]
        bearish_days = [d for d in day_data if d['is_bearish']]
        
        bullish_count_d = len(bullish_days)
        bearish_count_d = len(bearish_days)
        bullish_percent_d = (bullish_count_d / total_days * 100) if total_days > 0 else 0.0
        bearish_percent_d = (bearish_count_d / total_days * 100) if total_days > 0 else 0.0
        
        avg_range = sum(d['day_range'] for d in day_data) / total_days if total_days > 0 else 0.0
        
        # Calculate average times (in seconds since midnight) for highs and lows
        avg_bullish_high_time = sum(d['high_time_seconds'] for d in bullish_days) / len(bullish_days) if bullish_days else None
        avg_bullish_low_time = sum(d['low_time_seconds'] for d in bullish_days) / len(bullish_days) if bullish_days else None
        avg_bearish_high_time = sum(d['high_time_seconds'] for d in bearish_days) / len(bearish_days) if bearish_days else None
        avg_bearish_low_time = sum(d['low_time_seconds'] for d in bearish_days) / len(bearish_days) if bearish_days else None
        
        # Convert seconds to HH:MM:SS format
        def seconds_to_time_str(seconds):
            if seconds is None:
                return None
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        daily_stats_list.append({
            'day_of_week': dow,
            'day_name': day_names[dow],
            'total_days': total_days,
            'bullish_count': bullish_count_d,
            'bearish_count': bearish_count_d,
            'bullish_percent': round(bullish_percent_d, 2),
            'bearish_percent': round(bearish_percent_d, 2),
            'avg_price_range': round(avg_range, 2),
            'avg_bullish_high_time': seconds_to_time_str(avg_bullish_high_time),
            'avg_bullish_low_time': seconds_to_time_str(avg_bullish_low_time),
            'avg_bearish_high_time': seconds_to_time_str(avg_bearish_high_time),
            'avg_bearish_low_time': seconds_to_time_str(avg_bearish_low_time)
        })
    
    # Create result in format expected by save_results
    # Store Daily Scorecard data in grouping field as JSON
    result = {
        'grouping': {
            'calendar_week': calendar_week,
            'year_start': year_start,
            'year_end': year_end,
            'weekly_stats': {
                'total_weeks': total_weeks,
                'bullish_count': bullish_count,
                'bearish_count': bearish_count,
                'bullish_percent': round(bullish_percent, 2),
                'bearish_percent': round(bearish_percent, 2),
                'total_weekly_change': round(total_weekly_change, 2)
            },
            'daily_stats': daily_stats_list
        },
        'totals': {
            'total_weeks': total_weeks,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        },
        'kpis': {
            'bullish_percent': round(bullish_percent, 2),
            'bearish_percent': round(bearish_percent, 2),
            'total_weekly_change': round(total_weekly_change, 2)
        }
    }
    
    logger.info(f"Daily Scorecard completed: {total_weeks} weeks analyzed, {len(daily_stats_list)} days of week")
    
    return [result]

