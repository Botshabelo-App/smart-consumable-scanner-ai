import numpy as np
from PIL import Image

from ai_service.app.models.dummy_classifier import ConsumableClassifier
from ai_service.schemas import Condition


def test_dummy_classifier_returns_result():
    image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    clf = ConsumableClassifier()
    result = clf.predict(image, product_hint="milk")
    assert isinstance(result.condition, Condition)
    assert 0.0 <= result.confidence <= 1.0
