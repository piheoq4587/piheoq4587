"""Fast parallel ping of all 7 active models. 30 s timeout each.

Outputs:
  [OK]   model_name 2.5s "OK"
  [FAIL] model_name 30.0s timeout
  [FAIL] model_name 0.5s 502 Bad Gateway
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

CONFIG_DIR = Path.home() / ".claude" / "config"
sys.path.insert(0, str(CONFIG_DIR))

# Load env
ENV_FILE = CONFIG_DIR / "api-credentials.env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k.startswith("export "):
            k = k[len("export "):]
        os.environ.setdefault(k, v)

from openai import OpenAI

BASE_URL = os.environ.get("OPENAI_API_BASE", "https://tone.nyc.mn/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

ACTIVE_MODELS = [
    "claude-opus-4.7-n",
    "gpt-5.5-n",
    "gemini-3.1-pro-n",
    "claude-opus-4.6-n",
    "claude-sonnet-4.6-n",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-0309-reasoning",
]

def ping(model: str) -> tuple[str, bool, float, str]:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=25)
    t0 = time.time()
    try:
        # Opus needs few-shot wrap; for a quick test we bypass and only check connectivity
        msgs = [{"role": "user", "content": "Reply with exactly: OK"}]
        resp = client.chat.completions.create(
            model=model, messages=msgs, max_tokens=10, temperature=0.0,
        )
        elapsed = time.time() - t0
        content = (resp.choices[0].message.content or "").strip()
        return (model, True, elapsed, content[:30] or "(empty)")
    except Exception as e:
        elapsed = time.time() - t0
        err = str(e)[:80]
        return (model, False, elapsed, err)

def main():
    print(f"BASE_URL: {BASE_URL}")
    print(f"API_KEY:  {API_KEY[:14]}...{API_KEY[-4:]}" if API_KEY else "API_KEY: (missing!)")
    print(f"Testing {len(ACTIVE_MODELS)} models in parallel (timeout 25 s each)...\n")

    results = []
    with ThreadPoolExecutor(max_workers=7) as ex:
        futures = {ex.submit(ping, m): m for m in ACTIVE_MODELS}
        for fut in as_completed(futures):
            results.append(fut.result())

    # Sort: success first, then by latency
    results.sort(key=lambda r: (not r[1], r[2]))

    print(f"{'STATUS':6s} {'MODEL':35s} {'LATENCY':>8s}  RESULT")
    print("-" * 90)
    for model, ok, elapsed, content in results:
        st = "[OK]  " if ok else "[FAIL]"
        print(f"{st} {model:35s} {elapsed:6.2f}s  {content}")

    print()
    n_ok = sum(1 for r in results if r[1])
    print(f"Summary: {n_ok}/{len(results)} models alive")
    if n_ok > 0:
        print(f"\nFastest alive models (sorted by latency):")
        for model, ok, elapsed, _ in results:
            if ok:
                print(f"  {elapsed:5.2f}s  {model}")

if __name__ == "__main__":
    main()
