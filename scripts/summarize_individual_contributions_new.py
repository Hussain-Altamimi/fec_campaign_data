#!/usr/bin/env python3
"""Aggregate individual contributions by candidate.

DEPRECATED: Use 'python -m fec individual summarize' instead.

This script is a backward-compatibility wrapper that delegates to the
consolidated fec module.
"""

import sys
import warnings

warnings.warn(
    "This script is deprecated. Use 'python -m fec individual summarize' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import and run the CLI command
from fec.cli.individual import summarize

if __name__ == "__main__":
    summarize()
