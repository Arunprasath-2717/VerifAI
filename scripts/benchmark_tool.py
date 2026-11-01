#!/usr/bin/env python3
"""Standalone executable script for VerifAI Benchmark research CLI."""

import sys
from pathlib import Path

# Ensure root directory is on PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
