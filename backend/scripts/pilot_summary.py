# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Generate a weekly pilot summary from the local database.

Usage:
    cd backend
    python scripts/pilot_summary.py [--output reports/pilot_summary_YYYY-MM-DD.md]
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_scanner.app.db.database import Base, SessionLocal, engine
from ai_scanner.app.services.pilot_reporting import build_weekly_report

Base.metadata.create_all(bind=engine)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(f"reports/pilot_summary_{datetime.now(timezone.utc).date().isoformat()}.md"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        report = build_weekly_report(db)
        args.output.write_text(report)
        print(f"Summary written to {args.output}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
