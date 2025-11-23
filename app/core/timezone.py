"""
Timezone utilities for handling Brazilian time (America/Sao_Paulo)
All datetime objects in the application should be timezone-aware using Brazil timezone.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Brazil timezone (America/Sao_Paulo)
BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def now_br() -> datetime:
    """
    Get current datetime in Brazilian timezone
    
    Returns:
        datetime: Current datetime with Brazil timezone
    """
    return datetime.now(BRAZIL_TZ)


def utc_to_br(dt: datetime) -> datetime:
    """
    Convert UTC datetime to Brazilian timezone
    
    Args:
        dt: datetime object (timezone-aware or naive)
        
    Returns:
        datetime: datetime in Brazilian timezone
    """
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BRAZIL_TZ)


def br_to_utc(dt: datetime) -> datetime:
    """
    Convert Brazilian datetime to UTC
    
    Args:
        dt: datetime object in Brazilian timezone
        
    Returns:
        datetime: datetime in UTC timezone
    """
    if dt.tzinfo is None:
        # Assume Brazil timezone if naive
        dt = dt.replace(tzinfo=BRAZIL_TZ)
    return dt.astimezone(timezone.utc)


def make_aware(dt: datetime, tz: ZoneInfo = BRAZIL_TZ) -> datetime:
    """
    Make a naive datetime timezone-aware
    
    Args:
        dt: naive datetime object
        tz: timezone to use (default: Brazil timezone)
        
    Returns:
        datetime: timezone-aware datetime
    """
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=tz)
