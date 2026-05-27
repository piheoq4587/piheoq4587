#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
chain_healthcheck.py — 快速健康检查

检查项:
1) 链脚本存在性 (chain_select.py / chain_combine.py)
2) 关键命令可用性 (opencli / bioclaw)
3) UTF-8 输出一致性 (chain_combine 中文触发词)
4) chain_select 三模式冒烟 (small / mid / large)

用法:
  python chain_healthcheck.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / ".gemini" / "skills"
SCRIPTS = ROOT / "_chains" / "_scripts"


def run_cmd(cmd):
    try:
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=25,
            env=env,
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def print_result(name, ok, detail):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")


def main():
    # Ensure UTF-8 output on Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    fails = 0

    # 1) script presence
    must = ["chain_select.py", "chain_combine.py"]
    for m in must:
        ok = (SCRIPTS / m).exists()
        if not ok:
            fails += 1
        print_result(f"script:{m}", ok, str((SCRIPTS / m)))

    # 2) command availability
    for cmd in ["opencli", "bioclaw"]:
        p = shutil.which(cmd)
        ok = p is not None
        if not ok:
            fails += 1
        print_result(f"command:{cmd}", ok, p or "not found in PATH")

    # 3) UTF-8 check with chain_combine
    rc, out, err = run_cmd([
        sys.executable,
        str(SCRIPTS / "chain_combine.py"),
        "--match",
        "TIM 投稿全流程",
    ])
    utf8_ok = rc == 0 and "TIM 期刊投稿全流程" in out
    if not utf8_ok:
        fails += 1
    detail = "utf8 output ok" if utf8_ok else (err.strip() or "missing expected chinese output")
    print_result("utf8:chain_combine", utf8_ok, detail)

    # 4) chain_select smoke tests
    tests = [
        ("small", "chain-bio__mr-causal-genomics", "mendelian randomization for LDL and CAD"),
        ("mid", "chain-eng__frontend-design", "build a modern landing page with interactions"),
        ("large", "chain-bio__variant-annotation", "annotate VCF for HLA"),
    ]

    for label, chain, query in tests:
        rc, out, err = run_cmd([
            sys.executable,
            str(SCRIPTS / "chain_select.py"),
            chain,
            query,
        ])
        ok = False
        mode = ""
        if rc == 0 and out.strip():
            try:
                data = json.loads(out)
                mode = data.get("mode", "")
                if label == "small":
                    ok = mode == "menu-direct"
                elif label == "mid":
                    ok = mode in {"menu-with-desc", "llm-ranked"}
                else:
                    # large should always return non-empty questions after patch
                    qs = data.get("questions", [])
                    ok = mode == "ask-questions" and isinstance(qs, list) and len(qs) > 0
            except Exception:
                ok = False
        if not ok:
            fails += 1
        detail = f"mode={mode or 'n/a'}" if ok else (err.strip() or out[:200].replace("\n", " "))
        print_result(f"chain_select:{label}", ok, detail)

    print("\nSummary:")
    if fails == 0:
        print("ALL CHECKS PASSED")
        sys.exit(0)
    print(f"{fails} check(s) failed")
    sys.exit(1)


if __name__ == "__main__":
    main()
