"""
auto_tag.py — rule-based + LLM-fallback automatic chain-tag classifier.

Phases:
1. Rule matching (skill name pattern) → covers ~70%
2. Remaining → LLM batch classification (Opus 4.7-n via tone.nyc.mn proxy)
3. Write tags into each SKILL.md frontmatter (safe edit)

Usage:
  python auto_tag.py                  # dry-run, just count + dump unclassified
  python auto_tag.py --apply          # write tags from rules
  python auto_tag.py --apply --llm    # also run LLM on unclassified
"""
import os, re, json, sys, time
from pathlib import Path
from collections import defaultdict

ROOT = Path(os.path.expanduser('~/.gemini/skills'))
TAX = ROOT / '_taxonomy' / 'v1.json'
RULES_PATH = ROOT / '_chains' / '_scripts' / 'auto_tag_rules.json'

with open(TAX, encoding='utf-8') as f:
    tax = json.load(f)
all_tags = set()
for d in tax['domains'].values():
    all_tags.update(d['tags'])

with open(RULES_PATH, encoding='utf-8') as f:
    RULES = json.load(f)['rules']


def tag_by_rules(name):
    n = name.lower()
    matched = []
    for pat, tag_list in RULES:
        if pat.lower() in n:
            for t in tag_list:
                if t in all_tags and t not in matched:
                    matched.append(t)
    return matched


def llm_classify_batch(unclassified, descriptions, batch=15):
    """Send batches to Opus 4.7-n. Return dict skill_name -> [tags]."""
    import urllib.request, urllib.error

    env_path = Path(os.path.expanduser('~/.claude/config/api-credentials.env'))
    endpoint = key = None
    for line in env_path.read_text(encoding='utf-8-sig', errors='ignore').splitlines():
        if line.startswith('OPENAI_BASE_URL='):
            endpoint = line.split('=', 1)[1].strip().strip('"').strip("'")
        elif line.startswith('OPENAI_API_KEY='):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")

    url = endpoint.rstrip('/') + '/chat/completions'
    tag_list_str = '\n'.join(sorted(all_tags))

    out = {}
    for i in range(0, len(unclassified), batch):
        chunk = unclassified[i:i + batch]
        items_text = '\n'.join(
            f"{n}: {descriptions.get(n, '(no desc)')[:200]}" for n in chunk
        )
        prompt = f"""Classify each skill into 2-5 tags from the whitelist below.

Whitelist tags (only use these, no others):
{tag_list_str}

Skills to classify (name: description):
{items_text}

Output ONLY valid JSON: {{"skill-name": ["tag1","tag2"], ...}}. No markdown, no explanation."""

        # Few-shot priming for Opus 4.7-n (anti <l artifact)
        messages = [
            {"role": "user", "content": "Reply with the word READY"},
            {"role": "assistant", "content": "READY"},
            {"role": "user", "content": prompt},
        ]
        body = json.dumps({
            "model": "claude-opus-4.7-n",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.1,
        }).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST', headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}',
        })
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                # Strip Opus <l artifact prefix if present (5KB threshold)
                content = re.sub(r'^\s*<l[^>]*>\s*', '', content)
                # Find JSON block
                m = re.search(r'\{.*\}', content, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    for k, v in parsed.items():
                        valid = [t for t in v if t in all_tags]
                        if valid:
                            out[k] = valid
                print(f"  LLM batch {i // batch + 1}: {len(parsed)} classified")
        except Exception as e:
            print(f"  LLM batch {i // batch + 1} FAILED: {type(e).__name__}: {str(e)[:120]}")
        time.sleep(2)
    return out


def write_tags_to_skill(name, tags):
    """Safe-edit SKILL.md: insert/replace tags: [...] in frontmatter."""
    sk = ROOT / name / 'SKILL.md'
    if not sk.exists():
        return False
    text = sk.read_text(encoding='utf-8', errors='ignore')
    m = re.match(r'(?s)^---\s*\n(.+?)\n---', text)
    tag_line = f"tags: [{', '.join(tags)}]"
    if not m:
        new = f"---\nname: {name}\n{tag_line}\n---\n\n" + text
        sk.write_text(new, encoding='utf-8')
        return True
    front = m.group(1)
    if re.search(r'^tags:', front, re.MULTILINE):
        new_front = re.sub(r'(?ms)^tags:.*?(?=\n[\w\-]+:|$)', tag_line, front, count=1)
    else:
        new_front = front.rstrip() + '\n' + tag_line
    new_text = f"---\n{new_front}\n---" + text[m.end():]
    sk.write_text(new_text, encoding='utf-8')
    return True


def get_description(name):
    sk = ROOT / name / 'SKILL.md'
    if not sk.exists():
        return ''
    text = sk.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'(?ms)^description:\s*([>|]?)\s*\n?(.+?)(?=\n[\w\-]+:|---)', text)
    if m:
        return ' '.join(m.group(2).split())[:300]
    return ''


def main():
    apply_mode = '--apply' in sys.argv
    use_llm = '--llm' in sys.argv

    rule_results = {}
    unclassified = []
    descriptions = {}

    for skill_dir in sorted(ROOT.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith('_'):
            continue
        if not (skill_dir / 'SKILL.md').exists():
            continue
        tags = tag_by_rules(skill_dir.name)
        if tags:
            rule_results[skill_dir.name] = tags
        else:
            unclassified.append(skill_dir.name)
            descriptions[skill_dir.name] = get_description(skill_dir.name)

    total = len(rule_results) + len(unclassified)
    print(f"Rule classified: {len(rule_results)}/{total} ({100*len(rule_results)/total:.1f}%)")
    print(f"Unclassified:    {len(unclassified)}")

    if not apply_mode:
        out = ROOT / '_chains' / '_classify_dryrun.json'
        out.write_text(json.dumps({
            'rule_classified': rule_results,
            'unclassified': unclassified,
            'descriptions_for_llm': descriptions,
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n[DRY-RUN] dump: {out}")
        print(f"Add --apply to write tags. Add --llm for LLM classification of remaining {len(unclassified)}.")
        return

    # APPLY rule results
    for name, tags in rule_results.items():
        write_tags_to_skill(name, tags)
    print(f"\n[APPLY] wrote rule tags to {len(rule_results)} skills")

    # LLM phase
    if use_llm and unclassified:
        print(f"\n[LLM] classifying {len(unclassified)} skills via Opus 4.7-n...")
        llm_results = llm_classify_batch(unclassified, descriptions)
        for name, tags in llm_results.items():
            write_tags_to_skill(name, tags)
        print(f"[LLM] wrote tags to {len(llm_results)} skills")
        still_unclass = [n for n in unclassified if n not in llm_results]
        if still_unclass:
            (ROOT / '_chains' / '_unclassified_after_llm.json').write_text(
                json.dumps(still_unclass, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"  {len(still_unclass)} still unclassified — see _unclassified_after_llm.json")


if __name__ == '__main__':
    main()
