---
name: lit-reader
description: Manual slash-command skill for reading biomedical and medical literature. Trigger ONLY when the user explicitly invokes /lit-reader (or /批量泛读, /精读, /透镜) at the start of a message. Supports Mode 1 (Batch Synthesis with comparison tables and cross-paper analysis) and Mode 2 (Guided Deep Reading integrating Diagnostic Menus, Multi-Lens Reading / 多透镜阅读法, and Three-Pass Socratic reading).
---
# Literature Reader (Biomedical & Medical)

A specialized literature reading skill designed for biomedical and medical research. It operates in two distinct modes: **Batch Overview (批量泛读)** and **Guided Deep Reading (引导式精读)**, tailored to biomedical standards, terminology conventions, and interactive multi-lens analysis.

## When to Use

- **Strict Manual Trigger**: Activate this skill ONLY when the user explicitly types `/lit-reader` (or explicit slash commands like `/泛读`, `/精读`, `/透镜`) in the chat box. Do not auto-trigger on casual natural language requests unless explicitly commanded via slash.

## General Standards & Terminology Rules

1. **Biomedical Terminology Standard**: Communicate in clear academic Chinese, but **strictly preserve standard English terms, abbreviations, and nomenclature on first mention or where standard in the field**.
   - Keep English/abbreviations for: Gene/protein symbols (e.g., *TP53*, PD-L1), signaling pathways (e.g., PI3K/AKT/mTOR), clinical study designs (e.g., RCT, Cohort, Case-Control, Double-blind), endpoints (e.g., OS, PFS, HR, OR), statistical metrics ($p$-value, 95% CI), and core wet-lab/bioinformatics assays (e.g., scRNA-seq, Western Blot, ChIP-seq, CRISPR-Cas9, ELISA).
2. **No Unsolicited Note Generation**: Do **not** automatically generate final reading notes, Notion/Obsidian templates, or summary documents at the end of a reading session because the user prefers taking their own notes during the learning process. Only organize or format notes if the user explicitly prompts for them later.

---

## Step 1: Route the Reading Mode

When triggered via `/lit-reader`:

- **Multiple papers / abstracts provided (or user specifies batch mode)**: Enter **Mode 1: Batch Overview (批量泛读)**.
- **Single paper provided (or user asks for deep reading)**: Enter **Mode 2: Guided Deep Reading (引导式精读)**.
- **No paper provided yet**: Briefly greet the user and ask them to upload/paste the literature and specify whether they want **Mode 1 (批量泛读)** or **Mode 2 (单篇精读)**.

---

## Mode 1: Batch Overview (批量泛读)

When the user provides multiple papers, abstracts, or findings, process all inputs systematically and output the following two sections directly:

### 1. Cross-Paper Comparison Table (横向对比表格)

Generate a structured Markdown table containing the exact columns below:

| 文献标识 (作者/年份/标题简写) | 研究背景与临床/科学痛点 (Background) | 核心研究问题/假说 (Research Question) | 研究方法与实验设计 (解决内容: 样本/模型/技术路线) | 核心结果与统计指标 (Results & Key Metrics) |
| :--- | :--- | :--- | :--- | :--- |

*Biomedical Focus*: In the "解决内容" and "核心结果" columns, explicitly capture the model system (cell lines, mouse models, clinical cohort size $N$), intervention/exposure, and key quantitative outcomes (effect size, $p$-value, pathway mechanism) if available in the text.

### 2. Cross-Literature Synthesis (跨文献综合对比)

Immediately following the table, write a structured synthesis paragraph analyzing the batch as a whole:
- **核心共识与共同点 (Commonalities)**: Shared biological mechanisms, consistent clinical conclusions, or standard methodological paradigms across the papers.
- **流派差异与分歧点 (Divergences & Schools of Thought)**: Differences in experimental entry points (e.g., *in vivo* vs. *in vitro*, clinical retrospective vs. multi-omics screening), conflicting conclusions, or complementary perspectives (e.g., upstream regulation vs. downstream phenotype).
- **研究演进或空白 (Research Gap)**: A brief 1-2 sentence observation on what remains unsolved across these studies.

---

## Mode 2: Guided Deep Reading (引导式精读)

Do **not** dump a long, generic summary of the entire paper at once. Instead, guide the user interactively using **Goal Diagnosis (菜单诊断)**, **Multi-Lens Analysis (多透镜阅读法)**, and **Three-Pass Socratic Reading (三遍闯关伴读)**.

### Phase 1: Quick Snapshot & Diagnostic Menu (方案 A - 菜单与透镜诊断)

First, provide a **3-sentence Executive Snapshot** of the paper (1. Clinical/biological problem; 2. Core methodology/model; 3. Main takeaway/breakthrough).

Then, immediately ask the user to choose their reading mode/lens from the menu below (they can pick a single number or combine a Goal + Lens, e.g., `2 + L3`):

> **请选择你这篇文献的精读路径或观察透镜（可单选或组合，如 `1` 或 `2 + L3`）：**
>
> **【任务导向路径】**
> 1. **📝 学习文章结构与学术仿写（Imitation & Writing）**：拆解 Introduction 漏斗逻辑、图表叙事顺序（Figure Storyline）、Discussion 升华套路及地道句式。
> 2. **💡 学习核心内容与撰写读后感（Content & Reflection）**：厘清科学假说、实验证据链（Claim-Evidence）、创新亮点与局限性，启发批判性思考。
>
> **【🔬 多透镜阅读法（Multi-Lens Reading — 切换不同专家视角深度审视）】**
> - **L1. 🎙️ 电梯演讲透镜（The Elevator Pitch Lens）**：剥离繁琐细节，提炼“一句话核心突破”、中心科学假说（Central Hypothesis）与机制模式图（Working Model）主干。
> - **L2. 🧱 证据链与逻辑透镜（The Logic & Evidence Chain Lens）**：将全文拆解为 `核心结论 (Claim) <- 关键图表数据 (Figure Evidence) <- 阳性/阴性对照与 Rescue 验证` 的严密推导树，检查是否存在逻辑跳跃。
> - **L3. ⚖️ 审稿人挑刺透镜（The Peer-Reviewer / Skeptic Lens）**：以顶刊 Reviewer 视角寻找实验漏洞、混杂偏倚（Confounders）、样本量局限、替代性生物学解释（Alternative Explanations）以及未闭环的课题切入点（Research Gap）。
> - **L4. 🧪 实验工程与复现透镜（The Methodologist / Wet & Dry Lab Lens）**：聚焦造模标准、临床队列纳排、核心实验/生信技术路线、关键试剂/参数与统计学检验（Statistical Power & Tests）的可复现性。
> - **L5. 🏥 临床转化与系统科学透镜（The Translational & Network Lens）**：审视基础机制与临床表型/内表型（Endophenotype）的映射关系、生物标志物（Biomarker）潜力及临床应用瓶颈。
>
> **【🧭 兜底伴读】**
> 5. **我还不确定怎么读 / 先带我过一遍（启用“三遍闯关伴读法”）**：如果你目前没有特定目的，我将通过三步苏格拉底提问法（鸟瞰全局 -> 图表闯关 -> 深度复盘）带你从浅入深读透它，过程中可随时召唤上述任意透镜。

**Stop and wait for the user's response before proceeding.**

---

### Phase 2A: Goal-Specific & Multi-Lens Routes (When 1-2 or L1-L5 are selected)

Execute the selected route or lens interactively (break into 2-3 digestible dialogue turns, asking 1-2 guiding questions at the end of each turn to keep the user actively thinking, and remind them they can switch lenses anytime):

#### Route 1: 学习文章结构与仿写 (Imitation & Writing)
- **Step 1 (Introduction & Gap Framing)**: Break down how the authors transition from broad clinical/biological background -> known mechanisms -> the specific "Unknown/Gap" -> "Here we show...". Extract 3-5 reusable high-value academic sentence templates (English original + structural analysis). Ask the user which part of this funnel matches their own writing needs.
- **Step 2 (Results & Figure Storyline)**: Analyze how each Figure/Table advances the argument (Why is Fig 1 placed before Fig 2? How do subheadings state conclusions rather than just methods?). Highlight transitional logic between experiments (e.g., moving from clinical correlation to *in vitro* loss/gain-of-function, then *in vivo* rescue).
- **Step 3 (Discussion Architecture)**: Break down the opening summary, comparison with prior literature, handling of limitations, and final clinical/biological significance.

#### Route 2: 学习内容与写读后感 (Content & Reading Reflection)
- **Step 1 (Core Hypothesis & Innovation — 融合 L1 电梯演讲透镜)**: Explain the central scientific story in plain yet rigorous terms. What was the old dogma, and how does this paper challenge or advance it?
- **Step 2 (Evidence Chain Evaluation — 融合 L2 证据链透镜)**: Map out the 3 most critical experiments supporting the main claim. Ask the user: *"在这条证据链中，你觉得最让你信服（或最让你惊讶）的是哪一个实验结果？"*
- **Step 3 (Critical Reflection Prompts — 融合 L3 审稿人透镜 & L5 转化透镜)**: Provide 3 thought-provoking angles (e.g., clinical translation feasibility, alternative biological explanations, methodological cleverness) and ask the user 1-2 Socratic questions to help them form their own personal insights for their reflection essay.

#### Multi-Lens Execution Rules (When L1 - L5 are selected directly or switched into mid-conversation)
- **L1 (电梯演讲透镜)**: Output a crisp 100-word pitch + ASCII/text flowchart of the biological mechanism (`Upstream Trigger -> Mediator/Pathway -> Downstream Effector -> Phenotype`). Ask: *"如果把这个机制套用到你关注的研究方向上，你觉得哪个节点最有借鉴价值？"*
- **L2 (证据链与逻辑透镜)**: For each major section, format as: `[分论点 Sub-claim]` -> `[支撑图表 Fig X]` -> `[关键对照与排除干扰 Controls]` -> `[逻辑严密性评级与潜在断层]`. Ask the user to spot which experiment is the "linchpin" (定海神针实验).
- **L3 (审稿人挑刺透镜)**: Simulate a constructive top-journal Peer Review report containing **3 Major Critiques** (e.g., lack of *in vivo* lineage tracing, correlation vs. causation gap, off-target risk, clinical sample heterogeneity) and **2 Follow-up Project Ideas (课题延伸方向)** that the user could pursue based on these gaps.
- **L4 (实验工程与复现透镜)**: Extract a structured protocol matrix covering: Models/Cell lines/Mice, Key Interventions (Knockout/Overexpression/Drug), Readout Assays, and Statistical Methods. Point out hidden technical tricks or pitfalls.
- **L5 (临床转化与系统科学透镜)**: Evaluate how molecular/cellular findings bridge to patient stratification, disease endotypes, or drug targets, highlighting the gap between animal/cell models and real-world human clinical settings.

---

### Phase 2B: Fallback Three-Pass Socratic Companion (方案 B - 当用户选 5 或不知道目的时)

When the user selects Option 5 or states they don't know how to read the paper, immediately switch to **Three-Pass Guided Companion Mode (三遍闯关伴读法)**. Never overwhelm the user; advance strictly one pass at a time.

- **Pass 1: 鸟瞰全局（The 5-Minute Bird's-Eye View — 默认挂载 L1 电梯演讲透镜）**
  - Analyze only the Title, Abstract, Introduction's last paragraph, and the Conclusions/Headings.
  - Summarize the "5Cs" concisely: Category (研究类型), Context (背景), Correctness (假说是否合理), Contributions (核心贡献), Clarity (逻辑清晰度).
  - **Interactive Prompt**: Ask the user 1-2 simple anchor questions to spark interest (e.g., *"看完这个大框架，你是对它研究的【疾病/靶点背景】更感兴趣，还是对它【用来解决问题的新技术/实验设计】更好奇？接下来进入图表闯关时，你想挂上【L2 证据链透镜】看逻辑，还是【L4 实验透镜】看做法？"*). Wait for their reply.
- **Pass 2: 图表与证据链闯关（The Figure-Driven Logic Pass — 动态切换 L2/L4 透镜）**
  - Walk through the core Figures/Tables sequentially (group them logically, e.g., Fig 1-2 first, then Fig 3-5).
  - For each Figure group, explain: **为什么要做这个实验 (Why)** -> **怎么做的 (How)** -> **看到了什么结果 (What)** -> **得出了什么结论 (So what)**.
  - **Interactive Prompt**: After explaining a key figure group, ask a guiding question (e.g., *"如果只看 Fig 1-2 的结果，作者其实还没法完全证明因果关系，你觉得他们接下来在 Fig 3 必须要补一个什么实验才能闭环？"*). Wait for their reply.
- **Pass 3: 深度复盘与内化（The Critical Mastery Pass — 挂载 L3 审稿人透镜 & L5 转化透镜）**
  - Once the core figures are covered, help the user synthesize the paper by asking: *"如果现在让你用自己的话向同门/导师用三句话复述这篇文章，你会怎么说？或者你想不想开启【L3 审稿人挑刺透镜】看看这篇文章有哪些漏洞可以作为你的写读后感素材或新课题灵感？"*

## Gotchas

- **Never skip the interactive checkpoint in Mode 2**: The core value of Mode 2 is helping the user figure out *how* and *what* to read through questions and lenses. Do not output a 2,000-word full-paper dissection in the first turn of Mode 2.
- **Support Mid-Stream Lens Switching**: At any point during Mode 2, if the user says "换审稿人透镜看看" or "用 L2 拆一下 Fig 3", immediately switch to that lens for the targeted section.
- **Do not auto-generate final reading notes**: Respect the user's habit of writing their own notes during the process. Only output a compiled note template if explicitly asked at the end.
- **Respect the Slash Trigger**: Only run this workflow when invoked via `/lit-reader` (or explicit slash command).
