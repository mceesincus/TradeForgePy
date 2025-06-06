# tradeforgepy/utils/time_utils.py
from datetime import timezone, timedelta, datetime
from typing import Any

UTC_TZ = timezone.utc
"""A timezone object representing Coordinated Universal Time (UTC)."""

def ensure_utc(v: Any) -> datetime | Any:
    """
    Pydantic validator utility to ensure a datetime object is timezone-aware and in UTC.
    Handles naive datetimes, timezone-aware datetimes, and ISO 8601 strings.
    If the input is not a recognizable datetime format, it's returned as-is
    for Pydantic's default validation to handle.
    """
    if isinstance(v, datetime):
        if v.tzinfo is None:
            # For naive datetimes, assume UTC
            return v.replace(tzinfo=UTC_TZ)
        # For aware datetimes, convert to UTC
        return v.astimezone(UTC_TZ)
    
    if isinstance(v, str):
        try:
            # Handle ISO 8601 strings, including those with 'Z'
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC_TZ)
            return dt.astimezone(UTC_TZ)
        except (ValueError, TypeError):
            # If it's not a valid ISO string, pass it on for other validation
            pass
            
    # Return the original value if it's not a datetime or valid string
    # (e.g., None, which is valid for optional fields)
    return v