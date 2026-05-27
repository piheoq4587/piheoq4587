---
name: task-router
description: Universal task-to-tool routing engine. Invoke FIRST for any non-trivial task (≥2 steps, unclear tool choice, multi-domain). Classifies task → extracts entities → selects optimal tool chain from 766 MCP tools + 1,593+ skills + 198 chains = 2,557+ total capabilities. Uses runtime discovery — never relies on static lists. Outputs a ranked execution plan with concrete tool names, call order, and ID-mapping bridges. SKIP for single-step lookups where the tool is obvious.
tags: [meta:routing, meta:orchestration, pipeline]
---

# task-router — Universal Task Routing Engine

You are the **routing brain** of this system. Your sole job: given a user task, produce the optimal tool execution plan. You do NOT execute — you PLAN and HAND OFF.

## When to trigger

**Trigger** (route first, execute after):
- Task spans ≥2 steps or ≥2 tools
- Task touches multiple domains (e.g., drug + genomics + literature)
- User phrases task openly ("帮我分析…", "调查…", "从X到Y全流程")
- You're unsure which skill/tool chain to use
- Task requires ID/format mapping between tools (e.g., gene symbol → Ensembl → UniProt)

**Skip** (just execute directly):
- Single-tool lookup ("查 TP53 在 GTEx 的表达")
- User already named the tool/skill ("用 bioclaw plot-volcano…")
- Trivial one-liner (<1 min)

**Relationship to `task-planner`**: task-planner generates 2-3 candidate *strategies* for the user to pick. task-router generates the *detailed tool chain* for the chosen strategy. When task-planner is triggered, it consults task-router internally. When task-planner is NOT triggered (user chose a path already), use task-router directly.

---

## Routing Pipeline (5 phases)

### Phase 1: Task Classification

Parse the user request and assign **one primary domain** + **optional secondary domains**:

| Domain Code | Domain | Example Triggers |
|---|---|---|
| `DRUG` | Drug discovery / pharmacology | ADMET, 药物设计, 靶点-疾病, MoA, 化合物筛选 |
| `GENO` | Genomics / variants | VCF, 变异注释, GWAS, eQTL, 基因组分析 |
| `SCRA` | Single-cell RNA-seq | scRNA, 单细胞, 聚类, 细胞类型, 差异表达 |
| `BULK` | Bulk RNA-seq / proteomics | 差异表达, bulk, TMT, LFQ, 蛋白质组 |
| `LITR` | Literature / bibliography | 文献检索, 综述, 引文, PubMed, 预印本 |
| `CLIN` | Clinical / trials / guidelines | 临床试验, 诊疗指南, 病例, FDA, NICE |
| `PROT` | Protein structure / function | 蛋白结构, AlphaFold, PDB, 域, 相互作用 |
| `PATH` | Pathways / networks / enrichment | 通路, KEGG, Reactome, GO, PPI, 富集 |
| `VISU` | Visualization / figures | 火山图, heatmap, 生存曲线, 示意图, PPT |
| `STAT` | Statistics / modeling | 回归, Cox, 贝叶斯, 因果推断, meta分析 |
| `ENGR` | Software engineering | 代码, debug, CI/CD, API, 重构 |
| `WRIT` | Scientific writing / grants | 论文写作, 标书, 投稿, 审稿, 润色 |
| `CRIS` | CRISPR / gene editing | sgRNA设计, CRISPR筛选, base editing |
| `EPIG` | Epigenomics / methylation | 甲基化, ChIP-seq, ATAC-seq, Hi-C |
| `META` | Meta-skills / routing | skill创建, MCP配置, 系统优化 |

### Phase 2: Entity Extraction

Scan the request for **named entities** and normalize them:

| Entity Type | Pattern | Normalization Target | Example |
|---|---|---|---|
| Gene | `EGFR`, `TP53`, `BRCA1` | Symbol → Ensembl ID | `EGFR` → `ENSG00000146648` |
| Disease | `lung cancer`, `脓毒症` | EFO ID | `lung cancer` → `EFO_0001074` |
| Drug | `aspirin`, `阿司匹林` | ChEMBL ID | `aspirin` → `CHEMBL25` |
| Variant | `rs12345`, `BRAF V600E` | rsID or HGVS | keep as-is |
| Protein | `P05067`, `APP` | UniProt accession | `APP` → `P05067` |
| Pathway | `JAK-STAT`, `糖酵解` | KEGG/Reactome ID | `JAK-STAT` → `R-HSA-877300` |
| DOI/PMID | `10.1038/...`, `PMID:12345` | keep as-is | — |
| PDB | `1ABC`, `7CGO` | PDB ID | — |
| Cell line | `HeLa`, `MCF7` | Cellosaurus accession | `HeLa` → `CVCL_0030` |

### Phase 3: Tool Chain Assembly

Based on domain + entities, assemble the tool chain from these sources:

#### Source A: Existing Chain System (FASTEST — pre-built)

Check `~/.gemini/skills/_chains/chain-<domain>__<subtag>.md` for pre-built chains:
- 198+ chains across 14 super-domains
- Scripts: `chain_select.py` for LLM-ranking, `chain_combine.py` for pipeline matching

```
Quick check: ls ~/.gemini/skills/_chains/ | grep -i <keyword>
```

If a matching chain exists, use it as the backbone and extend only if needed.

#### Source B: MCP ToolUniverse Tools (766 tools)

Select from high-frequency tool families (ordered by usage):

| Family | Tools | Typical Use |
|---|---|---|
| OpenTargets (54) | `get_associated_targets`, `get_diseases_phenotypes`, `target_disease_evidence`, `get_drug_indications`, `get_drug_warnings`, `get_drug_mechanism_of_action` | 靶点-疾病-药物三角 |
| FDA Drug Label (158) | `get_indications`, `get_adverse_reactions`, `get_contraindications`, `get_mechanism_of_action`, `get_boxed_warning`, `get_pharmacokinetics` | FDA药品标签查询 |
| FAERS (21) | `count_reactions`, `count_seriousness`, `count_outcomes`, `search_serious_reports` | 药物不良事件 |
| RCSB PDB (40) | `get_protein_metadata`, `get_sequence`, `get_citation_info`, `get_binding_affinity`, `search_similar_structures` | 蛋白质结构 |
| Software Info (116) | `get_scanpy_info`, `get_rdkit_info`, `get_pandas_info`, ... | 软件库用法查询 |
| DrugBank (19) | `get_drug_basic_info`, `get_indications`, `get_pharmacology`, `get_targets`, `get_safety`, `get_chemistry`, `get_interactions` | 药物百科 |
| HPA (13) | `search_genes`, `get_disease_expression`, `get_comparative_expression`, `get_protein_interactions`, `get_cancer_prognostics` | 人类蛋白图谱 |
| UniProt (12) | `search`, `get_entry`, `get_function`, `get_disease_variants`, `id_mapping` | 蛋白质功能 |
| GWAS (13) | `search_associations`, `search_studies`, `get_variants_for_trait`, `get_associations_for_snp` | GWAS关联 |
| ADMET AI (9) | `predict_physicochemical`, `predict_CYP`, `predict_BBB`, `predict_toxicity`, `predict_bioavailability`, `predict_clearance` | ADMET预测 |
| Literature (15+) | `PubMed_search_articles`, `EuropePMC_search_articles`, `SemanticScholar_search_papers`, `ArXiv_search_papers`, `OpenAlex_literature_search` | 文献检索 |
| Guidelines (10) | `NICE_Clinical_Guidelines_Search`, `WHO_Guidelines_Search`, `PubMed_Guidelines_Search`, `TRIP_Database_Guidelines_Search` | 临床指南 |
| EU Health (21) | `search_cancer`, `search_covid_19`, `search_vaccination`, `search_mental_health`, ... | 欧洲健康数据 |
| Genomics (30+) | `ensembl_lookup_gene`, `clinvar_search_variants`, `geo_search_datasets`, `gnomad_get_gene_constraints`, `dbsnp_get_variant` | 基因组数据库 |

#### Source C: Skills (1,593+ — use dynamic discovery)

**NEVER rely on a static skill list**. Use runtime discovery to find matching skills:

```bash
# Method 1: Filesystem keyword scan (fastest)
ls ~/.gemini/skills/ | grep -iE '<2-3 keywords>'

# Method 2: Grep skill descriptions for deeper matching
grep -rl '<keyword>' ~/.gemini/skills/*/SKILL.md

# Method 3: For factory skills (symlinks to gemini)
ls ~/.factory/skills/ | grep -iE '<2-3 keywords>'
```

When ≥2 similar skills are found, apply **Multi-Skill Ranking**:
1. Read each candidate's SKILL.md description (first 5 lines)
2. Score by description relevance to the task (0-10)
3. Present top-3 to user with brief comparison:
   ```
   Found 4 similar skills for "single-cell analysis":
   1. scanpy (score: 9) — Standard scRNA-seq pipeline, QC → UMAP → clustering
   2. scrna-orchestrator (score: 8) — Full Scanpy pipeline from raw-count .h5ad
   3. single-cell-basic-analysis (score: 7) — Basic pipeline, count matrix input
   → Auto-select #1 (highest score) unless user overrides
   ```
4. **Auto-select the top-scoring skill** if score gap ≥2 points; otherwise ask user to choose.

### Phase 4: ID/Format Bridge Planning

For multi-tool chains, plan the **bridges** between tools:

| From → To | Bridge | Example |
|---|---|---|
| Gene symbol → Ensembl ID | `UniProt_id_mapping` or `ensembl_lookup_gene` | `EGFR` → `ENSG00000146648` |
| Ensembl → UniProt | `UniProt_id_mapping` | `ENSG00000146648` → `P00533` |
| Disease name → EFO | `OpenTargets_get_disease_id` or `OSL_get_efo_id` | `lung cancer` → `EFO_0001074` |
| Drug name → ChEMBL | `OpenTargets_get_drug_id` or `drugbank_vocab_search` | `aspirin` → `CHEMBL25` |
| Gene → Protein structure | `UniProt_search` → `alphafold_get_summary` | `EGFR` → `P00533` → AFDB |
| rsID → GWAS hits | `gwas_get_associations_for_snp` | `rs121913529` → trait list |
| Gene → TCGA expression | `bioclaw tcga_expression_for_gene` | direct by gene symbol |
| Gene → DepMap | `bioclaw depmap-analysis-for-gene` | direct by gene symbol |
| PDB → Ligand SMILES | `get_ligand_smiles_by_chem_comp_id` | `ATP` → SMILES |
| PMID → Full text | `ncbi-pmc-skill` or `EuropePMC_search_articles` | `12345` → abstract/full |

### Phase 5: Output the Plan

Present the plan as a structured execution roadmap:

```
## Task Router Plan

**Task**: <user's original request>
**Primary domain**: <CODE> | **Secondary**: <CODE(s)>

**Entities found**:
- Gene: EGFR → ENSG00000146648 / UniProt P00533
- Disease: lung cancer → EFO_0001074
- Drug: osimertinib → CHEMBL3350488

**Execution chain** (4 steps):

### Step 1: Target-Disease Evidence
- **Tool**: `OpenTargets_target_disease_evidence`
- **Input**: ensemblId=ENSG00000146648, efoId=EFO_0001074
- **Output**: Association scores, evidence types
- **Bridge**: gene symbol → Ensembl (from entity table above)

### Step 2: Drug-Target Mechanism
- **Tool**: `OpenTargets_get_drug_mechanism_of_action`
- **Input**: chemblId=CHEMBL3350488
- **Output**: MoA, target interactions
- **Bridge**: drug name → ChEMBL ID (from entity table)

### Step 3: Clinical Evidence
- **Tool**: `clinicaltrials-skill` → `search_clinical_trials`
- **Input**: condition=lung cancer, intervention=osimertinib
- **Output**: Active/completed trials

### Step 4: Resistance Mutations
- **Tool**: `clinvar_search_variants` + `cbioportal_get_mutations`
- **Input**: gene=EGFR, study=nsclc
- **Output**: T790M, C797S variants + clinical significance

**Fallbacks** (if any step fails):
- Step 1: `opentargets-skill` → fallback to `string-database` for PPI
- Step 3: `clinicaltrials-database` → fallback to `FDA_get_indications`

**Estimated time**: ~8 min | **Cost**: free (all API-based)
```

---

## Quick-Reference Domain → Chain Mapping

For the most common domain patterns, here are the pre-built chains:

| Domain Pattern | Chain ID | Key Skills/Tools |
|---|---|---|
| Drug target validation | `chain-clinic__precision-medicine` | OpenTargets + DrugBank + ChEMBL + clinicaltrials |
| Variant annotation | `chain-bio__variant-annotation` | clinvar + gnomAD + VEP + dbSNP |
| GWAS → gene | `chain-bio__gwas-pheno` | GWAS Catalog + eQTL + locus-to-gene |
| scRNA-seq analysis | `chain-bio__single-cell-rna` | scanpy + anndata + scvi-tools |
| Bulk RNA-seq | `chain-bio__bulk-rna-seq` | pydeseq2 + gsea + pathway enrichment |
| Literature review | `chain-lit__pubmed-europepmc` | PubMed + EuropePMC + Semantic Scholar |
| Cancer genomics | `chain-clinic__oncology` | cBioPortal + TCGA + COSMIC |
| Clinical guidelines | `chain-clinic__guidelines-evidence` | NICE + WHO + PubMed guidelines |
| ADMET prediction | `chain-clinic__drug-interaction` | ADMET AI + DrugBank + FAERS |
| Protein structure | `chain-bio__protein-structure` | AlphaFold + PDB + UniProt |
| Pathway enrichment | `chain-bio__pathway-enrichment` | GO + KEGG + Reactome + STRING |
| CRISPR design | `chain-bio__variant-calling` subset | design_sgrnas_by_gene + GuidePro |
| Writing/grants | `chain-paper__writing-intro` | scientific-writing + manuscript + research-grants |
| Visualization | `chain-vis__figure-publication` | scientific-visualization + matplotlib + seaborn |

---

## Interaction with Orchestrator Droid

For **deep multi-step tasks** (≥5 steps, ≥3 domains, error recovery needed), task-router outputs its plan and then **recommends spawning the `orchestrator` droid** to execute it:

```
**Deep orchestration recommended**: This task spans 3+ domains with 6+ steps.
Consider: spawn `orchestrator` droid with this plan for managed execution.
Command: Task subagent_type=orchestrator description="Execute drug-target analysis" prompt=<plan>
```

The orchestrator handles: context preservation across long chains, retry/fallback logic, progress tracking, and intermediate result validation.

---

## Invocation Patterns (tested & verified)

### How to Call MCP ToolUniverse Tools

MCP tools are invoked via `execute_tool` with **logical tool names** (no hash suffix needed):

```
# CORRECT — use the logical name from grep_tools/find_tools
execute_tool(tool_name="OpenTargets_get_disease_id_description_by_name", arguments={"diseaseName": "lung cancer"})

# INCORRECT — never use the hashed MCP function name
tooluniverse-literature___OpenTargets_get_disease_id_de_0cf6be4c(diseaseName="lung cancer")
```

**Discovery workflow**:
1. Use `grep_tools(pattern="keyword")` or `find_tools(query="description")` to discover tool names
2. Use `get_tool_info(tool_names="tool_name", detail_level="full")` to check required parameters
3. Use `execute_tool(tool_name="logical_name", arguments={...})` to invoke

### Known Required Parameters

Some tools have non-obvious required parameters that cause validation errors if omitted:

| Tool | Required Params | Notes |
|------|----------------|-------|
| `drugbank_vocab_search` | `search_fields` (list), `case_sensitive` (bool), `exact_match` (bool), `limit` (int) | Must specify which fields to search: `["Common name","Synonyms"]` |
| `ChEMBL_search_similar_molecules` | `similarity_threshold` (int 0-100), `max_results` (int) | Both required; threshold 80 is good default |
| `drugbank_full_search` | `search_fields` (list), `case_sensitive` (bool), `exact_match` (bool), `limit` (int) | Same pattern as vocab_search |
| `dict_search` / `dili_search` / `diqt_search` | `search_fields`, `case_sensitive`, `exact_match`, `limit` | All DrugBank-derived tools require these 4 |
| `search_clinical_trials` | `query_term` (required), `condition`/`intervention` optional | Use query_term for broad search |
| `OpenTargets_get_associated_drugs_by_disease_efoId` | `efoId` + `size` (int) | Size is required; use 50+ |
| `NICE_Clinical_Guidelines_Search` | `query` + `limit` | Both required |

### Known API Issues (as of 2026-05)

| Tool | Issue | Workaround |
|------|-------|-----------|
| `OpenTargets_get_associated_drugs_by_disease_efoId` | Returns null for all tested EFO IDs | Use `drugbank_vocab_search` → `drugbank_full_search` as fallback |
| `OpenTargets_get_associated_drugs_by_target_ensemblID` | Returns null for all tested Ensembl IDs | Same DrugBank fallback, or `ChEMBL_search_similar_molecules` |
| `OpenTargets_get_known_drugs_by_drug_chemblId` | Returns null for all tested ChEMBL IDs | Use `drugbank_vocab_search` by drug name instead |

### Fallback Chains for Drug Discovery

When OpenTargets drug endpoints return null, use this proven fallback:

```
Primary:   OpenTargets_get_associated_drugs_by_disease_efoId → NULL
Fallback:  drugbank_vocab_search(query="drug_name", search_fields=["Common name","Synonyms"], case_sensitive=false, exact_match=false, limit=10)
           → drugbank_full_search(query="DrugBank_ID", search_fields=["drugbank_id"], ...) for details
           → ChEMBL_search_similar_molecules(query="drug_name", similarity_threshold=80, max_results=5) for analogs
```

---

## Anti-patterns (don't do this)

- Don't execute the plan yourself — you ROUTE, the caller EXECUTES
- Don't list every possible tool — pick the top 1-2 per step
- Don't skip entity normalization — bad IDs cause downstream tool failures
- Don't ignore the chain system — pre-built chains are faster than ad-hoc assembly
- Don't generate plans for single-step tasks
- Don't omit fallback options for critical steps
- Don't use hardcoded skill/tool counts — always discover at runtime (system grows continuously)
- Don't present all 1,593+ skills to the user — rank and show top-3 per category

## Extensibility (auto-discovery)

The routing system is **fully dynamic** — new skills/tools automatically enter the system without manual SKILL.md updates:

| When | How it's discovered | What you do |
|------|---------------------|-------------|
| New gemini skill installed | Appears in `~/.gemini/skills/` | Filesystem scan in Phase 3 Source C finds it |
| New MCP tool registered | Appears in `grep_tools`/`find_tools` | Phase 3 Source B discovery finds it |
| New chain created | Appears in `~/.gemini/skills/_chains/` | Phase 3 Source A discovery finds it |
| Skill description updated | SKILL.md content changes | Grep-based ranking automatically adjusts |

**No manual maintenance required** — the routing pipeline always discovers the current state of the system at runtime.
