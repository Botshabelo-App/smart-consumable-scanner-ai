import random
from typing import List, Optional

import numpy as np
from PIL import Image

from ai_service.schemas import Condition, ProductCategory, ScanResult


class ConsumableClassifier:
    """Fallback camera-only classifier used when real models are not available."""

    def __init__(self):
        self.framework = "dummy"
        try:
            import tensorflow as tf  # noqa: F401
            self.framework = "tensorflow"
        except Exception:
            pass
        try:
            import torch  # noqa: F401
            if self.framework == "dummy":
                self.framework = "pytorch"
        except Exception:
            pass

    def predict(self, image: Image.Image, product_hint: Optional[str] = None) -> ScanResult:
        arr = np.array(image.convert("RGB").resize((224, 224)))
        mean_rgb = arr.mean(axis=(0, 1))
        brightness = float(np.linalg.norm(mean_rgb) / (255 * np.sqrt(3)))
        saturation = float((np.std(arr, axis=(0, 1)).mean()) / 255.0)

        findings: List[str] = []
        findings.append(f"Framework: {self.framework}")
        findings.append(f"Mean RGB: {mean_rgb.astype(int).tolist()}")
        findings.append(f"Brightness: {brightness:.2f}, Saturation: {saturation:.2f}")

        if saturation < 0.05:
            findings.append("Low color saturation detected (possible discoloration)")
        if brightness < 0.25:
            findings.append("Very low brightness (possible mold or rotting)")

        condition, confidence = self._classify(brightness, saturation, product_hint)
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

    def _classify(self, brightness: float, saturation: float, hint: Optional[str]) -> tuple[Condition, float]:
        conditions = list(Condition)
        if brightness > 0.7 and saturation > 0.2:
            return Condition.FRESH, random.uniform(0.75, 0.96)
        if brightness < 0.35:
            return Condition.EXPIRED, random.uniform(0.62, 0.89)
        if saturation < 0.08:
            return Condition.SUSPICIOUS, random.uniform(0.55, 0.82)
        condition = random.choice(conditions)
        confidence = random.uniform(0.55, 0.90)
        return condition, confidence

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
