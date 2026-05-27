# CLAUDE.md - Skill Routing System Memory

## Overview

This project has access to a comprehensive skill-based routing system with **969 skills** and **~220 chain files** covering **14 super-domains**. This document serves as the memory/bootstrap for ensuring optimal skill selection on every task.

---

## 1. Skill Invocation Protocol (4-Layer Funnel)

**Core Principle**: Before any non-trivial task, run through the funnel instead of "free writing mode".

### Layer 0: Task Intake
```
Is this trivial? (§3.2 exceptions)
- Single file edit (typo, rename, comment, import fix)
- Single grep/glob/read fact query
- Simple file move/rename/mkdir
- Debugging/troubleshooting (needs flexibility)
- User explicitly says "fast/direct/no skill search"
- Meta tasks (like writing documentation)

YES → Direct execution, skip funnel
NO → Enter Layer 1
```

### Layer 1: Domain Matching (14 Super-Domains)
```
bio      - Life sciences, bioinformatics, omics, proteins, single-cell
clinic   - Clinical medicine, ICU, sepsis, drugs, imaging, pathology
stat     - Statistics, causal inference, meta-analysis, regression
ds       - Data science, ML, data engineering
lit      - Literature discovery, citations, CNKI, OpenAlex, Scite
paper    - Paper writing, methods, results, discussion, review, submission
antiAI   - AI detection avoidance, humanization, de-slop
grant    - NSFC/NIH/grant proposal design
km       - Knowledge management, Obsidian, knowledge graphs
eng      - Code, testing, database, DevOps
vis      - PPT, diagrams, posters, web, infographics
meta     - Skill creation, audit, installation, MCP
think    - Critical thinking, reasoning, cognitive frameworks
dao      - Wisdom, principles, decision frameworks
```

### Layer 2: Tag Chain Opening
```
Path: ~/.gemini/skills/_chains/chain-<domain>__<tag>.md
Example: chain-bio__single-cell-rna.md (33 members)
```

### Layer 3: Precision Select (by member count)
```
≤5 members   → Direct menu (list all)
6-15 members → Menu + 1-line description
16-50 members → Run chain_select.py for top-5
>50 members  → Ask 2-3 clarifying questions
```

### Layer 4: Pipeline Match
```
Check predefined pipelines:
- systematic-review
- NSFC-grant
- manuscript-revise-respond
- daily-radar
- skill-audit
- obsidian-kb
- TIM-submission
- multi-omics-manuscript-planning
```

### Layer 5: Execute
```
- Use Skill("<skill-name>") to invoke
- Sequential: pipeline.steps order
- Parallel-compare: invoke separately, present comparison table
```

---

## 2. Mandatory Router Gate (v1.1)

After funnel conditions met, **first hop must be the router**:

| Task Type | Mandatory Router | Routes To |
|-----------|-----------------|-----------|
| Research/Bio/Clinical/Database/Literature | `research-tool-router` | chain-domain-{bio,clinic,lit,paper} |
| Visual/PPT/Poster/Web/Diagram | `design-router` | chain-domain-vis |
| Code/Debug/Refactor | `karpathy-guidelines` | chain-domain-eng |
| Word/PPT/Excel generation | Documents/Presentations/Spreadsheets plugin | Direct plugin skill |

**Exception**: If user explicitly names a router or skill, skip router gate and execute named item directly.

---

## 3. MCP/API/Tool Priority Hierarchy

Execute in this order, **never skip layers**:

```
1. User-specified MCP/Skill/tool in current message
2. Project instructions (CLAUDE.md) canonical router/path
3. Official databases/APIs/local CLIs (PubMed/UniProt/Reactome/ChEMBL etc.)
4. Installed Skill scripts/
5. Web search/browser (generic)
6. Model memory fallback (lowest priority, FORBIDDEN for research tasks)
```

### Life Science Research Stack (Layer 3):
```
PubMed / PMC / Crossref / Scite / OpenAlex / CNKI
ToolUniverse / Reactome / STRING / ChEMBL / UniProt / Open Targets
bioclaw / single-cell / proteomics / cytometry skills
```

---

## 4. Key Skills by Domain

### Research/Literature (domain: lit)
- `research-tool-router` - Canonical entry point for all research tasks
- `wos-starter-search` - Web of Science Clarivate (SCI authority)
- `sc-citation-analysis` - Semantic Scholar citations
- `openalex-database` - Open academic graph
- `asta-skill` - AI2 Asta intent routing

### Literature Ensemble (DEFAULT for "find papers" queries)
**5-way parallel by default** (v1.2):
1. `mcp__tooluniverse-literature__SemanticScholar_search_papers`
2. `mcp__tooluniverse-literature__openalex_literature_search`
3. `Skill('wos-starter-search')`
4. `mcp__scite__search_literature` (citation strength + retraction)
5. `mcp__tooluniverse-literature__advanced_literature_search_agent`

### Bioinformatics (domain: bio)
- `bioclaw` - 51 unified entry skills for plots, TCGA, GEO, etc.
- `scanpy`, `scvi-tools`, `scvelo` - Single-cell analysis
- `spatial-transcriptomics-agent` - Spatial omics
- `protein-structure-visualizer` - AlphaFold/PDB

### Clinical (domain: clinic)
- `cytokine-storm-analysis-agent` - ICU/Sepsis
- `coagulation-thrombosis-agent` - Coagulation
- `organoid-drug-response-agent` - Drug screening

### Visualization (domain: vis)
- `design-router` - Entry point for visual tasks
- `diagram-design` - 13 editorial-grade diagrams (architecture/flowchart/etc.)
- `scientific-slides` - Scientific presentations
- `baoyu-infographic` - Infographics

### Writing (domain: paper)
- `scientific-writing` - Academic writing
- `avoid-ai-writing` - Anti-AI detection
- `springer-nature-paper-writing` - Nature/Springer format

### Code (domain: eng)
- `karpathy-guidelines` - Code task principles:
  1. State assumptions/success criteria first
  2. Minimal implementation
  3. Surgical changes only
  4. Verification closure

### Meta-Analysis (tag: paper:meta-analysis)
- `meta-rob2-plot`, `meta-funnel-plot`, `meta-forest-*-plot`
- `meta-picos-generator`, `meta-protocol-writer`
- `prospero-registration-helper`, `INPLASY-registration-helper`

### Wisdom/Decision (domain: dao)
- `daozhi` - Wisdom main entry
- `daozhi-search` - Search wisdom library
- `daozhi-apply` - Apply wisdom to current problem
- `daozhi-distill` - Distill new wisdom from papers/cases

---

## 5. Parallel-Compare Mode (v1.2)

### Trigger Conditions (any one activates)
1. Query contains comparison words: 对比/比较/验证/互相印证/cross-check/多源/互补/全面/都跑/都用/全部
2. Funnel gives ≥3 equivalent candidate chains with no linear dependency
3. domain=lit + query is search-type ("找 X / search X / 查 X") → auto 5-way ensemble
4. User explicitly says "use more skills and MCPs"

### When NOT to use parallel-compare
- Single query single entity ("TP53 expression in GTEx") → 1 tool enough
- User named specific tool ("only use scite") → respect specification
- Pipeline tasks with dependencies (SR: PROSPERO → screening → RoB → forest)
- User says "fast/direct/no funnel"

---

## 6. Output Template (v1.1 Standardized)

After task completion, **MUST** report:

```
[Skill Funnel Report]
- Chain hit: <chain-name or "none (free mode + reason)">
- Pipeline hit: <pipeline-name or "none">
- Skills invoked: <skill1 / skill2 / ...>
- Router hit: <research-tool-router / design-router / karpathy-guidelines / none>

[Skill Output Detail]
Successfully used Skills:
  - <skill-name>: <what it did>
Failed or degraded MCP/Skill:
  - Tool: <name>
    Reason: <api key / network / init / permission / timeout / other>
    Fallback: <alternative path chosen>
  - (If none, write "none")
Output files:
  - <absolute path>
Verification (per §13 checklist):
  - <file type>: <verification command / result>
Notes / Limitations:
  - <if any>
```

---

## 7. MCP Registry Quick Reference

### Domain → MCP Clusters

**lit (literature)**:
- `mcp__scite__search_literature` - Citation strength
- `mcp__tooluniverse-literature__*` - SemanticScholar, OpenAlex, PubMed, arXiv, bioRxiv

**bio (biology)**:
- `mcp__tooluniverse-gene__*` - Ensembl, UniProt, HPA, Enrichr
- `mcp__tooluniverse-genomics__*` - gnomAD, GWAS, cBioPortal
- `mcp__tooluniverse-pathway__*` - KEGG, Reactome, WikiPathways

**clinic (clinical)**:
- `mcp__tooluniverse-disease__*` - ClinVar, OpenTargets, FAERS
- `mcp__tooluniverse-drug__*` - DrugBank, ChEMBL

**km (knowledge management)**:
- `mcp__infranodus__*` - Text analysis, concept bridges, research questions

**eng (engineering)**:
- `mcp__gitnexus__*` - Git context, impact, query
- `mcp__Context7__*` - Up-to-date library docs

---

## 8. Chain File Locations

Canonical: `~/.gemini/skills/_chains/`
Junctions: `~/.claude/skills/_chains/`, `~/.codex/skills/_chains/`, `~/.copilot/skills/_chains/`

Key chain files (examples):
- `chain-bio__single-cell-rna.md` (33 members)
- `chain-bio__proteomics.md`
- `chain-clinic__icu-sepsis.md`
- `chain-paper__meta-analysis.md`
- `chain-vis__diagram-design.md`
- `chain-lit__multi-source-search.md`

---

## 9. Funnel Quick Commands

```bash
# One-click routing
python ~/.gemini/skills/_chains/_scripts/skill_route.py "<task description>"

# Precision select from large chain
python ~/.gemini/skills/_chains/_scripts/chain_select.py <chain-name> "<query>"

# Pipeline match
python ~/.gemini/skills/_chains/_scripts/chain_combine.py --match "<task description>"

# Rebuild chain index
python ~/.gemini/skills/_chains/_scripts/build_chains.py

# Log usage for skill improvement
python ~/.gemini/skills/_chains/_scripts/log_usage.py <skill-name> --rating good --task "<description>"
```

---

## 10. Tier Classification (v1.2 Funnel Report)

| Tier | Scope | Output Format |
|------|-------|---------------|
| **Tier-S** | Simple/meta/single-step | 1-line: `[Funnel] tier=S \| domain=X \| skill=Y \| mode=Z \| reason=...` |
| **Tier-M** | Medium (2-4 steps, 1-2 domains) | Full template (candidates + selection reason + execution plan) |
| **Tier-L** | Heavy (≥5 steps, ≥3 domains) | Full template + spawn orchestrator |

**Funnel exemptions (only 2)**:
1. User explicitly says "fast/direct/no funnel" in current turn
2. Pure conversational response (no deliverable)

---

## 11. Zero-Hallucination Research Protocol

For research tasks:
1. Citations (title, DOI, PMID, author, year) MUST come from current turn's tool results
2. If not found, write "not retrieved" - NEVER fill from training memory
3. Attachments must be extracted/read before writing proposals
4. Non-trivial research must save MD/CSV/XLSX/DOCX files
5. Report must include: Methods, search queries, databases, timeframe, failed tools

### Minimum verification counts:
- quick: ≥5 tool/search/file operations
- survey: ≥30
- review: ≥60
- systematic: ≥100

---

## 12. Verification Checklist (Per-artifact)

### File types:
```
DOCX: python-docx can open; count paragraphs/tables; spot-check keywords
PDF: can extract text or render pages; check page count
PPTX: can open or render; no blank slides
XLSX: can read sheets; key tables exist
HTML/Web: local server or browser screenshot validates
```

### Code types:
```
- Tests pass (or note why not run)
- lint/format pass (or note why not run)
- git diff limited to task scope
- Interface contracts match upstream
```

### Research types:
```
- Evidence files exist (MD/CSV/XLSX on disk)
- Every citation traceable to current turn's tools
- Key conclusions correspond to attachments/tool output
- Limitations/conflicts/search failures explicitly written
```

---

## 13. Current Environment Notes

This session is running in a **cloud container** environment with:
- Repository: `piheoq4587/piheoq4587`
- Branch: `claude/slack-session-ArnmP`
- Reference backup: `/home/user/daozhi-backup-private/` (969 skills, full routing system)

The skill system reference materials are available at:
- Protocol: `/home/user/daozhi-backup-private/routing-system/SKILL_INVOCATION_PROTOCOL_v1.md`
- MCP Registry: `/home/user/daozhi-backup-private/routing-system/MCP_REGISTRY.md`
- Hierarchy: `/home/user/daozhi-backup-private/routing-system/HIERARCHY_PROTOCOL_PORTABLE.md`
- Bootstrap: `/home/user/daozhi-backup-private/routing-system/UNIFIED_CLI_BOOTSTRAP.md`
- Chain files: `/home/user/daozhi-backup-private/routing-system/chain-*.md`
- Skills: `/home/user/daozhi-backup-private/skills/`

---

## Version History

- v1.0 (2026-05-27): Initial memory document created from daozhi-backup-private analysis
  - Learned 4-layer funnel system
  - Documented 14 super-domains
  - Catalogued 969 skills
  - Recorded MCP Registry mappings
  - Captured routing protocols and output templates
