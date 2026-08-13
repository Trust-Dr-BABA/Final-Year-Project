# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies. The pip cache mount persists across builds even when the COPY
# layer below is invalidated by a source change, so editing one file doesn't force every [ml]
# wheel (xgboost alone is ~300MB) to be re-downloaded on the next build.
COPY backend /app/backend
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install "/app/backend[ml]"

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only the runtime code and data shared with it.
COPY backend /app/backend
COPY ml /app/ml
COPY shared /app/shared

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
