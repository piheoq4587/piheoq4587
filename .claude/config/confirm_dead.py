"""Re-test the 5 timeout-ed models with 35 s timeout. Sequential to avoid masking."""
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
    "claude-opus-4.7-n",
    "gpt-5.5-n",
    "gemini-3.1-pro-n",
    "claude-opus-4.6-n",
    "claude-sonnet-4.6-n",
]

def ping(model, timeout):
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
            return (True, elapsed, content[:30])
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        body = ""
        try: body = e.read().decode("utf-8")[:80]
        except: pass
        return (False, elapsed, f"HTTP {e.code} {body}")
    except (urllib.error.URLError, TimeoutError) as e:
        elapsed = time.time() - t0
        return (False, elapsed, f"timeout/url ({timeout}s)")
    except Exception as e:
        elapsed = time.time() - t0
        return (False, elapsed, f"err: {str(e)[:60]}")

print(f"Sequential retest (timeout=35s)\n")
for m in MODELS:
    ok, el, msg = ping(m, 35)
    flag = "OK " if ok else "XX "
    print(f"  {flag} {m:35s} {el:6.2f}s  {msg}", flush=True)
