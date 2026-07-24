from typing import List, Optional

import numpy as np
from PIL import Image

from ai_service.schemas import Condition, ProductCategory, ScanResult


class ConsumableClassifier:
    """Honest fallback used only when real PyTorch models are unavailable.

    It never fabricates a confident AI result. Instead it returns a low-confidence
    assessment based on simple image statistics and clearly labels it as fallback.
    """

    def __init__(self):
        self.framework = "fallback"

    def predict(self, image: Image.Image, product_hint: Optional[str] = None) -> ScanResult:
        arr = np.array(image.convert("RGB").resize((224, 224)))
        mean_rgb = arr.mean(axis=(0, 1))
        brightness = float(np.linalg.norm(mean_rgb) / (255 * np.sqrt(3)))
        saturation = float((np.std(arr, axis=(0, 1)).mean()) / 255.0)

        findings: List[str] = []
        findings.append("WARNING: real AI models are not loaded; using image-statistics fallback only.")
        findings.append(f"Mean RGB: {mean_rgb.astype(int).tolist()}")
        findings.append(f"Brightness: {brightness:.2f}, Saturation: {saturation:.2f}")

        if saturation < 0.05:
            findings.append("Low color saturation detected (possible discoloration)")
        if brightness < 0.25:
            findings.append("Very low brightness (possible mold or rotting)")

        condition, confidence = self._classify(brightness, saturation)
        category = self._infer_category(product_hint)

        return ScanResult(
            condition=condition,
            confidence=round(confidence, 3),
            product_name=product_hint or "Unknown product",
            category=category,
            packaging_type="unknown",
            findings=findings,
            expiry_risk="unknown",
        )

    def _classify(self, brightness: float, saturation: float) -> tuple[Condition, float]:
        if brightness > 0.7 and saturation > 0.2:
            return Condition.FRESH, 0.6
        if brightness < 0.35:
            return Condition.EXPIRED, 0.55
        if saturation < 0.08:
            return Condition.SUSPICIOUS, 0.55
        return Condition.NEAR_EXPIRY, 0.5

    def _infer_category(self, hint: Optional[str]) -> Optional[ProductCategory]:
        if not hint:
            return None
        hint_lower = hint.lower()
        mapping = {
            "milk": ProductCategory.DAIRY,
            "cheese": ProductCategory.DAIRY,
            "yogurt": ProductCategory.DAIRY,
            "beef": ProductCategory.MEAT,
            "chicken": ProductCategory.MEAT,
            "pork": ProductCategory.MEAT,
            "fish": ProductCategory.SEAFOOD,
            "apple": ProductCategory.PRODUCE,
            "bread": ProductCategory.FOOD,
            "water": ProductCategory.BEVERAGE,
            "juice": ProductCategory.BEVERAGE,
        }
        for key, value in mapping.items():
            if key in hint_lower:
                return value
        return None
