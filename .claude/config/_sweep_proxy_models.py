"""Bulk sweep: replace deprecated proxy URLs and model names per
LLM_PROXY_MODEL_ROUTING_PORTING_GUIDE_2026-05-06.

Replacements:
  cone.nyc.mn          -> tone.nyc.mn
  gpt-5.5 (no -n)      -> gpt-5.5-n
  gpt-5.4-mini         -> gpt-5.5-n   (active fast model now)
  gpt-5.4              -> gpt-5.5-n   (active GPT now)
  gpt-5.2              -> gpt-5.5-n
  claude-opus-4.7 (no -n)  -> claude-opus-4.7-n
  claude-opus-4.6 (no -n)  -> claude-opus-4.6-n
  claude-sonnet-4.6-thinking -> gpt-5.5-n   (Sonnet emergency-only; replace as default)
  claude-sonnet-4.6 (no -n) -> gpt-5.5-n   (same reason)
  gemini-3.1-pro (no -n)   -> gemini-3.1-pro-n

Skips:
  - hidden dirs starting with `.` except .claude/.gemini/.codex
  - .git, node_modules, __pycache__, .venv, venv, dist, build
  - *.bak, *.pyc, *.pyo
  - the central config files we already manually edited
  - any file whose path contains 'memory/' (journal entries are historical)
  - files larger than 2 MB

Usage:
  python _sweep_proxy_models.py            # dry run (no changes; print plan)
  python _sweep_proxy_models.py --apply    # write changes (creates .bak per file)
"""
from __future__ import annotations
import os
import re
import sys
import argparse
from pathlib import Path

ROOTS = [
    Path("C:/Users/Administrator/scicrew"),
    Path("C:/Users/Administrator/scicamel"),
    Path("C:/Users/Administrator/scisuper"),
    Path("C:/Users/Administrator/researchclaw"),
    Path("C:/Users/Administrator/AutoResearchClaw"),
    Path("C:/Users/Administrator/AutoResearchClaw_config"),
    Path("C:/Users/Administrator/.claude/config"),
    Path("C:/Users/Administrator/.claude/scripts"),
    Path("C:/Users/Administrator/.gemini/skills"),
    Path("C:/Users/Administrator/.codex/skills"),
    Path("C:/Users/Administrator/.antigravity/skills"),
    # Additional CLI skill stores (mostly junctions to .gemini/skills, so sweep is idempotent)
    Path("C:/Users/Administrator/.factory/skills"),
    Path("C:/Users/Administrator/.copilot/skills"),
    Path("C:/Users/Administrator/.cline/skills"),
    Path("C:/Users/Administrator/.cursor/skills"),
    Path("C:/Users/Administrator/.openclaw/skills"),
    Path("C:/Users/Administrator/.junie/skills"),
    Path("C:/Users/Administrator/.agents/skills"),
    Path("C:/Users/Administrator/.augment/skills"),
    Path("C:/Users/Administrator/.verdent/skills"),
    Path("C:/Users/Administrator/.tooluniverse-repo/skills"),
    Path("C:/Users/Administrator/.config/amp/skills"),
    Path("C:/Users/Administrator/.config/opencode/skill"),
]

# Patterns are ORDERED — most-specific first to avoid double-replacement
REPLACEMENTS: list[tuple[str, str]] = [
    # Proxy URL
    (r"\bcone\.nyc\.mn\b", "tone.nyc.mn"),
    # Sonnet thinking (compound name — replace before claude-sonnet-4.6 base)
    (r"\bclaude-sonnet-4\.6-thinking\b", "gpt-5.5-n"),
    # GPT 5.4-mini (compound name — replace before gpt-5.4 base)
    (r"\bgpt-5\.4-mini\b", "gpt-5.5-n"),
    # GPT 5.5 NOT followed by -n (use look-ahead via regex with negative)
    (r"\bgpt-5\.5(?!-n)\b", "gpt-5.5-n"),
    # GPT 5.4 (after we handled 5.4-mini above)
    (r"\bgpt-5\.4\b", "gpt-5.5-n"),
    # GPT 5.2
    (r"\bgpt-5\.2\b", "gpt-5.5-n"),
    # Sonnet 4.6 (no suffix) — replace as default model usage
    (r"\bclaude-sonnet-4\.6(?!-n)\b", "gpt-5.5-n"),
    # Gemini 3.1 pro NOT -n
    (r"\bgemini-3\.1-pro(?!-n)\b", "gemini-3.1-pro-n"),
    # Opus 4.7 NOT -n
    (r"\bclaude-opus-4\.7(?!-n)\b", "claude-opus-4.7-n"),
    # Opus 4.6 NOT -n
    (r"\bclaude-opus-4\.6(?!-n)\b", "claude-opus-4.6-n"),
]

SCAN_EXTS = {".py", ".yaml", ".yml", ".json", ".env", ".md", ".toml", ".ini", ".sh", ".ps1"}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".mypy_cache",
    "memory",  # journal/historical
    "archive", "backup", "backups", "backup_files",
    ".idea", ".vscode",
    # Historical reports/outputs — per migration guide §12, do not rewrite
    "workspace", "output", "outputs", "reports", "report", "results",
    "logs", "log", "history", "outputs_archive",
    # Internal diagnostic dumps
    "_diagnose_47n", "_smoke", "test_outputs", "test_results",
    # Skill registries / catalogs (read-only metadata)
    "_catalog", "registry_data",
    # Git worktrees — not active source
    "worktrees",
}

SKIP_FILE_NAMES = {
    # Already manually edited
    "llm_config.json",
    "llm_router.py",
    "api-credentials.env",
    "_sweep_proxy_models.py",
    "_smoke_log.json",
    "_smoke_log2.json",
    "opus_helper.py",
    # The migration guide itself
    "LLM_PROXY_MODEL_ROUTING_PORTING_GUIDE_2026-05-06.md",
    "LLM_ROUTER_README.md",
    "model-chains.md",
}

SKIP_FILE_PATTERNS = [
    re.compile(r"\.bak"),
    re.compile(r"\.pyc$"),
    re.compile(r"\.log$"),
    # Skip our own backup files
    re.compile(r"\.bak-\d{8}-\d{6}$"),
]

MAX_BYTES = 2 * 1024 * 1024


def should_scan(p: Path) -> bool:
    if p.name in SKIP_FILE_NAMES:
        return False
    if any(rx.search(str(p)) for rx in SKIP_FILE_PATTERNS):
        return False
    # Match by extension OR by literal dotfile name (.env / .env.local / etc.)
    name_lower = p.name.lower()
    is_dotenv = name_lower == ".env" or name_lower.startswith(".env.")
    if not is_dotenv and p.suffix.lower() not in SCAN_EXTS:
        return False
    try:
        if p.stat().st_size > MAX_BYTES:
            return False
    except OSError:
        return False
    # Skip if path contains skipped dir (case-insensitive)
    parts_lower = [x.lower() for x in p.parts]
    return not any(d.lower() in parts_lower for d in SKIP_DIRS)


def transform(text: str) -> tuple[str, list[tuple[str, int]]]:
    """Apply all replacements in order. Returns (new_text, [(pattern, count), ...]).

    Lines containing 'DISABLED' (case-insensitive) are skipped — those are
    intentional documentation listing the deprecated names; rewriting them
    collapses the list into duplicates.
    """
    lines = text.splitlines(keepends=True)
    hits: dict[str, int] = {}
    new_lines = []
    for ln in lines:
        if "disabled" in ln.lower() or "已禁用" in ln or "deprecated" in ln.lower():
            new_lines.append(ln)
            continue
        out = ln
        for pattern, repl in REPLACEMENTS:
            out, n = re.subn(pattern, repl, out)
            if n > 0:
                hits[pattern] = hits.get(pattern, 0) + n
        new_lines.append(out)
    return "".join(new_lines), [(p, n) for p, n in hits.items()]


def walk_files(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.is_file() and should_scan(p):
            yield p


def main(apply: bool):
    total_files = 0
    changed_files = 0
    total_hits = 0
    per_pattern_count: dict[str, int] = {}
    changed_paths: list[str] = []

    for root in ROOTS:
        for path in walk_files(root):
            total_files += 1
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            new_text, hits = transform(text)
            if not hits:
                continue
            changed_files += 1
            for pat, n in hits:
                total_hits += n
                per_pattern_count[pat] = per_pattern_count.get(pat, 0) + n
            changed_paths.append(str(path))
            if apply:
                # Write a single backup per session if not already present
                bak = path.with_suffix(path.suffix + ".bak-sweep20260506")
                if not bak.exists():
                    try:
                        bak.write_text(text, encoding="utf-8")
                    except Exception:
                        pass
                path.write_text(new_text, encoding="utf-8")

    print("=" * 70)
    print(f"Scanned files:  {total_files}")
    print(f"Files matched:  {changed_files}")
    print(f"Total hits:     {total_hits}")
    print(f"Mode:           {'APPLY (changes written, .bak created per file)' if apply else 'DRY-RUN (no changes)'}")
    print("\nPer-pattern hits:")
    for pat, n in sorted(per_pattern_count.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {pat}")
    print(f"\nFirst 25 affected files:")
    for p in changed_paths[:25]:
        print(f"  {p}")
    if len(changed_paths) > 25:
        print(f"  ... and {len(changed_paths) - 25} more")
    return 0 if total_files else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry run)")
    args = ap.parse_args()
    sys.exit(main(apply=args.apply))
