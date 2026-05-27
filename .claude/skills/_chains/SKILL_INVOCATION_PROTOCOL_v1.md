---
name: skill-invocation-protocol
description: Mandatory skill-first protocol for all CLIs (Claude Code / Codex / Copilot / Gemini / Antigravity). Forces 4-layer funnel before any non-trivial task to ensure consistent quality across CLIs and workstations. v1.1 adds mandatory router gate, MCP/API priority list, per-artifact verification checklist, and merged output template.
type: protocol
status: active
version: 1.1
created: 2026-05-08
updated: 2026-05-08
applies-to: [Claude Code, Codex, GitHub Copilot, Gemini, Antigravity, Cline, Cursor, Augment, Verdent, Junie, Factory AI]
canonical-path: ~/.gemini/skills/_chains/SKILL_INVOCATION_PROTOCOL_v1.md
junctions: [~/.claude/skills/_chains/, ~/.codex/skills/_chains/, ~/.copilot/skills/_chains/]
companion-doc: ~/.gemini/skills/_chains/HIERARCHY_PROTOCOL_PORTABLE.md
changelog:
  - "v1.1 (2026-05-08): Adopted 4 sections from portable transfer doc — §11 mandatory router gate, §12 MCP/API priority, §13 per-artifact verification, §14 merged output template. Existing §1–§10 unchanged."
  - "v1.0 (2026-05-08): Initial 4-layer funnel."
---

# Skill Invocation Protocol v1 (跨 CLI 强制版)

> **原文档发起人**：用户 (周春雷协作场景)
> **创立背景**：2026-05-07 在「周春雷×谱康合作方案」任务中，CLI 完成任务但**未调用任何 skill** → 输出可接受但**未达可能上限**。本文档把"按需调用"升级为"强制 funnel"。
> **跨 CLI 约束**：本文档是 **唯一权威**。任何 CLI（Claude Code / Codex / Copilot / Gemini / Cursor / Cline / Antigravity / Augment / Verdent / Junie / Factory AI）首次启动时必须读它一次；之后每次接到任务时必须按其 §3 决策。

---

## §1 为什么需要这套协议

### 1.1 漏洞描述
单 CLI（无论何家）在接到任务后**默认走自由编写模式**——直接组合内置工具（Read/Write/Bash/Edit）+ MCP 完成任务。这有 3 个后果：

1. **错过 1003 个已装 skill**：每个 skill 是一份「领域专家蒸馏」，含 SOP、模板、anti-pattern，是用户手工或半自动收集的。跳过 = 浪费资产。
2. **跨 CLI 输出风格不一致**：Claude 偏简洁、Codex 偏代码、Gemini 偏长文，但用户希望同一个任务给到不同 CLI 都得到**相近质量**——只有走相同的 skill 才能拉平。
3. **跨电脑迁移失效**：用户在 PC-A 训练了 1003 skill，到 PC-B 装好 junction 后，CLI 默认仍走自由模式 → 等于没装。

### 1.2 价值主张
| 项 | 自由模式 | Skill funnel 模式 |
|---|---|---|
| 上下文 token | 低 | 中（多读 1-2 个 chain 文件） |
| 决策速度 | 快（10s） | 中（30-90s 含 select） |
| 输出专业深度 | 取决于训练 | 取决于 skill 库 + 训练 |
| 跨 CLI 一致性 | 差异大 | 高度一致 |
| 跨电脑可移植 | 不可移植 | 完全可移植（只要 skill 库装好） |
| 用户验证成本 | 高 | 低 |

**结论**：除 §3 列出的「免 funnel 例外」之外，所有 CLI **必须**走 funnel。

---

## §2 体系结构（4 层 + 1 元层）

```
┌──────────────────────────────────────────────────────────┐
│ Layer 0  TASK INTAKE                                      │
│  - 接到用户消息后,先做 1 句"任务复杂度评估"               │
│  - 如属"trivial 例外"(§3.1),直接做,跳过 funnel          │
│  - 否则进 Layer 1                                         │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 1  DOMAIN MATCHING (14 super-domain)               │
│  bio / clinic / stat / ds / lit / paper / antiAI /        │
│  grant / km / eng / vis / meta / think / dao              │
│  - 用关键词 + 上下文判断属于哪 1-3 个 domain              │
│  - 工具:reference_skill_chain_system_v1.md 的触发词表  │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 2  TAG CHAIN OPENING                                │
│  - 打开对应的 chain-<domain>__<tag>.md 文件               │
│  - 路径:~/.gemini/skills/_chains/                       │
│  - 看 chain.member-count 决定下一步精筛策略              │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 3  PRECISION SELECT (按成员数自动)                  │
│   ≤5    → 直接 menu(列全部)                              │
│   6-15  → menu + 1 行简介                                 │
│   16-50 → 跑 chain_select.py 让 LLM 排 top-5              │
│   >50   → ask-questions 模式问用户 2-3 个澄清问题        │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 4  PIPELINE MATCH (元层)                            │
│  - 先跑 chain_combine.py --match "<query>"                │
│  - 命中预定义 pipeline → 走 pipeline.steps 顺序          │
│  - 未命中 → 单 skill / 多 skill parallel-compare         │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 5  EXECUTE                                          │
│  - 用 Skill() 工具(或等价)调用                            │
│  - 多 skill 时按 pipeline.mode 决定 (sequential /         │
│    parallel-compare / cascade-fallback)                   │
│  - 任务结束后向用户报告:用了哪些 skill / 各 skill 贡献   │
└──────────────────────────────────────────────────────────┘
```

---

## §3 强制启动条件 (Mandatory Triggers)

### 3.1 必须走 funnel 的情形（**至少满足 2 项**）
- 任务步骤 ≥ 3 个不同子任务
- 任务跨 ≥ 2 个 super-domain（如 bio + paper）
- 用户提到关键词：研究 / 规划 / 设计 / 调研 / 写论文 / 写标书 / 投稿 / 综述 / 实验方案 / 数据分析 / 类器官 / 流式 / 单细胞 / scRNA / GWAS / MR / NSFC / TIM / 标书 / Obsidian / 知识图谱 / 易学 / 图表 / 海报 / 网页 / 文献 / CNKI
- 任务最终成果**用于发表 / 外部审核 / 客户提交**（高质量门槛）
- 任务涉及"专业 SOP"（实验 protocol、临床路径、监管申报）

### 3.2 免 funnel 例外（trivial path）
- 单文件局部编辑（typo、rename、加注释、单 import 修复）
- 单一 grep/glob/read 的事实查询
- 简单文件移动 / 重命名 / mkdir
- 调试 / 排错（需要灵活）
- 用户**明确**说"快、直接、不要 search skill"
- 元任务（如本文档撰写）

### 3.3 半-funnel 模式（折中）
- 任务有 trivial 部分 + 非 trivial 部分 → trivial 部分直接做，非 trivial 部分必须走 funnel
- 例：用户说"读这个文件然后帮我写论文初稿"——读直接做，写论文必须走 `chain-domain-paper`

---

## §4 实操步骤（每个 CLI 接到任务时按这个走）

### Step 1：任务接收时的内心独白
```
[CLI 内心]
1. 这是 trivial 任务吗？(对照 §3.2)
   - 是 → 直接做,跳过 funnel
   - 否 → 进 Step 2
2. 这是哪 1-3 个 super-domain?
   - 列出 domain 候选
3. 关键触发词扫描:
   - 找到则记录 → 进 Step 3
4. 用户是否明确说"直接做"?
   - 是 → 跳过 funnel,但事后报告"我跳过了 funnel"
   - 否 → 进 Step 3
```

### Step 2：Domain → Chain 映射
对照 `~/.claude/projects/C--Users-Administrator/memory/reference_skill_chain_system_v1.md` 的 §"触发词 → Chain 总表"，找到 1-3 个候选 chain。

如果找不到合适的 chain：
- 跑 `python ~/.gemini/skills/_chains/_scripts/skill_route.py "<query>"` 让脚本帮你决定（见 §5）

### Step 3：打开 chain 文件
```bash
# Read 工具直接读
~/.gemini/skills/_chains/chain-<domain>__<tag>.md
```

观察 frontmatter 的 `member-count`，决定是直接 menu 还是 chain_select。

### Step 4：精筛 / pipeline 检查
```powershell
# 精筛(如成员 16-50)
python ~/.gemini/skills/_chains/_scripts/chain_select.py chain-bio__variant-annotation "annotate VCF for HLA"

# pipeline 检查(总是先跑这个)
python ~/.gemini/skills/_chains/_scripts/chain_combine.py --match "TIM 投稿全流程"
```

### Step 5：执行
- 单 skill：用 `Skill("<skill-name>")` 调用
- 多 skill 顺序：按 pipeline.steps 逐一执行
- 多 skill 并行对比：分别调用，最后呈现对比表

### Step 6：报告
任务结束后**必须**向用户报告。v1.1 起使用 **§14 合并输出模板**（短标签头行 + 长 body），最简形如：
```
[Skill Funnel Report]
- 命中 chain: chain-bio__single-cell-rna
- 命中 pipeline: 无
- 调用 skill: scanpy / single-cell-rna-qc / cell-type-annotation

[Skill Output Detail]
成功使用的 Skill: scanpy（QC 流程）/ single-cell-rna-qc（doublet 过滤）/ cell-type-annotation（marker 校验）
失败或降级的 MCP/Skill: 无
输出文件: <绝对路径>
验证: 见 §13 检查表（DOCX 可打开 / 段落数=N / 引用全部追溯到本轮工具）
```
若任务产出文件，必须按 **§13 Per-artifact verification checklist** 逐项打勾。详细模板见 §14。

---

## §5 一键检查脚本：`skill_route.py`

为简化每次手动 funnel，提供**单条命令**完成 Layer 1-4：

```bash
python ~/.gemini/skills/_chains/_scripts/skill_route.py "<任务描述>"
```

**输出**示例：
```
=== Skill Route Funnel ===
Query: 帮周春雷设计脓毒症-中药 CyTOF panel + 写合作方案 Word
Detected domains: [bio, clinic, paper, grant, vis]
Candidate chains:
  - chain-clinic__icu-sepsis (2 members)
  - chain-bio__single-cell-rna (38 members)  ← need chain_select
  - chain-bio__proteomics (15 members)
  - chain-paper__writing-strategy (≤5 members)
  - chain-grant__research-proposal
  - chain-vis__docx-word
Pipeline match: 无完全命中, 但 'tim-submission' 部分匹配 (35%)
Recommended action:
  1. Skill('cs-paper-strategist') 先定位期刊
  2. Skill('bio-flow-cytometry-clustering-phenotyping') panel 设计
  3. Skill('bio-imaging-mass-cytometry-spatial-analysis') IMC panel
  4. Skill('grant-proposal-assistant') Word 合作方案骨架
  5. Skill('anthropic-skills:docx-official') 生成 Word
Estimated time: 2-3 min funnel + execute
Confidence: 0.78
```

CLI 看到这个输出后必须按推荐动作执行（如不同意，向用户解释理由后再选）。

---

## §6 跨 CLI 一致性保证

### 6.1 4 CLI junction（已配置）
```
~/.gemini/skills/_chains/    ← canonical (源头)
~/.claude/skills/_chains/     ← junction
~/.codex/skills/_chains/      ← junction
~/.copilot/skills/_chains/    ← junction
```

任何 CLI 在 `_chains/` 目录下读到的内容**完全一致**。

### 6.2 其他 CLI 接入此协议的方法
1. **Codex / Copilot / Gemini**：在其 `AGENTS.md` / `system instructions` 加 1 行：
   ```
   Before any non-trivial task, read ~/.gemini/skills/_chains/SKILL_INVOCATION_PROTOCOL_v1.md and follow §3-§5.
   ```
2. **Cursor / Cline / Augment / Verdent / Junie / Factory AI / Antigravity**：
   - 在其 system prompt / config 加同样指令
   - 路径用绝对路径或 `~` 展开

3. **跨电脑迁移**：
   - 装好 1003 skill 库到 `~/.gemini/skills/`
   - 跑 `~/.gemini/skills/_chains/_scripts/junction_all.ps1` 创建 4 CLI junction
   - 跑 `~/.gemini/skills/_chains/_scripts/build_chains.py` 重建 chain 索引
   - 各 CLI 启动一次 → 自动生效

### 6.3 验证清单（跨电脑/跨 CLI 部署时）
```powershell
# 1. canonical 完整
Test-Path "~/.gemini/skills/_chains/SKILL_INVOCATION_PROTOCOL_v1.md"

# 2. 4 CLI junction 全活
foreach ($cli in @("claude", "codex", "copilot")) {
    Test-Path "~/.${cli}/skills/_chains/SKILL_INVOCATION_PROTOCOL_v1.md"
}

# 3. 关键脚本可执行
python ~/.gemini/skills/_chains/_scripts/chain_select.py --help
python ~/.gemini/skills/_chains/_scripts/chain_combine.py --help
python ~/.gemini/skills/_chains/_scripts/skill_route.py --help

# 4. 1 个端到端 dry-run
python ~/.gemini/skills/_chains/_scripts/skill_route.py "测试任务: 帮我做 GWAS Mendelian Randomization"
# 期望:返回 chain-bio__mr-causal-genomics + pipeline mr-analysis
```

---

## §7 Effectiveness Metrics（效率指标）

每次任务结束后 CLI **可选**记录到 `~/.gemini/skills/_chains/_metrics.jsonl`：

```json
{"timestamp": "2026-05-08T10:00:00Z", "task": "...", "skills_used": [...], "funnel_used": true, "user_feedback": "good", "duration_s": 180}
```

每月 1 次 Skill audit pipeline (`skill-audit`) 跑：
- skill_hit_rate = funnel 用 / 全部任务
- skill_diversity = 不同 skill 调用数 / 总调用数
- pipeline_match_rate = 命中 pipeline / 总 funnel

---

## §8 反例：2026-05-07 周春雷合作方案任务

### 8.1 任务
"读 6 份谱康公司 PDF，设计脓毒症-中药 CyTOF/IMC 数据补充方案 + 生成中医药类器官药筛合作 Word"。

### 8.2 实际执行（自由模式）
- 工具：Read / Write / Bash / PDF Tools / TodoWrite / AskUserQuestion / ExitPlanMode / python-docx
- Skill 调用：**0**
- 结果：A 数据补充方案 + B 合作 Word 都已交付，用户接受度 OK

### 8.3 应该执行（funnel 模式）
- Layer 1 domain: bio + clinic + paper + grant + vis
- Layer 2 chains: `chain-clinic__icu-sepsis` / `chain-bio__single-cell-rna` / `chain-bio__proteomics` / `chain-paper__writing-strategy` / `chain-grant__research-proposal` / `chain-vis__docx-word`
- Layer 3 精筛: `chain_select.py` 排序后选 top-5
- Layer 4 pipeline: 部分匹配 `tim-submission`，借用其 steps
- Layer 5 调用 skill：
  1. `cs-paper-strategist` 定位 IF 10-15 期刊
  2. `bio-flow-cytometry-clustering-phenotyping` 校验 30-marker panel 合理性
  3. `bio-imaging-mass-cytometry-spatial-analysis` 校验 IMC 三器官 panel
  4. `grant-proposal-assistant` 优化 Word 章节骨架
  5. `anthropic-skills:docx-official` 生成 Word（替代 python-docx 手写）
  6. `scientific-writing` + `avoid-ai-writing` 校对中文文风
- 预期增益：
  - panel 设计**严谨度** ↑ 30%（专业 skill 校验防遗漏关键 marker）
  - 期刊定位**准确度** ↑（不再凭训练记忆推荐）
  - Word **格式工整度** ↑（含目录/页眉页脚/Heading 样式自动）
  - 中文文风**专业度** ↑（去 AI 味）

### 8.4 教训
**「自由模式可完成 80 分输出，funnel 模式可拿 95 分」**——尤其是用户准备**外发**的产物（合作方案要发企业领导层），funnel 必须开。

---

## §9 后续维护

- **本协议版本号**：v1.0（2026-05-08 创立）
- **下一个里程碑**：v1.5（收集 1 个月 metrics 后回顾，调整阈值与触发词）
- **维护责任**：本机 CLI（任意一家）发现协议过时或 chain 文件结构变了，可以直接编辑本文（4 CLI junction 同步）
- **冲突解决**：如本协议与单 CLI 的本地 CLAUDE.md / AGENTS.md 冲突 → **本协议优先**（因为是跨 CLI 共识）

---

## §10 一句话总结

> **接任务 → 检查触发词 → 进 chain → 跑 chain_combine → 用 skill_route.py 一键拿推荐 → 调 Skill() → 报告**
>
> **不再"自己写"——除非任务确属 §3.2 例外。**

---

## §11 Mandatory Router Gate（v1.1 新增 / Adopted from portable transfer doc §4）

满足 §3.1 funnel 条件后，**第一跳必须是对应的 router**，再进 Layer 1 domain matching。这个网关替代过去"凭直觉直接进 chain"的隐式行为。

| 任务类型 | 强制 router | 路由后进入 |
|---|---|---|
| 研究 / 生信 / 临床 / 数据库 / 文献 | `research-tool-router` | `chain-domain-{bio,clinic,lit,paper}` 等 |
| 视觉 / PPT / 海报 / 网页 / 图表 | `design-router` | `chain-domain-vis` |
| 代码 / 调 bug / 重构 | `karpathy-guidelines` | `chain-domain-eng` |
| Word / PPT / Excel 文档生成 | `Documents` / `Presentations` / `Spreadsheets` plugin skill 之一 | 直接 plugin skill |

**例外**：用户在消息中**显式点名**了一个 router 或 skill，则跳过 router 网关、直接执行命名物。

**动作要求**：决定走 funnel 后，第一句内心独白必须包含 "Router → <name>"，并在 §14 输出模板里登记是哪个 router 命中。

---

## §12 MCP / API / Local-tool Priority Hierarchy（v1.1 新增 / Adopted from portable transfer doc §7）

执行阶段调任何工具都按这个优先级，**不要跳层**：

```
1. 用户在本轮消息里明确指定的 MCP / Skill / 工具
2. 项目指令（CLAUDE.md / AGENTS.md / GEMINI.md）写死的 canonical router 或路径
3. 官方数据库 / API / 本地 CLI（PubMed / UniProt / Reactome / ChEMBL 等）
4. 已安装 Skill 自带的 scripts/
5. Web search / 浏览器（generic）
6. 模型记忆兜底（最低优先级，研究任务下禁用）
```

生命科学研究的常用第 3 层栈：
```
PubMed / PMC / Crossref / Scite / OpenAlex / CNKI
ToolUniverse / Reactome / STRING / ChEMBL / UniProt / Open Targets
bioclaw / single-cell / proteomics / cytometry skills
```

**MCP 失败必须显式记录**（写进 §14 输出模板的"失败或降级"段）：
- MCP / 工具名
- 调用参数
- 失败原因（API key / 初始化 / 网络 / 权限 / 超时）
- 选用的 fallback 路线

---

## §13 Per-artifact Verification Checklist（v1.1 新增 / Adopted from portable transfer doc §9）

任务产出文件后，**最终回答前**必须逐项验证。

### §13.1 文件类
```
DOCX：python-docx 能打开；统计段落数 / 表格数；抽检关键术语
PDF：pypdf / pdfplumber 能提取文本或渲染页面；抽检页数
PPTX：python-pptx 能打开或截图渲染；目测无空白页
XLSX：openpyxl 能读取 sheet；关键表 / 关键单元格存在
HTML/Web：本地 server 起得来或浏览器截图；CSS 不破图
```

### §13.2 代码类
```
- 单元测试 / 集成测试通过（或注明未跑原因）
- lint / format 通过（或注明未跑原因）
- git diff 限定在任务范围，无误改外围
- 接口契约（API / DB schema）与上游一致
```

### §13.3 研究类
```
- 证据文件存在（Markdown / CSV / XLSX 落盘）
- 每条引用可追溯到本轮工具结果（zero-hallucination）
- 关键结论对应附件或工具输出
- 局限性 / 矛盾 / 检索失败显式写出
- 报告含 Methods + 检索式 + 数据库 + 时间窗 + 失败工具
```

### §13.4 验证证据写入 §14 输出模板的"验证"段
具体说明用什么命令/脚本验过、跑了多少行 / 多少页 / 多少表，避免"已验证"这种空话。

---

## §14 Standardized Output Template（v1.1 新增 / Merged from existing v1 §4 Step 6 + portable transfer doc §13）

任务结束后**必须**用以下合并模板报告。短标签头行保持向后兼容（既有约定不破），长 body 提供失败/输出/验证细节。

```
[Skill Funnel Report]
- 命中 chain: <chain-name 或 "无（自由模式 + 原因）">
- 命中 pipeline: <pipeline-name 或 "无">
- 调用 skill: <skill1 / skill2 / ...>
- Router 命中: <research-tool-router / design-router / karpathy-guidelines / 无>

[Skill Output Detail]
成功使用的 Skill：
  - <skill-name>: <做了什么>
  - ...
失败或降级的 MCP/Skill：
  - 工具: <name>
    原因: <api key / network / init / permission / timeout / 其他>
    fallback: <选用的替代路径>
  - （若无失败，写"无"）
输出文件：
  - <绝对路径>
  - ...
验证（按 §13 检查表逐项）：
  - <文件类型>: <验证命令 / 验证结果>
  - 例：DOCX: python-docx open OK；段落 142；3 张表
  - 例：研究: 18 条引用全部追溯到 PubMed / Scite 工具结果
备注 / 局限性：
  - <如有>
```

**简化模式**：如果任务确实属于 §3.2 trivial 例外（typo、单行修复），输出模板**可省略**，但若用户随后要求"补一份 funnel 报告"，必须按本模板补出。

---

## §15 · Parallel-Compare Default (v1.2 增量 · 2026-05-22)

### 触发条件（任一即激活）
1. Query 含**对比词**: 对比 / 比较 / 验证 / 互相印证 / cross-check / 多源 / 互补 / 全面 / 都跑 / 都用 / 全部
2. funnel 给出 ≥3 个等价候选 chain，且**无线性依赖**（不是 pipeline 形式）
3. domain=lit + query 是查找类（"找 X / search X / 查 X"）→ 自动走 §15.1 文献三路 ensemble
4. 用户明确说"我希望多用一些 skill 和 MCP"或类似表述

### §15.1 文献三路+ ensemble (lit-default-trio 升级版)

默认 5 路并发（不再是 3 路）：
- `mcp__tooluniverse-literature__SemanticScholar_search_papers`
- `mcp__tooluniverse-literature__openalex_literature_search`
- `Skill('wos-starter-search')`
- `mcp__scite__search_literature` (引用强度 + 撤稿信号)
- `mcp__tooluniverse-literature__advanced_literature_search_agent` (intent agent)

跳过 ensemble 的 6 个例外（参见 CLAUDE.md Phase 1 列表）保持不变。

### §15.2 Parallel Fire 输出格式

在 §14 funnel 报告里加新段：

```
[Parallel Fire Plan]
  M1: mcp__scite__search_literature("<query>")
  M2: mcp__tooluniverse-literature__SemanticScholar_search_papers("<query>")
  M3: Skill('wos-starter-search')("<query>")
  M4: Skill('asta-skill')
  ... (≤8 个并发候选)
  ↓
  Cross-Compare 步骤：
  1. 收齐返回 → dedup by DOI/title
  2. 标 hit table: M1=✓ M2=✓ M3=✗ M4=✓ (per row)
  3. 互补 / 互证 / 冲突 三栏汇总
  4. 选最佳 + 标记次优 + 解释为何
```

### §15.3 多 skill cross-application (智慧并用)

当用户说"用多个 wisdom / dao / 智慧一起分析"时：
- daozhi-search 找出 top-3 wisdom
- 对**每个** wisdom 独立跑 daozhi-apply
- 最后做 synthesis：哪些 wisdom 给出一致结论 / 哪些冲突 / 取舍理由

### §15.4 何时**不**走 parallel-compare

- query 是单查询单实体（"TP53 在 GTEx 表达"）→ 1 个工具够
- query 明确点名工具（"只用 scite 查"）→ 尊重指定
- 链式 pipeline 任务（有先后依赖，如 SR：先 PROSPERO 注册 → 再 screening → 再 RoB → 再 forest）→ 走 pipeline 不走 parallel
- 用户明示"快直接 / 不走 funnel"

---

*本文档同步存在于 `~/.gemini/skills/_chains/`、`~/.claude/skills/_chains/`、`~/.codex/skills/_chains/`、`~/.copilot/skills/_chains/`。修改任意一处即四处同步（junction）。*

*v1.1 portable companion：`~/.gemini/skills/_chains/HIERARCHY_PROTOCOL_PORTABLE.md`（来自 2026-05-08 transfer 包，整本 verbatim 保存以便跨电脑迁移）。*
