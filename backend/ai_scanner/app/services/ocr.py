# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import re
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Tuple

import pytesseract
from PIL import Image as PILImage
from PIL import ImageEnhance, ImageFilter, ImageOps


@dataclass
class OcrExtraction:
    raw_text: str = ""
    product_name: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    batch_number: Optional[str] = None
    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    label_confidence: float = 0.0
    fields: List[str] = field(default_factory=list)


_DATE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})"), "%Y-%m-%d"),
    (re.compile(r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})"), "%d-%m-%Y"),
    (re.compile(r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{2})"), "%d-%m-%y"),
    (re.compile(r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})"), "%m-%d-%Y"),
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


class OcrEngine:
    """Pre-process images and run Tesseract OCR to extract packaging fields."""

    @staticmethod
    def _preprocess(image: PILImage.Image) -> PILImage.Image:
        # Work on a copy; keep original dimensions.
        img = image.convert("L")

        # Auto-contrast (histogram stretch) handles low-light and washed-out labels.
        img = ImageOps.autocontrast(img, cutoff=1)

        # Sharpen text edges to help curved and reflective labels.
        img = ImageEnhance.Sharpness(img).enhance(2.0)

        # Mild contrast boost after sharpening.
        img = ImageEnhance.Contrast(img).enhance(1.5)

        # Denoise to reduce reflection speckles.
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # Scale small images up so tiny date text reaches Tesseract's comfort zone.
        w, h = img.size
        min_dim = min(w, h)
        if min_dim < 800:
            factor = max(2, 800 / min_dim)
            img = img.resize((int(w * factor), int(h * factor)), PILImage.Resampling.LANCZOS)

        return img

    @staticmethod
    def _is_likely_label_line(line: str) -> bool:
        return any(re.search(kw, line, re.IGNORECASE) for kw in _LABEL_KEYWORDS)

    @staticmethod
    def _extract_dates(line: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        expiry: Optional[datetime] = None
        production: Optional[datetime] = None
        low = line.lower()
        is_expiry = any(
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
        is_production = any(
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
                if candidate.year < 1950:
                    candidate = candidate.replace(year=candidate.year + 100)
                if candidate.year > 2100:
                    continue
                if is_expiry:
                    expiry = expiry or candidate
                elif is_production:
                    production = production or candidate
                else:
                    if expiry is None or candidate > expiry:
                        expiry = candidate
        return production, expiry

    @staticmethod
    def _extract_barcode(text: str) -> Optional[str]:
        for match in re.finditer(r"\b\d{8,14}\b", text):
            return match.group(0)
        return None

    @staticmethod
    def _extract_batch(line: str) -> Optional[str]:
        patterns = [
            re.compile(r"(?:batch|lot)\s*(?:no\.?|number)?\s*[:\-]?\s*([A-Z0-9\-]{3,})", re.IGNORECASE),
            re.compile(r"(?:batch|lot)[:\-]?\s*([A-Z0-9\-]{3,})", re.IGNORECASE),
            re.compile(r"\b([A-Z]{1,3}\d{2,}[A-Z0-9]*)\b"),
        ]
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _looks_like_product_word(word: str) -> bool:
        if len(word) < 3:
            return False
        if re.search(r"\d{4,}", word):
            return False
        if re.search(r"\b\d{1,2}[\-/\. ]\d{1,2}[\-/\. ]\d{2,4}\b", word):
            return False
        letters = sum(1 for c in word if c.isalpha())
        if letters < 3 or letters / max(len(word), 1) < 0.5:
            return False
        return True

    def _extract_words(self, image: PILImage.Image) -> Tuple[List[dict], PILImage.Image]:
        preprocessed = self._preprocess(image)
        try:
            data = pytesseract.image_to_data(preprocessed, output_type=pytesseract.Output.DICT)
        except Exception:
            data = pytesseract.image_to_data(image.convert("RGB"), output_type=pytesseract.Output.DICT)

        words = []
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = (data["text"][i] or "").strip()
            conf = int(data["conf"][i] or -1)
            if not text or conf < 30 or len(text) < 2:
                continue
            words.append(
                {
                    "text": text,
                    "conf": conf,
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "w": data["width"][i],
                    "h": data["height"][i],
                    "line": data["line_num"][i],
                }
            )
        return words, preprocessed

    @staticmethod
    def _words_to_lines(words: List[dict]) -> List[str]:
        # Sort by y then x; group by close y.
        words = sorted(words, key=lambda w: (w["y"], w["x"]))
        lines: List[List[dict]] = []
        for w in words:
            placed = False
            for line in lines:
                if abs(line[-1]["y"] - w["y"]) <= max(line[-1]["h"], w["h"]) * 0.6:
                    line.append(w)
                    placed = True
                    break
            if not placed:
                lines.append([w])
        return [" ".join(word["text"] for word in sorted(line, key=lambda x: x["x"])) for line in lines]

    @staticmethod
    def _best_brand(lines: List[str]) -> Optional[str]:
        # Brand is often the first prominent all-caps or title line near the top.
        for line in lines[:8]:
            if not OcrEngine._is_likely_label_line(line) and len(line) >= 3:
                if line.isupper() and len(line.split()) <= 4:
                    return line.strip()
                if line.istitle() and len(line.split()) <= 5:
                    return line.strip()
        return None

    @staticmethod
    def _best_product_name(lines: List[str], brand: Optional[str] = None) -> Optional[str]:
        candidates = []
        for line in lines:
            if OcrEngine._is_likely_label_line(line):
                continue
            if brand and line.lower() == brand.lower():
                continue
            if OcrEngine._looks_like_product_word(line):
                candidates.append(line)
        if not candidates:
            return None
        # Prefer the longest clean marketing-style line; if brand was found, prefer it for product name too.
        if brand:
            for c in candidates:
                if brand.lower() in c.lower() and len(c) > len(brand):
                    return c.strip()
        return max(candidates, key=len).strip()

    def extract(self, image: PILImage.Image) -> OcrExtraction:
        try:
            words, preprocessed = self._extract_words(image)
            lines = self._words_to_lines(words)
            raw_text = "\n".join(lines)
            avg_conf = sum(w["conf"] for w in words) / len(words) if words else 0.0

            production_date: Optional[datetime] = None
            expiry_date: Optional[datetime] = None
            batch_number: Optional[str] = None
            detected_fields: List[str] = []

            for line in lines:
                prod, exp = self._extract_dates(line)
                if prod and production_date is None:
                    production_date = prod
                    detected_fields.append("production_date")
                if exp and expiry_date is None:
                    expiry_date = exp
                    detected_fields.append("expiry_date")
                if batch_number is None:
                    b = self._extract_batch(line)
                    if b:
                        batch_number = b
                        detected_fields.append("batch_number")

            brand = self._best_brand(lines)
            product_name = self._best_product_name(lines, brand=brand) or brand
            barcode = self._extract_barcode(raw_text)
            if barcode:
                detected_fields.append("barcode")
            if product_name:
                detected_fields.append("product_name")
            if brand:
                detected_fields.append("brand")

            return OcrExtraction(
                raw_text=raw_text,
                product_name=product_name,
                brand=brand,
                barcode=barcode,
                batch_number=batch_number,
                production_date=production_date,
                expiry_date=expiry_date,
                label_confidence=round(avg_conf / 100, 3),
                fields=detected_fields,
            )
        except Exception:
            return OcrExtraction()


extract_from_image = OcrEngine().extract


def extract_from_bytes(content: bytes) -> OcrExtraction:
    return extract_from_image(PILImage.open(BytesIO(content)))
