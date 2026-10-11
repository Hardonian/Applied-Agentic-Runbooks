# =============================================================================
# Multi-stage Production Dockerfile for Agent Factory
# =============================================================================
# Stage 1: Build Dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc     && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Hardened Runtime
FROM python:3.11-slim AS runner
WORKDIR /app
RUN groupadd -g 1000 appgroup && useradd -u 1000 -g appgroup -s /bin/bash appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY . /app/
RUN chown -R appuser:appgroup /app

ENV PATH=/home/appuser/.local/bin:$PATH     PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

CMD ["python", "scripts/run_agent.py"]
