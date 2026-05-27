#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
log_usage.py — Append one usage record to _metrics.jsonl.

CLI 调完 Skill 后跑一次：
  python log_usage.py <skill-name>
  python log_usage.py <skill-name> --rating good      # good / ok / bad
  python log_usage.py <skill-name> --task "<short>"   # 任务上下文
  python log_usage.py <skill-name> --funnel-tier S    # S / M / L

被 chain_select.py 的 _load_freq() 读取，给最近 30 天调用过的 skill 加 0.15 分。
science-core 成员独享 0.20 bonus（自动识别）。
"""
import argparse, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

METRICS = Path(__file__).resolve().parent.parent / "_metrics.jsonl"


def main():
    p = argparse.ArgumentParser(description="Log one Skill invocation")
    p.add_argument("skill", help="Skill name (e.g. meta-rob2-plot)")
    p.add_argument("--rating", choices=["good", "ok", "bad"], default="ok",
                   help="User feedback (default: ok)")
    p.add_argument("--task", default="", help="Short task description")
    p.add_argument("--funnel-tier", choices=["S", "M", "L"], default="M")
    p.add_argument("--duration-s", type=int, default=0, help="Wall-clock duration in seconds")
    args = p.parse_args()

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "skill": args.skill,
        "rating": args.rating,
        "task": args.task[:200],
        "funnel_tier": args.funnel_tier,
        "duration_s": args.duration_s,
    }
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    with METRICS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"OK logged: {args.skill} (rating={args.rating}, tier={args.funnel_tier})")


if __name__ == "__main__":
    main()
