FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple

COPY ai_service/ ./ai_service/

# Pre-download YOLOv8 nano weights and spoilage checkpoint at build time
RUN python - <<'PY'
from ultralytics import YOLO
YOLO('yolov8n.pt', verbose=False)
from ai_service.app.models.real_classifier import _download_spoilage_checkpoint
_download_spoilage_checkpoint()
PY

EXPOSE 8000

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
