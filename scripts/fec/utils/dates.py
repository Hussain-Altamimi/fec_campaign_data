"""Date parsing utilities for FEC data.

FEC dates can be in several formats:
- MMDDYYYY (8 chars): e.g., "01152024" for January 15, 2024
- MDDYYYY (7 chars): e.g., "1152024" for January 15, 2024
- MM/DD/YYYY: e.g., "01/15/2024"
"""


def extract_year_from_date(date_str: str | None) -> int | None:
    """Extract year from FEC date string.

    Handles MMDDYYYY, MDDYYYY, and MM/DD/YYYY formats.

    Args:
        date_str: Date string in FEC format

    Returns:
        Year as integer, or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Handle MM/DD/YYYY format
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3 and len(parts[2]) == 4:
            try:
                return int(parts[2])
            except ValueError:
                return None

    # Handle MMDDYYYY format (8 chars) - year is last 4
    if len(date_str) == 8:
        try:
            return int(date_str[4:8])
        except ValueError:
            return None

    # Handle MDDYYYY format (7 chars) - year is last 4
    if len(date_str) == 7:
        try:
            return int(date_str[3:7])
        except ValueError:
            return None

    return None


def extract_month_from_date(date_str: str | None) -> int | None:
    """Extract month from FEC date string.

    Handles MMDDYYYY, MDDYYYY, and MM/DD/YYYY formats.

    Args:
        date_str: Date string in FEC format

    Returns:
        Month as integer (1-12), or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Handle MM/DD/YYYY format
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3 and len(parts[0]) in (1, 2):
            try:
                return int(parts[0])
            except ValueError:
                return None

    # Handle MMDDYYYY format (8 chars) - month is first 2
    if len(date_str) == 8:
        try:
            return int(date_str[0:2])
        except ValueError:
            return None

    # Handle MDDYYYY format (7 chars) - month is first 1
    if len(date_str) == 7:
        try:
            return int(date_str[0:1])
        except ValueError:
            return None

    return None


def convert_to_iso_date(date_str: str | None) -> str | None:
    """Convert FEC date to ISO 8601 (YYYY-MM-DD) format.

    Handles MMDDYYYY, MDDYYYY, and MM/DD/YYYY formats.

    Args:
        date_str: Date in FEC format (e.g., "12/31/2024" or "12312024")

    Returns:
        Date in YYYY-MM-DD format (e.g., "2024-12-31"), or None if invalid/empty
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    month = None
    day = None
    year = None

    # Handle MM/DD/YYYY format
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3:
            try:
                month = int(parts[0])
                day = int(parts[1])
                year = int(parts[2])
            except ValueError:
                return None
    # Handle MMDDYYYY format (8 chars)
    elif len(date_str) == 8:
        try:
            month = int(date_str[0:2])
            day = int(date_str[2:4])
            year = int(date_str[4:8])
        except ValueError:
            return None
    # Handle MDDYYYY format (7 chars)
    elif len(date_str) == 7:
        try:
            month = int(date_str[0:1])
            day = int(date_str[1:3])
            year = int(date_str[3:7])
        except ValueError:
            return None
    else:
        return None

    # Validate date components
    if month is None or day is None or year is None:
        return None
    if not (1 <= month <= 12):
        return None
    if not (1 <= day <= 31):
        return None
    if not (1900 <= year <= 2100):
        return None

    # Return ISO 8601 format
    return f"{year:04d}-{month:02d}-{day:02d}"
