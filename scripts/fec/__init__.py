"""FEC data processing utilities and CLI.

This package provides tools for downloading, processing, and analyzing
FEC (Federal Election Commission) campaign finance data.

Usage:
    python -m fec [command]

Commands:
    update check    - Check for FEC data updates
    update run      - Download and process updates
    update status   - Show update state
    individual      - Individual contributions commands (coming soon)
    bioguide        - Bioguide crosswalk commands (coming soon)
    verify          - Verify data integrity
"""

__version__ = "1.0.0"

# Re-export key classes for convenience
from .config import Config, UpdateState, CycleState
from .detect import ChangeInfo, detect_changes
from .verify import ValidationResult, verify_all

__all__ = [
    "Config",
    "UpdateState",
    "CycleState",
    "ChangeInfo",
    "detect_changes",
    "ValidationResult",
    "verify_all",
]
