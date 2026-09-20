# Aero-Astra: Nebius x NVIDIA Global AI Hackathon Submission Guide

Target: **Best Apps and Agents track**
Deadline: **Oct 30, 2026, 10:00am PDT** (that is 10:30pm IST on Oct 30). Plan to submit by Oct 27.
Written: Sep 20, 2026, from the Devpost overview page and the repo files you shared.

Files I could not read, so parts of this guide are written without seeing them: `backend/api.py`, `backend/llm_client.py` (binary in the upload), `src/App.jsx`, `backend/sentinel/train.py`, `backend/simulator/faults.py`, `recovery.py`, `schemas.py`. Send them as text if you want exact patches.

How to read confidence labels in this guide:

- **Verified** means stated on the Devpost overview page or visible in your code.
- **Inference** means my reasoning from the code or from how these platforms usually work.
- **Confirm** means check the Devpost Rules page or Nebius docs before relying on it.

---

## 0. Hard requirements and where you stand today

| Requirement (Verified, Devpost overview) | Status today | Fix in section |
|---|---|---|
| Runs on Nebius Token Factory or Nebius AI Cloud | Fails. ATHENA calls NVIDIA NIM, SHERLOCK calls local MLX/Ollama with OpenRouter fallback | 4, 8 |
| Uses at least one NVIDIA open source model | Partial. ATHENA lists a Nemotron model, but served from NVIDIA's endpoint, not Nebius | 4 |
| Working demo URL | Fails. Needs three local terminals and Apple Silicon for MLX | 8 |
| Public repo with open source license visible at top | Fails. README says MIT, no `LICENSE` file in the tree | 6 |
| README with setup and how Nemotron/Token Factory are used | Fails. README describes Llama/MLX, docstrings mention Gemini | 12 |
| Demo video, 3 minutes or less, public YouTube, audio covers Token Factory and Nemotron use | Not started | 14 |
| Written explanation of what changed during the submission period (project predates it) | Not started | 2.5 |
| Feedback on Nebius and NVIDIA tools | Not started | 15 |

Judging criteria (Verified): Technological Implementation, Design, Potential Impact, Quality of the Idea. Design and Idea are your strong criteria (inference). Implementation is fixable (sections 4 to 8). Impact needs honest framing (section 9).

---

## 1. Timeline

| Dates | Goal | Exit test |
|---|---|---|
| Sep 21 to Sep 27 | Separate repo, Nebius provider in SHERLOCK and ATHENA, smoke test | `scripts/nebius_smoke_test.py` passes for both models |
| Sep 28 to Oct 4 | RAG embeddings without Ollama, cold-start reproducibility | Fresh venv on a clean clone runs the full pipeline |
| Oct 5 to Oct 11 | Deploy on Nebius, remove localhost hardcodes | Public URL runs a full incident end to end |
| Oct 12 to Oct 18 | Honesty audit (section 9), stretch features (section 10), README | No display value that fakes backend data |
| Oct 19 to Oct 25 | Video, Devpost text, feedback, changelog | Draft submission saved on Devpost |
| Oct 26 to Oct 29 | Buffer, final test on the public URL, make repo public, submit | Submission confirmation email |

---

## 2. Create the separate submission repository

### 2.1 Why a new repository

- GitHub does not let you fork your own repo into the same account, so a copy is the way to get a clean workspace.
- Clone with full history, do not squash. The rules ask you to explain what changed during the submission period. Git history plus a baseline tag is your proof.
- Your original repo stays untouched as a fallback.

### 2.2 One-shot setup script

Prerequisites: `git`, GitHub CLI (`brew install gh`), then `gh auth login`.
Save as `setup_submission_repo.sh` outside the project folder, run with `bash setup_submission_repo.sh`.

```bash
#!/usr/bin/env bash
set -euo pipefail

SRC_URL="https://github.com/Meet-Shah10/Aero_Astra.git"
GH_USER="Meet-Shah10"
NEW_NAME="Aero_Astra_Nebius"
HACKATHON_START="2026-08-26 00:00"   # Confirm on the Devpost Rules page

git clone "$SRC_URL" "$NEW_NAME"
cd "$NEW_NAME"

BASE_BRANCH="$(git branch --show-current)"

# Baseline tag: last commit before the submission period started.
BASELINE_SHA="$(git rev-list -1 --before="$HACKATHON_START" "$BASE_BRANCH" || true)"
if [ -n "$BASELINE_SHA" ]; then
  git tag -a pre-hackathon-baseline "$BASELINE_SHA" \
    -m "State before the Nebius x NVIDIA submission period"
  echo "Baseline tag set at $BASELINE_SHA"
else
  echo "No commit before $HACKATHON_START. Skipping baseline tag."
fi

# Point origin at the NEW repo and make the old one push-proof.
git remote rename origin upstream-original
git remote set-url --push upstream-original DISABLED

# Private while you work. Flip to public in section 2.6.
gh repo create "$GH_USER/$NEW_NAME" --private --source=. --remote=origin
git push -u origin "$BASE_BRANCH" --tags

git checkout -b nebius-submission
git push -u origin nebius-submission

echo "Done. Work in: $(pwd)  (branch nebius-submission)"
```

Manual alternative if you do not want `gh`: create an empty private repo named `Aero_Astra_Nebius` on github.com, then run the clone, tag, and remote commands above by hand, and use `git remote add origin https://github.com/Meet-Shah10/Aero_Astra_Nebius.git`.

### 2.3 Check the baseline tag

```bash
git tag -n
git log --oneline pre-hackathon-baseline -1
git log --oneline pre-hackathon-baseline..HEAD | wc -l   # commits made since
```

If the tag is missing, none of your commits predate Aug 26 (or the date is wrong). Adjust `HACKATHON_START` after you read the Rules page.

### 2.4 Scan history for leaked secrets before anything goes public

```bash
git log --all --oneline -S"sk-or-"
git log --all --oneline -S"nvapi-"
git log --all --oneline -- .env
git ls-files | grep -E '\.env$|\.pkl$|\.joblib$|\.pdf$|\.gguf$|\.safetensors$'
```

Any hit on the first three means you rotate that key now (OpenRouter and NVIDIA dashboards) and rewrite history with `git filter-repo` before making the repo public. Rotating is mandatory even after a rewrite, because the old key already sat in a repo.

### 2.5 Working rules in the new repo

1. All work happens on `nebius-submission`. Merge to `main` only at the end.
2. One logical change per commit. Use prefixes: `nebius:`, `deploy:`, `rag:`, `fix:`, `docs:`, `feat:`.
3. Keep `CHANGELOG_SUBMISSION.md` at the repo root. Add a line for every significant change, with the date. Paste it into the Devpost "what changed" field at the end.

Template:

```markdown
# Changes made during the submission period (starts 2026-08-26, confirm on Rules page)

Baseline: tag `pre-hackathon-baseline`

## Added
- 2026-09-2x: Nebius Token Factory provider for SHERLOCK and ATHENA (Nemotron)
- ...

## Changed
- ...

## Removed
- ...
```

At the end, produce evidence with:

```bash
git diff --stat pre-hackathon-baseline..HEAD
git shortlog -sn pre-hackathon-baseline..HEAD
```

### 2.6 Visibility

Keep the repo private while you work. Before you submit (Oct 26 to Oct 28):

```bash
gh repo edit Meet-Shah10/Aero_Astra_Nebius --visibility public --accept-visibility-change-consequences
```

Then open the repo in a logged-out browser window and confirm the LICENSE badge shows at the top of the page.

---

## 3. Accounts and credits

1. Register on the hackathon page and accept the rules.
2. Create a Nebius account and a Token Factory API key. Store it in `.env` only.
3. Credits: a third-party listing reports a $25 Token Factory credit with an event code and another $25 for the Nebius Builders Program, plus Tavily credits. **Confirm** the code and terms on the Devpost Resources page. Do not trust the third-party listing for the code.
4. Budget check: SHERLOCK plus ATHENA use a few thousand tokens per incident (inference). Set `max_tokens` conservatively and log usage during testing so you know the cost before demo day.

---

## 4. Workstream A: Nebius Token Factory integration

Goal: SHERLOCK and ATHENA make real runtime calls to Token Factory, using Nemotron models, and a demo-mode switch guarantees no silent fallback to another provider.

### 4.1 Environment variables

Create `.env.example` in the repo root and commit it. Copy to `.env` locally and never commit `.env`.

```dotenv
# Nebius Token Factory (required for the submission build)
NEBIUS_API_KEY=
# OpenAI-compatible base URL. Copy it from the Token Factory docs. Confirm.
NEBIUS_BASE_URL=
# Exact model slugs from the Token Factory model catalog. Confirm.
# The Devpost page suggests Nemotron Ultra for heavy reasoning, Nano or Super for fast calls.
NEBIUS_MODEL_SHERLOCK=
NEBIUS_MODEL_ATHENA=
# 1 = use only Nebius (demo, video, hosted build). 0 = allow local fallbacks for development.
NEBIUS_ONLY=1

# Development-only fallbacks
OPENROUTER_API_KEY=
NVIDIA_API_KEY=
```

Confirm `python-dotenv`'s `load_dotenv()` runs in `api.py` before the agents are constructed. Check with `grep -n "load_dotenv" backend/api.py`.

### 4.2 New file `backend/nebius.py`

```python
"""Nebius Token Factory provider factory for the AERO-ASTRA LLM fallback chain."""
from __future__ import annotations

import logging
import os

from openai import OpenAI

from backend.llm_client import LLMProvider

log = logging.getLogger(__name__)


def nebius_only() -> bool:
    return os.environ.get("NEBIUS_ONLY", "0") == "1"


def nebius_provider(model_env: str, timeout_s: int = 120) -> LLMProvider | None:
    """Build a Token Factory provider. model_env names the env var holding the model slug."""
    key = os.environ.get("NEBIUS_API_KEY")
    base = os.environ.get("NEBIUS_BASE_URL")
    model = os.environ.get(model_env)
    missing = [
        name for name, val in (
            ("NEBIUS_API_KEY", key),
            ("NEBIUS_BASE_URL", base),
            (model_env, model),
        ) if not val
    ]
    if missing:
        if nebius_only():
            raise RuntimeError(f"NEBIUS_ONLY=1 but these env vars are missing: {missing}")
        log.warning("Nebius provider disabled, missing env vars: %s", missing)
        return None
    log.info("Nebius provider ready | model=%s", model)
    return LLMProvider(
        name=f"Nebius Token Factory ({model})",
        client=OpenAI(base_url=base, api_key=key),
        model=model,
        timeout_s=timeout_s,
    )
```

This matches how `athena/agent.py` already constructs `LLMProvider(name=..., client=..., model=..., timeout_s=...)`. If `llm_client.py` defines the dataclass differently, adjust here.

### 4.3 Patch ATHENA (`backend/athena/agent.py`)

Add the import at the top:

```python
from backend.nebius import nebius_only, nebius_provider
```

In `AthenaAgent.__init__`, replace the block that builds NVIDIA NIM and Ollama providers with:

```python
self._providers: list[LLMProvider] = []

# 1. Nebius Token Factory: primary, and the only provider when NEBIUS_ONLY=1
nebius = nebius_provider("NEBIUS_MODEL_ATHENA", timeout_s=180)
if nebius:
    self._providers.append(nebius)

# 2. Development fallbacks: keep your existing NVIDIA NIM and Ollama blocks here,
#    indented under this condition, unchanged.
if not nebius_only():
    ...  # existing NVIDIA NIM (nemotron, deepseek) and Ollama provider blocks
```

Behavior note (Verified in code): on the last retry, `plan()` skips `providers[0]` and calls `providers[1:]`. With `NEBIUS_ONLY=1` the chain has one provider, so all attempts use Nebius. With `NEBIUS_ONLY=0`, the last attempt goes to a non-Nebius provider. That is why demo and video runs must use `NEBIUS_ONLY=1`.

### 4.4 Patch SHERLOCK (`backend/sherlock/agent.py`)

Add the import:

```python
from backend.nebius import nebius_only, nebius_provider
```

Directly after the existing `self._providers = build_clients(...)` call:

```python
nebius = nebius_provider("NEBIUS_MODEL_SHERLOCK")
if nebius_only():
    self._providers = [nebius]
elif nebius:
    self._providers.insert(0, nebius)
```

### 4.5 Model choice

Use Nemotron for both agents so the "NVIDIA open source model" requirement is unambiguous. Suggested split (inference, tune after testing):

- SHERLOCK: a smaller Nemotron. The job is constrained classification over a graph-validated candidate set, so it does not need the largest model, and latency matters because the stream freezes while it runs.
- ATHENA: a larger Nemotron. It writes procedure steps, weighs ORACLE scores, and needs a 4096 token JSON.

Record measured latency and JSON-validity rate per model in the README (see section 12). That is real evidence for the Technological Implementation criterion.

### 4.6 Smoke test `scripts/nebius_smoke_test.py`

```python
"""Prove a real Token Factory call works for both agent models."""
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    base_url=os.environ["NEBIUS_BASE_URL"],
    api_key=os.environ["NEBIUS_API_KEY"],
)

for env in ("NEBIUS_MODEL_SHERLOCK", "NEBIUS_MODEL_ATHENA"):
    model = os.environ[env]
    t0 = time.time()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": 'Return only this JSON: {"ok": true}'}],
        max_tokens=64,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    print(env, model, f"{time.time() - t0:.2f}s", repr(resp.choices[0].message.content))
```

Run: `python scripts/nebius_smoke_test.py`

### 4.7 Integration risks to test (all Inference until you test them)

1. **JSON mode.** ATHENA sends `response_format={"type": "json_object"}`. If the chosen model or endpoint rejects it, the call errors. The smoke test above checks it.
2. **Reasoning output.** Nemotron models may emit reasoning text before the JSON. ATHENA's `_try_parse_json` extracts from the first `{` to the last `}`, which handles preamble. SHERLOCK's parser does not have brace extraction, so port that fallback from ATHENA if SHERLOCK fails to parse.
3. **Token budget.** If a model spends tokens on reasoning, ATHENA's 4096 `max_tokens` may truncate the JSON. Watch for the "empty response" `ValueError` in `_call_llm`.
4. **Timeouts.** SHERLOCK uses the default `timeout_s`. Raise it if cold starts on a large model time out.
5. **Provenance.** Add `provider` and `model` fields to the `sherlock` and `athena` WebSocket messages and show them in the UI. This needs `api.py`. It is the cheapest way to show judges the Nebius calls are real.

---

## 5. Workstream B: RAG embeddings without Ollama

Problem (Verified in code): `AthenaRAGPipeline` embeds with Ollama `nomic-embed-text`, falling back to Gemini, and your build manifest records `nomic-embed-text`. A hosted Nebius deployment has no Ollama and no Gemini key. If the embedder cannot start, `ATHENA.plan()` catches the exception and silently plans without FDIR context. Your demo would lose the RAG grounding without any error.

Options:

- **A (simplest):** local `sentence-transformers` embedder. The package is already in `requirements.txt`, runs on CPU, no external service.
- **B:** a Token Factory embedding model, if the catalog has one. **Confirm.** This adds another Nebius usage point to cite.

Option A snippet for `backend/athena/rag/pipeline.py`:

```python
LOCAL_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class LocalEmbedder:
    def __init__(self, model: str = LOCAL_EMBED_MODEL):
        from sentence_transformers import SentenceTransformer
        self.model = model
        self._m = SentenceTransformer(model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._m.encode(texts, normalize_embeddings=True).tolist()
```

Then:

1. In `build_embedder()`, try `LocalEmbedder` first (or your Nebius embedder), then keep the Ollama and Gemini paths as development fallbacks.
2. Change the module default `EMBED_MODEL = OLLAMA_EMBED_MODEL` to the new model name. `is_ready()` compares the manifest against this constant, so a mismatch triggers a reseed on every restart.
3. Query and documents must use the same embedding model. Never mix `nomic-embed-text` vectors with a different model at query time.
4. Rebuild: `python -m backend.athena.rag.seed --force-rebuild`
5. Do not commit the Chroma binaries. Reseed at container start. It is 20 documents, so it takes seconds.
6. Add a startup log line, `RAG ready | docs=20 | embed=<model>`, and a `/health` field for it.

Also fix a labeling problem: `seed.py` says the corpus is "synthesized from the handbook's published content", and the metadata source is `NASA-HDBK-1002-synthetic`. But the ATHENA prompt and `retrieve()` present the passages as retrieved from NASA-HDBK-1002 ("authoritative"). In README, video, and Devpost text, call it a curated FDIR knowledge base written for this project, modeled on NASA fault-management practice. Do not call it retrieval from the NASA handbook.

---

## 6. Workstream C: Cold-start reproducibility

A judge must be able to clone and run. Test everything in this section in a fresh directory and a fresh virtual environment.

### 6.1 License

Add `LICENSE` at the repo root (MIT text below). Confirm the copyright holder name and whether teammates go on it.

```text
MIT License

Copyright (c) 2026 Meet Shah

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 6.2 Dependencies (Inference from imports, verify with a fresh venv)

Your `requirements.txt` does not list several packages your code imports:

| Imported in | Package likely missing from requirements |
|---|---|
| `sherlock/graph.py` | `networkx` |
| `sentinel/utils.py`, `engines.py`, `train.py` | `xgboost`, `torch`, `joblib`, `tqdm` |
| `athena/rag/pipeline.py` | `langchain-text-splitters`, and `pymupdf` or `pypdf` (the fallback import fails if neither exists) |

Also, `sentinel/utils.py` imports `torch` at module load, and `engines.py` imports `utils`. Every SENTINEL import therefore pulls PyTorch. For the container, install CPU-only torch, or move the torch and LSTM imports inside the functions that use them.

Also resolve these disagreements between your docs and Makefile:

- README says `pip install -r requirements.txt`, Makefile says `pip install -r backend/requirements.txt`. Only the root file appears in the tree.
- README runs `python backend/api.py`, Makefile runs `cd backend && python api.py`. Your modules import as `backend.xxx`, so the working directory matters. Pick one command, make it work, and use it everywhere.

Verification loop:

```bash
cd "$(mktemp -d)"
git clone https://github.com/Meet-Shah10/Aero_Astra_Nebius.git app && cd app
git checkout nebius-submission
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then fill in real values
python backend/api.py
```

Fix every `ModuleNotFoundError` until the backend starts, then add the packages to `requirements.txt` with pinned versions from `pip freeze`.

### 6.3 SENTINEL model artifact

`sentinel_production.pkl` is gitignored and needs the OPS-SAT dataset (`backend/data/raw/opssat/dataset.csv`, downloaded from Zenodo) plus training. A judge will not do that. Choose one:

1. Commit the `.pkl` with plain git if it is under a few MB. Do not use Git LFS: your own Makefile has a check for LFS pointer stubs, which shows this already broke once.
2. Train at container build time from a small committed sample.

Then confirm `make check` passes on a clean clone. Make sure `backend/models/sentinel_ensemble.json` and `sentinel_scaler.joblib` (already in the tree) load.

### 6.4 Replay playlist

`backend/replay/playlist.json` (3 to 4 MB) drives the demo. Either commit it or generate it in the Docker build with `python backend/replay/generate.py`. Confirm the generated output is deterministic (seeds are set in `generate.py`).

### 6.5 Repo cleanup

- Delete `public/globe-debug.html`. It is a debug page that imports from `framer.com` and `esm.sh` at runtime.
- Check the `framer` dependency in `package.json` is actually used. Remove it if not.
- Confirm `public/textures/earth/*` and `public/simple_satellite_low_poly_free.glb` are committed, since the frontend fetches them at runtime.
- Attribution: the satellite GLB is named "free", which often means a Creative Commons license that requires credit. Check the source license and add a "Credits" section to the README. Do the same for the three.js example Earth textures.
- Add `.dockerignore` (`.venv`, `node_modules`, `.git`, `backend/athena/rag/vectorstore`, `__pycache__`, `.env`).

---

## 7. Workstream D: Frontend configuration

Find hardcoded backend addresses:

```bash
grep -rn "localhost" src backend --include=*.js --include=*.jsx --include=*.py
grep -rn "ws://" src
```

Known: `src/components/sandbox/useSandboxWs.js` hardcodes `ws://localhost:8000/ws/sandbox`. `App.jsx` (not shared) very likely hardcodes `ws://localhost:8000/ws` too.

Replace with one helper, for example `src/config.js`:

```js
const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
export const WS_BASE = import.meta.env.VITE_WS_URL ?? `${proto}://${window.location.host}`;
export const WS_URL = `${WS_BASE}/ws`;
export const SANDBOX_WS_URL = `${WS_BASE}/ws/sandbox`;
```

Create `.env.development` with `VITE_WS_URL=ws://localhost:8000` for local development. Vite's proxy in `vite.config.js` covers only `/api`, not WebSockets. In production (nginx in section 8) everything shares one origin, so no env var is needed.

---

## 8. Workstream E: Deploy on Nebius

**Confirm** the exact Nebius product and setup steps in the Nebius docs. This section gives a generic container layout that works on any Nebius VM or container service.

Inference: since the LLM calls go to Token Factory, the app itself needs no GPU. A small CPU instance is enough. The Devpost page encourages, but does not require, Nebius Serverless Endpoints for the app and Serverless Jobs for background work. Using them earns extra credibility with the Nebius-specific judges.

Files to add at the repo root.

`Dockerfile` (backend):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["python", "backend/api.py"]
```

Confirm `api.py` binds `host="0.0.0.0"`, otherwise the container will not accept outside connections. Check with `grep -n "uvicorn.run" backend/api.py`.

`Dockerfile.web` (frontend plus reverse proxy):

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

`nginx.conf`:

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;

  location / {
    try_files $uri /index.html;
  }

  location /api/ {
    proxy_pass http://backend:8000;
  }

  location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
  }
}
```

`docker-compose.yml`:

```yaml
services:
  backend:
    build: .
    env_file: .env
    expose:
      - "8000"
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

Deploy steps:

1. Provision a small VM on Nebius AI Cloud, install Docker.
2. Copy the repo, create `.env` on the server with real keys and `NEBIUS_ONLY=1`. Never bake keys into images.
3. `docker compose up -d --build`
4. Open the public IP in a browser. Run one full incident.
5. Put HTTPS in front if you have a domain (Caddy is the least effort). Browsers block `ws://` from `https://` pages, but with one origin the scheme follows the page, so it works either way.
6. Add a `GET /health` endpoint to `api.py` that returns provider names, model slugs, RAG doc count, and uptime.
7. Keep the demo URL live until judging results are published. **Confirm** the judging window on the Rules page.

Optional (encouraged, Verified on the page): run ORACLE's Monte Carlo as a Nebius Serverless Job. It is the heaviest deterministic step (`n_runs` times `steps` per action, for every action in the catalog).

---

## 9. Workstream F: Honesty and accuracy audit

Judges read the repo and the video. Several UI values do not come from real backend data (Verified in the files you shared). Each is a credibility risk under Potential Impact and Technological Implementation. Fix or relabel every one.

| File | What it shows | Where it actually comes from | Fix |
|---|---|---|---|
| `oracle/oracleAdapter.js` | Outcome distribution (nominal / degraded / mission loss counts of 100) | Derived from the normalized safety score, not the real Monte Carlo outcome counts | Pass the real `outcome_counts` from `MonteCarloResult` through the WebSocket message, or label it "estimated from safety score" |
| `oracle/oracleAdapter.js` | Battery SOC trajectory chart | Generated by `generateDynamicSocTrajectory` (a formula from mean and std) | Record per-step mean and std SOC inside `run_monte_carlo` and send it. Or label "illustrative" |
| `oracle/oracleAdapter.js` | Mean and P90 time to recovery | Formula from success probability | Compute from the runs, or remove the fields |
| `oracle/oracleAdapter.js` and `OracleView.jsx` | "Processing" progress with run counter (Run 37 / 100) | A timer replaying results that finished before the animation started | Label it "replaying results" or remove the fake progress |
| `AgentDetailPage.jsx` (ATHENA) | "Nominal recovery: 85%" | It shows `effectiveness_score`, which the LLM judged | Relabel "Effectiveness (LLM-judged)" |
| `AgentDetailPage.jsx` (VITALS offline branch) | "RUL ESTIMATE 12 ORBITS", "+4.2C/hr", "85.2%" | Hardcoded strings | Delete, or label "sample values, backend offline" |
| `AnomalyLabels.jsx` | "+4.2C/hr", "-114.7 dBm" | Hardcoded strings | Bind to the live telemetry message |
| `OracleHeader.jsx` | "Input from ATHENA, 6 candidate actions" | Static text. In your pipeline ORACLE ranks the whole catalog before ATHENA plans | Correct the text |
| `oracle/oracleFixture.js` | Mock ORACLE results when the backend is offline | Fabricated numbers | Disable the mock path in the hosted build so it can never appear in a demo |

SENTINEL framing (Verified from `engine_b.py`): its own docstring says the XGBoost model, trained on flatline features, structurally cannot flag any of the six simulated faults. The demo faults trigger through physics thresholds (Engine B), residual correlation (Engine C, ADCS only), and the vitals fallback. Describe SENTINEL exactly like that. Say XGBoost detects stuck-sensor flatlines, trained on real OPS-SAT data.

Impact framing: telemetry is simulated. Say so in the first paragraph of the README. Tie the value to the concrete problem: LEO operators cannot staff a ground pass for every anomaly, and LLM agents that invent root causes or safety numbers are unusable in that setting. Your architecture answers that directly: graph-constrained root cause, LLM never produces safety scores, deterministic GUARDIAN gate, Monte Carlo grounding. That is the specific, credible case the Impact criterion asks for.

Doc consistency: agent docstrings still say "Claude/Gemini via OpenRouter". Update them to match the Nebius reality.

---

## 10. Workstream G: Changes that make the "significant update" real (optional stretch)

The Nebius migration and deployment are a real delta, but a bigger delta strengthens both the rules requirement and the judging. Pick two or three, in this order of value per hour (my inference):

1. **Real Monte Carlo outputs in the UI.** Return true outcome counts and per-step SOC mean and std from `run_monte_carlo`. This removes three rows from the audit table above.
2. **LLM provenance panel.** A UI panel listing each LLM call: agent, model, provider, latency, tokens, attempts. Data source: the timing you already have plus `llm_attempts` in the schemas.
3. **ORACLE on Nebius Serverless Jobs.** Also earns explicit alignment with the Best Apps and Agents track text.
4. **Nemotron-written SCRIBE runbook.** Today the runbook is compiled from records in the frontend. An LLM-written executive summary (from `overall_reasoning`) grounded in the audit trail is a natural Token Factory use.
5. **Tavily.** There is a $3,000 "Best Use of Tavily" bonus (Verified). One possible use is CHRONICLE pulling live space-weather advisories as context for SHERLOCK. Only do this if it produces a real, demonstrable benefit. Do not bolt it on for the prize.

---

## 11. Test plan (acceptance criteria)

Run everything on the deployed URL, not only locally.

- [ ] Fresh clone, fresh venv, `pip install -r requirements.txt`, backend starts with no `ModuleNotFoundError`
- [ ] `python scripts/nebius_smoke_test.py` prints a valid JSON reply for both models
- [ ] With `NEBIUS_ONLY=1`, the backend log shows `Nebius Token Factory` on every SHERLOCK and ATHENA call, and no other provider name appears
- [ ] Temporarily set a wrong `NEBIUS_API_KEY`: the app fails loudly (SHERLOCK and ATHENA errors), it does not silently use another provider
- [ ] Run all three replay loops (TCS thermal runaway, propulsion thruster fault, EPS cascade). For each: SENTINEL fires, SHERLOCK returns a root cause inside the graph candidate set, ORACLE ranks actions, ATHENA plan validates, GUARDIAN assigns a tier, SCRIBE report renders
- [ ] Record for each loop: `llm_attempts` for SHERLOCK and ATHENA, total latency, GUARDIAN tier. Put the table in the README
- [ ] Anti-hallucination path: force a bad model output (temporarily edit a prompt) and confirm the retry and reprompt path recovers or raises `SherlockDiagnosisError` / `AthenaError`
- [ ] Sandbox tab: run a fault, then a compare run (Run A and Run B)
- [ ] RAG: confirm the ATHENA prompt log shows FDIR context retrieved (`RAG retrieved N chars`)
- [ ] Open the public URL from a phone and from a logged-out browser
- [ ] No console errors, no `localhost` requests in the browser network tab
- [ ] Audit table from section 9: every row fixed or relabeled

---

## 12. README template

Replace your README top section with this structure. Everything in angle brackets is data you measure and fill in.

```markdown
# Aero-Astra: Autonomous Satellite Fault Management on Nebius + NVIDIA Nemotron

Track: Best Apps and Agents
Live demo: <public URL>
Demo video: <YouTube URL>
License: MIT

## The problem
<2 to 3 sentences: satellite operators cannot staff every anomaly; LLM agents that invent root causes
or safety numbers are unsafe. Say plainly that telemetry in this demo is physics-simulated.>

## What it does
Seven cooperating agents run a full incident: SENTINEL detects, SHERLOCK diagnoses, ORACLE simulates,
ATHENA plans, GUARDIAN gates execution, SCRIBE writes the audit runbook, CHRONICLE logs everything.

## How Nebius and NVIDIA are used
| Component | Model | Where it runs | Why |
|---|---|---|---|
| SHERLOCK (root cause) | <Nemotron model slug> | Nebius Token Factory | <reason> |
| ATHENA (recovery plan) | <Nemotron model slug> | Nebius Token Factory | <reason> |
| App hosting | n/a | Nebius AI Cloud <or Serverless Endpoints> | <reason> |
| ORACLE Monte Carlo | n/a | <local / Serverless Jobs> | <reason> |
Measured: SHERLOCK median latency <x> s, ATHENA <y> s, first-attempt JSON validity <z>% over <n> runs.

## Why the LLM cannot hallucinate its way into a bad recovery
1. Root cause must come from a dependency-graph candidate set, checked in code
2. The LLM never outputs safety scores; ORACLE's Monte Carlo scores are injected after validation
3. Irreversibility comes from a hardcoded lookup, never from the LLM
4. GUARDIAN is a deterministic 5-rule gate with no LLM

## Architecture
<paste your diagram from the current README, update the model boxes>

## Run it
### Hosted
<URL>
### Locally
<exact commands from the fresh-clone test in section 6.2, with NEBIUS_* env vars>

## What is real and what is simulated
- Simulated: satellite telemetry (physics simulator), six injected faults
- Real: LLM calls, Monte Carlo runs, validation and gating logic, OPS-SAT-trained flatline detector
- Knowledge base: 20 curated FDIR passages written for this project, modeled on NASA fault management practice

## What changed during the hackathon
<paste CHANGELOG_SUBMISSION.md>

## Credits and licenses
<3D model, textures, datasets, libraries>
```

---

## 13. Devpost project description outline

Use the same sections Devpost expects, in this order:

1. **What it does** (3 sentences, name the track)
2. **The problem** (real audience: LEO mission operations teams; the specific pain)
3. **How we built it** (Token Factory, which Nemotron models, why those sizes, what runs where)
4. **Guardrails** (the four anti-hallucination mechanisms above; this is your strongest technical differentiator)
5. **Challenges** (JSON reliability, latency while the stream is frozen, RAG without Ollama, whatever you truly hit)
6. **Accomplishments** (measured numbers from your test table)
7. **What is simulated** (say it plainly)
8. **What changed during the submission period** (paste the changelog)
9. **What is next** (real telemetry feeds, constellation scale)

---

## 14. Demo video script (3 minutes maximum, public on YouTube)

The page requires audio that explains how you used Token Factory and Nemotron. Record one continuous screen capture, then add voiceover.

| Time | Screen | Voiceover points |
|---|---|---|
| 0:00 to 0:20 | Title, then the dashboard with the Earth scene | The problem in two sentences. One line: telemetry is simulated |
| 0:20 to 0:50 | Architecture diagram | The agents, the guardrail idea, what runs on Nebius |
| 0:50 to 1:20 | Stream freezes at the fault, SENTINEL page | What SENTINEL saw and which engine fired |
| 1:20 to 1:50 | SHERLOCK page, dependency graph, causal chain | Graph-constrained candidates. Say "Nemotron on Nebius Token Factory" and show the provenance panel or backend log with the Nebius call |
| 1:50 to 2:20 | ORACLE results, ATHENA plan, GUARDIAN tier, approve, SCRIBE runbook | Monte Carlo scores come from the simulator, not the LLM. GUARDIAN is deterministic |
| 2:20 to 2:45 | Nebius console or terminal showing Token Factory usage, `/health` output | Which models, which product, measured latency |
| 2:45 to 3:00 | Impact slide | Who benefits, what is next |

Rules for the recording:

- Run it against the public URL with `NEBIUS_ONLY=1`.
- Do a full rehearsal first and time it. Trim to 2:50.
- Do not show API keys or the `.env` file. Blur the terminal if needed.
- Every claim in the voiceover must match a section 9 fixed value.

---

## 15. Feedback submission (required, and a $100 "Most Valuable Feedback" prize exists)

Keep notes while you build. Suggested structure:

```markdown
### Nebius Token Factory
- Onboarding: <time from signup to first successful call, friction points>
- API: <OpenAI compatibility gaps found, e.g. response_format behavior, error messages>
- Models: <how you picked the Nemotron models, what surprised you>
- Latency and reliability: <numbers>
- Docs: <what was missing or wrong>
- Suggestions: <3 concrete requests>

### NVIDIA Nemotron
- Instruction following on strict JSON: <numbers>
- Reasoning output handling: <how you dealt with it>
- Suggestions: <...>

### Nebius AI Cloud / Serverless (if used)
- <deployment notes>
```

Specific, measured, and actionable beats general praise.

---

## 16. Final submission checklist

- [ ] Rules page reread; submission period start date confirmed and `pre-hackathon-baseline` tag matches
- [ ] Track selected: Best Apps and Agents
- [ ] Repo public, LICENSE visible at the top, README complete with the Nebius/Nemotron table
- [ ] `.env` and secrets absent from the repo and the full history (section 2.4)
- [ ] Public demo URL works from a logged-out browser and a phone; it will stay up through judging
- [ ] Video uploaded to YouTube as public, 3:00 or shorter, audio covers Token Factory and Nemotron
- [ ] Feedback section filled in
- [ ] "What changed" text pasted from `CHANGELOG_SUBMISSION.md`
- [ ] Audit table (section 9) closed
- [ ] Devpost submission saved as draft by Oct 25, final submit by Oct 27
- [ ] Confirmation email received

---

## Appendix: items to confirm on the Rules page or Nebius docs

1. Exact submission period start date
2. Whether runtime calls to Token Factory must be the only inference path, or whether other providers as fallbacks are allowed
3. Token Factory base URL, model slugs, JSON mode support, embedding models
4. Which Nebius product to use for hosting (AI Cloud VM vs Serverless Endpoints) and its setup steps
5. Credit codes and terms (third-party listing only)
6. How long the demo URL must stay live, and when judging ends
7. Team size limits and who to list on the license
8. Rules on third-party assets (3D model, textures) and existing code disclosure
