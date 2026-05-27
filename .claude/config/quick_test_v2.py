"""Direct HTTP ping (bypass OpenAI client retries). 12 s strict timeout per model."""
import os, sys, time, json
import urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ENV = Path.home() / ".claude" / "config" / "api-credentials.env"
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k.startswith("export "): k = k[7:]
        os.environ.setdefault(k, v)

BASE = os.environ.get("OPENAI_API_BASE", "https://tone.nyc.mn/v1").rstrip("/")
KEY = os.environ.get("OPENAI_API_KEY", "")

MODELS = [
    "claude-opus-4.7-n",
    "gpt-5.5-n",
    "gemini-3.1-pro-n",
    "claude-opus-4.6-n",
    "claude-sonnet-4.6-n",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-0309-reasoning",
]

def ping(model):
    t0 = time.time()
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply OK"}],
        "max_tokens": 10,
        "temperature": 0.0,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8"))
            elapsed = time.time() - t0
            content = data["choices"][0]["message"].get("content") or ""
            return (model, True, elapsed, content.strip()[:30] or "(empty)")
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        return (model, False, elapsed, f"HTTP {e.code}")
    except urllib.error.URLError as e:
        elapsed = time.time() - t0
        return (model, False, elapsed, f"URLError {str(e.reason)[:40]}")
    except TimeoutError:
        return (model, False, 12.0, "timeout (>12s)")
    except Exception as e:
        elapsed = time.time() - t0
        return (model, False, elapsed, f"err: {str(e)[:40]}")

print(f"BASE: {BASE}", flush=True)
print(f"KEY:  {KEY[:14]}...{KEY[-4:]}" if KEY else "KEY: missing", flush=True)
print(f"Pinging {len(MODELS)} models in parallel (12s timeout each)\n", flush=True)
sys.stdout.flush()

results = []
with ThreadPoolExecutor(max_workers=7) as ex:
    futs = {ex.submit(ping, m): m for m in MODELS}
    for fut in as_completed(futs, timeout=20):
        try:
            r = fut.result(timeout=15)
            print(f"  {'OK ' if r[1] else 'XX '} {r[0]:35s} {r[2]:5.2f}s  {r[3]}", flush=True)
            results.append(r)
        except Exception as e:
            print(f"  XX  {futs[fut]:35s}  exec error: {e}", flush=True)
            results.append((futs[fut], False, 15.0, f"exec: {e}"))

n_ok = sum(1 for r in results if r[1])
print(f"\n{n_ok}/{len(MODELS)} models alive", flush=True)
print("\nFastest alive (sorted by latency):", flush=True)
for r in sorted([r for r in results if r[1]], key=lambda x: x[2]):
    print(f"  {r[2]:5.2f}s  {r[0]}", flush=True)
print("\nDead/slow models:", flush=True)
for r in [r for r in results if not r[1]]:
    print(f"  {r[2]:5.2f}s  {r[0]}  -> {r[3]}", flush=True)
