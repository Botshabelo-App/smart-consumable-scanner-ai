from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile

from ai_service.app.models.classifier import classifier
from ai_service.app.services.image_processor import guess_product_hint, load_image
from ai_service.schemas import ScanResult


@asynccontextmanager
async def lifespan(app: FastAPI):
    if hasattr(classifier, "warm_up"):
        classifier.warm_up()
    yield


app = FastAPI(
    title="Smart Consumable Scanner AI Inference Service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "framework": classifier.framework}


@app.post("/analyze", response_model=ScanResult, tags=["analysis"])
async def analyze(
    image: UploadFile = File(...),
    product_hint: Optional[str] = Form(None),
):
    pil_image = await load_image(image)
    hint = product_hint or guess_product_hint(image.filename)
    return classifier.predict(pil_image, product_hint=hint)
