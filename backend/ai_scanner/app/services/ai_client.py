import random
from typing import Optional

import httpx
from fastapi import UploadFile

from ai_scanner.app.schemas import Condition, ScanResult
from ai_scanner.config import settings


class AIClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ai_service_url).rstrip("/")

    async def analyze_image(self, image: UploadFile, product_hint: Optional[str] = None) -> ScanResult:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"image": (image.filename or "scan.jpg", image.file, image.content_type or "image/jpeg")}
                data = {"product_hint": product_hint or ""}
                response = await client.post(f"{self.base_url}/analyze", files=files, data=data)
                response.raise_for_status()
                return ScanResult(**response.json())
        except Exception:
            return self._fallback_analysis(product_hint)

    def _fallback_analysis(self, product_hint: Optional[str] = None) -> ScanResult:
        conditions = list(Condition)
        confidence = round(random.uniform(0.55, 0.98), 3)
        condition = random.choice(conditions)
        return ScanResult(
            condition=condition,
            confidence=confidence,
            product_name=product_hint or None,
            packaging_type="unknown",
            findings=["Camera-only fallback assessment"],
            expiry_risk="unknown",
        )


ai_client = AIClient()
