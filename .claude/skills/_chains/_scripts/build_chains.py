"""
build_chains.py — 扫 ~/.gemini/skills/*/SKILL.md frontmatter 的 tags 字段,
反向汇总成 ~/.gemini/skills/_chains/<tag>.md 视图。

用法: python build_chains.py
"""
import os, re, json, sys, io
# Force UTF-8 stdout on Windows GBK consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pathlib import Path
from collections import defaultdict

ROOT = Path(os.path.expanduser('~/.gemini/skills'))
TAX  = ROOT / '_taxonomy' / 'v1.json'
OUT  = ROOT / '_chains'
OUT.mkdir(exist_ok=True, parents=True)

with open(TAX, encoding='utf-8') as f:
    tax = json.load(f)

# Collect all known tags (whitelist)
all_tags = set()
for dom_data in tax['domains'].values():
    all_tags.update(dom_data['tags'])

# Scan every skill's SKILL.md
tag_to_skills = defaultdict(list)
domain_to_skills = defaultdict(set)
all_skills = []
unclassified = []

for skill_dir in sorted(ROOT.iterdir()):
    if not skill_dir.is_dir() or skill_dir.name.startswith('_'):
        continue
    sk = skill_dir / 'SKILL.md'
    if not sk.exists():
        continue
    all_skills.append(skill_dir.name)
    try:
        text = sk.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    # Extract frontmatter
    m = re.match(r'(?s)^---\s*\n(.+?)\n---', text)
    if not m:
        unclassified.append(skill_dir.name)
        continue
    front = m.group(1)
    # Find tags: list (YAML, supports both inline and block)
    tags = []
    inline = re.search(r'^tags:\s*\[(.+?)\]', front, re.MULTILINE)
    if inline:
        tags = [t.strip().strip('"').strip("'") for t in inline.group(1).split(',')]
    else:
        block = re.search(r'(?ms)^tags:\s*\n((?:\s*-\s*.+\n)+)', front)
        if block:
            tags = re.findall(r'-\s*(.+?)\s*$', block.group(1), re.MULTILINE)
            tags = [t.strip().strip('"').strip("'") for t in tags]
    if not tags:
        unclassified.append(skill_dir.name)
        continue
    for t in tags:
        if t not in all_tags:
            continue  # ignore unknown tags
        tag_to_skills[t].append(skill_dir.name)
        domain = t.split(':')[0]
        domain_to_skills[domain].add(skill_dir.name)

# Generate per-tag chain markdown
for tag in sorted(tag_to_skills):
    safe = tag.replace(':', '__')
    chain_file = OUT / f'chain-{safe}.md'
    members = sorted(tag_to_skills[tag])
    body = f"""---
chain-tag: {tag}
chain-type: tag-view
member-count: {len(members)}
default-mode: menu
---

# Chain: `{tag}`

包含 **{len(members)}** 个 skill。当用户提到 `{tag}` 相关功能时,从下面挑选(menu)或同时调多个对比(parallel-compare)。

## 成员 skill (auto-generated, 勿手动编辑)

<!-- BEGIN AUTO-MEMBERS -->
{chr(10).join(f"- `{m}`" for m in members)}
<!-- END AUTO-MEMBERS -->
"""
    chain_file.write_text(body, encoding='utf-8')

# Generate domain super-chains (e.g. chain-domain-bio includes ALL bio:* skills)
for dom, members in domain_to_skills.items():
    chain_file = OUT / f'chain-domain-{dom}.md'
    members = sorted(members)
    body = f"""---
chain-domain: {dom}
chain-type: domain-super-view
member-count: {len(members)}
default-mode: menu+narrow
---

# Domain Chain: `{dom}` ({tax['domains'].get(dom,{}).get('label','?')})

包含 **{len(members)}** 个 skill,覆盖该域所有 sub-tag。

## 子 chain(narrow scope)

{chr(10).join(f"- `chain-{t.replace(':','__')}.md`" for t in sorted(tax['domains'].get(dom,{}).get('tags',[])))}

## 全部成员

<!-- BEGIN AUTO-MEMBERS -->
{chr(10).join(f"- `{m}`" for m in members)}
<!-- END AUTO-MEMBERS -->
"""
    chain_file.write_text(body, encoding='utf-8')

# Build summary
summary = {
    'total_skills_scanned': len(all_skills),
    'classified': len(all_skills) - len(unclassified),
    'unclassified': len(unclassified),
    'unclassified_list_first50': unclassified[:50],
    'tags_with_members': len(tag_to_skills),
    'domains_active': len(domain_to_skills),
    'top10_largest_chains': sorted([(t, len(s)) for t,s in tag_to_skills.items()], key=lambda x:-x[1])[:10],
}
(OUT / '_build_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"✅ Build complete")
print(f"  Total skills: {summary['total_skills_scanned']}")
print(f"  Classified: {summary['classified']}")
print(f"  Unclassified (need tagging): {summary['unclassified']}")
print(f"  Active tags: {summary['tags_with_members']} / {len(all_tags)}")
print(f"  Active domains: {summary['domains_active']} / {len(tax['domains'])}")
