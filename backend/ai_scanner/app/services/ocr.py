# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Optional, Tuple

import pytesseract
from PIL import Image
from PIL import Image as PILImage


@dataclass
class OcrExtraction:
    raw_text: str
    product_name: Optional[str] = None
    barcode: Optional[str] = None
    batch_number: Optional[str] = None
    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


_DATE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # ISO / dashed / dotted / slashed 4-digit year
    (re.compile(r"(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})"), "%Y-%m-%d"),
    (re.compile(r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})"), "%d-%m-%Y"),
    # 2-digit year (assume 20YY for 00-49, 19YY for 50-99)
    (re.compile(r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{2})"), "%d-%m-%y"),
]


_LABEL_KEYWORDS = [
    r"best\s*before",
    r"best\s*by",
    r"use\s*by",
    r"expiry",
    r"expiration",
    r"exp\b",
    r"bb\b",
    r"consume\s*before",
    r"sell\s*by",
    r"mfg\b",
    r"manufactur(?:ing|ed)",
    r"production",
    r"produced",
    r"packed",
    r"batch",
    r"lot\b",
    r"lot\s*no",
    r"batch\s*no",
    r"b/n",
    r"l/n",
]


def _is_likely_label_line(line: str) -> bool:
    low = line.lower()
    return any(re.search(keyword, low) for keyword in _LABEL_KEYWORDS)


def _extract_dates(line: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    expiry: Optional[datetime] = None
    production: Optional[datetime] = None
    low = line.lower()
    is_expiry_label = any(
        re.search(k, low)
        for k in [
            r"best\s*before",
            r"best\s*by",
            r"use\s*by",
            r"expiry",
            r"expiration",
            r"exp\b",
            r"bb\b",
            r"consume\s*before",
            r"sell\s*by",
        ]
    )
    is_production_label = any(
        re.search(k, low)
        for k in [
            r"mfg\b",
            r"manufactur(?:ing|ed)",
            r"production",
            r"produced",
            r"packed",
            r"packing",
        ]
    )

    for pattern, fmt in _DATE_PATTERNS:
        for match in pattern.finditer(line):
            try:
                groups = match.groups()
                candidate = datetime.strptime("-".join(groups), fmt)
            except ValueError:
                continue
            # Normalise two-digit years
            if candidate.year < 1950:
                candidate = candidate.replace(year=candidate.year + 100)
            if candidate.year > 2099:
                continue

            if is_expiry_label:
                expiry = expiry or candidate
            elif is_production_label:
                production = production or candidate
            else:
                # If no label keyword, prefer the latest date as expiry because
                # expiry dates are usually printed larger / more prominently.
                if expiry is None or candidate > expiry:
                    expiry = candidate
    return production, expiry


def _extract_barcode(text: str) -> Optional[str]:
    # Look for 8-14 digit numeric sequences typical of EAN/UPC barcodes.
    for match in re.finditer(r"\b\d{8,14}\b", text):
        code = match.group(0)
        # EAN-13 checksum is too simple to verify blindly; accept if it starts
        # with a common GS1 prefix region digit (0-9).
        if code[0].isdigit():
            return code
    return None


def _extract_batch(line: str) -> Optional[str]:
    patterns = [
        re.compile(r"(?:batch|lot)\s*(?:no\.?|number)?\s*[:\-]?\s*([A-Z0-9\-]{3,})", re.IGNORECASE),
        re.compile(r"(?:batch|lot)[:\-]?\s*([A-Z0-9\-]{3,})", re.IGNORECASE),
        re.compile(r"\b([A-Z]{1,2}\d{3,}[A-Z0-9]*)\b"),
    ]
    for pattern in patterns:
        match = pattern.search(line)
        if match:
            return match.group(1).strip()
    return None


def _looks_like_product_name(line: str) -> bool:
    # Product names are usually alphabetic marketing names, not label lines or short codes.
    if len(line) < 3 or _is_likely_label_line(line):
        return False
    if re.search(r"\d{4,}", line):
        return False
    if re.search(r"\b\d{1,2}[\-/\. ]\d{1,2}[\-/\. ]\d{2,4}\b", line):
        return False
    letters = sum(1 for c in line if c.isalpha())
    if letters < 3 or letters / max(len(line), 1) < 0.5:
        return False
    return True


def _pick_product_name(lines: List[str]) -> Optional[str]:
    candidates = [line for line in lines if _looks_like_product_name(line)]
    if not candidates:
        return None
    # Prefer the longest all-caps or title-style line near the top.
    candidates.sort(key=lambda l: (-len(l), l))
    return candidates[0].strip()


def extract_from_image(image: PILImage.Image) -> OcrExtraction:
    """Run OCR on an image and extract product-package fields."""
    try:
        rgb = image.convert("RGB")
        text = pytesseract.image_to_string(rgb).strip()
    except Exception:
        text = ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    batch_number: Optional[str] = None
    for line in lines:
        prod, exp = _extract_dates(line)
        if prod and production_date is None:
            production_date = prod
        if exp and expiry_date is None:
            expiry_date = exp
        if batch_number is None:
            batch_number = _extract_batch(line)

    product_name = _pick_product_name(lines)
    barcode = _extract_barcode(text)

    return OcrExtraction(
        raw_text=text,
        product_name=product_name,
        barcode=barcode,
        batch_number=batch_number,
        production_date=production_date,
        expiry_date=expiry_date,
    )


def extract_from_bytes(content: bytes) -> OcrExtraction:
    return extract_from_image(PILImage.open(BytesIO(content)))
