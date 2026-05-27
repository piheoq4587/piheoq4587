"""
install_new.py — Install all staged new skills into ~/.gemini/skills/ canonical.

Logic:
- For each source repo, walk skills (each has SKILL.md)
- Compute target name (apply renames)
- Skip if exact same content (dedup)
- If name collides but content differs, suffix with -<src>
- Copy to canonical
- Track install log
"""
import os, shutil, json, hashlib, re
from pathlib import Path

STAGING = Path(os.path.expanduser('~/skills-staging-2026-05/raw'))
CANON = Path(os.path.expanduser('~/.gemini/skills'))

# Map of (source-relative-path, target-name) for each repo. None = use upstream name.
SOURCES = {
    'lishix': {'path': '.', 'rename': {'composer': 'paper-composer', 'strategist': 'paper-strategist'},
               'skills_at_top': ['composer', 'strategist']},
    'shiyanw': {'path': '.', 'is_single_skill': True, 'target': 'ai-revision-guard'},
    'conor': {'path': '.', 'is_single_skill': True, 'target': 'avoid-ai-writing'},
    'posit': {'path': '.', 'rename': {}, 'skills_at_top': True, 'rename_prefix': 'posit-'},
    'lyndon': {'path': 'skills', 'rename': {}, 'skip_prefixes': ['mlb-']},
    'brycewang2': {'path': 'skills', 'rename': {
        '00-Full-empirical-analysis-skill_StatsPAI': 'empirical-analysis-statspai',
        '00.1-Full-empirical-analysis-skill_Python': 'empirical-analysis-python',
        '00.2-Full-empirical-analysis-skill_Stata': 'empirical-analysis-stata',
        '00.3-Full-empirical-analysis-skill_R': 'empirical-analysis-r',
        '44-matsuikentaro1-humanizer_academic': 'humanizer-academic-en',
        '45-stephenturner-skill-deslop': 'skill-deslop',
        '46-hardikpandya-stop-slop': 'stop-slop-skill',
        '48-copaper-ai-chinese-de-aigc': 'de-aigc-chinese',
        '49-voidborne-d-humanize-chinese': 'humanize-chinese',
    }},
    'openclaw': {'path': 'skills', 'rename': {}},
    'scholar': {'path': 'skills', 'rename': {}, 'rename_prefix': 'cs-',
                'skip_files': ['obsidian-skills.UPSTREAM-LICENSE.txt', 'obsidian-skills.UPSTREAM-SOURCE.txt']},
    'luwill': {'path': '.', 'subpaths': ['medical-imaging-review', 'paper-slide-deck', 'research-proposal'],
               'subdir_path': 'skills',
               'subdir_skills': ['literature-scout', 'paper-analyst', 'quality-editor', 'survey-director', 'survey-writer']},
}


def has_skill_md(p):
    return (p / 'SKILL.md').exists()


def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest() if path.exists() else None


def install_one(src_dir, target_name, log):
    """Copy src_dir to CANON/target_name with dedup."""
    if not has_skill_md(src_dir):
        log['skipped_no_skill_md'].append(str(src_dir))
        return
    target = CANON / target_name
    src_md_hash = file_hash(src_dir / 'SKILL.md')
    if target.exists():
        existing_hash = file_hash(target / 'SKILL.md')
        if existing_hash == src_md_hash:
            log['skipped_identical'].append(target_name)
            return
        # Collision but content differs — suffix with source repo name
        suffix = src_dir.parts[len(STAGING.parts):][0]  # repo dir name
        new_name = f"{target_name}-{suffix}"
        target = CANON / new_name
        if target.exists():
            log['skipped_collision_resolved_exists'].append(new_name)
            return
        log['renamed_due_to_collision'].append({'from': target_name, 'to': new_name})
        target_name = new_name
    try:
        shutil.copytree(src_dir, target)
        log['installed'].append(target_name)
    except Exception as e:
        log['errors'].append({'name': target_name, 'err': str(e)})


def main():
    log = {
        'installed': [], 'skipped_identical': [], 'skipped_no_skill_md': [],
        'renamed_due_to_collision': [], 'skipped_collision_resolved_exists': [],
        'errors': [], 'skipped_filter': [],
    }

    for src_name, conf in SOURCES.items():
        src_root = STAGING / src_name
        if not src_root.exists():
            print(f"  [SKIP] {src_name} not staged")
            continue
        print(f"\n=== {src_name} ===")

        if conf.get('is_single_skill'):
            install_one(src_root, conf['target'], log)
            continue

        if 'skills_at_top' in conf:
            tops = conf['skills_at_top'] if isinstance(conf['skills_at_top'], list) else [
                d.name for d in src_root.iterdir() if d.is_dir() and not d.name.startswith('.') and has_skill_md(d)
            ]
            for s in tops:
                src = src_root / s
                if not src.is_dir():
                    continue
                if conf.get('skip_files') and s in conf['skip_files']:
                    log['skipped_filter'].append(s)
                    continue
                target_name = conf.get('rename', {}).get(s, s)
                if conf.get('rename_prefix') and not target_name.startswith(conf['rename_prefix']):
                    target_name = conf['rename_prefix'] + target_name
                install_one(src, target_name, log)

        if 'subpaths' in conf:
            for s in conf['subpaths']:
                src = src_root / s
                if src.is_dir():
                    install_one(src, s, log)
            for s in conf.get('subdir_skills', []):
                src = src_root / conf.get('subdir_path', 'skills') / s
                if src.is_dir():
                    install_one(src, s, log)

        if 'path' in conf and conf['path'] != '.' and 'subpaths' not in conf:
            # walk path/
            base = src_root / conf['path']
            if not base.exists():
                continue
            for d in base.iterdir():
                if not d.is_dir() or d.name.startswith('.'):
                    continue
                if not has_skill_md(d):
                    continue
                if conf.get('skip_prefixes'):
                    if any(d.name.startswith(p) for p in conf['skip_prefixes']):
                        log['skipped_filter'].append(d.name)
                        continue
                if conf.get('skip_files') and d.name in conf['skip_files']:
                    log['skipped_filter'].append(d.name)
                    continue
                target_name = conf.get('rename', {}).get(d.name, d.name)
                if conf.get('rename_prefix') and not target_name.startswith(conf['rename_prefix']):
                    target_name = conf['rename_prefix'] + target_name
                install_one(d, target_name, log)

    out = CANON / '_chains' / '_install_log.json'
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n=== Summary ===")
    print(f"Installed:                  {len(log['installed'])}")
    print(f"Skipped (identical):        {len(log['skipped_identical'])}")
    print(f"Skipped (no SKILL.md):      {len(log['skipped_no_skill_md'])}")
    print(f"Skipped (filter mlb/etc):   {len(log['skipped_filter'])}")
    print(f"Renamed (collision):        {len(log['renamed_due_to_collision'])}")
    print(f"Errors:                     {len(log['errors'])}")
    if log['renamed_due_to_collision']:
        print("\nRenames:")
        for r in log['renamed_due_to_collision']:
            print(f"  {r['from']} -> {r['to']}")
    if log['errors']:
        print("\nErrors (first 5):")
        for e in log['errors'][:5]:
            print(f"  {e}")
    print(f"\nFull log: {out}")


if __name__ == '__main__':
    main()
