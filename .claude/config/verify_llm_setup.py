"""LLM Setup Health Check (LLM_PROXY_MODEL_ROUTING_PORTING_GUIDE_2026-05-06).

Run after reboot or whenever you want to confirm:
  - llm_router config loads correctly
  - Endpoint + key are visible
  - All 9 active roles resolve to chains with no disabled models
  - Each active model is reachable (1 ping per model)
  - Disabled aliases (gpt-5.5, gpt-5.4*, gpt-5.2) correctly return 502
  - Timeout/cooldown policy values are sensible

Usage:
    python ~/.claude/config/verify_llm_setup.py            # quick verification (no API calls)
    python ~/.claude/config/verify_llm_setup.py --ping     # ping each active model (slow, ~60s)
    python ~/.claude/config/verify_llm_setup.py --full     # ping + verify disabled aliases 502
"""
from __future__ import annotations
import sys
import os
import time
import json
import argparse
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent
if str(CONFIG_DIR) not in sys.path:
    sys.path.insert(0, str(CONFIG_DIR))

OK = "[OK]"
WARN = "[!!]"
FAIL = "[XX]"

ACTIVE_MODELS = [
    "claude-opus-4.7-n",
    "gpt-5.5-n",
    "gemini-3.1-pro-n",
    "claude-opus-4.6-n",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-0309-reasoning",
    "claude-sonnet-4.6-n",
]
DISABLED_ALIASES = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.2"]


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_config() -> tuple[bool, dict]:
    """Step 1: load config + endpoint."""
    section("Step 1: Config + Endpoint")
    try:
        from llm_router import get_endpoint, list_roles, get_chain, get_policy, get_model_meta
    except ImportError as e:
        print(f"{FAIL} Cannot import llm_router: {e}")
        print(f"     Ensure ~/.claude/config/llm_router.py exists")
        return False, {}
    print(f"{OK} llm_router imported")

    ep = get_endpoint()
    print(f"     base_url:  {ep['base_url']}")
    if not ep["api_key"]:
        print(f"{FAIL} API key NOT set in environment (OPENAI_API_KEY)")
        print(f"     Check ~/.claude/config/api-credentials.env")
        return False, {}
    print(f"     api_key:   {ep['api_key'][:14]}...{ep['api_key'][-4:]}  ({OK})")

    roles = list_roles()
    if len(roles) != 9:
        print(f"{WARN} Expected 9 roles, found {len(roles)}: {roles}")
    else:
        print(f"{OK} 9 roles defined")
    return True, {"roles": roles, "endpoint": ep}


def check_chains_and_disabled() -> bool:
    """Step 2: verify no disabled models leak into any chain."""
    section("Step 2: Role chains + Disabled-model isolation")
    from llm_router import list_roles, get_chain, get_model_meta

    leaks = []
    for role in list_roles():
        chain = get_chain(role)
        for m in chain:
            if m in DISABLED_ALIASES:
                leaks.append((role, m))
        head = chain[0] if chain else "?"
        marker = OK if chain else FAIL
        print(f"  {marker}  {role:20s} -> {head}  (chain length={len(chain)})")

    if leaks:
        print(f"\n{FAIL} Disabled aliases found in chains:")
        for role, m in leaks:
            print(f"     {role}: {m}")
        return False
    print(f"\n{OK} No disabled aliases (gpt-5.5/5.4/5.4-mini/5.2) in any active chain")

    # confirm each active model is registered
    missing = []
    for m in ACTIVE_MODELS:
        if not get_model_meta(m):
            missing.append(m)
    if missing:
        print(f"{WARN} Active models not registered in llm_config.json: {missing}")
    else:
        print(f"{OK} All {len(ACTIVE_MODELS)} active models registered")
    return True


def check_policy() -> bool:
    """Step 3: verify timeout/cooldown values are sane."""
    section("Step 3: Timeout + Cooldown policy")
    from llm_router import get_policy

    checks = [
        ("request_timeout_seconds",    120,   60,   600),
        ("cooldown_ttl_seconds",       900,   60,   3600),
        ("max_retries_per_model",      1,     0,    5),
        ("agent_timeout_base_seconds", 600,   60,   3600),
        ("agent_timeout_max_seconds",  1800,  300,  7200),
    ]
    all_ok = True
    for key, expected, lo, hi in checks:
        val = get_policy(key)
        if val is None:
            print(f"  {WARN} {key}: missing from config")
            all_ok = False
            continue
        marker = OK if lo <= val <= hi else WARN
        diff = "" if val == expected else f"  (expected {expected})"
        print(f"  {marker}  {key}: {val}s{diff}")
        if not (lo <= val <= hi):
            all_ok = False
    return all_ok


def check_dependent_files() -> bool:
    """Step 4: verify dependent program/skill configs reference new chain."""
    section("Step 4: Dependent program/skill configs")
    # marker = list of acceptable substrings (any one must be present)
    # Markers updated 2026-05-07 — Grok-first or Opus-primary both acceptable.
    # Opus-primary is the v3 baseline (proxy may recover); Grok-first is the
    # 2026-05-07 hot patch when proxy degraded to Grok-only. Both routes are
    # ultimately resolved by llm_router.py reading llm_config.json.
    paths_to_check = [
        ("~/scicrew/.env",                  ["AI_MODEL_PRIMARY=claude-opus-4.7-n", "AI_MODEL_PRIMARY=grok-4.20-0309-non-reasoning",
                                              "PRIMARY_MODEL=claude-opus-4.7-n", "PRIMARY_MODEL=grok-4.20-0309-non-reasoning"]),
        ("~/scicrew/config/settings.yaml",  ["primary: claude-opus-4.7-n", "primary: grok-4.20-0309-non-reasoning"]),
        ("~/scicamel/.env",                 ["PRIMARY_MODEL=claude-opus-4.7-n", "PRIMARY_MODEL=grok-4.20-0309-non-reasoning"]),
        ("~/scicamel/configs/models.yaml",  ['primary: "claude-opus-4.7-n"', 'primary: "grok-4.20-0309-non-reasoning"']),
        ("~/scisuper/.env",                 ["AI_MODEL_PRIMARY=claude-opus-4.7-n", "AI_MODEL_PRIMARY=grok-4.20-0309-non-reasoning",
                                              "PRIMARY_MODEL=claude-opus-4.7-n", "PRIMARY_MODEL=grok-4.20-0309-non-reasoning"]),
        ("~/scisuper/config/settings.yaml", ['primary: "claude-opus-4.7-n"', 'primary: "grok-4.20-0309-non-reasoning"']),
        ("~/researchclaw/.env",             ["AI_MODEL_PRIMARY=claude-opus-4.7-n", "AI_MODEL_PRIMARY=grok-4.20-0309-non-reasoning",
                                              "PRIMARY_MODEL=claude-opus-4.7-n", "PRIMARY_MODEL=grok-4.20-0309-non-reasoning"]),
        ("~/researchclaw/config.arc.yaml",  ['primary_model: "claude-opus-4.7-n"', 'primary_model: "grok-4.20-0309-non-reasoning"']),
    ]
    all_ok = True
    for relpath, markers in paths_to_check:
        full = Path(os.path.expanduser(relpath))
        if not full.exists():
            print(f"  --   {relpath}: not present (skipped)")
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        ok = any(m in text for m in markers)
        # also verify no lone `gpt-5.5` (without -n) and no cone.nyc.mn
        bad = []
        for pattern, label in [
            ("cone.nyc.mn",     "old proxy URL"),
            ("=gpt-5.5\n",      "disabled gpt-5.5"),
            ("=gpt-5.4\n",      "disabled gpt-5.4"),
            ("=gpt-5.4-mini\n", "disabled gpt-5.4-mini"),
            ("=gpt-5.2\n",      "disabled gpt-5.2"),
        ]:
            if pattern in text:
                bad.append(label)
        if bad:
            ok = False
            print(f"  {FAIL} {relpath}: contains {bad}")
            all_ok = False
        elif ok:
            print(f"  {OK}  {relpath}")
        else:
            print(f"  {WARN} {relpath}: no marker matched ({markers[0][:40]}...)")
            all_ok = False
    return all_ok


def ping_active_models() -> bool:
    """Step 5 (optional --ping): live HTTP ping each active model."""
    section("Step 5: Live ping each active model")
    from llm_router import call_llm
    from openai import OpenAI
    from llm_router import get_endpoint
    ep = get_endpoint()
    client = OpenAI(api_key=ep["api_key"], base_url=ep["base_url"], timeout=60)

    all_ok = True
    for m in ACTIVE_MODELS:
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                max_tokens=10,
                temperature=0.0,
            )
            content = (resp.choices[0].message.content or "").strip()
            elapsed = round(time.time() - t0, 2)
            if content:
                print(f"  {OK}  {m:35s} {elapsed:5.2f}s  -> {content[:30]!r}")
            else:
                # tool-calling models may return empty content but tool_calls; still alive
                print(f"  {OK}  {m:35s} {elapsed:5.2f}s  -> (empty content, model alive)")
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            err = str(e)[:80]
            print(f"  {FAIL} {m:35s} {elapsed:5.2f}s  -> ERROR: {err}")
            all_ok = False
    return all_ok


def verify_disabled_502() -> bool:
    """Step 6 (optional --full): confirm disabled aliases still 502."""
    section("Step 6: Confirm disabled aliases return HTTP 502")
    from openai import OpenAI
    from llm_router import get_endpoint
    ep = get_endpoint()
    client = OpenAI(api_key=ep["api_key"], base_url=ep["base_url"], timeout=30)

    all_correct = True
    for m in DISABLED_ALIASES:
        try:
            client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            # If this returned without exception, the alias is unexpectedly alive
            print(f"  {WARN} {m}: returned successfully (no longer disabled?)")
            all_correct = False
        except Exception as e:
            err = str(e).lower()
            if "502" in err or "bad_response" in err or "openai_error" in err:
                print(f"  {OK}  {m}: still returns 502 (correctly disabled)")
            else:
                print(f"  {WARN} {m}: error but not 502: {str(e)[:80]}")
    return all_correct


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ping", action="store_true", help="Live-ping each active model (slow)")
    ap.add_argument("--full", action="store_true", help="Ping + verify disabled aliases (slowest)")
    args = ap.parse_args()

    print("LLM Setup Health Check  —  LLM_PROXY_MODEL_ROUTING_PORTING_GUIDE_2026-05-06")
    print(f"Timestamp:  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Config dir: {CONFIG_DIR}")

    ok1, _ = check_config()
    if not ok1:
        return 1
    ok2 = check_chains_and_disabled()
    ok3 = check_policy()
    ok4 = check_dependent_files()
    ok5 = ok6 = True
    if args.ping or args.full:
        ok5 = ping_active_models()
    if args.full:
        ok6 = verify_disabled_502()

    section("Summary")
    summary = [
        ("Config + endpoint",         ok1),
        ("Role chains + isolation",   ok2),
        ("Timeout/cooldown policy",   ok3),
        ("Dependent configs",         ok4),
        ("Active model pings",        ok5),
        ("Disabled-alias 502 check",  ok6),
    ]
    for name, ok in summary:
        print(f"  {OK if ok else FAIL}  {name}")
    overall = all(ok for _, ok in summary)
    print(f"\n{'OVERALL: ALL GOOD — NEW POLICY IS LIVE' if overall else 'OVERALL: SOMETHING NEEDS ATTENTION'}")
    return 0 if overall else 2


if __name__ == "__main__":
    sys.exit(main())
