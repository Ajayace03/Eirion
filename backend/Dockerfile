# ── EIRION Backend — Production Dockerfile ────────────────────────────────────
# Python 3.11 slim → installs torch CPU + PyTorch Geometric + RDKit + ReportLab
# Note: torch CPU-only build keeps image ~2GB instead of ~6GB for CUDA
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python dependencies ─────────────────────────────────────────────
COPY requirements.txt .

# Install torch CPU-only first (avoids pulling full CUDA build)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.11.0+cpu \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
        torch-geometric==2.7.0 && \
    pip install --no-cache-dir -r requirements.txt

# ── Generate Prisma Python client ────────────────────────────────────────────
COPY schema.prisma .
RUN prisma generate --schema=schema.prisma

# ── Copy application source ──────────────────────────────────────────────────
COPY . .

# ── Run database migration on startup, then launch API ────────────────────────
# Health endpoint available at /health — used by docker-compose healthcheck
EXPOSE 8000

CMD ["sh", "-c", "prisma db push --schema=schema.prisma && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1"]
