# Changes made during the submission period
# Baseline: tag `pre-hackathon-baseline` (last commit before 2026-08-26)
# Confirm exact submission period start date on the Devpost Rules page.

## Added
- 2026-09-20: `backend/nebius.py` — Nebius Token Factory provider factory for SHERLOCK and ATHENA
- 2026-09-20: `backend/nebius.py` — `NEBIUS_ONLY=1` mode: hard-fails if Token Factory env vars are missing, ensuring demo never silently falls back to another provider
- 2026-09-20: `backend/sherlock/agent.py` — Nebius Token Factory (Nemotron) injected as highest-priority provider; all other providers demoted to dev-only fallbacks
- 2026-09-20: `backend/athena/agent.py` — Nebius Token Factory (Nemotron) injected as highest-priority provider; NVIDIA NIM and Ollama demoted to dev-only fallbacks
- 2026-09-20: `backend/athena/rag/pipeline.py` — `LocalEmbedder` class (sentence-transformers/all-MiniLM-L6-v2): offline, CPU, no API key, no Ollama required
- 2026-09-20: `backend/athena/rag/pipeline.py` — `build_embedder()` now tries Local → Ollama → Gemini (was Ollama → Gemini)
- 2026-09-20: `scripts/nebius_smoke_test.py` — smoke test that makes real Token Factory calls to both agent models, prints latency and response content
- 2026-09-20: `Dockerfile` — backend container (python:3.12-slim, CPU-only, PYTHONPATH=/app)
- 2026-09-20: `Dockerfile.web` — frontend container (Node 20 build + nginx serve)
- 2026-09-20: `nginx.conf` — SPA routing + WebSocket proxy + /health passthrough
- 2026-09-20: `docker-compose.yml` — backend + web services wired with health-check dependency
- 2026-09-20: `src/config.js` — central WebSocket URL config derived from window.location.host
- 2026-09-20: `.env.example` — env var template committed to repo
- 2026-09-20: `LICENSE` — MIT license file
- 2026-09-20: `.dockerignore` — keeps secrets and large artefacts out of Docker images
- 2026-09-20: `.env.development` — Vite dev env for local WS URL

## Changed
- 2026-09-20: `requirements.txt` — added 7 missing packages: networkx, xgboost, torch (CPU), joblib, tqdm, langchain-text-splitters, pymupdf
- 2026-09-20: `backend/api.py` — added `GET /health` endpoint (providers, models, RAG doc count, uptime)
- 2026-09-20: `backend/api.py` — fixed `uvicorn.run` module path: `api:app` → `backend.api:app` (required for Docker / project-root launch)
- 2026-09-20: `src/App.jsx` — replaced hardcoded `ws://localhost:8000/ws` with import from `src/config.js`
- 2026-09-20: `src/components/sandbox/useSandboxWs.js` — replaced hardcoded `ws://localhost:8000/ws/sandbox` with import from `src/config.js`
- 2026-09-20: `backend/sherlock/agent.py` — updated docstring: Claude/Gemini/OpenRouter → Nemotron/Token Factory
- 2026-09-20: `backend/athena/agent.py` — updated docstring: Claude/Gemini/OpenRouter → Nemotron/Token Factory

## Removed
- (nothing removed yet)

---
*Run `git diff --stat pre-hackathon-baseline..HEAD` and `git shortlog -sn pre-hackathon-baseline..HEAD` for evidence.*
