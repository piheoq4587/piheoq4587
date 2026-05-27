---
chain-domain: science-core
chain-type: curated-prelist
member-count: 38
default-mode: always-on-prelist
created: 2026-05-22
purpose: 科研任务中"最高 ROI"的思维 + 文献 + 元方法 skill + 强 MCP cluster。任何科研类任务（研究/规划/调研/写论文/标书/综述）funnel 时优先考虑这批。
---

# Chain: science-core

**预加载策略**：当用户消息含科研触发词（研究/规划/设计/调研/写论文/标书/投稿/综述/实验方案/数据分析/类器官/流式/单细胞/scRNA/GWAS/MR/NSFC/TIM/科研问题/思路/idea/hypothesis），funnel **必须**先扫一遍这批，再做 domain-specific routing。

3 个 cluster + 1 个 MCP 集群。

---

## 🧠 Cluster A · 推理 + 思维核心 (12)

科研任何阶段都可能需要的思维护栏。命中"判断/决定/思考/反思/check/校准/反例/对照"等关键词时优先：

- `scientific-critical-thinking` — 科研批判性思维总览
- `scout-mindset-bias-check` — Galef 童子军心态偏倚检查
- `bayesian-reasoning-calibration` — 贝叶斯更新 + 置信度校准
- `cognitive-fallacies-guard` — 27 种思维谬误自查
- `layered-reasoning` — 分层推理（事实/解读/价值）
- `dialectical-mapping-steelmanning` — 对立观点对抗映射
- `decomposition-reconstruction` — 拆解-重组
- `hypothesis-generation` — 假设生成
- `hypogenic` — 假设生成升级版（LLM-augmented）
- `what-if-oracle` — 反事实推演
- `propose-counterfactual` — 反事实命题构造
- `claim-strength-calibrator` — 论断强度校准 (aipoch T-extra)

---

## 📚 Cluster B · 文献综合核心 (10)

任何需要"读文献、综述、引用、验证、检索"的研究都必经：

- `sc-systematic-review` — 系统综述方法学
- `sc-meta-analysis` — meta 统计
- `sc-fact-verification` — 引文事实核查
- `sc-scholar-evaluation` — 学者评估
- `sc-citation-analysis` — 引文链分析
- `sc-reproducibility-checklist` — 可复现性
- `sc-asreview-screening` — AI 辅助筛选
- `lit-synthesizer` — 文献综合
- `research-tool-router` — 工具路由（v1.1 mandatory router gate）
- `literature-scout` — 文献侦察兵（默认 trio: S2 + OpenAlex + WoS）

---

## 🔬 Cluster C · 元方法 + 期刊投稿 (8)

新装 120 中筛出最有"独占价值"的：

- `karpathy-guidelines` — 工程优先级（v1.1 mandatory router）
- `verification-before-completion` — 完成前验证
- `systematic-debugging` — 系统化调试
- `evidence-level-ranker` — 证据等级排序 (aipoch T-extra)
- **`springer-nature-paper-writing`** — workbench 模式最强（21 模板 + init script）
- **`garch-nature-figure`** — Nature 配图哲学最强（claim→archetype→backend gate）
- **`meta-rob2-plot`** — SR/MA 必备
- **`retraction-watcher`** — 撤稿监控（仅此一家）

---

## 🛠️ Cluster D · 强 MCP cluster (5 群)

每个 cluster ≈ 几十到上百个 MCP tool。任务命中科研意图时直接走对应 cluster：

### tooluniverse 全栈 (600+ tools / 15 servers)
Harvard 蒸馏的科研全栈，分 15 server：
```
tooluniverse-literature   — PubMed/Scholar/arXiv/Crossref/EuropePMC/bioRxiv/medRxiv
tooluniverse-gene         — UniProt/HPA/Ensembl/enrichr/dbsnp/jaspar
tooluniverse-disease      — clinvar/OpenTargets/cBioPortal/FAERS/Monarch
tooluniverse-drug         — drugbank/chembl/ADMETAI/FDA labels
tooluniverse-genomics     — gnomad/GWAS Catalog/ENCODE/GTEx/cBioPortal
tooluniverse-pathway      — KEGG/Reactome/WikiPathways/HumanBase PPI
tooluniverse-cell         — cellosaurus/cellxgene/HPA/biopython
tooluniverse-ontology     — OLS/MeSH/HPO/EFO/GO/MedlinePlus
tooluniverse-health       — FDA/DailyMed/NICE/WHO/CMA guidelines
```

### infranodus (知识图谱 + content gaps + bridges)
```
mcp__infranodus__analyze_text                    — 文本 → 图
mcp__infranodus__generate_content_gaps           — 主题空缺
mcp__infranodus__develop_conceptual_bridges      — 概念桥
mcp__infranodus__generate_research_questions     — 研究问题
mcp__infranodus__retrieve_from_knowledge_base    — GraphRAG
```

### scite (引文证据强度)
```
mcp__scite__search_literature      — supporting/disputing/mentioning
mcp__scite__search_clinical_trials
mcp__scite__search_grants
mcp__scite__search_patents
mcp__scite__get_clinical_trial / _grant / _maude_report
```

### agentmemory (episodic memory)
跨 CLI 共享，4 处配置好（claude/codex/copilot/desktop）：
```
http://localhost:3111 + iii.exe v0.11.2
agentmemory-bridge skill — 把 episodic → MEMORY v2 蒸馏
```

### gitnexus (代码图谱)
```
mcp__gitnexus__list_repos / group_sync / context / impact / query
mcp__gitnexus__shape_check / api_impact / route_map / detect_changes
```

---

## 何时由 funnel 调用本 chain

`skill_route.py` 在 Layer 2 之前**永远先扫这个 chain**（实现见 `skill_route.py` 后续 v3 升级，未实现时由 user/CLI 手动加载）。

只要满足**任一**：
- 任务关键词含「研究 / 规划 / 设计 / 调研 / 写论文 / 标书 / 投稿 / 综述 / 实验方案 / 数据分析 / 思路 / hypothesis」
- 跨 ≥2 域且至少 1 域是 bio/clinic/lit/paper
- Tier-L 任务

→ **Cluster A 必走**（思维护栏）+ **Cluster B 至少 1 个**（文献基础）+ **Cluster D 对应 MCP cluster**（数据后端）+ Cluster C 按需。

---

## "用得多 = 更聪明"机制

本 chain 的成员在 Phase 5B 的 `_metrics.jsonl` 里独占"science-core-bonus"字段，调用频次 / 用户评分进入 `chain_select.py` 第 4 维重排。频繁使用的 skill 排序自动上浮。
