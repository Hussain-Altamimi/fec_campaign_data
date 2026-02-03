#!/usr/bin/env python3
"""Add transaction_year column to individual contribution files.

DEPRECATED: Use 'python -m fec individual add-year' instead.

This script is a backward-compatibility wrapper that delegates to the
consolidated fec module.
"""

import sys
import warnings

warnings.warn(
    "This script is deprecated. Use 'python -m fec individual add-year' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import and run the CLI command
from fec.cli.individual import add_year

if __name__ == "__main__":
    add_year()
