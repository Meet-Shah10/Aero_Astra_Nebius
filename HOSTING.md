# Aero-Astra — Hosting & Run Guide

Everything you need to run the prototype locally or deploy it on a Nebius AI Cloud VM.

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11 – 3.13 | [python.org](https://python.org) or `brew install python` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) or `brew install node` |
| Docker + Docker Compose | latest | [docs.docker.com](https://docs.docker.com/get-docker/) |
| git | any | pre-installed on most systems |

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/Meet-Shah10/Aero_Astra_Nebius.git
cd Aero_Astra_Nebius
git checkout nebius-submission
```

---

## Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in **all four Nebius fields**. Everything else is optional.

```dotenv
# ── Required: Nebius Token Factory ───────────────────────────────────────────
NEBIUS_API_KEY=<your Token Factory API key>
NEBIUS_BASE_URL=<base URL from Token Factory docs, e.g. https://api.studio.nebius.ai/v1>

# Smaller Nemotron for SHERLOCK (root-cause, fast, ~2048 tokens)
NEBIUS_MODEL_SHERLOCK=<model slug, e.g. nvidia/llama-3.1-nemotron-70b-instruct>

# Larger Nemotron for ATHENA (recovery plan, 4096 tokens)
NEBIUS_MODEL_ATHENA=<model slug, e.g. nvidia/llama-3.1-nemotron-70b-instruct>

# 1 = demo / hosted mode: only Nebius Token Factory is used, no local fallbacks
NEBIUS_ONLY=1

# ── Optional: development fallbacks (ignored when NEBIUS_ONLY=1) ─────────────
# OPENROUTER_API_KEY=
# NVIDIA_API_KEY=
```

> **Where to get credentials:**  
> Sign in at [studio.nebius.ai](https://studio.nebius.ai) → API Keys → Create key.  
> The base URL and exact model slugs are listed in the Token Factory catalogue page.

---

## Step 3 — Verify Token Factory connectivity

Before starting the full app, confirm both models are reachable:

```bash
# Install minimal deps
python3 -m venv .venv && source .venv/bin/activate
pip install openai python-dotenv

python scripts/nebius_smoke_test.py
```

Expected output:

```
NEBIUS_MODEL_SHERLOCK  <slug>  1.23s  '{"ok": true}'
NEBIUS_MODEL_ATHENA    <slug>  1.78s  '{"ok": true}'

Smoke test passed — both models responded via Nebius Token Factory.
```

If either call fails: check `.env`, rotate keys if needed, confirm the base URL ends in `/v1`.

---

## Option A — Run locally (no Docker)

### Install Python dependencies

```bash
source .venv/bin/activate   # if not already active
pip install -r requirements.txt
```

> **Note on PyTorch:** `requirements.txt` lists `torch>=2.3.0`. On Apple Silicon or a machine without a GPU, pip will install the CPU build automatically. On Linux you can force it with:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements.txt
> ```

### Start the backend

```bash
# From the project root (not from inside backend/)
python backend/api.py
```

Backend runs at **http://localhost:8000**.  
Confirm it started cleanly:

```bash
curl http://localhost:8000/health
```

Expected JSON:

```json
{
  "status": "ok",
  "uptime_s": 2.1,
  "nebius_only": true,
  "sherlock": { "providers": ["Nebius Token Factory (...)"], "models": ["..."] },
  "athena":   { "providers": ["Nebius Token Factory (...)"], "models": ["..."] },
  "rag":      { "doc_count": 20, "embed_model": "sentence-transformers/all-MiniLM-L6-v2" }
}
```

> **RAG auto-seeds on first start.** If `rag.doc_count` is 0, the vectorstore is being built — wait ~10 seconds and re-check.

### Start the frontend

Open a second terminal:

```bash
npm install
npm run dev
```

Frontend at **http://localhost:5173**.

---

## Option B — Run with Docker Compose (recommended for Nebius VM)

This is the one-command production path. Docker builds the frontend, starts nginx, and wires everything together.

```bash
# Make sure .env is filled in (Step 2)
docker compose up -d --build
```

The first build takes ~3–5 minutes (downloads Python deps and builds the React app).

Open **http://\<server-ip\>** in your browser.

Verify:

```bash
curl http://localhost/health
docker compose logs backend --tail=50
docker compose logs web     --tail=20
```

To stop:

```bash
docker compose down
```

To rebuild after a code change:

```bash
docker compose up -d --build
```

---

## Deploy on Nebius AI Cloud (step-by-step)

### 1. Provision a VM

- Go to [console.eu.nebius.com](https://console.eu.nebius.com) → Compute → Create VM
- Image: **Ubuntu 22.04** (or latest LTS)
- CPU: 2 vCPU, 8 GB RAM is enough (no GPU needed — LLM runs on Token Factory)
- Storage: 20 GB SSD
- Add an SSH key

### 2. Install Docker on the VM

```bash
ssh ubuntu@<vm-ip>

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker          # apply group without logout

# Verify
docker run --rm hello-world
```

### 3. Clone and configure

```bash
git clone https://github.com/Meet-Shah10/Aero_Astra_Nebius.git
cd Aero_Astra_Nebius
git checkout nebius-submission

cp .env.example .env
nano .env              # fill in NEBIUS_* values, set NEBIUS_ONLY=1
```

### 4. Run

```bash
docker compose up -d --build
```

### 5. Open the firewall

In the Nebius console → Networking → Security Groups: allow **port 80** (TCP) inbound.

Open `http://<vm-ip>` in a browser. Run a full incident end-to-end to confirm everything works.

### 6. (Optional) Add HTTPS with Caddy

```bash
sudo apt install -y caddy

# /etc/caddy/Caddyfile
your-domain.com {
    reverse_proxy localhost:80
}

sudo systemctl restart caddy
```

Caddy automatically provisions a Let's Encrypt certificate. Once behind HTTPS the WebSocket upgrades to `wss://` automatically (no config change needed — nginx passes the Upgrade header through).

---

## Using the App

Once the frontend is open:

1. **Dashboard loads** — the telemetry replay starts streaming automatically.
2. **SENTINEL fires** — within ~6 seconds the stream freezes at the fault frame and the agent console highlights.
3. **Activate SHERLOCK** — navigate to the SHERLOCK page, click **▶ Activate SHERLOCK**. Nemotron on Token Factory diagnoses the root cause.
4. **Activate ATHENA** — ORACLE runs Monte Carlo simulation (~5 s), then ATHENA (Nemotron) writes the recovery plan.
5. **GUARDIAN** — fires automatically after SHERLOCK, sets the safety tier.
6. **Approve** — on the GUARDIAN page approve the plan. SCRIBE compiles the audit runbook.

---

## Health & monitoring

| Endpoint | What it returns |
|---|---|
| `GET /health` | Provider names, model slugs, RAG doc count, uptime |
| `GET /api/replay/status` | Current replay state |

Watch live logs:

```bash
# Docker
docker compose logs -f backend

# Local
# Logs are printed to the terminal where you ran python backend/api.py
```

Key log lines to confirm everything is working:

```
INFO  nebius       Nebius Token Factory provider ready | model_env=NEBIUS_MODEL_SHERLOCK
INFO  nebius       Nebius Token Factory provider ready | model_env=NEBIUS_MODEL_ATHENA
INFO  athena.rag   LocalEmbedder ready | model=sentence-transformers/all-MiniLM-L6-v2
INFO  athena.rag   RAG vectorstore loaded | docs=20
INFO  api          Nebius Token Factory (...) - LLM call succeeded
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `RuntimeError: NEBIUS_ONLY=1 but env vars missing` | Check `.env` — all four `NEBIUS_*` vars must be set |
| `/health` returns `"nebius_only": false` | Set `NEBIUS_ONLY=1` in `.env` and restart |
| `ModuleNotFoundError` on backend start | `pip install -r requirements.txt` in the active venv |
| RAG `doc_count: 0` on first start | Wait ~10 s — vectorstore is building. Delete `backend/athena/rag/vectorstore/` and restart if it stays at 0 |
| WebSocket disconnects immediately | Confirm backend is running and nginx is proxying `/ws` — check `docker compose logs web` |
| `ws://` blocked on `https://` page | Add HTTPS (see Caddy step above) — once the page is `https://`, WebSocket auto-upgrades to `wss://` |
| Port 80 in use locally | Change `"80:80"` to `"8080:80"` in `docker-compose.yml` and open `http://localhost:8080` |
| Docker build fails on torch download | Add `--index-url https://download.pytorch.org/whl/cpu` to the `pip install` line in `Dockerfile` |

---

## File map (what each file does)

```
Aero_Astra_Nebius/
├── backend/
│   ├── api.py              FastAPI app — WebSocket, /health, replay loop, agent triggers
│   ├── nebius.py           Token Factory provider factory (reads NEBIUS_* env vars)
│   ├── llm_client.py       Multi-provider LLM fallback chain (OpenAI-compat)
│   ├── sherlock/           Root-cause diagnosis agent (graph + Nemotron)
│   ├── athena/             Recovery planning agent (Nemotron + RAG)
│   │   └── rag/            FDIR knowledge base (sentence-transformers vectorstore)
│   ├── sentinel/           Anomaly detectors (XGBoost + physics + residual)
│   ├── oracle/             Monte Carlo safety simulator
│   ├── simulator/          Physics-based satellite telemetry engine
│   ├── guardian/           Deterministic 5-rule safety gate
│   ├── vitals/             Live subsystem health metrics
│   ├── replay/             Pre-recorded fault playlist (playlist.json)
│   └── models/             Pre-trained SENTINEL model artefacts (.pkl/.joblib)
├── scripts/
│   └── nebius_smoke_test.py  Proves Token Factory calls work before full launch
├── src/                    React/Vite frontend
│   └── config.js           Central WS URL (no hardcoded localhost)
├── public/
│   ├── textures/earth/     Earth texture maps (used by 3-D globe)
│   └── ne_110m_land.json   GeoJSON land map (used by Globe3D)
├── simple_satellite_low_poly_free.glb  3-D satellite model
├── Dockerfile              Backend container
├── Dockerfile.web          Frontend container (Node build + nginx)
├── docker-compose.yml      Wires backend + web with health-check dependency
├── nginx.conf              SPA routing + WebSocket proxy + /health passthrough
├── .env.example            Env var template — copy to .env
├── requirements.txt        Python dependencies
└── package.json            Node dependencies
```
