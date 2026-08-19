# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import urllib.parse
from datetime import datetime
from typing import Any, Dict, Optional

import httpx


def _parse_date(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, int):
        # assume Unix timestamp seconds
        return datetime.utcfromtimestamp(value)
    if isinstance(value, str):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
    return None


def lookup_barcode(code: str) -> Optional[Dict[str, Any]]:
    """Look up a barcode via Open Food Facts and normalize the response."""
    try:
        with httpx.Client(timeout=10.0) as client:
            url = f"https://world.openfoodfacts.org/api/v2/product/{urllib.parse.quote(code)}.json"
            resp = client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
    except Exception:
        return None

    if data.get("status") != 1:
        return None
    product = data.get("product", {})
    return {
        "name": product.get("product_name") or product.get("generic_name"),
        "brand": product.get("brands", "").split(",")[0].strip() if product.get("brands") else None,
        "manufacturer": product.get("owner") or product.get("brands"),
        "categories": product.get("categories", ""),
        "packaging": product.get("packaging", ""),
        "quantity": product.get("quantity"),
        "image_url": product.get("image_url"),
        "nutrition_grade": product.get("nutrition_grade_fr"),
        "expiration_date": _parse_date(product.get("expiration_date")),
        "manufacturing_places": product.get("manufacturing_places"),
        "countries": product.get("countries", ""),
    }
