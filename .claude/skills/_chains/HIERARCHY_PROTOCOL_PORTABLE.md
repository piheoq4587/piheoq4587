<!--
来源：周春雷 OneDrive transfer 包（skill_system_transfer_20260508_083550/TRANSFER_DOCS/SKILL_CALL_HIERARCHY_PROTOCOL_FOR_CLI.md）
本机落地日期：2026-05-08
关系：本文档是 SKILL_INVOCATION_PROTOCOL_v1.md 的 portable companion，verbatim 保存以便跨电脑迁移。
v1.1 协议已采纳本文档的 §0 / §4 router 强制 / §7 工具优先级 / §9 验证清单 / §13 输出模板,详见同目录 SKILL_INVOCATION_PROTOCOL_v1.md §11–§14。
-->

# Skill 调用层级协议（跨 CLI 迁移版）

适用对象：Codex、Claude Code、Gemini CLI、Copilot CLI，以及任何能读取本地 `SKILL.md`、项目指令和 shell 的研究/写作/开发型 CLI。

目标：让 CLI 在执行复杂任务时，不再“单点调用某个 Skill”，而是按层级完成任务识别、Skill 组合、证据约束、执行验证和产物落盘。这样通常比单独调用一个 Skill 更高效，因为它先用轻量路由缩小范围，再只读取和执行与任务相关的 Skill。

---

## 0. 必须先承认的边界

这套协议不能保证“任何时候都 100% 调到最完美 Skill”。它能保证的是：

1. 优先检索已安装 Skill 和 chain，而不是凭模型记忆硬做。
2. 对复杂任务先分层路由，再组合 2-5 个最相关 Skill。
3. 只加载必要 `SKILL.md` 和必要 references/scripts，避免上下文被 1000+ Skill 撑爆。
4. 工具/MCP 不可用时，要显式记录失败原因并切换 fallback。
5. 输出必须有可验证产物、路径和证据来源。

如果某个 CLI 没有访问本机 Skill 目录、没有相应 MCP、API key 缺失、或项目指令不允许写文件，那么它只能执行降级版本。

---

## 1. Canonical Skill 系统结构

推荐的跨 CLI 目录层级：

```text
~/.gemini/skills/                         # canonical skill store
  <skill-name>/SKILL.md                    # 单个 skill 入口
  <skill-name>/scripts/                    # 可执行脚本，优先运行而非重写
  <skill-name>/references/                 # 大型参考材料，按需读取
  <skill-name>/assets/                     # 模板、字体、图片等输出资源
  _chains/
    chain-domain-bio.md                    # domain super chain
    chain-domain-lit.md
    chain-domain-paper.md
    chain-domain-vis.md
    chain-domain-eng.md
    chain-<domain>__<tag>.md               # tag chain
    _scripts/
      chain_select.py                      # 大 chain 中 LLM/ranking top-k
      chain_combine.py                     # 预定义 pipeline 匹配
      build_chains.py
      junction_all.ps1                     # 同步到多个 CLI

~/.codex/skills/                           # junction or mirror
~/.claude/skills/                          # junction or mirror
~/.copilot/skills/                         # junction or mirror
```

关键原则：`~/.gemini/skills` 是唯一 canonical。其他 CLI 目录应为 junction/symlink/mirror，避免四套 Skill 互相漂移。

---

## 2. 任务进入后的总调用流程

每个复杂任务按以下顺序执行。

```text
User task
  |
  v
0. 读项目指令 / AGENTS.md / CLAUDE.md / GEMINI.md
  |
  v
1. 判断任务类型：研究、写作、文档、代码、设计、数据分析、自动化、医学/法律等
  |
  v
2. 若任务复杂：先用 task-planner 生成或内化 2-3 条 skill-combo 方案
  |
  v
3. 用 tool-router / domain-chain 缩小 Skill 范围
  |
  v
4. 用 chain 规则选择具体 Skill
  |
  v
5. 按 progressive disclosure 读取最少上下文
  |
  v
6. 执行：优先 Skill scripts / MCP / 官方数据库 / 本地工具
  |
  v
7. 验证：文件、日志、统计、引用、测试、截图、DOCX 可打开等
  |
  v
8. 产物落盘 + 路径报告 + 失败/降级说明
```

---

## 3. 第一层：复杂度与审批门

### 3.1 复杂任务触发 task-planner

满足任一条件时，先走 `task-planner` 或等价计划层：

- >= 3 个步骤
- >= 2 个 Skill / 数据源 / MCP
- 用户说“调查、分析、设计方案、综述、标书、论文、系统搭建”
- 研究任务需要文献、数据库、附件、写作和文件产物结合
- 可能存在多条路线且成本/时间差异明显

输出要求：

```text
方案 A：快而可用
方案 B：深度证据链
方案 C：工程/自动化/平台化
```

如果用户明确要求“直接做”“不要问”“已经批准”，则不必停在方案选择，直接执行最稳路线，但仍要在内部按计划推进。

### 3.2 简单任务跳过 planner

以下跳过：

- 单条命令
- 单文件小改
- 用户已明确指定某个 Skill
- 简单事实查询

---

## 4. 第二层：通用 Router

在不知道用哪个 Skill 前，不直接靠模型知识做。先用 router。

### 4.1 研究/生命科学/数据库

首选：

```text
research-tool-router
```

路由到：

- 文献：PubMed / Scite / ScholarSearch / OpenAlex / Crossref / CNKI
- 生信：bioclaw / single-cell / proteomics / metabolomics / cytometry
- 医学机制：sepsis / cytokine / thrombosis / organoid / clinical
- 数据库：ToolUniverse / OpenTargets / Reactome / STRING / ChEMBL / UniProt

### 4.2 视觉/网页/PPT/图

首选：

```text
design-router
```

路由到：

- scientific-slides
- scientific-schematics
- diagram-design
- baoyu-infographic
- web-design-engineer
- pptx / html-ppt / poster skills

### 4.3 代码任务

首选：

```text
karpathy-guidelines
```

核心约束：

- 先说明假设和成功标准
- 最小实现
- 外科手术式改动
- 验证闭环

### 4.4 文档 / Word / PPT / 表格

首选：

```text
Documents / Presentations / Spreadsheets plugin skills
```

并使用本地运行时验证文件：

- DOCX：`python-docx` 打开、统计 paragraphs/tables
- PPTX：渲染/截图检查
- XLSX：读取 sheet 和关键单元格

---

## 5. 第三层：Skill Chain 选择规则

进入 `~/.gemini/skills/_chains/` 后，按 domain 和 tag 选择。

### 5.1 Domain 层

常用 domain：

```text
bio      生命科学、生信、组学、蛋白、单细胞
clinic   临床医学、ICU、脓毒症、药物、影像、病理
lit      文献发现、引文、CNKI、OpenAlex、Scite
paper    论文写作、方法、结果、讨论、审稿、投稿
grant    国自然/NSFC/NIH/课题设计
vis      PPT、图示、海报、网页、信息图
eng      代码、测试、数据库、DevOps
stat     统计、因果、meta、回归
km       知识库、Obsidian、知识图谱
meta     skill 创建、审计、安装、MCP
```

### 5.2 Chain 成员数决定选择方式

```text
<= 5 个成员：直接列菜单或选最匹配
6-15 个成员：列菜单 + 1 行说明
16-50 个成员：运行 chain_select.py 返回 top-5
>50 个成员：先问 2-3 个澄清问题，或用 task-planner 分流
```

示例：

```powershell
python ~/.gemini/skills/_chains/_scripts/chain_select.py `
  ~/.gemini/skills/_chains/chain-clinic__icu-sepsis.md `
  "脓毒症 中性粒细胞 质谱流式 类器官药筛 论文补强"
```

### 5.3 Pipeline 组合

若任务命中预定义 pipeline，优先组合执行：

```powershell
python ~/.gemini/skills/_chains/_scripts/chain_combine.py --match "<用户任务>"
```

典型 pipeline：

- systematic review
- NSFC grant
- manuscript revise/respond
- daily radar
- skill audit
- obsidian-kb
- TIM submission
- multi-omics manuscript planning

---

## 6. 第四层：Progressive Disclosure 读取策略

不要一次读所有 Skill。按三层读取：

1. Metadata：name + description，常驻或列表检索。
2. `SKILL.md`：只有命中后读取。
3. `scripts/ references/ assets/`：只有执行需要时读取或运行。

读取规则：

```text
先读 SKILL.md 前 150-250 行。
如果 SKILL.md 指向 scripts，优先运行脚本。
如果 references 很大，先 rg 关键词，不整包读取。
如果有模板 assets，优先复用模板。
```

---

## 7. 第五层：MCP / API / 本地工具优先级

优先级：

```text
1. 用户明确指定的 MCP/Skill
2. 项目指令指定的 canonical router
3. 官方数据库/API/本地 CLI
4. 已安装 Skill 的 scripts
5. Web search / 浏览器
6. 模型知识兜底
```

生命科学研究建议：

```text
PubMed / PMC / Crossref / Scite / OpenAlex
ToolUniverse / Reactome / STRING / ChEMBL / UniProt
bioclaw / local scripts
```

如果 MCP 失败，必须记录：

```text
MCP 名称
调用参数
失败原因
是否由 API key、初始化、网络、权限导致
fallback 路线
```

---

## 8. 第六层：Zero-Hallucination 研究协议

研究任务必须遵守：

1. 引用题名、DOI、PMID、作者、年份必须来自本轮工具结果。
2. 搜不到就写“未检索到”，不能用训练记忆补。
3. 附件内容必须先抽取/阅读，再写方案。
4. 非平凡研究任务要保存 Markdown/CSV/XLSX/DOCX 等文件。
5. 报告中写 Methods、检索式、数据库、时间、失败工具。

最低验证：

```text
quick：>= 5 次工具/检索/文件读写
survey：>= 30 次
review：>= 60 次
systematic：>= 100 次
```

这个数字是“努力下限”，不是机械刷调用。若用户只要快速方案，可以明确说明是 rapid evidence scan。

---

## 9. 第七层：质量闭环

每个任务结束前做验证。

### 9.1 文件类

```text
DOCX：python-docx 能打开；统计段落/表格；抽检关键词
PDF：能提取文本或渲染页面；抽检页数
PPTX：能打开或渲染；截图无空白
XLSX：能读取 sheet；关键表存在
HTML/Web：本地服务器或浏览器截图验证
```

### 9.2 代码类

```text
测试通过
lint/format 通过或说明未运行原因
git diff 限定在任务范围
```

### 9.3 研究类

```text
证据文件存在
引用可追溯
关键结论对应附件或工具结果
局限性写明
```

---

## 10. 推荐写入各 CLI 的最小系统提示

把下面片段加入每台电脑的 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 或等价项目指令。

```markdown
## Skill Hierarchy Protocol

Before executing non-trivial tasks, use the local Skill hierarchy rather than isolated single-skill calls.

Canonical skill store:
- `~/.gemini/skills/`
- Chain files: `~/.gemini/skills/_chains/`

Call flow:
1. Read project instructions first.
2. For complex tasks, consult `task-planner` unless the user explicitly requested direct execution or named a specific Skill.
3. For research/bio/clinical/database tasks, consult `research-tool-router`.
4. For visual/design/PPT/web tasks, consult `design-router`.
5. For code tasks, consult `karpathy-guidelines`.
6. Match trigger words to domain chains, then tag chains.
7. Select Skill by chain member count:
   - <=5: choose directly or menu
   - 6-15: menu + short descriptions
   - 16-50: run `chain_select.py`
   - >50: ask clarifying questions or use planner
8. Read only the matched `SKILL.md`; load references/scripts/assets only as needed.
9. Prefer official databases, MCP tools, and bundled scripts over model memory.
10. For research, use zero-hallucination: citations must come from this turn's tools.
11. Save substantive deliverables to files and report absolute paths.
12. Verify outputs before final response.
```

---

## 11. 跨电脑安装/同步步骤

在新电脑上执行前，先确认 Skill 目录存在。

```powershell
Test-Path "$HOME\.gemini\skills"
Test-Path "$HOME\.gemini\skills\_chains"
```

如果已有 canonical skill store，建立到其他 CLI 的 junction。

```powershell
$canonical = "$HOME\.gemini\skills"
$targets = @("$HOME\.codex\skills", "$HOME\.claude\skills", "$HOME\.copilot\skills")
foreach ($target in $targets) {
  if (!(Test-Path $target)) {
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    New-Item -ItemType Junction -Path $target -Target $canonical | Out-Null
  }
}
```

如果本机已有脚本：

```powershell
powershell -File "$HOME\.gemini\skills\_chains\_scripts\junction_all.ps1"
```

重建 chain index：

```powershell
python "$HOME\.gemini\skills\_chains\_scripts\build_chains.py"
```

快速自检：

```powershell
Get-ChildItem "$HOME\.gemini\skills" -Directory | Measure-Object
Get-ChildItem "$HOME\.gemini\skills\_chains" -Filter "chain-*.md" | Measure-Object
Get-Content "$HOME\.gemini\skills\_chains\chain-domain-bio.md" -TotalCount 20
```

---

## 12. 一个完整任务的示范：脓毒症 + 公司仪器 + Word 方案

正确调用方式：

```text
1. 读 AGENTS.md，识别为复杂研究/写作/附件阅读/Word 产物任务。
2. 触发 task-planner，但用户已要求直接完成时内部化计划。
3. research-tool-router：定位 sepsis / organoid / cytometry / manuscript。
4. chain-clinic__icu-sepsis：找 cytokine-storm-analysis-agent、coagulation-thrombosis-agent。
5. chain-bio__multi-omics-integration / cytometry：找 flow-cytometry、mass cytometry、IMC pipeline。
6. organoid-drug-response-agent：设计类器官药筛指标。
7. manuscript/scientific-writing：组织正式方案。
8. 附件抽取 PDF/PPTX 正文。
9. PubMed/Crossref 实时检索，引用只用本轮结果。
10. 生成 DOCX + MD + evidence 文件。
11. python-docx 验证 DOCX 可打开。
```

比单独调用更高效的原因：

- 单独 `organoid-drug-response-agent` 会漏掉质谱流式、组织空间成像和脓毒症免疫轴。
- 单独 `manuscript` 会写得漂亮但可能缺实验指标。
- 单独 `research-tool-router` 只负责路由，不会自动生成 Word。
- 层级组合能把“附件能力-课题机制-文献证据-谈判文本-文件验证”串成闭环。

---

## 13. 失败处理模板

最终回答中必须写：

```text
成功使用的 Skill：
- ...

失败或降级的 MCP/Skill：
- 工具：...
- 原因：...
- fallback：...

输出文件：
- ...

验证：
- ...
```

---

## 14. 最小伪代码

```python
def execute_task(task):
    instructions = read_project_instructions()
    task_type = classify(task)
    complexity = estimate_complexity(task)

    if complexity >= 3 and not user_named_specific_skill(task):
        plan = use_skill("task-planner", task)
        if user_requested_direct_execution(task):
            plan = choose_default_best_plan(plan)
        else:
            ask_user_to_select(plan)

    routers = []
    if task_touches_research_bio_clinic_database(task):
        routers.append("research-tool-router")
    if task_touches_visual_design(task):
        routers.append("design-router")
    if task_touches_code(task):
        routers.append("karpathy-guidelines")

    candidates = []
    for router in routers:
        candidates += route(router, task)

    chains = match_domain_and_tag_chains(task)
    candidates += select_from_chains(chains, task)

    selected = rank_and_deduplicate(candidates)
    for skill in selected:
        read_minimal_skill_md(skill)
        run_scripts_or_tools_if_available(skill)

    if research_task(task):
        enforce_zero_hallucination()

    outputs = create_deliverables()
    verify(outputs)
    return final_report(outputs, used_skills, failed_tools, limitations)
```

---

## 15. 推荐文件名

建议把本文件在其他电脑保存为：

```text
SKILL_CALL_HIERARCHY_PROTOCOL_FOR_CLI.md
```

并在项目级 `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` 中加入：

```markdown
Before complex tasks, read `SKILL_CALL_HIERARCHY_PROTOCOL_FOR_CLI.md` and follow its routing hierarchy.
```

