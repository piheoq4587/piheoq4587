---
name: MCP Registry v1
description: Maps tags/domains → MCP tool clusters. Parsed by skill_route.py to recommend MCPs alongside skills. Edit additions in canonical `~/.gemini/skills/_chains/MCP_REGISTRY.md` — 4-CLI junction propagates.
version: 1.0
created: 2026-05-22
canonical-path: ~/.gemini/skills/_chains/MCP_REGISTRY.md
parsed-by: skill_route.py recommend_mcps()
---

# MCP Registry — 自然语言 → 多 MCP 同时触发

## 一、解析规则

`skill_route.py` 读取本文件，按以下规则匹配：

1. **tag 精确匹配**：当 detect_domains() 返回 `(domain, sub)`，先查 `## tag: <domain>:<sub>` 段
2. **domain 兜底匹配**：tag 段未命中时，查 `## domain: <domain>` 段
3. **fire-all 模式**：当 Layer 4 标记 `parallel-compare` 时，把对应段下所有 MCP 全部输出，让用户选

每个 `- mcp__*` 行下可有 `  > <一行说明>` 缩进注释（解析器会保留作为提示）。

---

## 二、按 tag 精确匹配

### tag: lit:journal-radar
- mcp__scite__search_literature
  > Smart Citation strength + retraction flag — 唯一直接判断引用是否 supporting/contradicting
- mcp__scite__search_grants
  > 资助项目雷达
- mcp__tooluniverse-literature__advanced_literature_search_agent
  > 包装的检索 agent（处理意图）
- mcp__tooluniverse-literature__Unpaywall_check_oa_status
  > 开放获取状态检测
- Skill('retraction-watcher')
- Skill('smart-journal-monitor')
- Skill('journal-impact-factor-trend')
- Skill('journal-matchmaker')

### tag: lit:multi-source-search
- mcp__tooluniverse-literature__SemanticScholar_search_papers
  > 跨学科 + 引文图 + field-of-study 过滤
- mcp__tooluniverse-literature__openalex_literature_search
  > 全 disciplines + venue metadata
- mcp__tooluniverse-literature__PubMed_search_articles
  > 生医 + MeSH 检索
- mcp__tooluniverse-literature__EuropePMC_search_articles
  > 生医二线 + 全文索引
- mcp__tooluniverse-literature__ArXiv_search_papers
  > 物理 / CS / 数学预印本
- mcp__tooluniverse-literature__BioRxiv_search_preprints
  > 生物预印本
- mcp__tooluniverse-literature__MedRxiv_search_preprints
  > 医学预印本
- mcp__tooluniverse-literature__Crossref_search_works
  > DOI 元数据通用源
- Skill('wos-starter-search')
  > Web of Science Clarivate 收录权威核验
- Skill('yz-academic-search')
  > 7-源协调包装
- Skill('asta-skill')
  > Ai2 Asta intent → tool 路由

### tag: lit:asta-mcp
- Skill('asta-skill')
  > 需先单独注册 Asta MCP server（见 SKILL.md）

### tag: lit:citation-verify
- mcp__scite__search_literature
  > 验证引用 supporting/disputing
- mcp__tooluniverse-literature__Unpaywall_check_oa_status
- Skill('sc-fact-verification')
- Skill('sc-citation-analysis')

### tag: lit:wos-clarivate
- Skill('wos-starter-search')

### tag: paper:meta-analysis
- Skill('meta-rob2-plot')
- Skill('meta-funnel-plot')
- Skill('meta-forest-binary-plot')
- Skill('meta-forest-continuous-plot')
- Skill('meta-screening-fulltext')
- Skill('meta-baujat-plot')
- Skill('meta-picos-generator')
- Skill('meta-protocol-writer')
- Skill('INPLASY-registration-helper')
- Skill('prospero-registration-helper')
- Skill('rct-bias-assessment-rob2')
- Skill('sc-systematic-review')
- Skill('sc-meta-analysis')
- mcp__scite__search_literature
  > 验证 meta 收录文献的引用强度

### tag: paper:nature-submission
- Skill('garch-nature-figure')
- Skill('npb-figure')
- Skill('npb-citation')
- Skill('npb-reviewer-sim')
- Skill('npb-templates')
- Skill('yz-nature-figure')
- Skill('yz-nature-writing')
- Skill('yz-nature-response')
- Skill('springer-nature-paper-writing')

### tag: paper:workbench
- Skill('springer-nature-paper-writing')
  > Workbench-mode 唯一实现（21 templates + init script）

### tag: paper:ml-figures
- Skill('ml-paper-figures')

### tag: paper:ip-patent
- Skill('patent-claim-mapper')
- Skill('patent-landscape')
- Skill('patent-assistant')
- mcp__scite__search_patents
  > Smart Citation 专利检索
- Skill('uspto-database')

### tag: paper:reviewer-response
- Skill('rebuttal-letter-strategist')
- Skill('peer-review-response-drafter')
- Skill('response-letter')
- Skill('response-tone-polisher')
- Skill('npb-reviewer-sim')
- Skill('yz-nature-response')
- Skill('cs-review-response')

### tag: clinic:irb-ethics
- Skill('irb-application-assistant')
- Skill('iacuc-protocol-drafter')
- Skill('hipaa-compliance-auditor')
- Skill('medical-device-mdr-auditor')
- Skill('ectd-xml-compiler')
- Skill('blind-review-sanitizer')
- Skill('protocol-deviation-classifier')

### tag: clinic:clinical-writing
- Skill('discharge-summary-writer')
- Skill('automated-soap-note-generator')
- Skill('medical-scribe-dictation')
- Skill('virtual-patient-roleplay')
- Skill('unstructured-medical-text-miner')
- Skill('adverse-event-narrative')

### tag: stat:bias-assessment
- Skill('rct-bias-assessment-rob2')
- Skill('diagnostic-study-quality-assessment-quadas-2')
- Skill('probast-quality-assessment-for-prediction-model-studies')
- Skill('quapas-quality-assessment-for-prognosis-studies')
- Skill('cohort-study-quality-assessment-nos')
- Skill('Case-control-study-quality-assessment-nos')
- Skill('quality-assessment')

### tag: grant:nih-r01
- Skill('nih-biosketch-builder')
- Skill('grant-mock-reviewer')
- Skill('grant-budget-justification')
- Skill('dei-statement-drafter')
- Skill('academic-cv-generator')

---

## 三、按 domain 兜底匹配

### domain: lit
- mcp__scite__search_literature
- mcp__tooluniverse-literature__SemanticScholar_search_papers
- mcp__tooluniverse-literature__openalex_literature_search
- mcp__tooluniverse-literature__PubMed_search_articles
- mcp__tooluniverse-literature__advanced_literature_search_agent
- Skill('research-tool-router')
  > 强制 router（v1.1 §11）

### domain: bio
- mcp__tooluniverse-gene__ensembl_lookup_gene
- mcp__tooluniverse-gene__UniProt_search
- mcp__tooluniverse-gene__HPA_search_genes_by_query
- mcp__tooluniverse-gene__enrichr_gene_enrichment_analysis
- mcp__tooluniverse-genomics__gnomad_get_gene_constraints
- mcp__tooluniverse-genomics__GWAS_search_associations_by_gene
- mcp__tooluniverse-genomics__cBioPortal_get_cancer_studies
- mcp__tooluniverse-pathway__kegg_get_pathway_info
- mcp__tooluniverse-pathway__Reactome_get_pathway_reactions
- mcp__tooluniverse-pathway__WikiPathways_search
- mcp__tooluniverse-cell__HPA_get_rna_expression_in_specific_tissues
- mcp__tooluniverse-cell__cellosaurus_search_cell_lines

### domain: clinic
- mcp__tooluniverse-disease__clinvar_search_variants
- mcp__tooluniverse-disease__OpenTargets_target_disease_evidence
- mcp__tooluniverse-disease__cBioPortal_get_mutations
- mcp__tooluniverse-disease__OSL_get_efo_id_by_disease_name
- mcp__tooluniverse-disease__FAERS_search_adverse_event_reports
- mcp__tooluniverse-health__FDA_get_indications_by_drug_name
- mcp__tooluniverse-health__DailyMed_search_spls
- mcp__tooluniverse-health__NICE_Clinical_Guidelines_Search
- mcp__tooluniverse-health__WHO_Guidelines_Search
- mcp__tooluniverse-drug__drugbank_full_search
- mcp__tooluniverse-drug__ChEMBL_search_similar_molecules
- mcp__tooluniverse-drug__OpenTargets_get_drug_indications_by_chemblId

### domain: think
- Skill('scientific-critical-thinking')
- Skill('scout-mindset-bias-check')
- Skill('bayesian-reasoning-calibration')
- Skill('cognitive-fallacies-guard')
- Skill('layered-reasoning')
- Skill('dialectical-mapping-steelmanning')
- Skill('decomposition-reconstruction')
- Skill('hypothesis-generation')
- Skill('hypogenic')
- Skill('what-if-oracle')
- Skill('claim-strength-calibrator')
- Skill('evidence-level-ranker')
  > 纯 Skill 域，无对应 MCP

### domain: km
- mcp__infranodus__analyze_text
- mcp__infranodus__generate_content_gaps
- mcp__infranodus__develop_text_tool
- mcp__infranodus__develop_conceptual_bridges
- mcp__infranodus__generate_research_questions
- mcp__infranodus__retrieve_from_knowledge_base
- mcp__agentmemory__* (when reconnected)

### domain: ds
- mcp__Context7__resolve-library-id
- mcp__Context7__get-library-docs
  > Up-to-date Python/R/JS 库文档

### domain: paper
- mcp__scite__search_literature
  > 引用强度核验
- mcp__tooluniverse-literature__Unpaywall_check_oa_status
- Skill('research-tool-router')
- Skill('design-router')
  > 视觉/PPT/海报子任务时

### domain: grant
- mcp__scite__search_grants
- mcp__tooluniverse-literature__openalex_literature_search
  > 资助方向 + 同行 lab 检索

### domain: eng
- mcp__gitnexus__context
- mcp__gitnexus__impact
- mcp__gitnexus__query
- mcp__gitnexus__shape_check
- mcp__Context7__resolve-library-id
- Skill('karpathy-guidelines')
  > 强制 router（v1.1 §11）

### domain: meta
- mcp__mcp-registry__list_connectors
- mcp__mcp-registry__search_mcp_registry
- mcp__mcp-registry__suggest_connectors
- mcp__prompts-chat__search_skills
- mcp__prompts-chat__search_prompts

---

## 四、Parallel-fire 默认配置

当 funnel 判定为 `parallel-compare` 模式（≥2 个候选 chain 且无依赖），以下 MCP cluster **必须同时发起**：

### lit-default-trio→quintet (literature ensemble · v1.2 升级 5 路)
```
mcp__tooluniverse-literature__SemanticScholar_search_papers     # 引文图 + field-of-study
mcp__tooluniverse-literature__openalex_literature_search        # 全 disciplines + venue metadata
Skill('wos-starter-search')                                     # WoS Clarivate 收录权威
mcp__scite__search_literature                                   # 引用强度 + 撤稿信号 ★新增
mcp__tooluniverse-literature__advanced_literature_search_agent  # intent agent ★新增
```

### bio-ensemble (multi-omics quick lookup)
```
mcp__tooluniverse-gene__ensembl_lookup_gene
mcp__tooluniverse-genomics__GWAS_search_associations_by_gene
mcp__tooluniverse-disease__OpenTargets_target_disease_evidence
mcp__tooluniverse-pathway__kegg_get_pathway_info
```

### clinic-ensemble (precision-medicine quick lookup)
```
mcp__tooluniverse-disease__clinvar_search_variants
mcp__tooluniverse-disease__OpenTargets_target_disease_evidence
mcp__tooluniverse-health__FDA_get_indications_by_drug_name
mcp__tooluniverse-drug__drugbank_full_search
```

---

## 五、连接状态备注

某些 MCP 当前可能 disconnected。`skill_route.py` 不检查在线状态，只列出 registry 中的清单 — 实际调用失败时按协议 §12 fallback 链走，并在 §14 输出模板 "失败或降级" 段记录。

**易失联 MCP**（按经验）：
- `mcp__scite__*` — 偶尔断连
- `mcp__agentmemory__*` — 取决于本地 :3111 服务
- `mcp__chrome-devtools__*` — 需要 Chrome 启动 + 扩展
- `mcp__gitnexus__*` — 需要 group_sync 一次

**always-on**：tooluniverse-*, Context7, prompts-chat, mcp-registry
