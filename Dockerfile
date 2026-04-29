# ── Treaties — Research Intelligence Engine ──
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source first so pip install -e can find packages
COPY pyproject.toml .
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY scripts/ ./scripts/

# Install Python deps
RUN pip install --no-cache-dir -e "."

# Create snapshot dir
RUN mkdir -p /app/snapshots

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
