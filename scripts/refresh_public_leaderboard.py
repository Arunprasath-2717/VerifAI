#!/usr/bin/env python3
"""Weekly refresh of sourced public LiveBench benchmark scores.

Run: .venv/bin/python scripts/refresh_public_leaderboard.py
Exit nonzero on fetch/validation failure. Never destroys the last valid file.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.modules.benchmarks.public_leaderboard import (
    refresh_public_snapshot,
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    try:
        snapshot, changed = refresh_public_snapshot()
    except Exception as exc:  # noqa: BLE001 - CLI must convert refresh errors to exit status
        print(
            (
                f"PUBLIC_LEADERBOARD_REFRESH_FAILED: {type(exc).__name__}: "
                f"{str(exc)[:180]}"
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    print(
        f"LiveBench {snapshot['benchmark_release']} · "
        f"source update {snapshot['source_updated_at']} · "
        f"{snapshot['total_models']} models · {'updated' if changed else 'unchanged'}"
    )
