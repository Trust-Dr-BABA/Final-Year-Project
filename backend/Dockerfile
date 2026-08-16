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
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only the runtime code and data shared with it, owned by the non-root user that runs it —
# running as root inside the container widens the blast radius of any future RCE-class bug for no
# benefit here (nothing in this image needs root: no privileged ports, no system-level installs at
# runtime).
COPY --chown=appuser:appuser backend /app/backend
COPY --chown=appuser:appuser ml /app/ml
COPY --chown=appuser:appuser shared /app/shared

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
