# ── Raspberry Pi 5 (ARM64) Docker image for Object Detection Server ──
FROM python:3.11-slim-bookworm

LABEL description="YOLOv8 Object Detection Server with FastAPI"
LABEL org.opencontainers.image.authors="jesryljade"

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies for OpenCV (headless) and numpy on ARM64 Bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0t64 \
    libgomp1 \
    libopenblas0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create model directory
RUN mkdir -p /app/models

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/hello')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
