# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import re
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
import calendar
from typing import Dict, List, Optional, Tuple

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
    # Every date found on the label with its original text and interpretation.
    date_candidates: List[dict] = field(default_factory=list)
    # detected | needs_verification per extracted field (missing fields are absent).
    field_status: Dict[str, str] = field(default_factory=dict)


_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"

# (regex, format label). Order matters: full dates before month/year forms.
_DATE_REGEXES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"(?<!\d)(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})(?!\d)"), "YYYY-MM-DD"),
    (re.compile(r"(?<!\d)(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})(?!\d)"), "DD/MM/YYYY"),
    (re.compile(r"(?<!\d)(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{2})(?!\d)"), "DD/MM/YY"),
    (re.compile(rf"(?<!\d)(\d{{1,2}})\s*[-/\. ]?\s*{_MON}\s*[-/\. ]?\s*(\d{{4}}|\d{{2}})(?!\d)", re.IGNORECASE), "DD MON YYYY"),
    (re.compile(rf"\b{_MON}\s*[-/\. ]?\s*(\d{{4}})(?!\d)", re.IGNORECASE), "MON YYYY"),
    (re.compile(r"(?<!\d)(\d{1,2})[-/\.](\d{4})(?!\d)"), "MM/YYYY"),
    (re.compile(r"(?<![\d\-/\.])(\d{4})[-/\.](\d{1,2})(?![-/\.\d])"), "YYYY-MM"),
]

_DATE_TYPE_KEYWORDS: List[Tuple[str, str]] = [
    ("best_before", r"best\s*before|best\s*by|\bbb\b|\bbbe\b|\bb\.b\.?"),
    ("expiry", r"use\s*by|expiry|expiration|expires|\bexp\b\.?|consume\s*(?:by|before)|sell\s*by"),
    ("packaging", r"packed|packing\s*date|\bpkd\b|packaged"),
    ("production", r"\bmfg\b|\bmfd\b|manufactur(?:ing|ed)|production|produced|\bprod\b|\bdom\b"),
]


def _month_end(year: int, month: int) -> datetime:
    return datetime(year, month, calendar.monthrange(year, month)[1])


def _interpret(fmt: str, groups: Tuple[str, ...]) -> Optional[Tuple[datetime, str, str]]:
    """Return (date, status, note) or None if the text is not a plausible date."""
    status, note = "detected", ""
    try:
        if fmt == "YYYY-MM-DD":
            y, m, d = int(groups[0]), int(groups[1]), int(groups[2])
        elif fmt in ("DD/MM/YYYY", "DD/MM/YY"):
            d, m, y = int(groups[0]), int(groups[1]), int(groups[2])
            if fmt == "DD/MM/YY":
                y += 2000
            if m > 12 and d <= 12:
                d, m = m, d
                status, note = "needs_verification", "Day/month order unclear; read as MM/DD."
        elif fmt == "DD MON YYYY":
            d, m, y = int(groups[0]), _MONTHS[groups[1].lower()[:3]], int(groups[2])
            if y < 100:
                y += 2000
        elif fmt in ("MON YYYY", "MM/YYYY", "YYYY-MM"):
            if fmt == "MON YYYY":
                m, y = _MONTHS[groups[0].lower()[:3]], int(groups[1])
            elif fmt == "MM/YYYY":
                m, y = int(groups[0]), int(groups[1])
            else:
                y, m = int(groups[0]), int(groups[1])
            if not (2000 <= y <= 2100 and 1 <= m <= 12):
                return None
            return _month_end(y, m), "detected", "Month/year only; read as the last day of that month."
        else:
            return None
        if not 2000 <= y <= 2100:
            return None
        return datetime(y, m, d), status, note
    except (ValueError, KeyError):
        return None


def _date_type_at(line: str, pos: int) -> Optional[str]:
    """Label type of the closest keyword before `pos` (or anywhere in the line)."""
    best: Optional[Tuple[int, str]] = None
    fallback: Optional[str] = None
    for dtype, pattern in _DATE_TYPE_KEYWORDS:
        for m in re.finditer(pattern, line, re.IGNORECASE):
            if m.start() <= pos and (best is None or m.start() > best[0]):
                best = (m.start(), dtype)
            fallback = fallback or dtype
    return best[1] if best else fallback


def find_dates(lines: List[str]) -> List[dict]:
    """Find all dates in OCR lines, keeping the original text and the label type.

    A label on a line without a date (e.g. "BEST BEFORE") applies to the next line.
    Dates with no label are reported as "unlabelled" and are never assumed to be expiry.
    """
    out: List[dict] = []
    pending_type: Optional[str] = None
    for line in lines:
        masked = line
        found_in_line = False
        for regex, fmt in _DATE_REGEXES:
            for m in regex.finditer(masked):
                parsed = _interpret(fmt, m.groups())
                if not parsed:
                    continue
                value, status, note = parsed
                dtype = _date_type_at(line, m.start()) or pending_type or "unlabelled"
                if dtype == "unlabelled":
                    status = "needs_verification"
                    note = (note + " " if note else "") + "No label next to this date; not assumed to be the expiry date."
                out.append({
                    "type": dtype,
                    "original_text": line.strip(),
                    "matched_text": m.group(0).strip(),
                    "format": fmt,
                    "interpreted": value.date().isoformat(),
                    "status": status,
                    "note": note.strip(),
                })
                found_in_line = True
                masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
        if found_in_line:
            pending_type = None
        else:
            pending_type = _date_type_at(line, len(line))
    return out


def pick_date(candidates: List[dict], types: Tuple[str, ...]) -> Tuple[Optional[datetime], Optional[str]]:
    """First candidate of the given types, preferring confirmed readings."""
    matches = [c for c in candidates if c["type"] in types]
    matches.sort(key=lambda c: (types.index(c["type"]), c["status"] != "detected"))
    if not matches:
        return None, None
    c = matches[0]
    return datetime.fromisoformat(c["interpreted"]), c["status"]


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
    def _extract_barcode(text: str) -> Optional[str]:
        for match in re.finditer(r"\b\d{8,14}\b", text):
            return match.group(0)
        return None

    @staticmethod
    def _extract_batch(line: str) -> Tuple[Optional[str], Optional[str]]:
        """Return (batch, status); unlabelled code-like text needs verification."""
        labelled = [
            re.compile(r"(?:batch|lot|b/n|l/n)\s*(?:no\.?|number|code)?\s*[:\-#]?\s*([A-Z0-9][A-Z0-9\-/]{2,})", re.IGNORECASE),
        ]
        for pattern in labelled:
            match = pattern.search(line)
            if match:
                return match.group(1).strip(), "detected"
        match = re.search(r"\b([A-Z]{1,3}\d{2,}[A-Z0-9]*)\b", line)
        if match and not re.search(r"\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}", line):
            return match.group(1).strip(), "needs_verification"
        return None, None

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

            detected_fields: List[str] = []
            field_status: Dict[str, str] = {}

            date_candidates = find_dates(lines)
            expiry_date, expiry_status = pick_date(date_candidates, ("expiry", "best_before"))
            production_date, production_status = pick_date(date_candidates, ("production",))
            if expiry_date:
                detected_fields.append("expiry_date")
                field_status["expiry_date"] = expiry_status
            if production_date:
                detected_fields.append("production_date")
                field_status["production_date"] = production_status

            batch_number: Optional[str] = None
            for line in lines:
                b, b_status = self._extract_batch(line)
                if b and (batch_number is None or (b_status == "detected" and field_status.get("batch_number") != "detected")):
                    batch_number = b
                    field_status["batch_number"] = b_status
            if batch_number:
                detected_fields.append("batch_number")

            brand = self._best_brand(lines)
            product_name = self._best_product_name(lines, brand=brand) or brand
            barcode = self._extract_barcode(raw_text)
            if barcode:
                detected_fields.append("barcode")
                field_status["barcode_code"] = "needs_verification"
            if product_name:
                detected_fields.append("product_name")
                field_status["product_name"] = "needs_verification"
            if brand:
                detected_fields.append("brand")
                field_status["brand"] = "needs_verification"

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
                date_candidates=date_candidates,
                field_status=field_status,
            )
        except Exception:
            return OcrExtraction()


extract_from_image = OcrEngine().extract


def decode_barcodes(content: bytes) -> List[str]:
    """Decode standard 1D/2D symbols (EAN/UPC/Code128/QR/DataMatrix) from the photo pixels."""
    try:
        import zxingcpp
    except ImportError:
        return []
    try:
        img = PILImage.open(BytesIO(content))
        img = ImageOps.exif_transpose(img).convert("RGB")
        results = zxingcpp.read_barcodes(img)
        if not results:
            results = zxingcpp.read_barcodes(ImageOps.autocontrast(img.convert("L")))
        return [r.text for r in results if r.text]
    except Exception:
        return []


def extract_from_bytes(content: bytes) -> OcrExtraction:
    img = PILImage.open(BytesIO(content))
    return extract_from_image(ImageOps.exif_transpose(img))
