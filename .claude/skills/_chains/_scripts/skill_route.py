#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
skill_route.py — 一键 Skill Funnel

接任意 query,输出:
  Layer 1: detected domains
  Layer 2: candidate chains
  Layer 3: precision-select strategy (按 member-count)
  Layer 4: pipeline match
  Layer 5: recommended skills

用法:
  python ~/.gemini/skills/_chains/_scripts/skill_route.py "<任务描述>"
  python ~/.gemini/skills/_chains/_scripts/skill_route.py --json "<任务描述>"

输出: stdout 人类可读 + (option) jsonl 元数据.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from collections import Counter

# Force UTF-8 stdout on Windows (GBK default breaks Chinese + Unicode marks)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CHAINS_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
PIPELINES_FILE = SCRIPTS_DIR / "pipelines.json"
MCP_REGISTRY_FILE = CHAINS_DIR / "MCP_REGISTRY.md"
WISDOM_INDEX_FILE = Path.home() / ".claude" / "projects" / "C--Users-Administrator" / "memory" / "wisdom" / "INDEX.md"
# 道智触发词：用户明确指定的关键词集合
DAOZHI_TRIGGERS = re.compile(
    # 中文单字/词
    r"(道|术|智慧|本质|原则|架构|思路|"
    # 决策类
    r"决策|决定|抉择|选择|"
    # "怎么"问句
    r"怎么办|怎么处理|该怎么做|如何决定|怎么想|怎么选|怎么判断|"
    # 智慧库相关查询
    r"用什么智慧|用什么思路|用什么方法|用什么框架|"
    # 英文等价
    r"decision|principle|framework|approach|mental.{0,2}model|"
    r"how.{0,3}(decide|choose|approach)|what.{0,3}(framework|principle))",
    re.IGNORECASE,
)

# ============================================================
# §1. Trigger Word → Domain Mapping (汇总自 reference_skill_chain_system_v1.md)
# ============================================================
TRIGGER_TABLE = {
    # bio
    r"(单细胞|scRNA|scATAC|10x|multiome)": ["bio", "single-cell-rna"],
    r"((?-i:\bGWAS\b|\bMR\b)|fine-mapping|colocalization|孟德尔|two-sample MR)": ["bio", "mr-causal-genomics"],
    r"(ChIP-seq|ATAC-seq|CLIP-seq|peak calling)": ["bio", "bulk-chip-seq"],
    r"(RNA-seq|DEG|deseq2|edgeR|差异基因)": ["bio", "bulk-rna-seq"],
    r"(变异|VCF|variant|MAF|突变)": ["bio", "variant-calling"],
    r"((?-i:\bHLA\b|\bTMB\b|\bMSI\b)|signature|突变签名)": ["bio", "tmb-msi"],
    r"(cfDNA|ctDNA|液体活检|液体活检)": ["bio", "liquid-biopsy-cfdna"],
    r"(单细胞|流式|CyTOF|质谱流式|mass cytometry)": ["bio", "single-cell-rna"],
    r"((?-i:\bIMC\b)|imaging mass|空间蛋白|spatial proteomics)": ["bio", "imaging-genomics"],
    r"(类器官|organoid|3D 培养)": ["bio", "single-cell-perturb"],
    r"(代谢组|metabolomics|脂质组)": ["bio", "metabolomics"],
    r"(蛋白组|proteomics|外泌体|exosome)": ["bio", "proteomics"],
    r"(微生物组|肠道菌|microbiome|16S)": ["bio", "microbiome"],
    r"(CAR-T|T 细胞工程)": ["bio", "cart-design"],
    r"(抗体设计|antibody|nanobody)": ["bio", "antibody-design"],
    r"(蛋白结构|AlphaFold|结构预测|docking)": ["bio", "protein-structure"],
    r"(通路|enrichment|KEGG|reactome|GSEA)": ["bio", "pathway-enrichment"],
    # clinic
    r"(脓毒症|sepsis|ICU|重症)": ["clinic", "icu-sepsis"],
    r"(肿瘤|cancer|oncology|化疗)": ["clinic", "oncology"],
    r"(心血管|心肌|cardio|血栓)": ["clinic", "cardiovascular"],
    r"(影像|radiology|(?-i:\bCT\b|\bMRI\b)|放射)": ["clinic", "imaging-radiology"],
    r"(病理|pathology|组织切片|HE 染色)": ["clinic", "pathology"],
    r"(指南|guideline|GIN|NICE|WHO|证据)": ["clinic", "guidelines-evidence"],
    r"(药物相互作用|drug.interaction|DDI)": ["clinic", "drug-interaction"],
    r"(临床试验|clinical trial|RCT|protocol)": ["clinic", "clinical-trial-design"],
    r"(罕见病|rare disease|遗传病)": ["clinic", "rare-disease"],
    r"(精准医学|precision medicine|分层治疗)": ["clinic", "precision-medicine"],
    r"(神经|neuro|脑|脊髓)": ["clinic", "neurology"],
    r"(骨科|脊柱|orthop|spine)": ["clinic", "orthopedics-spine"],
    # stat
    r"(回归|regression|因果|causal|双重差分|断点回归|(?-i:\bDID\b|\bRD\b|\bTMLE\b))": ["stat", None],
    r"(生存分析|survival|Cox|KM)": ["stat", None],
    r"(贝叶斯|Bayesian|MCMC)": ["stat", None],
    r"(meta|系统综述|PRISMA|systematic review)": ["paper", "writing-methods"],
    # ds
    r"(R 实证|tidyverse|fixest|Quarto)": ["ds", "r-tidyverse"],
    r"(Python pandas|sklearn|scikit-learn)": ["ds", "python-pandas"],
    r"(Python 科学计算|scipy|numpy)": ["ds", "python-scientific"],
    r"(Stata|\.do)": ["ds", "stata-do"],
    r"(matplotlib|可视化|绘图)": ["ds", "viz-matplotlib"],
    r"(ggplot|tidy plot)": ["ds", "viz-ggplot"],
    r"(plotly|交互图)": ["ds", "viz-plotly"],
    r"(jupyter|notebook|ipynb)": ["ds", "notebook-jupyter"],
    r"(quarto|rmarkdown)": ["ds", "notebook-quarto-rmd"],
    # lit
    r"(文献检索|scholar|openalex|pubmed)": ["lit", None],
    r"(CNKI|知网|中文文献)": ["lit", "cnki-chinese"],
    r"(每日学术|晨报|paper digest|每日雷达)": ["lit", "daily-radar"],
    r"(预印本|preprint|biorxiv|medrxiv)": ["lit", None],
    r"(引用|citation|fact check|假引用)": ["lit", "citation-verify"],
    # paper
    r"(论文|paper|manuscript|草稿|稿件)": ["paper", None],
    r"(投稿|submit|cover letter)": ["paper", "submission"],
    r"(审稿|reviewer|rebuttal|return|返修)": ["paper", "reviewer-response"],
    r"(自审|自查|self-review|质量)": ["paper", "self-review"],
    r"(图表|figure|publication chart)": ["paper", None],
    r"(立题|ideation|research question)": ["paper", "writing-strategy"],
    r"(综述|review|narrative review)": ["paper", "writing-methods"],
    r"(TIM|龙华期刊|Translational Integrative Medicine)": ["paper", "tim-submission"],
    # antiAI
    r"(降 ?AI 率|AI 检测|aigc|GPTzero)": ["antiAI", None],
    r"(humanize|去 AI 味|deslop|stop slop)": ["antiAI", "deslop"],
    # grant
    r"(NSFC|国自然|标书|面上项目|青年基金|重点研发)": ["grant", "nsfc-cn"],
    r"(NIH|R01|grant proposal)": ["grant", "nih"],
    r"(合作方案|cooperation|MoU|联合实验室)": ["grant", "research-proposal"],
    # km
    r"(Obsidian|vault|MD 笔记)": ["km", "obsidian"],
    r"(InfraNodus|知识图谱|图谱)": ["km", "infranodus-graph"],
    r"(记忆蒸馏|dreaming sweep|long memory)": ["km", "memory-distill"],
    # eng
    r"(写代码|debug|bug|fix|TDD)": ["eng", "daily-coding"],
    r"(数据库|SQL|schema)": ["eng", "database-design"],
    r"(安全|security|渗透|审计)": ["eng", "security-audit"],
    r"(测试|pytest|jest|test automation)": ["eng", "test-automation"],
    r"(CI/CD|github actions|jenkins|deploy)": ["eng", "ci-cd"],
    r"(性能|profiling|benchmark|监控)": ["eng", "performance-profiling"],
    r"(API 设计|REST|GraphQL)": ["eng", "api-design"],
    r"(架构|architecture|系统设计)": ["eng", "architecture-design"],
    r"(前端|UI|UX|React|Vue)": ["eng", "frontend-design"],
    r"(git|分支|merge|rebase)": ["eng", "git-workflow"],
    r"(重构|refactor)": ["eng", "refactoring"],
    # vis
    r"(PPT|slides|幻灯|演示)": ["vis", "slides-pptx"],
    r"(海报|poster|宣传图)": ["vis", "posters"],
    r"(网页|HTML|landing page|web design)": ["vis", "web-design"],
    r"(图|diagram|流程图|架构图|drawio|mermaid)": ["vis", "diagrams"],
    r"(Word|docx|文档生成)": ["vis", "docx-word"],
    # think / meta / dao
    r"(决策|reasoning|思维|矩阵)": ["think", None],
    r"(skill 系统|skill audit|skill 整理)": ["meta", "skill-audit"],
    r"(易学|yixue|八字|道术|laozi)": ["dao", None],
    # research / planning generic (fallback)
    r"(研究|规划|设计|调研|实验方案)": ["paper", "writing-strategy"],

    # ============================================================
    # § v2 增量 (2026-05-22) — 120 新 skill 触发覆盖
    # ============================================================
    # Meta-analysis / SR (32 skill cluster)
    r"(meta.?(analysis|分析)|系统综述|SR/MA|森林图|forest plot|漏斗图|funnel plot|Baujat|PICOS|sensitivity analysis|敏感性分析|risk of bias|偏倚风险|RoB2?)": ["paper", "meta-analysis"],
    r"(PRISMA|PROSPERO|INPLASY|SR (注册|register))": ["paper", "meta-analysis"],
    r"(QUADAS|PROBAST|QUAPAS|NOS quality|质量评估|偏倚评估|bias assessment)": ["stat", "bias-assessment"],

    # Nature 系列投稿（12 skill cluster）
    r"(Nature(.{0,5})(Communications|Comm|Med|Methods)|顶刊投稿|nature 子刊|nature 系列)": ["paper", "nature-submission"],
    r"(Springer.{0,3}Nature|SciAdv|二轮返修|second.round)": ["paper", "nature-submission"],
    r"(workbench (模式|init|启动)|paper-workbench|双线程审稿|init_workbench)": ["paper", "workbench"],
    r"(NMI pastel|nature 配色|Nature.{0,5}figure|顶刊配图)": ["paper", "nature-submission"],

    # ML/AI 论文配图（NeurIPS / ICML）
    r"(NeurIPS|ICML|AAAI|ACL|EMNLP|ICLR|ml.?paper.?figure|ablation.?图|scaling.?law|hero.?figure|Pareto.{0,5}frontier|training.?dynamics|qualitative.?samples)": ["paper", "ml-figures"],

    # Figure polish (8+5 skill cluster)
    r"(volcano|火山图|火山plot)": ["paper", "tables-figures"],
    r"(heatmap.?(美化|polish|风格))": ["paper", "tables-figures"],
    r"(circos|环形.?(图|基因组))": ["paper", "tables-figures"],
    r"(western.?blot|印迹定量|condensed bands)": ["paper", "tables-figures"],
    r"(microscopy.?scale|显微.?(标尺|scale bar)|microscopy.?bar)": ["paper", "tables-figures"],
    r"(FACS.?gating|流式 gating|gating.?(style|viz))": ["paper", "tables-figures"],
    r"(pseudotime.?(trajectory|viz)|拟时序.?可视化)": ["paper", "tables-figures"],
    r"(DPI.?(升|upscale|提升)|分辨率不够|图.?(模糊|升 dpi))": ["paper", "tables-figures"],
    r"(graphical abstract|图形摘要|视觉摘要)": ["paper", "tables-figures"],
    r"(mechanism flowchart|机制流程|signaling.?cascade)": ["paper", "tables-figures"],

    # Journal radar (7 skill cluster)
    r"(撤稿|retraction|retracted paper)": ["lit", "journal-radar"],
    r"(期刊.?(雷达|监控|monitor)|journal.?monitor|smart journal)": ["lit", "journal-radar"],
    r"(IF.?(趋势|追踪)|impact factor.?(trend|trajectory)|JCR.?分区|影响因子.?变化)": ["lit", "journal-radar"],
    r"(emerging topic|新兴主题|topic.?scout|hot.?topic)": ["lit", "journal-radar"],
    r"(competitor.?trial|竞品.?(试验|临床)|funding.?(forecast|trend)|keyword.?velocity)": ["lit", "journal-radar"],
    r"(translational.?gap|临床.?转化.?(差距|gap)|target.?novelty)": ["lit", "journal-radar"],

    # Multi-source literature search (3 skill cluster)
    r"(WoS|Web of Science|Clarivate|Scopus|多源(检索|文献)|7 ?源|six-source|six.?database)": ["lit", "multi-source-search"],
    r"(Asta|Ai2 Asta|Allen AI|S2 intent)": ["lit", "asta-mcp"],

    # Patent (3 skill cluster)
    r"(专利|patent|claim chart|权利要求|patent.?landscape|IP.?(分析|landscape))": ["paper", "ip-patent"],

    # IRB / ethics / compliance (7 skill cluster)
    r"(IRB|IACUC|HIPAA|MDR|FDA.?MDR|伦理.?(审批|申请)|动物伦理|医疗器械.?合规|eCTD)": ["clinic", "irb-ethics"],

    # NIH grant + CV (5 skill cluster)
    r"(NIH|biosketch|R01|K99|F32|预算.?(说明|justification)|grant.?mock|DEI statement)": ["grant", "nih-r01"],
    r"(学术.?CV|academic.?CV|medical.?CV|medical-cv-resume)": ["grant", "research-proposal"],

    # Rebuttal / reviewer response (5 skill cluster)
    r"(rebuttal|审稿(回复|响应)|response.?letter|reviewer.?response|返修信|逐条回复|q.?and.?a.?prep)": ["paper", "reviewer-response"],

    # Clinical writing (6 skill cluster)
    r"(SOAP|discharge.?summary|出院.?(小结|总结)|adverse.?event.?(narrative|叙述)|临床.?记录.?(挖|miner)|virtual.?patient)": ["clinic", "clinical-writing"],

    # Research planners (5 skill cluster)
    r"(MR.?(planner|研究规划)|两样本 MR|FAERS.?planner|网络.?毒理.?docking|多组学.?ML)": ["paper", "protocol-design"],

    # ============================================================
    # § v3 增量 (2026-05-24) — AHE + Ctx2Skill + SkVM 三层
    # ============================================================
    # Phase 1: AHE 嫁接 (harness-evolution skill)
    r"(harness.?(evolution|进化|演化|证伪)|AHE|跑.?harness|verify.?prediction|验证.?prediction|harness.?report)": ["meta", "harness-evolution"],
    r"(预测.?验证|prediction.?verification|可证伪契约|falsifiable contract)": ["meta", "harness-evolution"],
    r"(decision.?observability|component.?observability|experience.?observability)": ["meta", "harness-evolution"],

    # Phase 2: Ctx2Skill 复刻 (ctx2skill skill)
    r"(ctx2skill|context.?to.?skill|上下文.?(转|→|抽).?skill|从.{0,8}(文档|论文|manual|codebase).?(蒸馏|抽取|提取).?skill)": ["meta", "ctx2skill"],
    r"(self.?play.?(loop|循环)|多 agent 自博弈|challenger.?reasoner.?judge)": ["meta", "ctx2skill"],
    r"(Cross.?Time.?Replay|cross-time replay|历史版本.?回放)": ["meta", "ctx2skill"],

    # 🆕 Skill Generation Auto-Dispatcher (2026-05-24, feedback_skill_creation_auto_dispatch)
    # 用户说"把/将/帮我把 X 变成 skill"等自然语言时，自动 dispatch 到正确工具
    # Dispatcher 在 Claude session 层做（看输入大小选 ctx2skill vs daozhi-distill）
    r"((把|将|帮我把|帮我).{0,10}(文章|论文|文档|paper|manual|代码|材料|内容).{0,10}(变|转|做|生成|抽).{0,5}(成|为)?.{0,3}skill)": ["meta", "ctx2skill"],
    r"(从.{0,10}(文章|论文|文档|paper|manual|代码|材料).{0,5}(生成|提取|抽出|蒸馏|做出|做成).{0,5}skill)": ["meta", "ctx2skill"],
    r"(把.{0,5}(这|这篇|这段|这个).{0,10}(变|转|做|生成).{0,5}skill)": ["meta", "ctx2skill"],
    r"(extract.?skill(s)?.?from|generate.?skill.?from|distill.?.{0,20}into.?skill|turn.?.{0,20}into.?(a|some|reusable)?.?skill|convert.?.{0,15}to.?skill|create.?skill.?from)": ["meta", "ctx2skill"],
    r"((把|帮我).{0,15}(变|转|做).{0,3}(可复用|reusable).?skill)": ["meta", "ctx2skill"],

    # Phase 3: SkVM 编译/运行时 (跨域，eng + meta)
    r"(SkVM|skill.?(compiler|编译器|VM)|skill.?(profiling|分析|画像)|AOT.?compile|JIT.?compile)": ["meta", "skvm"],
    r"(跨 LLM.?optimization|skill.?跨平台|skill.?执行优化|skill.?runtime)": ["meta", "skvm"],
}


def detect_domains(query: str):
    """Layer 1: domain matching"""
    domains = Counter()
    matched_chains = set()
    for pattern, (domain, sub) in TRIGGER_TABLE.items():
        if re.search(pattern, query, re.IGNORECASE):
            domains[domain] += 1
            if sub:
                matched_chains.add(f"chain-{domain}__{sub}")
    return domains, matched_chains


def find_chains(query: str, candidate_chain_names: set):
    """Layer 2: tag chain opening. Trigger-hits sorted before keyword-hits."""
    chains = []
    for chain_path in sorted(CHAINS_DIR.glob("chain-*.md")):
        name = chain_path.stem
        try:
            text = chain_path.read_text(encoding="utf-8")
            m = re.search(r"member-count:\s*(\d+)", text)
            count = int(m.group(1)) if m else None
        except Exception:
            count = None

        in_candidates = name in candidate_chain_names
        chain_name_keywords = name.replace("chain-", "").replace("__", " ").replace("-", " ")
        keyword_hit = any(kw in query.lower() for kw in chain_name_keywords.split() if len(kw) > 3)

        if in_candidates or keyword_hit:
            chains.append({
                "name": name,
                "path": str(chain_path),
                "member_count": count,
                "via": "trigger" if in_candidates else "keyword",
            })
    # Sort: trigger-hits first (explicit TRIGGER_TABLE match wins over weak keyword name match)
    chains.sort(key=lambda c: (0 if c["via"] == "trigger" else 1, c["name"]))
    return chains


def precision_strategy(member_count):
    """Layer 3: precision select"""
    if member_count is None:
        return "menu (count unknown — read chain file directly)"
    if member_count <= 5:
        return "menu (list all)"
    if member_count <= 15:
        return "menu + 1-line description"
    if member_count <= 50:
        return "chain_select.py LLM rerank top-5"
    return "ask-questions narrow"


def _trigger_matches(trigger: str, query_lower: str) -> bool:
    """Match trigger against query with word-boundary guard for ASCII triggers.

    Pure ASCII triggers (e.g. 'RD', 'DID', 'fixest') require word boundary so
    'Word' does NOT trigger 'RD'. CJK / non-ASCII triggers use substring.
    """
    t_low = trigger.lower().strip()
    if not t_low:
        return False
    if all(ord(c) < 128 for c in t_low):
        pattern = r'(?<![a-zA-Z0-9_])' + re.escape(t_low) + r'(?![a-zA-Z0-9_])'
        return re.search(pattern, query_lower) is not None
    return t_low in query_lower


def match_pipeline(query: str):
    """Layer 4: pipeline match"""
    if not PIPELINES_FILE.exists():
        return None, 0.0
    pipelines = json.loads(PIPELINES_FILE.read_text(encoding="utf-8")).get("pipelines", {})
    q_low = query.lower()
    best_id, best_score = None, 0
    for pid, p in pipelines.items():
        triggers = p.get("trigger_phrases", [])
        score = sum(1 for t in triggers if _trigger_matches(t, q_low))
        if score > best_score:
            best_id, best_score = pid, score
    if best_id:
        ratio = best_score / max(len(pipelines[best_id].get("trigger_phrases", [1])), 1)
        return {"id": best_id, "label": pipelines[best_id]["label"],
                "trigger_hits": best_score, "match_ratio": round(ratio, 2)}, ratio
    return None, 0.0


def _parse_mcp_registry():
    """Parse MCP_REGISTRY.md into {tag_or_domain_key: [mcp_or_skill_lines]}.
    Returns dict where keys are 'tag:<tag>' or 'domain:<domain>' or 'cluster:<name>'."""
    if not MCP_REGISTRY_FILE.exists():
        return {}
    text = MCP_REGISTRY_FILE.read_text(encoding="utf-8", errors="ignore")
    sections = {}
    # Match sections: ### tag: X / ### domain: X / ### cluster-name (under "## Parallel-fire")
    pattern = re.compile(
        r"^###\s+(tag:\s*[^\n]+|domain:\s*\w+|[\w-]+\s*\([^\)]+\))",
        re.MULTILINE
    )
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        header = m.group(1).strip().lower()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        body = text[start:end]
        items = re.findall(r"^-\s+([^\n]+)", body, re.MULTILINE)
        # strip annotation lines that start with '>'
        items = [it.strip() for it in items if not it.strip().startswith(">")]
        # normalize key
        if header.startswith("tag:"):
            key = "tag:" + header.split(":", 1)[1].strip()
        elif header.startswith("domain:"):
            key = "domain:" + header.split(":", 1)[1].strip()
        else:
            key = "cluster:" + header
        sections[key] = items
    return sections


def recommend_mcps(domains, candidate_chain_names):
    """Layer 5b: collect MCP/Skill recommendations from MCP_REGISTRY.md.
    Returns list of unique items in priority order: tag-specific first, then domain fallback."""
    registry = _parse_mcp_registry()
    seen = set()
    result = []

    # 1. tag-specific (highest priority)
    for chain_name in candidate_chain_names:
        # chain-<domain>__<sub> → tag <domain>:<sub>
        m = re.match(r"chain-(\w+)__(.+)$", chain_name)
        if not m:
            continue
        tag_key = f"tag:{m.group(1)}:{m.group(2)}"
        if tag_key in registry:
            for item in registry[tag_key]:
                if item not in seen:
                    seen.add(item)
                    result.append((tag_key, item))

    # 2. domain fallback (if tag didn't match anything for that domain)
    for d, _ in domains.most_common():
        domain_key = f"domain:{d}"
        if domain_key in registry:
            for item in registry[domain_key]:
                if item not in seen:
                    seen.add(item)
                    result.append((domain_key, item))

    return result


def recommend_daozhi(query):
    """Layer 5c: read wisdom INDEX.md → return top-5 applicable daozhi entries.
    Returns [] if query doesn't contain daozhi triggers (不打扰)."""
    if not DAOZHI_TRIGGERS.search(query or ""):
        return []
    if not WISDOM_INDEX_FILE.exists():
        return []
    text = WISDOM_INDEX_FILE.read_text(encoding="utf-8", errors="ignore")
    # Parse "By Trigger Keyword" table: lines like "| keyword | wisdom_id, ... |"
    candidates = {}  # wisdom_id → score
    # 1. Trigger keyword exact match
    for m in re.finditer(r"\*\s*\*([^*]+)\*\*\s*\|\s*([^\n|]+)", text):
        # legacy pattern, fallback
        pass
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("| "): continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 2: continue
        kws, wids = parts[0], parts[1]
        # extract chinese / english keywords
        kw_tokens = re.split(r"[/\s,，、]+", kws.replace("**", ""))
        for kw in kw_tokens:
            kw = kw.strip().lower()
            if kw and len(kw) >= 2 and kw in query.lower():
                for wid in re.findall(r"(wisdom-[\w-]+|dao-[\w-]+)", wids):
                    candidates[wid] = candidates.get(wid, 0) + 3
    # 2. Also extract all wisdom entries from "## By Type" and give baseline +1 if domain matches
    all_wisdoms = re.findall(r"\*\*(wisdom-[\w-]+)\*\*\s*·\s*([^·\n]+)·\s*`\[([^\]]+)\]`", text)
    for wid, name, doms in all_wisdoms:
        doms_list = [d.strip() for d in doms.split(",")]
        for d in doms_list:
            if d.lower() in query.lower():
                candidates[wid] = candidates.get(wid, 0) + 1
    # Sort by score desc, take top 5
    top = sorted(candidates.items(), key=lambda x: -x[1])[:5]
    # Pull one-line "name" for each
    result = []
    for wid, score in top:
        # find name in text
        m = re.search(rf"\*\*{re.escape(wid)}\*\*\s*·\s*([^·\n]+)", text)
        nm = m.group(1).strip() if m else wid
        result.append({"id": wid, "name": nm, "score": score})
    return result


def recommend_skills(domains, chains, pipeline):
    """Layer 5: recommended skill list"""
    rec = []
    if pipeline:
        # if pipeline match, walk steps
        if PIPELINES_FILE.exists():
            pipelines = json.loads(PIPELINES_FILE.read_text(encoding="utf-8")).get("pipelines", {})
            for step in pipelines[pipeline["id"]].get("steps", []):
                role = step.get("role", "?")
                # Step may declare 'skills' (skill list), 'tool' (raw command),
                # or 'chain' (sub-chain reference).
                if "skills" in step:
                    rec.append({"role": role, "skills": step["skills"],
                                "select": step.get("select", "menu")})
                elif "tool" in step:
                    rec.append({"role": role, "tool": step["tool"],
                                "select": step.get("select", "tool")})
                elif "chain" in step:
                    rec.append({"role": role, "chain": step["chain"],
                                "select": step.get("select", "menu")})
                else:
                    rec.append({"role": role, "skills": [],
                                "select": step.get("select", "menu")})
    else:
        # no pipeline → show top chains' first member if known
        for ch in chains[:5]:
            rec.append({"role": ch["name"], "chain_path": ch["path"], "select": "menu"})
    return rec


def main():
    parser = argparse.ArgumentParser(description="One-shot skill funnel routing")
    parser.add_argument("query", nargs="?", help="Task description")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    if not args.query:
        print(__doc__)
        return

    domains, candidates = detect_domains(args.query)
    chains = find_chains(args.query, candidates)
    pipeline, p_ratio = match_pipeline(args.query)
    rec = recommend_skills(domains, chains, pipeline)
    # Phase 4 (v2): also pull MCP recommendations from MCP_REGISTRY.md
    # Use ALL chain names found (not just top-10), to surface tag-specific MCPs
    mcps = recommend_mcps(domains, {c["name"] for c in chains})
    # Phase 5 (v3): 道智库 surface (only when query contains decision triggers)
    daozhi = recommend_daozhi(args.query)
    # Phase 6 (v4.1): auto_parallel_mode — 默认 top-2 并发 (非 single-pick 情况)
    confidence = min(1.0, 0.3 + 0.1 * len(chains) + p_ratio * 0.4)
    has_compare = bool(re.search(r"对比|比较|都跑|多源|全面|all|compare", args.query or "", re.IGNORECASE))
    has_decision = bool(DAOZHI_TRIGGERS.search(args.query or ""))
    if has_compare:
        parallel = {"mode": "parallel-all", "max_fire": 8, "reason": "user said '对比/全面/都跑/compare'"}
    elif has_decision:
        parallel = {"mode": "parallel-top5", "max_fire": 5, "reason": "decision-type query"}
    elif confidence < 0.7:
        parallel = {"mode": "parallel-top2", "max_fire": 2, "reason": f"confidence={confidence:.2f}<0.7 → default top-2 (v4.1)"}
    else:
        parallel = {"mode": "single", "max_fire": 1, "reason": f"confidence={confidence:.2f}>=0.7 → single best"}

    payload = {
        "query": args.query,
        "detected_domains": [d for d, _ in domains.most_common()],
        "candidate_chains": [
            {"name": c["name"], "members": c["member_count"],
             "strategy": precision_strategy(c["member_count"])}
            for c in chains[:10]
        ],
        "pipeline_match": pipeline,
        "recommended_steps": rec,
        "recommended_mcps_and_skills": [
            {"source": src, "item": item} for src, item in mcps[:20]
        ],
        "recommended_daozhi": daozhi,
        "parallel_mode": parallel,
        "confidence": confidence,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    # Pretty print
    print("=" * 60)
    print("Skill Route Funnel")
    print("=" * 60)
    print(f"Query: {payload['query']}")
    print(f"\n[Layer 1] Detected domains:")
    print(f"  {' / '.join(payload['detected_domains']) or '(none — generic task)'}")
    print(f"\n[Layer 2-3] Candidate chains:")
    if not payload["candidate_chains"]:
        print("  (no chain matched — task may be trivial OR new domain)")
    for c in payload["candidate_chains"]:
        members = c["members"] if c["members"] is not None else "?"
        print(f"  - {c['name']}  ({members} members)  → {c['strategy']}")

    print(f"\n[Layer 4] Pipeline match:")
    if pipeline:
        print(f"  [HIT] {pipeline['label']}  (id: {pipeline['id']}, "
              f"hits: {pipeline['trigger_hits']}, ratio: {pipeline['match_ratio']})")
    else:
        print("  [MISS] no pipeline matched (use single skill or parallel-compare)")

    print(f"\n[Layer 5] Recommended steps:")
    for i, step in enumerate(rec, 1):
        if "skills" in step and step["skills"]:
            print(f"  {i}. [{step['role']}] " +
                  " / ".join(f"Skill('{s}')" for s in step["skills"]) +
                  f"  ({step['select']})")
        elif "tool" in step:
            print(f"  {i}. [{step['role']}] $ {step['tool']}  ({step['select']})")
        elif "chain" in step:
            print(f"  {i}. [{step['role']}] → chain {step['chain']}  ({step['select']})")
        elif "chain_path" in step:
            print(f"  {i}. {step['role']}  ({step['chain_path']})")
        else:
            print(f"  {i}. [{step['role']}] (empty step)")

    # Phase 4 (v2): MCP + Skill registry recommendations
    if payload.get("recommended_mcps_and_skills"):
        print(f"\n[Layer 5b] MCP + Skill registry (parallel-fire candidates):")
        last_source = None
        for entry in payload["recommended_mcps_and_skills"]:
            if entry["source"] != last_source:
                print(f"  via {entry['source']}:")
                last_source = entry["source"]
            print(f"    - {entry['item']}")
        print(f"  (Tip: fire multiple in parallel for evidence-ensemble queries)")

    # Phase 5 (v3): 道智库 surface (only when triggers hit)
    if payload.get("recommended_daozhi"):
        print(f"\n[Layer 5c] 道智库建议 (适用于此问题):")
        for d in payload["recommended_daozhi"]:
            print(f"  · {d['id']} — {d['name']} (score={d['score']})")
        print(f"  (说\"用 X 分析\" 走 daozhi-apply; \"全部对比\" 走 §15.3 多 wisdom 综合)")

    # Phase 6 (v4.1): auto_parallel_mode
    pm = payload.get("parallel_mode", {})
    print(f"\n[Layer 5e] 并发模式: {pm.get('mode','?')} (max_fire={pm.get('max_fire','?')})")
    print(f"  理由: {pm.get('reason','?')}")
    if pm.get("max_fire", 1) >= 2:
        print(f"  ⇒ 5 CLI 默认 fire top-{pm.get('max_fire')} candidates 并发, cross-compare 后 synthesize")

    print(f"\nConfidence: {payload['confidence']:.2f}")
    print("=" * 60)
    print("\nNext: open the candidate chain files OR call recommended Skill().")
    print("If no chain matched, this task may be either trivial (skip funnel)")
    print("or a new domain (consider adding a new chain).")


if __name__ == "__main__":
    main()
