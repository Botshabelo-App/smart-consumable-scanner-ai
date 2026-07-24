# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import os
from typing import Optional

from PIL import Image

from ai_service.schemas import ScanResult


def _build_classifier():
    if os.environ.get("AI_USE_DUMMY", "false").lower() == "true":
        from ai_service.app.models.dummy_classifier import ConsumableClassifier
        return ConsumableClassifier()
    try:
        from ai_service.app.models.real_classifier import RealProductPipeline
        return RealProductPipeline()
    except Exception as exc:
        print(f"Could not load RealProductPipeline ({exc}); falling back to dummy classifier.")
        from ai_service.app.models.dummy_classifier import ConsumableClassifier
        return ConsumableClassifier()


classifier = _build_classifier()
