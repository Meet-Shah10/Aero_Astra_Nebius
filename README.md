# 🛰️ Aero-Astra: Autonomous Satellite Fault Management on Nebius + NVIDIA Nemotron

**Track:** Best Apps and Agents — Nebius × NVIDIA Global AI Hackathon  
**Live demo:** _\<public URL — fill in after Nebius deployment\>_  
**Demo video:** _\<YouTube URL — fill in after recording\>_  
**License:** MIT

---

## The problem

LEO satellite operators cannot staff a ground pass for every anomaly. Current automated responses are rule-based and brittle; LLM agents that invent root causes or hallucinate safety numbers are unusable in this setting. Aero-Astra answers that directly: a multi-agent pipeline where every root cause comes from a dependency-graph candidate set, every safety score comes from a deterministic Monte Carlo simulator, and a five-rule GUARDIAN gate blocks unsafe actions before any recommendation reaches the operator.

> **What is simulated:** satellite telemetry is produced by a physics simulator with six injected fault types. No real satellite hardware is connected.

---

## What it does

Seven cooperating agents run a full incident autonomously:

| Agent | Role |
|---|---|
| **SENTINEL** | Anomaly detection (XGBoost flatline + physics threshold + residual correlation) |
| **SHERLOCK** | Graph-constrained root-cause diagnosis via Nemotron on Nebius Token Factory |
| **ORACLE** | Monte Carlo safety simulation over the recovery action catalog |
| **ATHENA** | Recovery plan synthesis via Nemotron on Nebius Token Factory |
| **GUARDIAN** | Deterministic 5-rule safety gate (no LLM) |
| **SCRIBE** | Audit runbook compiler |
| **CHRONICLE** | Persistent event log |

---

## How Nebius and NVIDIA are used

| Component | Model | Where it runs | Why |
|---|---|---|---|
| SHERLOCK (root cause) | _\<NEBIUS_MODEL_SHERLOCK — fill in slug\>_ | Nebius Token Factory | Graph-constrained classification; Nemotron's instruction-following keeps the response within the candidate set |
| ATHENA (recovery plan) | _\<NEBIUS_MODEL_ATHENA — fill in slug\>_ | Nebius Token Factory | Verbose 4096-token JSON planning; needs a larger, structured-output-capable model |
| App hosting | — | Nebius AI Cloud | CPU-only VM (no GPU needed — inference is on Token Factory) |

> **Measured:** _\<fill in SHERLOCK median latency, ATHENA median latency, first-attempt JSON validity % over N runs after smoke testing\>_

---

## Why the LLM cannot hallucinate its way into a bad recovery

1. Root cause must come from a dependency-graph candidate set, validated in code (SHERLOCK Phase 3)
2. The LLM never outputs safety scores — ORACLE's Monte Carlo scores are injected after plan validation
3. Irreversibility flags come from a hardcoded lookup, never from the LLM
4. GUARDIAN is a deterministic 5-rule gate with no LLM involvement

---

## Run it

### Hosted (Nebius AI Cloud)
_\<URL — fill in after deployment\>_

### Locally (Nebius Token Factory for LLM, no local GPU needed)

```bash
git clone https://github.com/Meet-Shah10/Aero_Astra_Nebius.git
cd Aero_Astra_Nebius
git checkout nebius-submission

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: fill in NEBIUS_API_KEY, NEBIUS_BASE_URL,
#            NEBIUS_MODEL_SHERLOCK, NEBIUS_MODEL_ATHENA
# Set NEBIUS_ONLY=1 to disable all non-Nebius providers.

python backend/api.py         # Tab 1
npm install && npm run dev    # Tab 2
```

### Docker (Nebius AI Cloud VM)

```bash
cp .env.example .env  # fill in NEBIUS_* values
docker compose up -d --build
# Open http://<server-ip> in your browser
# Verify: curl http://<server-ip>/health
```

---

## What is real and what is simulated

| Layer | Status |
|---|---|
| Satellite telemetry | **Simulated** — physics simulator, six injected fault types |
| LLM inference (SHERLOCK, ATHENA) | **Real** — live calls to Nebius Token Factory (Nemotron) |
| Monte Carlo safety simulation (ORACLE) | **Real** — deterministic runs in-process |
| Validation and gating logic | **Real** — graph checks, Pydantic schemas, GUARDIAN rules |
| SENTINEL XGBoost flatline detector | **Real** — trained on OPS-SAT telemetry data (Zenodo) |
| FDIR knowledge base (RAG) | **Curated** — 20 passages written for this project, modeled on NASA fault management practice (not retrieved from the handbook itself) |

---

## What changed during the hackathon

See [CHANGELOG_SUBMISSION.md](./CHANGELOG_SUBMISSION.md).

---

## Credits and licenses

- Satellite 3D model: [`simple_satellite_low_poly_free.glb`](https://sketchfab.com) — verify source license and add attribution
- Earth textures (`public/textures/earth/`): verify three.js / NASA source licenses and add attribution
- OPS-SAT dataset: Zenodo — see SENTINEL training scripts for citation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React / Vite  (port 5173)                │
│  Dashboard · Agent Console · Oracle 3-D View · Sandbox         │
└────────────────────┬────────────────────────────────────────────┘
                     │  WebSocket  ws://localhost:8000/ws
┌────────────────────▼────────────────────────────────────────────┐
│                   FastAPI Backend  (port 8000)                   │
│                                                                  │
│  SENTINEL  ──►  SHERLOCK  ──►  ORACLE  ──►  ATHENA  ──►  GUARDIAN│
│  (anomaly      (root-cause     (MC sim)    (mitigation  (safety  │
│   detect)       diagnosis)                  planning)    gate)   │
│                                                                  │
│  CHRONICLE (always-on audit log)   SCRIBE (runbook compiler)    │
└──────────┬──────────────────────────────────┬───────────────────┘
           │  OpenAI-compat REST               │  OpenAI-compat REST
  ┌────────▼────────┐                ┌─────────▼─────────┐
  │  MLX-LM :8080   │                │  MLX-LM :8081     │
  │  (SHERLOCK LLM) │                │  (ATHENA LLM)     │
  └─────────────────┘                └───────────────────┘
        Llama 3.2 3B-4bit                Llama 3.1 8B-4bit
      + Llama 3.2 1B draft            (standard inference)
     (speculative decoding)
```

Agents are **manually activated** from the UI — SENTINEL and CHRONICLE run continuously; SHERLOCK, ORACLE, and ATHENA fire only when the operator clicks **▶ Activate** on their respective pages.

---

## Usage Flow

1. **Launch** — the dashboard loads and the telemetry replay begins streaming.
2. **Wait for SENTINEL** — within ~6 seconds, SENTINEL detects the injected fault. The stream **freezes** at the fault frame.
3. **Click SHERLOCK** — navigate to SHERLOCK page and click **▶ Activate SHERLOCK**. Nemotron on Token Factory diagnoses the root cause.
4. **Click ATHENA** — ORACLE runs Monte Carlo simulation, then ATHENA (Nemotron) generates a recovery plan.
5. **GUARDIAN** fires automatically — classifies severity tier (`AUTOMATED_GUARDED`, `MANUAL_INTERLOCK`, or `AUTONOMOUS_SAFED`).
6. **Approve & execute** — SCRIBE compiles the audit runbook.

---

## Project Structure

```
Aero_Astra_Nebius/
├── backend/
│   ├── api.py                  # FastAPI app — WebSocket, /health endpoint, replay loop
│   ├── nebius.py               # Nebius Token Factory provider factory
│   ├── llm_client.py           # Multi-provider LLM client with fallback chain
│   ├── sherlock/               # SHERLOCK agent (root-cause diagnosis)
│   │   ├── agent.py            # Nebius → MLX → Ollama provider chain
│   │   ├── prompts.py
│   │   └── graph.py            # Satellite dependency graph (6 nodes, 18 edges)
│   ├── athena/                 # ATHENA agent (mitigation planning + RAG)
│   │   ├── agent.py            # Nebius → NVIDIA NIM → Ollama provider chain
│   │   └── rag/                # FDIR knowledge base (sentence-transformers vectorstore)
│   ├── sentinel/               # SENTINEL anomaly detectors
│   ├── oracle/                 # ORACLE Monte Carlo simulator
│   ├── simulator/              # Physics-based satellite telemetry engine
│   └── replay/                 # Pre-recorded telemetry playlist (playlist.json)
├── scripts/
│   └── nebius_smoke_test.py    # Proves real Token Factory calls work
├── src/
│   ├── config.js               # Central WebSocket URL config (no hardcoded localhost)
│   ├── App.jsx                 # Root React component, WebSocket state machine
│   └── components/
├── Dockerfile                  # Backend container (python:3.12-slim)
├── Dockerfile.web              # Frontend container (Node 20 + nginx)
├── docker-compose.yml          # Backend + web services
├── nginx.conf                  # SPA routing + WebSocket proxy
├── .env.example                # Env var template — copy to .env and fill in
├── CHANGELOG_SUBMISSION.md     # Changes made during the submission period
├── LICENSE                     # MIT
├── requirements.txt
├── package.json
└── vite.config.js
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `RuntimeError: NEBIUS_ONLY=1 but env vars missing` | Fill in `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL_SHERLOCK`, `NEBIUS_MODEL_ATHENA` in `.env` |
| Backend `ModuleNotFoundError` | Run `pip install -r requirements.txt` in a fresh venv |
| SHERLOCK button not appearing | Wait for SENTINEL to fire (~6 s after backend start) |
| RAG vectorstore empty | Delete `backend/athena/rag/vectorstore/` and restart backend to auto-reseed |
| `ws://` blocked on `https://` page | Set up TLS (e.g. Caddy) — nginx proxies `wss://` automatically when behind HTTPS |
| Port conflict | `lsof -i :8000` and kill the conflicting process |

---

## License

MIT — see [LICENSE](./LICENSE)
