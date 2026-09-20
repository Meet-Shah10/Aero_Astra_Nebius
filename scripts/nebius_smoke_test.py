"""
Prove real Nebius Token Factory calls work for both agent models.

Usage:
    python scripts/nebius_smoke_test.py

Expected output (on success):
    NEBIUS_MODEL_SHERLOCK  <model-slug>  1.23s  '{"ok": true}'
    NEBIUS_MODEL_ATHENA    <model-slug>  1.78s  '{"ok": true}'

Exit code 0 = pass. Non-zero = at least one call failed.
"""
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()   # reads from .env in cwd or parent directories

required = ["NEBIUS_API_KEY", "NEBIUS_BASE_URL", "NEBIUS_MODEL_SHERLOCK", "NEBIUS_MODEL_ATHENA"]
missing = [k for k in required if not os.environ.get(k)]
if missing:
    print(f"ERROR: Missing env vars: {missing}", file=sys.stderr)
    print("Copy .env.example to .env and fill in the Nebius credentials.", file=sys.stderr)
    sys.exit(1)

client = OpenAI(
    base_url=os.environ["NEBIUS_BASE_URL"],
    api_key=os.environ["NEBIUS_API_KEY"],
)

failures = 0
for env in ("NEBIUS_MODEL_SHERLOCK", "NEBIUS_MODEL_ATHENA"):
    model = os.environ[env]
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": 'Return only this JSON: {"ok": true}'}],
            max_tokens=64,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        elapsed = time.time() - t0
        content = repr(resp.choices[0].message.content)
        print(f"{env:<30} {model:<50} {elapsed:.2f}s  {content}")
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"{env:<30} {model:<50} {elapsed:.2f}s  ERROR: {exc}", file=sys.stderr)
        failures += 1

if failures:
    print(f"\n{failures} call(s) failed. See errors above.", file=sys.stderr)
    sys.exit(1)
else:
    print("\nSmoke test passed — both models responded via Nebius Token Factory.")
