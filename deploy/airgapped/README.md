# Air-gapped Agent Factory deployment

1. On a connected staging host, mirror the API, PostgreSQL, Redis, Prometheus,
   Grafana, Nginx, and either Ollama or vLLM images into an approved OCI archive.
2. Transfer the archive and this directory through the organization’s controlled
   media process, verify SHA-256 checksums, then load images into the private registry.
3. Copy `offline.env.example` to `offline.env`; keep all cloud API keys empty and set
   the local OpenAI-compatible endpoint to Ollama or vLLM.
4. Start with `docker compose --env-file offline.env -f ../docker-compose.production.yml
   -f docker-compose.airgapped.yml up -d`.
5. Verify `/live`, `/ready`, `/api/v1/arena/leaderboard`, and both WebSocket routes.

The arena, proof generation, packet capture, and telemetry conversion are deterministic
without network access. Pre-pull model weights and pin their checksums before isolation.
