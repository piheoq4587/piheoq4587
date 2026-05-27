"""
chain_combine.py — Lookup pipeline by trigger phrase or pipeline name.

用法:
  python chain_combine.py --list                       # 列出所有 pipeline
  python chain_combine.py --match "TIM 投稿全流程"     # 触发词匹配
  python chain_combine.py --get tim-submission         # 直接取
"""
import json, os, re, sys
from pathlib import Path

PIPE = Path(os.path.expanduser('~/.gemini/skills/_chains/_scripts/pipelines.json'))
data = json.load(open(PIPE, encoding='utf-8'))


def list_pipelines():
    out = []
    for k, v in data['pipelines'].items():
        out.append({"name": k, "label": v['label'], "steps": len(v['steps']),
                    "triggers": v.get('trigger_phrases', [])})
    return out


def _trigger_matches(trigger: str, query_lower: str) -> bool:
    """Match trigger against query.

    For pure-ASCII triggers (e.g. 'RD', 'DID', 'fixest'), require word boundary
    to avoid false positives like 'Word' matching 'RD'. For CJK / non-ASCII
    triggers, substring match is fine since CJK has no word-boundary issue.
    """
    t_low = trigger.lower().strip()
    if not t_low:
        return False
    if all(ord(c) < 128 for c in t_low):
        pattern = r'(?<![a-zA-Z0-9_])' + re.escape(t_low) + r'(?![a-zA-Z0-9_])'
        return re.search(pattern, query_lower) is not None
    return t_low in query_lower


def match_pipeline(query):
    q = query.lower()
    matches = []
    for k, v in data['pipelines'].items():
        for t in v.get('trigger_phrases', []):
            if _trigger_matches(t, q):
                matches.append({"name": k, "label": v['label'], "trigger_hit": t,
                                "pipeline": v})
                break
    return matches


def get_pipeline(name):
    if name in data['pipelines']:
        return {"name": name, **data['pipelines'][name]}
    return None


def main():
    if '--list' in sys.argv:
        print(json.dumps(list_pipelines(), ensure_ascii=False, indent=2))
    elif '--match' in sys.argv:
        i = sys.argv.index('--match')
        q = sys.argv[i + 1]
        print(json.dumps(match_pipeline(q), ensure_ascii=False, indent=2))
    elif '--get' in sys.argv:
        i = sys.argv.index('--get')
        name = sys.argv[i + 1]
        p = get_pipeline(name)
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
