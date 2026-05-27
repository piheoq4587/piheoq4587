"""Retry-with-backoff test. Sequential, 3 attempts each, 25s timeout."""
import os, sys, time, json
import urllib.request, urllib.error
from pathlib import Path

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
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-0309-reasoning",
    "claude-opus-4.7-n",
    "gpt-5.5-n",
    "gemini-3.1-pro-n",
    "claude-opus-4.6-n",
    "claude-sonnet-4.6-n",
]

def ping(model, timeout=25):
    t0 = time.time()
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply OK"}],
        "max_tokens": 10, "temperature": 0.0,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/chat/completions", data=payload,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            elapsed = time.time() - t0
            content = (data["choices"][0]["message"].get("content") or "").strip()
            return (True, elapsed, content[:30] or "(empty)")
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        return (False, elapsed, f"HTTP {e.code}")
    except Exception as e:
        elapsed = time.time() - t0
        return (False, elapsed, str(e)[:50])

# Retry each model up to 3 times, treat any 1 success as "alive"
for m in MODELS:
    results = []
    for attempt in range(3):
        ok, el, msg = ping(m, 25)
        results.append((ok, el, msg))
        if ok:
            break
        time.sleep(2)
    any_ok = any(r[0] for r in results)
    flag = "OK " if any_ok else "XX "
    summary = "  |  ".join(f"{'ok' if r[0] else 'fail'}/{r[1]:.1f}s" for r in results)
    last = results[-1]
    print(f"  {flag} {m:35s}  attempts: [{summary}]  last: {last[2]}", flush=True)
