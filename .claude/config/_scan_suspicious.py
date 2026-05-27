"""Scan for lines where the sweep collapsed a deprecated-models list into duplicates."""
import re
from pathlib import Path

patterns = [
    re.compile(r"gpt-5\.5-n[, ]+gpt-5\.5-n[, ]+gpt-5\.5-n"),
    re.compile(r"claude-opus-4\.7-n[, ]+claude-opus-4\.7-n[, ]+claude-opus-4\.7-n"),
    re.compile(r"claude-opus-4\.6-n[, ]+claude-opus-4\.6-n[, ]+claude-opus-4\.6-n"),
    re.compile(r"gemini-3\.1-pro-n[, ]+gemini-3\.1-pro-n[, ]+gemini-3\.1-pro-n"),
]
ROOTS = [
    "C:/Users/Administrator/scicrew",
    "C:/Users/Administrator/scicamel",
    "C:/Users/Administrator/scisuper",
    "C:/Users/Administrator/researchclaw",
    "C:/Users/Administrator/AutoResearchClaw",
    "C:/Users/Administrator/AutoResearchClaw_config",
    "C:/Users/Administrator/.gemini/skills",
]
EXTS = {".py", ".yaml", ".yml", ".json", ".env", ".md", ".toml", ".ini", ".sh", ".ps1"}
suspicious = []
for root in ROOTS:
    rp = Path(root)
    if not rp.exists():
        continue
    for path in rp.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith(".bak-sweep20260506") or path.name.endswith(".bak"):
            continue
        s = str(path).lower().replace("\\", "/")
        if "worktrees" in s or "workspace" in s or "/output" in s or "memory" in s:
            continue
        if path.suffix.lower() not in EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for ln_no, line in enumerate(text.splitlines(), 1):
            for pat in patterns:
                if pat.search(line):
                    suspicious.append((str(path), ln_no, line.strip()[:180]))
                    break
print(f"Suspicious lines: {len(suspicious)}")
for fp, ln, snip in suspicious[:60]:
    print(f"{fp}:{ln}")
    print(f"  -> {snip}")
