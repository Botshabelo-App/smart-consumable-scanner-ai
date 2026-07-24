# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from io import BytesIO
from typing import Optional

from fastapi import UploadFile
from PIL import Image


async def load_image(upload: UploadFile, max_size: int = 1024) -> Image.Image:
    content = await upload.read()
    image = Image.open(BytesIO(content))
    image = image.convert("RGB")
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return image


def guess_product_hint(filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    name = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return name.replace("_", " ").replace("-", " ") if name else None
