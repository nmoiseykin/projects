"""Timezone conversion helpers."""
from datetime import datetime
import pytz
from app.core.config import settings


def convert_cst_to_ny(timestamp: datetime) -> datetime:
    """
    Convert timestamp from America/Chicago (CST) to America/New_York (NY).
    
    Args:
        timestamp: Datetime object in CST
        
    Returns:
        Datetime object in NY timezone
    """
    cst = pytz.timezone(settings.TZ_DB_SOURCE)
    ny = pytz.timezone(settings.TZ_TRADING)
    
    # If timestamp is naive, assume it's in CST
    if timestamp.tzinfo is None:
        timestamp = cst.localize(timestamp)
    
    # Convert to NY
    return timestamp.astimezone(ny)


def parse_time_string(time_str: str) -> str:
    """
    Parse time string and ensure it's in HH:MM:SS format.
    
    Args:
        time_str: Time string (e.g., "09:45", "9:45:00")
        
    Returns:
        Time string in HH:MM:SS format
    """
    parts = time_str.split(":")
    if len(parts) == 2:
        return f"{time_str}:00"
    return time_str



