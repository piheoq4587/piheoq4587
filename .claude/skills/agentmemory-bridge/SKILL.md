---
name: agentmemory-bridge
description: Bridge between short-term agentmemory (real-time, cross-agent episodic store on :3111) and long-term MEMORY v2 (curated markdown notes + InfraNodus graphs + OneDrive backup). Pulls "valuable" memories agentmemory captured during sessions, distills them via the user's LLM proxy, and writes them to MEMORY v2 markdown files (project_/feedback_/reference_/user_ files). Complements dreaming-sweep — that skill reads JSONL transcripts; this one reads agentmemory's curated episodic store (cleaner signal). Use when user says "蒸馏 agent memory" / "把 episodic 入库" / "agentmemory 同步到 v2" / "把今天聊的有价值的存下来" or when running periodic memory consolidation.
tags: [memory, agentmemory, distillation, MEMORY-v2, episodic, long-term, bridge]
---

# agentmemory-bridge

## Why this exists

You have **two complementary memory systems**:

```
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│  agentmemory (real-time, episodic)  │    │  MEMORY v2 (long-term, curated)     │
│  ─────────────────────────────────  │    │  ─────────────────────────────────  │
│  • Captures everything live         │    │  • Hand-curated markdown notes      │
│  • Shared across 4+ CLI via MCP     │    │  • Survives across machines         │
│  • Auto-importance scoring          │    │  • InfraNodus 5 graphs (semantic)   │
│  • SQLite store on :3111            │    │  • OneDrive backup                  │
│  • Lifecycle: hours-to-days         │    │  • Lifecycle: months-to-years       │
└─────────────────────────────────────┘    └─────────────────────────────────────┘
                  │                                            ▲
                  │              this skill                    │
                  └──────────────distills────────────────────►│
                            (valuable signal only)
```

**Without the bridge**: agentmemory's accumulated wisdom evaporates when its store rotates / when you reformat the laptop / when iii engine has a hiccup.

**With the bridge**: high-value memories get promoted to MEMORY v2 (durable, auditable, semantically indexed).

## Trigger this when

- User says: "蒸馏 agent memory / agentmemory 同步 / 把今天聊的有价值的存下来 / 把 episodic 入库 / dump important memories / distill agentmemory to v2 / 长期保存有价值的 / consolidate cross-agent memory"
- Periodic (weekly / nightly): run via Windows Task Scheduler or manual `python ~/.gemini/skills/agentmemory-bridge/sync_to_v2.py`
- End of a long multi-CLI work block where agents shared significant decisions
- Before clearing agentmemory or before iii engine upgrade

## Architecture

```
                    ┌───────────────────────────────────┐
   [Claude Code] ───►                                   │
   [Codex CLI] ─────►       agentmemory MCP             │
   [Cursor] ────────►       (shared episodic store)     │
   [Gemini CLI] ────►       :3111  +  :3113 viewer      │
                    └────────────┬──────────────────────┘
                                 │ REST / MCP / SQLite
                                 ▼
                    ┌───────────────────────────────────┐
                    │  sync_to_v2.py  (this skill)      │
                    │  • Pull memories                  │
                    │  • Filter: importance ≥ threshold │
                    │  • LLM distill via tone.nyc.mn    │
                    │    (grok-4.20 reasoning)          │
                    │  • Tag by type                    │
                    │  • Avoid duplicating existing v2  │
                    └────────────┬──────────────────────┘
                                 ▼
                    ┌───────────────────────────────────┐
                    │  ~/.claude/projects/.../memory/   │
                    │  ├── user_profile.md              │
                    │  ├── feedback_*.md  (preferences) │
                    │  ├── project_*.md  (decisions)    │
                    │  └── reference_*.md  (facts)      │
                    └────────────┬──────────────────────┘
                                 │ (existing pipeline)
                                 ▼
                    ┌───────────────────────────────────┐
                    │  dreaming-sweep (auto)            │
                    │  → MEMORY.md index updates        │
                    │  → InfraNodus 5 graphs (kg-sync)  │
                    │  → OneDrive backup                │
                    └───────────────────────────────────┘
```

## How memories get routed (4 v2 types)

agentmemory tags each observation; the bridge maps tags to MEMORY v2 file naming:

| agentmemory tag | → MEMORY v2 file pattern | Example |
|---|---|---|
| `preference` / `taste` / `style` | `feedback_<topic>.md` | `feedback_writing_style.md` |
| `decision` / `plan` / `roadmap` | `project_<scope>.md` | `project_tim_journal.md` |
| `fact` / `reference` / `api-key` / `dataset` | `reference_<topic>.md` | `reference_wos_api.md` |
| `identity` / `expertise` / `affiliation` | append to `user_profile.md` | Persistent user attributes |
| (untagged) | held in agentmemory only | Not promoted to v2 |

## Running the sync

### Manual (when user asks)

```bash
# Preview what would be promoted (no writes)
python ~/.gemini/skills/agentmemory-bridge/sync_to_v2.py --dry-run

# Real sync
python ~/.gemini/skills/agentmemory-bridge/sync_to_v2.py

# Sync with custom importance threshold
python ~/.gemini/skills/agentmemory-bridge/sync_to_v2.py --min-importance 0.7
```

### Scheduled (weekly, Sunday 23:00)

Once stable, register via Windows Task Scheduler:
```powershell
schtasks /Create /TN "agentmemory-to-v2-weekly" `
  /TR "python C:\Users\Administrator\.gemini\skills\agentmemory-bridge\sync_to_v2.py" `
  /SC WEEKLY /D SUN /ST 23:00 /F
```

## What "valuable" means (filter rules)

The bridge applies these heuristics to decide what goes to v2 (and what stays only in episodic):

1. **Explicit user mark**: user said "记下来" / "save this" / "important" / "remember"
2. **High importance score** from agentmemory (≥ 0.7 by default)
3. **Decision-shape**: contains "决定 / chose / picked / will use / shipped"
4. **Reference-shape**: contains URL / DOI / API key / file path / config snippet
5. **Cross-session repetition**: same fact mentioned in ≥2 sessions
6. **Not already in v2**: deduplication against existing MEMORY v2 markdown

Skipped:
- Trivial chitchat / acknowledgments
- Transient debugging steps
- Already in v2 (deduped by fuzzy match against existing notes)

## Integration with dreaming-sweep

Both feed MEMORY v2 but from different angles:

| | dreaming-sweep | agentmemory-bridge |
|---|---|---|
| **Source** | Raw session JSONL transcripts | agentmemory curated episodic store |
| **Signal** | Noisier (every turn) | Cleaner (already importance-scored) |
| **LLM model** | Per skill config (grok / opus) | Same proxy (grok-4.20 reasoning) |
| **Cadence** | Auto on long sessions (≥15 turns) | Periodic (weekly) + on-demand |
| **Best for** | Capturing user preferences from conversation tone | Capturing cross-agent decisions / facts |

They are **complementary** — run both. `dreaming-sweep` catches what only this session said; `agentmemory-bridge` catches what multiple agents agreed on.

## Status (2026-05-22)

| Component | State |
|---|---|
| agentmemory server (:3111) | ✓ running (iii engine v0.11.2, native binary) |
| agentmemory viewer (:3113) | ✓ running |
| MCP wired to Claude Code | ✓ user scope |
| MCP wired to Claude Desktop | ✓ via claude_desktop_config.json |
| MCP wired to Codex | ✓ via ~/.codex/config.toml |
| LLM embeddings | ✓ OPENAI_API_KEY → tone.nyc.mn `/v1/embeddings` |
| LLM chat (CONSOLIDATION/GRAPH_EXTRACTION) | ✓ ANTHROPIC_API_KEY → tone.nyc.mn `/v1/messages` + `grok-4.20-0309-reasoning` (无 `<l` artifact) |
| GRAPH_EXTRACTION_ENABLED | ✓ enabled |
| CONSOLIDATION_ENABLED | ✓ enabled |
| AGENTMEMORY_AUTO_COMPRESS | ✓ enabled |
| AGENTMEMORY_INJECT_CONTEXT | ✓ enabled |
| Bridge script | ✓ `sync_to_v2.py` (manual; scheduling later) |

## Limits

- **agentmemory is young** — APIs may change. The bridge isolates v2 from churn.
- **Importance scoring is heuristic** — review `--dry-run` output before first prod runs.
- **LLM distill needs the proxy**: relies on `~/.claude/config/api-credentials.env` having `OPENAI_API_BASE=https://tone.nyc.mn/v1` and `LLM_ROUTER_PRIMARY=grok-4.20-0309-reasoning`.

## Cross-CLI availability

Canonical at `~/.gemini/skills/agentmemory-bridge/`. Junctioned to `~/.{claude,codex,copilot}/skills/agentmemory-bridge/`.

Same bridge invocable from any CLI:
```bash
# Claude Code
/skill agentmemory-bridge
# Codex
/skill agentmemory-bridge
# Any CLI direct
python ~/.gemini/skills/agentmemory-bridge/sync_to_v2.py
```
