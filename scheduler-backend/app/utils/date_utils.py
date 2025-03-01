from datetime import datetime, timezone

def to_utc_isoformat(dt: datetime) -> str:
    """
    Convert a datetime object to an ISO 8601 formatted string in UTC with a trailing 'Z'.
    If the datetime is naive (i.e. no timezone information), it is assumed to be in UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    # Use strftime to ensure the 'Z' suffix for UTC.
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
