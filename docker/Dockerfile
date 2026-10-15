FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN python -m pip install --no-cache-dir build
COPY pyproject.toml README.md ./
COPY agent_factory ./agent_factory
RUN python -m build --wheel --outdir /wheels

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/home/agent/.local/bin:$PATH
RUN groupadd --gid 10001 agent && useradd --uid 10001 --gid agent --create-home agent
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
WORKDIR /app
COPY alembic.ini ./
COPY alembic ./alembic
RUN mkdir -p /app/artifacts/arena && chown -R agent:agent /app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/live')"]
CMD ["uvicorn", "agent_factory.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
