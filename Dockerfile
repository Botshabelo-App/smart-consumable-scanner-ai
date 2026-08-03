FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OCR and image processing.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source and install Python dependencies.
COPY backend/ ./backend/
COPY ai-service/ ./ai-service/
COPY main.py ./
COPY pyproject.toml ./

RUN pip install --no-cache-dir -r backend/requirements.txt -r ai-service/requirements.txt

# The backend uses this URL to reach the AI service inside the same container.
ENV AI_SERVICE_URL=http://localhost:8080/ai
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
