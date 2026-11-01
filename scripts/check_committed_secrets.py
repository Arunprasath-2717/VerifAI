"""Fail CI on common hardcoded credentials in tracked source files.

This is a preventive guard, not a substitute for GitHub secret scanning,
credential rotation, or a review of repository history.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "Google API key": re.compile(r"\bAI" + r"za[0-9A-Za-z_-]{35}\b"),
    "GitHub personal access token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    "OpenAI-like private key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
    "PEM private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
SOURCE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".env",
    ".sh",
}
EXCLUDED = {"package-lock.json", "requirements-lock.txt"}


def main() -> int:
    tracked = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    findings = []
    examined = 0
    for rel in tracked:
        if not rel:
            continue
        path = ROOT / rel
        if (
            path.name in EXCLUDED
            or path.suffix not in SOURCE_SUFFIXES
            or not path.is_file()
        ):
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        examined += 1
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(source):
                line = source.count("\n", 0, match.start()) + 1
                findings.append((rel, line, name))
    for file, line, kind in findings:
        print(
            f"::error file={file},line={line}::Potential hardcoded {kind}; "
            "matched value withheld"
        )
    print(f"Scanned {examined} tracked source/config files; findings: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
