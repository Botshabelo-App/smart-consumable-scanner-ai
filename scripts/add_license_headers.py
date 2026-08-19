"""Add or update license headers in project source files.

Usage:
    python scripts/add_license_headers.py [paths...]

Defaults to: backend ai-service mobile/src mobile/scripts backend/scripts ai-service/scripts
"""
import argparse
import sys
from pathlib import Path

PY_HEADER = """# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""

TS_HEADER = """// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

"""

COPYRIGHT_MARKERS = {
    "#": "Copyright 2026 Moeketsi Daniel",
    "//": "Copyright 2026 Moeketsi Daniel",
}


def needs_header(text: str, comment: str) -> bool:
    return COPYRIGHT_MARKERS[comment] not in text[:500]


def add_header(path: Path, header: str, comment: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if not needs_header(text, comment):
        return False
    lines = text.splitlines(keepends=True)
    prefix = []
    # Preserve shebang and encoding cookie in Python files.
    while lines and lines[0].startswith(("#!", "# -*- coding")):
        prefix.append(lines.pop(0))
        if lines and lines[0] == "\n":
            prefix.append(lines.pop(0))
    new_text = "".join(prefix) + header + "".join(lines)
    path.write_text(new_text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        default=["backend", "ai-service", "mobile/src", "mobile/scripts", "backend/scripts", "ai-service/scripts"],
    )
    args = parser.parse_args()

    updated = 0
    skipped = 0
    for root in args.paths:
        base = Path(root)
        if not base.exists():
            print(f"Skipping missing path: {root}")
            continue
        for ext, (header, comment) in {
            ".py": (PY_HEADER, "#"),
            ".ts": (TS_HEADER, "//"),
            ".tsx": (TS_HEADER, "//"),
        }.items():
            for path in base.rglob(f"*{ext}"):
                if "node_modules" in path.parts or ".venv" in path.parts or "__pycache__" in path.parts:
                    continue
                if add_header(path, header, comment):
                    updated += 1
                    print(f"Updated: {path}")
                else:
                    skipped += 1
    print(f"\nUpdated: {updated}, Already present or skipped: {skipped}")


if __name__ == "__main__":
    main()
