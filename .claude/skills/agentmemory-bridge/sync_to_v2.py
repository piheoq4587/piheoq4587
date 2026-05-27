#!/usr/bin/env python
"""Pull valuable memories from agentmemory (:3111/MCP) → distill via tone.nyc.mn → write MEMORY v2 markdown.

Usage:
    sync_to_v2.py [--dry-run] [--min-importance 0.7] [--since 7d] [--limit 50]

Notes:
    - agentmemory v0.9.21's API surface is still settling. This script uses subprocess
      JSON-RPC over `agentmemory mcp` (the MCP stdio shim) because it's the most stable
      contract right now. SQLite direct-read is faster but the schema is private.
    - Distillation uses the user's OPENAI_API_BASE proxy (tone.nyc.mn) with grok-4.20.
    - Writes to ~/.claude/projects/<encoded-cwd>/memory/{feedback,project,reference}_*.md
"""
from __future__ import annotations
import argparse, json, os, pathlib, subprocess, sys, time, hashlib, re
from typing import Any

# --- Config -----------------------------------------------------------------
DEFAULT_MIN_IMPORTANCE = 0.7
DEFAULT_LIMIT = 50
DEFAULT_SINCE = "7d"
LLM_MODEL = os.environ.get("PRIMARY_MODEL", "grok-4.20-0309-reasoning")
LLM_BASE = os.environ.get("OPENAI_API_BASE") or os.environ.get("OPENAI_BASE_URL") or "https://tone.nyc.mn/v1"
LLM_KEY = os.environ.get("OPENAI_API_KEY", "")

MEMORY_DIR_DEFAULT = pathlib.Path.home() / ".claude" / "projects" / "C--Users-Administrator" / "memory"


# --- agentmemory MCP probe (subprocess JSON-RPC) ---------------------------
def call_mcp(method: str, params: dict | None = None, *, timeout: int = 20) -> Any:
    """One-shot JSON-RPC call against `agentmemory mcp` stdio shim."""
    msg_init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "agentmemory-bridge", "version": "1.0"}}}
    msg_call = {"jsonrpc": "2.0", "id": 2, "method": method, "params": params or {}}
    payload = json.dumps(msg_init) + "\n" + json.dumps(msg_call) + "\n"
    try:
        proc = subprocess.run(
            ["agentmemory", "mcp"],
            input=payload, capture_output=True, text=True, timeout=timeout, encoding="utf-8"
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[bridge] MCP call failed: {e}", file=sys.stderr)
        return None
    # Parse last JSON line that has id=2
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == 2:
            return obj.get("result") or obj.get("error")
    return None


def list_tools() -> list[dict]:
    r = call_mcp("tools/list")
    return r.get("tools", []) if isinstance(r, dict) else []


def fetch_memories(min_importance: float, since: str, limit: int) -> list[dict]:
    """Try a few likely tool names — agentmemory's exact tool set evolves."""
    candidates = [
        ("search_memories", {"importance_min": min_importance, "limit": limit, "since": since}),
        ("list_memories", {"min_importance": min_importance, "limit": limit}),
        ("memories.list", {"limit": limit}),
        ("get_memories", {"limit": limit}),
    ]
    tools = {t["name"] for t in list_tools()}
    if not tools:
        print("[bridge] no MCP tools enumerated — agentmemory server may be down", file=sys.stderr)
        return []
    print(f"[bridge] available tools: {sorted(tools)[:10]}...", file=sys.stderr)
    for name, args in candidates:
        if name in tools:
            r = call_mcp("tools/call", {"name": name, "arguments": args})
            if isinstance(r, dict):
                # MCP standard tool response shape
                items = r.get("content") or r.get("memories") or []
                if isinstance(items, list):
                    return items
    print("[bridge] no matching listing tool found in agentmemory MCP", file=sys.stderr)
    return []


# --- LLM distillation -------------------------------------------------------
def llm_distill(memories: list[dict]) -> list[dict]:
    """Ask LLM to classify each memory into v2 file type and write a clean note line."""
    if not memories or not LLM_KEY:
        return []
    import urllib.request
    prompt = (
        "You are distilling short episodic memories into long-term notes for MEMORY v2.\n"
        "For each input memory, output one JSON line: {\"v2_type\": \"feedback|project|reference|user\", "
        "\"v2_file\": \"<short_topic>.md\", \"note\": \"<1-2 sentence durable summary, no chit-chat>\", "
        "\"skip\": false}. If trivial / already-noted / chit-chat, output {\"skip\": true}.\n\n"
        "Memories (one per line):\n"
        + "\n".join(json.dumps(m, ensure_ascii=False) for m in memories)
    )
    req = urllib.request.Request(
        f"{LLM_BASE.rstrip('/')}/chat/completions",
        data=json.dumps({"model": LLM_MODEL, "messages": [{"role": "user", "content": prompt}],
                         "temperature": 0.2}).encode(),
        headers={"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[bridge] LLM call failed: {e}", file=sys.stderr)
        return []
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            j = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not j.get("skip"):
            out.append(j)
    return out


# --- v2 writer --------------------------------------------------------------
def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_")[:60] or "untitled"


def write_to_v2(distilled: list[dict], memory_dir: pathlib.Path, dry_run: bool) -> int:
    memory_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for d in distilled:
        t = d.get("v2_type", "reference")
        if t == "user":
            target = memory_dir / "user_profile.md"
            existing = target.read_text(encoding="utf-8") if target.exists() else ""
            note = d.get("note", "").strip()
            if note and note not in existing:
                if not dry_run:
                    with target.open("a", encoding="utf-8") as f:
                        f.write(f"\n- {note}  (auto-bridged {time.strftime('%Y-%m-%d')})")
                count += 1
                print(f"  [append-user] {note[:80]}")
        else:
            topic = slug(d.get("v2_file", "untitled").replace(".md", ""))
            target = memory_dir / f"{t}_{topic}.md"
            note = d.get("note", "").strip()
            # dedup by content hash
            if target.exists() and note in target.read_text(encoding="utf-8"):
                continue
            if not dry_run:
                exists = target.exists()
                with target.open("a", encoding="utf-8") as f:
                    if not exists:
                        f.write(f"---\nname: {topic}\nsource: agentmemory-bridge\n---\n\n")
                    f.write(f"- {note}  (auto-bridged {time.strftime('%Y-%m-%d')})\n")
            count += 1
            print(f"  [{'dry-run' if dry_run else 'write'}] {t}_{topic}.md ← {note[:60]}...")
    return count


# --- Main -------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Don't write to disk; show what would happen")
    ap.add_argument("--min-importance", type=float, default=DEFAULT_MIN_IMPORTANCE)
    ap.add_argument("--since", default=DEFAULT_SINCE, help="e.g. 7d, 24h, 30d")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--memory-dir", type=pathlib.Path, default=MEMORY_DIR_DEFAULT)
    args = ap.parse_args()

    print(f"[bridge] pulling memories: importance≥{args.min_importance}, since={args.since}, limit={args.limit}",
          file=sys.stderr)
    mems = fetch_memories(args.min_importance, args.since, args.limit)
    print(f"[bridge] got {len(mems)} memories from agentmemory", file=sys.stderr)
    if not mems:
        print("[bridge] nothing to distill — exit", file=sys.stderr)
        return

    print(f"[bridge] distilling via {LLM_MODEL} @ {LLM_BASE}", file=sys.stderr)
    distilled = llm_distill(mems)
    print(f"[bridge] LLM kept {len(distilled)}/{len(mems)} for v2 promotion", file=sys.stderr)

    written = write_to_v2(distilled, args.memory_dir, args.dry_run)
    print(f"[bridge] {'would write' if args.dry_run else 'wrote'} {written} v2 entries → {args.memory_dir}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
