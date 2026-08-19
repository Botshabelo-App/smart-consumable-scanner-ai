# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import os
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
from torchvision.models import EfficientNet_B0_Weights, MobileNet_V3_Small_Weights, efficientnet_b0, mobilenet_v3_small
from torchvision.models._meta import _IMAGENET_CATEGORIES  # type: ignore
from ultralytics import YOLO

from ai_service.schemas import Condition, ProductCategory, ScanResult


# COCO food-related class IDs that are useful for consumable products
COCO_FOOD_IDS = {46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 39, 40, 41, 42, 43, 44, 45}

IMAGENET_TO_PRODUCT: dict[str, Tuple[str, ProductCategory]] = {
    "banana": ("banana", ProductCategory.PRODUCE),
    "apple": ("apple", ProductCategory.PRODUCE),
    "orange": ("orange", ProductCategory.PRODUCE),
    "lemon": ("lemon", ProductCategory.PRODUCE),
    "lime": ("lime", ProductCategory.PRODUCE),
    "strawberry": ("strawberry", ProductCategory.PRODUCE),
    "grape": ("grape", ProductCategory.PRODUCE),
    "watermelon": ("watermelon", ProductCategory.PRODUCE),
    "pear": ("pear", ProductCategory.PRODUCE),
    "peach": ("peach", ProductCategory.PRODUCE),
    "plum": ("plum", ProductCategory.PRODUCE),
    "apricot": ("apricot", ProductCategory.PRODUCE),
    "mango": ("mango", ProductCategory.PRODUCE),
    "pineapple": ("pineapple", ProductCategory.PRODUCE),
    "pomegranate": ("pomegranate", ProductCategory.PRODUCE),
    "broccoli": ("broccoli", ProductCategory.PRODUCE),
    "cauliflower": ("cauliflower", ProductCategory.PRODUCE),
    "carrot": ("carrot", ProductCategory.PRODUCE),
    "cucumber": ("cucumber", ProductCategory.PRODUCE),
    "potato": ("potato", ProductCategory.PRODUCE),
    "tomato": ("tomato", ProductCategory.PRODUCE),
    "bell pepper": ("bell pepper", ProductCategory.PRODUCE),
    "lettuce": ("lettuce", ProductCategory.PRODUCE),
    "mushroom": ("mushroom", ProductCategory.PRODUCE),
    "onion": ("onion", ProductCategory.PRODUCE),
    "garlic": ("garlic", ProductCategory.PRODUCE),
    "bread": ("bread", ProductCategory.FOOD),
    "bagel": ("bagel", ProductCategory.FOOD),
    "pretzel": ("pretzel", ProductCategory.FOOD),
    "pizza": ("pizza", ProductCategory.FOOD),
    "hotdog": ("hot dog", ProductCategory.FOOD),
    "sandwich": ("sandwich", ProductCategory.FOOD),
    "cake": ("cake", ProductCategory.FOOD),
    "doughnut": ("doughnut", ProductCategory.FOOD),
    "waffle": ("waffle", ProductCategory.FOOD),
    "ice cream": ("ice cream", ProductCategory.FROZEN),
    "wine bottle": ("wine", ProductCategory.BEVERAGE),
    "beer bottle": ("beer", ProductCategory.BEVERAGE),
    "beer glass": ("beer", ProductCategory.BEVERAGE),
    "water bottle": ("water", ProductCategory.BEVERAGE),
    "coffee mug": ("coffee", ProductCategory.BEVERAGE),
    "cup": ("tea/coffee", ProductCategory.BEVERAGE),
    "milk can": ("milk", ProductCategory.DAIRY),
    "wine": ("wine", ProductCategory.BEVERAGE),
    "beer": ("beer", ProductCategory.BEVERAGE),
    "whiskey": ("whiskey", ProductCategory.BEVERAGE),
    "water": ("water", ProductCategory.BEVERAGE),
    "juice": ("juice", ProductCategory.BEVERAGE),
    "soft drink": ("soft drink", ProductCategory.BEVERAGE),
    "milk": ("milk", ProductCategory.DAIRY),
    "cheese": ("cheese", ProductCategory.DAIRY),
    "yogurt": ("yogurt", ProductCategory.DAIRY),
    "butter": ("butter", ProductCategory.DAIRY),
    "egg": ("egg", ProductCategory.FOOD),
    "beef": ("beef", ProductCategory.MEAT),
    "steak": ("beef", ProductCategory.MEAT),
    "chicken": ("chicken", ProductCategory.MEAT),
    "pork": ("pork", ProductCategory.MEAT),
    "lamb": ("lamb", ProductCategory.MEAT),
    "meat loaf": ("meat", ProductCategory.MEAT),
    "meatball": ("meat", ProductCategory.MEAT),
    "salmon": ("salmon", ProductCategory.SEAFOOD),
    "fish": ("fish", ProductCategory.SEAFOOD),
    "shrimp": ("shrimp", ProductCategory.SEAFOOD),
    "lobster": ("lobster", ProductCategory.SEAFOOD),
    "packet": ("packaged product", ProductCategory.PACKAGED),
    "pill bottle": ("medicine/supplement", ProductCategory.OTHER),
    "canned": ("canned product", ProductCategory.PACKAGED),
    "soup": ("canned/prepared food", ProductCategory.PACKAGED),
}

HINT_TO_PRODUCT: dict[str, Tuple[str, ProductCategory]] = {
    "milk": ("milk", ProductCategory.DAIRY),
    "cheese": ("cheese", ProductCategory.DAIRY),
    "yogurt": ("yogurt", ProductCategory.DAIRY),
    "butter": ("butter", ProductCategory.DAIRY),
    "beef": ("beef", ProductCategory.MEAT),
    "steak": ("beef", ProductCategory.MEAT),
    "chicken": ("chicken", ProductCategory.MEAT),
    "pork": ("pork", ProductCategory.MEAT),
    "lamb": ("lamb", ProductCategory.MEAT),
    "fish": ("fish", ProductCategory.SEAFOOD),
    "salmon": ("salmon", ProductCategory.SEAFOOD),
    "shrimp": ("shrimp", ProductCategory.SEAFOOD),
    "apple": ("apple", ProductCategory.PRODUCE),
    "banana": ("banana", ProductCategory.PRODUCE),
    "orange": ("orange", ProductCategory.PRODUCE),
    "bread": ("bread", ProductCategory.FOOD),
    "egg": ("egg", ProductCategory.FOOD),
    "water": ("water", ProductCategory.BEVERAGE),
    "juice": ("juice", ProductCategory.BEVERAGE),
    "beer": ("beer", ProductCategory.BEVERAGE),
    "wine": ("wine", ProductCategory.BEVERAGE),
    "whiskey": ("whiskey", ProductCategory.BEVERAGE),
    "soft drink": ("soft drink", ProductCategory.BEVERAGE),
    "energy drink": ("energy drink", ProductCategory.BEVERAGE),
    "coffee": ("coffee", ProductCategory.BEVERAGE),
    "tea": ("tea", ProductCategory.BEVERAGE),
    "oil": ("cooking oil", ProductCategory.OTHER),
    "baby food": ("baby food", ProductCategory.PACKAGED),
    "canned": ("canned product", ProductCategory.PACKAGED),
    "frozen": ("frozen food", ProductCategory.FROZEN),
    "dry": ("dry product", ProductCategory.DRY),
    "powder": ("powder product", ProductCategory.DRY),
    "flour": ("flour", ProductCategory.DRY),
    "sugar": ("sugar", ProductCategory.DRY),
    "rice": ("rice", ProductCategory.DRY),
}


def _download_spoilage_checkpoint() -> Path:
    checkpoint_dir = Path(__file__).resolve().parents[3] / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / "spoilage_mobilenetv3.pth"
    if not path.exists():
        url = "https://huggingface.co/Xyphitos/fridgeai-spoilage/resolve/main/spoilage_mobilenetv3.pth"
        urllib.request.urlretrieve(url, path)
    return path


class RealProductPipeline:
    """Camera-first production AI pipeline using real pretrained models + CV features."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.yolo: Optional[YOLO] = None
        self.imagenet_model: Optional[torch.nn.Module] = None
        self.spoilage_model: Optional[torch.nn.Module] = None
        self.imagenet_transform = None
        self.imagenet_labels: List[str] = []
        self.framework = "pytorch"
        self._loaded = False

    def warm_up(self) -> None:
        """Load/download all models. Call once at startup."""
        if self._loaded:
            return

        # Object detection
        self.yolo = YOLO("yolov8n.pt", verbose=False)

        # General product recognition (ImageNet)
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1
        self.imagenet_model = efficientnet_b0(weights=weights).to(self.device).eval()
        self.imagenet_transform = weights.transforms()
        self.imagenet_labels = weights.meta["categories"]

        # Fresh/spoiled classifier for produce
        self.spoilage_model = mobilenet_v3_small(weights=None)
        self.spoilage_model.classifier = nn.Sequential(
            nn.Linear(576, 256),
            nn.Hardswish(),
            nn.Dropout(0.2),
            nn.Linear(256, 1),
        )
        checkpoint_path = _download_spoilage_checkpoint()
        state = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        self.spoilage_model.load_state_dict(state)
        self.spoilage_model = self.spoilage_model.to(self.device).eval()

        self._loaded = True

    def predict(self, image: Image.Image, product_hint: Optional[str] = None) -> ScanResult:
        if not self._loaded:
            self.warm_up()

        rgb_image = image.convert("RGB")
        np_image = np.array(rgb_image)

        # 1. Detect and crop product region
        crop, detection_info = self._detect_and_crop(rgb_image)

        # 2. Product classification via ImageNet + hint + YOLO
        product_name, category, product_conf = self._classify_product(crop, product_hint, detection_info)

        # 3. Condition assessment
        condition, confidence, condition_reasons = self._assess_condition(
            crop, category, np_image, product_hint
        )

        # 4. Packaging type estimate
        packaging_type = self._estimate_packaging(crop)

        findings = [
            f"Detection: {detection_info.get('label', 'none')} (conf {detection_info.get('confidence', 0):.2f})",
            f"Product classification: {product_name} ({category.value if category else 'unknown'}) (conf {product_conf:.2f})",
            *condition_reasons,
        ]

        if category in (ProductCategory.PACKAGED, ProductCategory.FROZEN, ProductCategory.DRY, ProductCategory.BEVERAGE):
            findings.append(
                "Limitation: smartphone camera cannot reliably determine the internal condition of sealed or opaque products."
            )

        return ScanResult(
            condition=condition,
            confidence=round(confidence, 3),
            product_name=product_name,
            category=category,
            packaging_type=packaging_type,
            findings=findings,
            expiry_risk="unknown",
        )

    def _detect_and_crop(self, image: Image.Image) -> Tuple[Image.Image, dict]:
        if self.yolo is None:
            return image, {}
        results = self.yolo(image, verbose=False)
        if not results or not results[0].boxes:
            return image, {}

        boxes = results[0].boxes
        # Pick the largest detection among food-related COCO classes
        candidate = None
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if cls_id in COCO_FOOD_IDS:
                if candidate is None or conf > candidate[1]:
                    candidate = (box.xyxy[0].cpu().numpy(), conf, cls_id)

        if candidate is None:
            # fall back to highest-confidence detection
            best = max(boxes, key=lambda b: float(b.conf[0]))
            candidate = (best.xyxy[0].cpu().numpy(), float(best.conf[0]), int(best.cls[0]))

        x1, y1, x2, y2 = candidate[0].astype(int)
        conf = candidate[1]
        cls_id = candidate[2]
        names = self.yolo.names
        label = names.get(cls_id, "unknown")

        # add small margin
        width, height = image.size
        margin = int(min(width, height) * 0.05)
        x1, y1 = max(0, x1 - margin), max(0, y1 - margin)
        x2, y2 = min(width, x2 + margin), min(height, y2 + margin)
        crop = image.crop((x1, y1, x2, y2))
        return crop, {"label": label, "confidence": conf, "bbox": [x1, y1, x2, y2]}

    def _classify_product(
        self, crop: Image.Image, product_hint: Optional[str], detection_info: dict
    ) -> Tuple[str, Optional[ProductCategory], float]:
        if self.imagenet_model is None or self.imagenet_transform is None:
            return product_hint or "unknown", None, 0.0

        tensor = self.imagenet_transform(crop).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.imagenet_model(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu()

        top5_values, top5_indices = torch.topk(probs, 5)
        top5_labels = [(self.imagenet_labels[int(i)], float(v)) for i, v in zip(top5_indices, top5_values)]

        # Hint override (clean up noisy filename-based hints, do not trust blindly)
        if product_hint:
            hint_lower = product_hint.lower()
            for key, (name, cat) in HINT_TO_PRODUCT.items():
                if key in hint_lower:
                    return name, cat, 0.7

        # YOLO label fallback for COCO objects commonly seen in consumables
        yolo_label = detection_info.get("label", "")
        yolo_map = {
            "banana": ("banana", ProductCategory.PRODUCE),
            "apple": ("apple", ProductCategory.PRODUCE),
            "orange": ("orange", ProductCategory.PRODUCE),
            "broccoli": ("broccoli", ProductCategory.PRODUCE),
            "carrot": ("carrot", ProductCategory.PRODUCE),
            "bottle": ("bottle", ProductCategory.BEVERAGE),
            "wine glass": ("wine", ProductCategory.BEVERAGE),
            "cup": ("tea/coffee", ProductCategory.BEVERAGE),
            "cake": ("cake", ProductCategory.FOOD),
            "sandwich": ("sandwich", ProductCategory.FOOD),
            "hot dog": ("hot dog", ProductCategory.FOOD),
            "pizza": ("pizza", ProductCategory.FOOD),
            "donut": ("doughnut", ProductCategory.FOOD),
        }
        if yolo_label in yolo_map:
            name, cat = yolo_map[yolo_label]
            return name, cat, detection_info.get("confidence", 0.7)

        # ImageNet top-5 matching
        for label, conf in top5_labels:
            label_lower = label.lower()
            for key, (name, cat) in IMAGENET_TO_PRODUCT.items():
                if key in label_lower:
                    return name, cat, conf

        return top5_labels[0][0] if top5_labels else "unknown", None, float(top5_labels[0][1]) if top5_labels else 0.0

    def _assess_condition(
        self, crop: Image.Image, category: Optional[ProductCategory], full_np: np.ndarray, product_hint: Optional[str]
    ) -> Tuple[Condition, float, List[str]]:
        reasons: List[str] = []

        # Image quality / sharpness
        gray_full = cv2.cvtColor(full_np, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray_full, cv2.CV_64F).var()
        if laplacian_var < 80:
            reasons.append(f"Low image sharpness ({laplacian_var:.1f}); quality may affect accuracy")

        # Color / texture analysis on the crop
        crop_np = np.array(crop)
        hsv = cv2.cvtColor(crop_np, cv2.COLOR_RGB2HSV)
        mean_hsv = hsv.mean(axis=(0, 1))
        std_hsv = hsv.std(axis=(0, 1))
        hue, sat, val = float(mean_hsv[0]), float(mean_hsv[1]), float(mean_hsv[2])
        reasons.append(f"Mean HSV: hue={hue:.1f}, saturation={sat:.1f}, value={val:.1f}")

        # Dark spot / bruise / mold detection
        gray_crop = cv2.cvtColor(crop_np, cv2.COLOR_RGB2GRAY)
        dark_threshold = min(80, max(30, int(val * 0.2)))
        _, dark_mask = cv2.threshold(gray_crop, dark_threshold, 255, cv2.THRESH_BINARY_INV)
        # filter out tiny noise pixels
        kernel = np.ones((3, 3), np.uint8)
        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)
        dark_contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_dark_area = max(50, int(crop_np.shape[0] * crop_np.shape[1] * 0.001))
        dark_area = sum(cv2.contourArea(c) for c in dark_contours if cv2.contourArea(c) > min_dark_area)
        total_pixels = crop_np.shape[0] * crop_np.shape[1]
        dark_ratio = dark_area / total_pixels
        if dark_ratio > 0.05:
            reasons.append(f"Dark spots / bruising / mold detected: {dark_ratio:.1%} of surface")

        # Apply spoilage model for produce / meat / seafood / dairy where surface is visible
        if category in (ProductCategory.PRODUCE, ProductCategory.MEAT, ProductCategory.SEAFOOD, ProductCategory.DAIRY):
            p_spoiled = self._spoilage_score(crop)
            reasons.append(f"Spoilage model P(spoiled)={p_spoiled:.3f}")
            condition, confidence = self._condition_from_spoilage(p_spoiled)
            if dark_ratio > 0.05 and p_spoiled < 0.5:
                condition = Condition.SUSPICIOUS
                confidence = 0.6
                reasons.append("Surface discoloration overrides low spoilage score")
            return condition, confidence, reasons

        # Packaging analysis for sealed / packaged products
        return self._assess_packaging(crop_np, reasons)

    def _spoilage_score(self, crop: Image.Image) -> float:
        if self.spoilage_model is None:
            return 0.5
        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        tensor = transform(crop).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logit = self.spoilage_model(tensor).squeeze()
            return float(torch.sigmoid(logit).cpu())

    def _condition_from_spoilage(self, p: float) -> Tuple[Condition, float]:
        if p < 0.20:
            return Condition.FRESH, round(1 - p, 3)
        if p < 0.45:
            return Condition.NEAR_EXPIRY, round(0.55 + abs(0.30 - p), 3)
        if p < 0.70:
            return Condition.SUSPICIOUS, round(p, 3)
        return Condition.EXPIRED, round(p, 3)

    def _assess_packaging(self, crop_np: np.ndarray, reasons: List[str]) -> Tuple[Condition, float, List[str]]:
        gray = cv2.cvtColor(crop_np, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            reasons.append("No clear packaging contour found")
            return Condition.SUSPICIOUS, 0.55, reasons

        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area / hull_area) if hull_area > 0 else 1.0
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = max(w, h) / max(min(w, h), 1)
        reasons.append(f"Packaging contour: solidity={solidity:.2f}, aspect_ratio={aspect_ratio:.2f}")

        # Damage / deformation indicators
        if solidity < 0.80:
            reasons.append("Packaging deformation or damage detected")
            return Condition.SUSPICIOUS, round(0.55 + (0.85 - solidity), 3), reasons
        if aspect_ratio > 2.5 or aspect_ratio < 0.4:
            reasons.append("Unusual packaging aspect ratio")
            return Condition.SUSPICIOUS, 0.62, reasons

        # Swelling: convexity high and shape close to circular/oval
        if solidity > 0.95 and aspect_ratio < 1.4 and area > (crop_np.shape[0] * crop_np.shape[1] * 0.3):
            reasons.append("Possible packaging swelling")
            return Condition.SUSPICIOUS, 0.60, reasons

        reasons.append("Packaging appears intact")
        return Condition.FRESH, 0.80, reasons

    def _estimate_packaging(self, crop: Image.Image) -> str:
        arr = np.array(crop)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=30, minLineLength=30, maxLineGap=5)
        if lines is None:
            return "unknown"
        # lines can be (N,1,4) or (N,4) depending on OpenCV build
        lines = lines.reshape(-1, 4)
        angles = []
        for x1, y1, x2, y2 in lines:
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
            angles.append(angle)
        if not angles:
            return "unknown"
        # If many parallel lines -> box/carton
        hist, _ = np.histogram(angles, bins=18, range=(0, 180))
        dominant = hist.max()
        if dominant > len(angles) * 0.4:
            return "box/carton"
        return "flexible/unknown"
