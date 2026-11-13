# Supply-chain note: why this image is Alpine, not Debian slim
# ------------------------------------------------------------
# The `image-security` job in .github/workflows/supply-chain.yml runs
#   trivy image --severity CRITICAL,HIGH --exit-code 1   (ignore-unfixed=false)
# so *any* open CRITICAL/HIGH advisory fails it, whether or not a patch exists.
#
# `python:3.12-slim` (Debian 13.7) carries 49 HIGH advisories. 47 of them are
# marked by the Debian security tracker as "affected"/"fix_deferred" with no
# fixed source version -- util-linux/bsdutils/mount/login and their libs,
# ncurses, libacl1, libsqlite3-0, libsystemd0/libudev1, perl-base. There is
# nothing to upgrade *to*, so no Dockerfile edit on a Debian base can clear the
# gate; the only alternatives were ignoring findings or softening the gate, and
# neither is acceptable for a supply-chain control.
#
# `python:3.12-alpine3.22` carries 13 HIGH advisories and every one has a
# published fix in the Alpine SecDB, so `apk upgrade` really does take the OS
# layer to zero: musl 1.2.5-r12 -> r13, openssl 3.5.6-r0 -> 3.5.9-r0, libuuid
# 2.41-r9 -> 2.41.6-r1, zlib 1.3.2-r0 -> 1.4-r0, xz-libs, ca-certificates,
# tzdata.
#
# The last finding was CVE-2025-47273 (setuptools < 78.1.1), which trivy
# attributes to pip's *vendored* setuptools copy (pip/_vendor/vendor.txt pins
# setuptools==70.3.0). Upgrading pip does not move it -- pip 25.0.1 and pip 26.3
# both vendor 70.3.0 -- and `pip install -U setuptools` does not touch it
# either. The wheel is already built in the builder stage, so the runtime stage
# drops the package installer once the app is installed. That removes the
# vulnerable code instead of suppressing the report, and is standard hardening
# for a production image.
#
# Consequence: `pip install` no longer works inside a running container.
# Add Python dependencies at build time (or run the builder stage).
#
# If the base ever moves back to Debian, this gate will go red again on the same
# unpatched Debian advisories. That is Debian 13's patch queue, not this file.

FROM python:3.12-alpine3.22 AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN apk upgrade --no-cache
RUN python -m pip install --no-cache-dir build
COPY pyproject.toml README.md ./
COPY agent_factory ./agent_factory
RUN python -m build --wheel --outdir /wheels

FROM python:3.12-alpine3.22 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/home/agent/.local/bin:$PATH
# Upgrade every installed package to its SecDB-fixed version, then add the
# shared libraries the app's binary wheels link against (psycopg2 -> libpq,
# stdlib sqlite3 -> sqlite-libs). addgroup/adduser are the busybox equivalents
# of the Debian groupadd/useradd calls this replaces; uid/gid 10001 is kept so
# volume ownership and the existing k8s securityContext are unchanged.
RUN apk upgrade --no-cache \
    && apk add --no-cache ca-certificates libpq sqlite-libs \
    && addgroup -g 10001 agent \
    && adduser -u 10001 -G agent -h /home/agent -s /sbin/nologin -D agent
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels \
    && python -m pip uninstall -y pip wheel \
    && rm -rf /root/.cache/pip
WORKDIR /app
COPY alembic.ini ./
COPY alembic ./alembic
RUN mkdir -p /app/artifacts/arena && chown -R agent:agent /app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/live')"]
CMD ["uvicorn", "agent_factory.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
