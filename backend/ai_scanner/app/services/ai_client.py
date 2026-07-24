# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from typing import Optional

import httpx
from fastapi import UploadFile

from ai_scanner.app.schemas import ScanResult
from ai_scanner.config import settings


class AIAnalysisError(Exception):
    """Raised when the AI inference service cannot be reached or returns an error."""

    pass


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
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise AIAnalysisError(f"AI inference service unavailable: {exc}") from exc


ai_client = AIClient()
