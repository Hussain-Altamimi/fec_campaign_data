#!/usr/bin/env python3
"""Create FEC-to-Bioguide ID crosswalk.

DEPRECATED: Use 'python -m fec bioguide create' instead.

This script is a backward-compatibility wrapper that delegates to the
consolidated fec module.
"""

import sys
import warnings

warnings.warn(
    "This script is deprecated. Use 'python -m fec bioguide create' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import and run the CLI command
from fec.cli.bioguide import create

if __name__ == "__main__":
    create()
