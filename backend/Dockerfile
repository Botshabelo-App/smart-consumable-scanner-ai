FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_scanner/ ./ai_scanner/
COPY alembic.ini* ./ 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "ai_scanner.main:app", "--host", "0.0.0.0", "--port", "8000"]
