"""
chain_select.py — 三段式精筛器:从 chain 中选最合用的 skill。

用法:
  python chain_select.py <chain-name> "<user-query>"        # 自动模式(LLM 排序)
  python chain_select.py <chain-name> "<user-query>" --top 5  # 取前 5

例:
  python chain_select.py chain-bio__variant-annotation "annotate clinical VCF for HLA"
  python chain_select.py chain-domain-paper "TIM submission, R 实证 paper"

输出 JSON:
{
  "chain": "...",
  "total_members": 139,
  "mode": "llm-ranked",         # 或 "menu" / "ask-questions"
  "questions": [...],            # 如果 mode==ask-questions
  "top_picks": [
    {"name": "...", "score": 0.92, "why": "..."},
    ...
  ]
}
"""
import hashlib
import json, os, re, sys, time
from pathlib import Path
import urllib.request, urllib.error

ROOT = Path(os.path.expanduser('~/.gemini/skills'))
CHAINS = ROOT / '_chains'
CACHE_DIR = CHAINS / '_cache'
METRICS_FILE = CHAINS / '_metrics.jsonl'
SCIENCE_CORE_FILE = CHAINS / 'chain-domain-science-core.md'


def _load_creds():
    """Lazy-load LLM endpoint + key. Returns (endpoint, key, error_msg).

    Fresh machines or menu-mode-only runs must not crash here.
    """
    env_path = Path(os.path.expanduser('~/.claude/config/api-credentials.env'))
    if not env_path.exists():
        return None, None, f"api-credentials.env not found at {env_path}"
    endpoint = key = None
    try:
        for line in env_path.read_text(encoding='utf-8-sig', errors='ignore').splitlines():
            if line.startswith('OPENAI_BASE_URL='):
                endpoint = line.split('=', 1)[1].strip().strip('"').strip("'")
            elif line.startswith('OPENAI_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('"').strip("'")
    except Exception as e:
        return None, None, f"failed to parse env: {type(e).__name__}: {e}"
    if not endpoint or not key:
        return None, None, "OPENAI_BASE_URL or OPENAI_API_KEY missing in env"
    return endpoint, key, None


# Backward-compat: keep module-level vars but populate lazily on first LLM call.
endpoint = key = None


def read_chain(chain_name):
    fp = CHAINS / f"{chain_name}.md"
    if not fp.exists():
        return None
    text = fp.read_text(encoding='utf-8', errors='ignore')
    # Primary: AUTO-MEMBERS block (build_chains.py-generated chains)
    m = re.search(r'<!-- BEGIN AUTO-MEMBERS -->\s*\n(.*?)\n<!-- END AUTO-MEMBERS -->', text, re.DOTALL)
    if m:
        return re.findall(r'-\s*`([^`]+)`', m.group(1))
    # Fallback: hand-written chains — scan whole body for `- \`name\`` patterns,
    # excluding frontmatter and lines that are sub-chain references.
    body = re.sub(r'(?s)^---\n.*?\n---\n', '', text, count=1)
    candidates = re.findall(r'^\s*-\s*`([^`]+)`', body, re.MULTILINE)
    # Filter out items that look like chain refs ("chain-...md")
    members = [c for c in candidates if not c.startswith('chain-') and not c.endswith('.md')]
    return members


def _normalize_words(text):
    return re.findall(r'[a-zA-Z0-9_\-]+|[\u4e00-\u9fff]+', (text or '').lower())


def _load_freq(window_days=30):
    """Read _metrics.jsonl, return {skill_name: weighted_count} in last N days.
    good=1.0, ok=0.5, bad=-0.5 weights. Used by _local_rank for freq_bonus."""
    if not METRICS_FILE.exists():
        return {}
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    weights = {"good": 1.0, "ok": 0.5, "bad": -0.5}
    counts = {}
    try:
        for line in METRICS_FILE.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                ts = datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
                if ts < cutoff:
                    continue
                w = weights.get(r.get("rating", "ok"), 0.5)
                counts[r["skill"]] = counts.get(r["skill"], 0.0) + w
            except Exception:
                continue
    except Exception:
        return {}
    return counts


def _load_science_core_set():
    """Parse chain-domain-science-core.md, return set of member skill names."""
    if not SCIENCE_CORE_FILE.exists():
        return set()
    try:
        text = SCIENCE_CORE_FILE.read_text(encoding='utf-8', errors='ignore')
        # Skill names in `` backticks across whole doc
        return set(re.findall(r'`([a-zA-Z][\w\-]+)`', text))
    except Exception:
        return set()


def _local_rank(members, query, top_k=5):
    """Deterministic local fallback ranking when LLM is unavailable/timeout.

    Score = token_overlap + 0.75*name_hit + freq_bonus + science_core_bonus
    """
    q_words = set(_normalize_words(query))
    freq = _load_freq(window_days=30)
    science_core = _load_science_core_set()
    scored = []
    for name in members:
        desc = get_skill_desc(name)
        hay = f"{name} {desc}".lower()
        n_words = set(_normalize_words(hay))
        overlap = len(q_words & n_words)
        name_hit = 0
        for w in q_words:
            if len(w) >= 3 and w in name.lower():
                name_hit += 1
        # NEW v2: 4th and 5th dimensions
        freq_bonus = freq.get(name, 0.0) * 0.15
        sci_bonus = 0.20 if name in science_core else 0.0
        score = overlap + 0.75 * name_hit + freq_bonus + sci_bonus
        scored.append((score, name, desc, freq_bonus, sci_bonus))

    scored.sort(key=lambda x: (-x[0], x[1]))
    top = []
    for score, name, _desc, fb, sb in scored[:top_k]:
        norm = min(1.0, round(score / 6.0, 3))
        why_parts = ["token overlap"]
        if fb > 0:    why_parts.append(f"freq+{fb:.2f}")
        if sb > 0:    why_parts.append("science-core")
        why = " + ".join(why_parts)
        top.append({"name": name, "score": norm, "why": why})
    return top


def _cache_key(prefix, payload):
    raw = json.dumps({"prefix": prefix, **payload}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()


def _cache_get(prefix, payload, ttl_sec=24 * 3600):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        fp = CACHE_DIR / f"{_cache_key(prefix, payload)}.json"
        if not fp.exists():
            return None
        item = json.loads(fp.read_text(encoding='utf-8'))
        ts = int(item.get('ts', 0))
        if int(time.time()) - ts > ttl_sec:
            return None
        return item.get('data')
    except Exception:
        return None


def _cache_set(prefix, payload, data):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        fp = CACHE_DIR / f"{_cache_key(prefix, payload)}.json"
        fp.write_text(json.dumps({"ts": int(time.time()), "data": data}, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def get_skill_desc(name):
    sk = ROOT / name / 'SKILL.md'
    if not sk.exists():
        return ''
    text = sk.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'(?ms)^description:\s*([>|]?)\s*\n?(.+?)(?=\n[\w\-]+:|---)', text)
    if m:
        return ' '.join(m.group(2).split())[:300]
    return ''


def llm_rank(members, query, top_k=5):
    """Use Opus 4.7-n to rank skills by relevance to query.

    Returns list of {name, score, why} dicts.
    On failure returns a single dict with {error: "..."} so callers can detect
    failure (no longer fakes a recommendation by returning members[0]).
    """
    ep, k, err = _load_creds()
    if err:
        return [{"error": f"llm_rank skipped: {err}",
                 "fallback": "use menu mode or read chain file directly"}]

    cache_payload = {
        "members": members,
        "query": query,
        "top_k": top_k,
        "mode": "llm_rank_v2",
    }
    cached = _cache_get('llm_rank', cache_payload)
    if cached:
        return cached

    descs = {}
    for m in members:
        descs[m] = get_skill_desc(m)
    items = '\n'.join(f"{n}: {descs[n][:180]}" for n in members)
    prompt = f"""Rank these skills by relevance to the user query.

User query: {query}

Skills (name: description):
{items}

Output ONLY valid JSON: {{"ranked": [{{"name":"...","score":0.0-1.0,"why":"<10 words"}}, ...]}}.
Return top {top_k} most relevant. No markdown, no explanation outside JSON."""

    messages = [
        {"role": "user", "content": "Reply with the word READY"},
        {"role": "assistant", "content": "READY"},
        {"role": "user", "content": prompt},
    ]
    body = json.dumps({
        "model": "claude-opus-4.7-n",
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.0,
    }).encode('utf-8')
    req = urllib.request.Request(ep.rstrip('/') + '/chat/completions',
                                 data=body, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': f'Bearer {k}'})
    timeout_sec = int(os.environ.get('CHAIN_SELECT_LLM_TIMEOUT', '12'))
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as r:
            data = json.loads(r.read())
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            content = re.sub(r'^\s*<l[^>]*>\s*', '', content)
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                ranked = json.loads(m.group(0)).get('ranked', [])
                if ranked:
                    _cache_set('llm_rank', cache_payload, ranked)
                    return ranked
                return [{"error": "llm_rank: empty ranked list",
                         "fallback": "use menu mode"}]
    except Exception as e:
        return [{"error": f"llm_rank failed: {type(e).__name__}: {e}",
                 "fallback": "use menu mode or read chain file directly"}]
    return [{"error": "llm_rank: no JSON in response",
             "fallback": "use menu mode"}]


def gen_clarify_questions(chain_name, members):
    """For very large chains (>50), generate 2-3 narrow-down questions via LLM.

    Returns list of {q, options} dicts. On failure returns [] (caller can fall
    back to menu mode or top-5 sample).
    """
    ep, k, err = _load_creds()
    if err:
        return []  # caller already provides fallback_top5 or menu

    cache_payload = {
        "chain_name": chain_name,
        "members_sample": members[:30],
        "mode": "clarify_v2",
    }
    cached = _cache_get('clarify', cache_payload)
    if cached:
        return cached

    sample = members[:30]
    descs = {n: get_skill_desc(n)[:120] for n in sample}
    items = '\n'.join(f"{n}: {d}" for n, d in descs.items())
    prompt = f"""Look at this chain of {len(members)} skills and propose 2-3 multiple-choice questions
that, if the user answers, would narrow them down to <10 candidates.

Chain: {chain_name}
Sample skills (first 30):
{items}

Output ONLY JSON: {{"questions": [{{"q":"...","options":["a","b","c","d"]}}, ...]}}. No markdown."""

    messages = [
        {"role": "user", "content": "READY?"},
        {"role": "assistant", "content": "READY"},
        {"role": "user", "content": prompt},
    ]
    body = json.dumps({
        "model": "claude-opus-4.7-n",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.1,
    }).encode('utf-8')
    req = urllib.request.Request(ep.rstrip('/') + '/chat/completions',
                                 data=body, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': f'Bearer {k}'})
    timeout_sec = int(os.environ.get('CHAIN_SELECT_LLM_TIMEOUT', '12'))
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as r:
            data = json.loads(r.read())
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            content = re.sub(r'^\s*<l[^>]*>\s*', '', content)
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                qs = json.loads(m.group(0)).get('questions', [])
                if qs:
                    _cache_set('clarify', cache_payload, qs)
                return qs
    except Exception:
        pass
    return []


def _default_clarify_questions(query):
    """Always-available narrowing questions for large chains."""
    q = (query or '').lower()
    options_scope = ["单基因/单变异", "基因列表/批量", "疾病/队列层面", "还不确定"]
    options_data = ["临床注释(ClinVar/ACMG)", "人群频率(gnomAD)", "功能预测/通路", "结构变异/CNV"]
    options_out = ["快速答案(<=3项)", "完整候选列表(top10)", "带证据说明", "先给推荐再细化"]

    if 'vcf' in q or 'cnv' in q or 'sv' in q:
        options_data = ["VCF 小变异注释", "SV/CNV 注释", "两者都要", "不确定"]

    return [
        {"q": "你这次的分析对象范围是?", "options": options_scope},
        {"q": "你最关心哪类证据?", "options": options_data},
        {"q": "你希望输出形式是?", "options": options_out},
    ]


def main():
    if len(sys.argv) < 3:
        print("Usage: chain_select.py <chain-name> '<query>' [--top N]")
        sys.exit(1)
    chain_name = sys.argv[1]
    query = sys.argv[2]
    top_k = 5
    if '--top' in sys.argv:
        i = sys.argv.index('--top')
        top_k = int(sys.argv[i + 1])

    members = read_chain(chain_name)
    if members is None:
        print(json.dumps({"error": f"chain not found: {chain_name}"}))
        return
    if not members:
        print(json.dumps({"error": f"chain empty: {chain_name}"}))
        return

    n = len(members)
    out = {"chain": chain_name, "total_members": n}

    if n <= 5:
        out["mode"] = "menu-direct"
        out["members"] = members
    elif n <= 15:
        out["mode"] = "menu-with-desc"
        out["members"] = [{"name": m, "desc": get_skill_desc(m)[:100]} for m in members]
    elif n <= 50:
        out["mode"] = "llm-ranked"
        picks = llm_rank(members, query, top_k=top_k)
        if picks and isinstance(picks, list) and picks[0].get('error'):
            out["top_picks"] = _local_rank(members, query, top_k=top_k)
            out["degraded"] = {
                "reason": picks[0].get('error', 'llm unavailable'),
                "fallback": "local-rank"
            }
        else:
            out["top_picks"] = picks
        out["see_more_count"] = n - top_k
    else:
        out["mode"] = "ask-questions"
        qs = gen_clarify_questions(chain_name, members)
        if not qs:
            qs = _default_clarify_questions(query)
            out["degraded"] = {
                "reason": "clarify LLM unavailable or empty",
                "fallback": "default-questions"
            }
        out["questions"] = qs
        out["next_step"] = "answer questions, re-run with refined query"
        # Also give an LLM-ranked top-5 as backup
        fb = llm_rank(members[:50], query, top_k=5)
        if fb and isinstance(fb, list) and fb[0].get('error'):
            out["fallback_top5"] = _local_rank(members[:50], query, top_k=5)
            out.setdefault("degraded", {
                "reason": fb[0].get('error', 'llm unavailable'),
                "fallback": "local-rank"
            })
        else:
            out["fallback_top5"] = fb

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
