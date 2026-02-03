#!/usr/bin/env python3
"""Download FEC individual contributions data.

DEPRECATED: Use 'python -m fec individual download' instead.

This script is a backward-compatibility wrapper that delegates to the
consolidated fec module.
"""

import sys
import warnings

warnings.warn(
    "This script is deprecated. Use 'python -m fec individual download' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import and run the CLI command
from fec.cli.individual import download

if __name__ == "__main__":
    download()
