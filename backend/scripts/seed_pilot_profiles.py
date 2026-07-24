"""Seed default pilot profiles for RC1 deployment.

Usage:
    cd backend
    python scripts/seed_pilot_profiles.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_scanner.app.db.database import Base, SessionLocal, engine
from ai_scanner.app.db.models import PilotProfile

Base.metadata.create_all(bind=engine)

PROFILES = [
    {
        "name": "School Canteen",
        "organization_type": "school_canteen",
        "settings": {
            "require_photo_of_kitchen_area": False,
            "default_inspection_mode": "single_scan",
            "alert_conditions": ["expired", "suspicious"],
        },
        "branding": {
            "report_header": "School Canteen Food Safety Inspection",
            "report_footer": "For internal use only.",
        },
        "inspection_workflow": {
            "steps": ["scan", "verify", "record", "report"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Supermarket",
        "organization_type": "supermarket",
        "settings": {
            "require_barcode": True,
            "batch_tracking": True,
            "shelf_life_alert_days": 3,
        },
        "branding": {
            "report_header": "Supermarket Freshness Audit",
        },
        "inspection_workflow": {
            "steps": ["scan", "ai_check", "shelf_decision", "report"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Warehouse",
        "organization_type": "warehouse",
        "settings": {
            "pallet_mode": True,
            "require_batch_number": True,
            "temperature_check": True,
        },
        "branding": {
            "report_header": "Warehouse Receiving Inspection",
        },
        "inspection_workflow": {
            "steps": ["scan_pallet", "verify_batch", "ai_check", "report"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Food Manufacturer",
        "organization_type": "food_manufacturer",
        "settings": {
            "quality_control_mode": True,
            "traceability_required": True,
        },
        "branding": {
            "report_header": "Manufacturer Quality Control",
        },
        "inspection_workflow": {
            "steps": ["sample", "scan", "lab_check_optional", "record"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Wholesaler",
        "organization_type": "wholesaler",
        "settings": {
            "bulk_scan_mode": True,
            "invoice_link": True,
        },
        "branding": {
            "report_header": "Wholesaler Incoming Inspection",
        },
        "inspection_workflow": {
            "steps": ["scan_lot", "ai_check", "accept_or_reject", "report"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Restaurant",
        "organization_type": "restaurant",
        "settings": {
            "cold_chain_check": True,
            "expiry_alert_hours": 24,
        },
        "branding": {
            "report_header": "Restaurant Receiving Inspection",
        },
        "inspection_workflow": {
            "steps": ["scan", "temp_check", "ai_check", "store"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Hotel",
        "organization_type": "hotel",
        "settings": {
            "hospitality_mode": True,
            "min_shelf_life_days": 7,
        },
        "branding": {
            "report_header": "Hotel F&B Quality Check",
        },
        "inspection_workflow": {
            "steps": ["scan", "ai_check", "accept", "log"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Municipal Health Department",
        "organization_type": "municipal_health",
        "settings": {
            "enforcement_mode": True,
            "gps_required": True,
            "signature_required": True,
        },
        "branding": {
            "report_header": "Municipal Health Inspection Report",
        },
        "inspection_workflow": {
            "steps": ["scan", "verify", "override_if_needed", "sign", "report"],
            "require_override_reason": True,
        },
    },
    {
        "name": "Government Food Inspector",
        "organization_type": "government_inspector",
        "settings": {
            "enforcement_mode": True,
            "chain_of_custody": True,
            "gps_required": True,
        },
        "branding": {
            "report_header": "Government Food Inspector Report",
        },
        "inspection_workflow": {
            "steps": ["scan", "record_evidence", "ai_check", "decision", "report"],
            "require_override_reason": True,
        },
    },
]


def seed():
    db = SessionLocal()
    try:
        for profile in PROFILES:
            existing = db.query(PilotProfile).filter(PilotProfile.name == profile["name"]).first()
            if existing:
                print(f"Skipping existing profile: {profile['name']}")
                continue
            db.add(PilotProfile(
                name=profile["name"],
                organization_type=profile["organization_type"],
                settings=json.dumps(profile["settings"]),
                branding=json.dumps(profile["branding"]),
                inspection_workflow=json.dumps(profile["inspection_workflow"]),
            ))
        db.commit()
        print("Default pilot profiles seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
