# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Seed common manufacturers into the database.

Usage:
    cd backend
    DATABASE_URL=postgresql://... python scripts/seed_manufacturers.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_scanner.app.db.database import SessionLocal
from ai_scanner.app.db.models import Manufacturer

MANUFACTURERS = [
    {"name": "Coca-Cola", "country": "United States"},
    {"name": "PepsiCo", "country": "United States"},
    {"name": "Nestlé", "country": "Switzerland"},
    {"name": "Tiger Brands", "country": "South Africa"},
    {"name": "Clover", "country": "South Africa"},
    {"name": "Parmalat", "country": "Italy"},
    {"name": "Danone", "country": "France"},
    {"name": "Heineken", "country": "Netherlands"},
    {"name": "SAB", "country": "South Africa"},
    {"name": "Unilever", "country": "United Kingdom/Netherlands"},
]


def seed():
    db = SessionLocal()
    for item in MANUFACTURERS:
        existing = db.query(Manufacturer).filter(Manufacturer.name == item["name"]).first()
        if not existing:
            db.add(Manufacturer(**item))
    db.commit()
    print(f"Seeded {len(MANUFACTURERS)} manufacturers.")
    db.close()


if __name__ == "__main__":
    seed()
