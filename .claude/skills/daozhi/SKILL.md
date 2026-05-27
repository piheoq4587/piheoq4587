---
name: daozhi
description: |
  道智 · Wisdom Library 总入口。蒸馏现代材料(论文/案例/经验/心智模型) → 本地智慧库 → 决策时主动建议适用智慧。
  与 daoshu(古文典籍)互补不冲突。3 子模式:
  (1) 蒸馏 daozhi-distill: 输入材料 → 提炼成原则/心智模型/启发式/案例模式 → 存入 memory/wisdom/
  (2) 检索 daozhi-search: 输入问题 → 扫 INDEX → 输出适用智慧候选
  (3) 应用 daozhi-apply: 输入(智慧+问题) → 按 operations 步骤分析
  触发词: 「道」「术」「智」「智慧」「法」「本质」「原则」「架构」「思路」「怎么办」「怎么处理」「该怎么做」「如何决定」「decision」「principle」「framework」「mental model」「我蒸馏过哪些智慧」「道智库」
tags: [km:memory-distill, think:decision-matrix, dao:dao-distillation]
---

# 道智 · Wisdom Library

> 「道生之，德畜之，物形之，势成之。」——《老子》51 章
> 道智库 = 把抽象之道（原则/心智模型）+ 具体之势（案例/经验）化作随时可调的工具。

道智库与 daoshu 的分工：

| | daoshu (已有) | daozhi (新建) |
|---|---|---|
| 蒸馏对象 | 古文典籍 / 思想资料 | 论文 / 案例 / 决策 / 个人经验 / 心智模型 |
| 输出格式 | 完整的 dao-{name}/ 子 skill 包 | 单条 wisdom-*.md (memory/wisdom/) |
| 隔离原则 | 严格（每道独立 prompt） | 轻量（轻 frontmatter 索引） |
| 应用方式 | 用户授权后加载该 dao | search → apply 两步 |

两库共享同一 INDEX（互引用，不重复存储）。

---

## 入口分流（Phase 0）

| 用户输入特征 | 模式 | 跳转 |
|------------|------|------|
| 提供材料（论文段落 / 案例 / 决策日志）+ "蒸馏 / 提炼智慧 / 从这段提原则" | **蒸馏** | → `daozhi-distill` |
| 提出问题 + 含「道/术/智/智慧/法/本质/原则/架构/思路/怎么办/怎么处理/decision/principle」 | **检索** | → `daozhi-search` |
| 「用 wisdom-X 分析 Y」/ 「用 Z 智慧拆解 W」 | **应用** | → `daozhi-apply` |
| 「我有哪些智慧」/「道智库索引」 | **索引** | → 读 `~/.claude/projects/.../memory/wisdom/INDEX.md` |
| 模糊"帮我想想这个问题"，但有决策含义 | **检索-推荐模式** | → `daozhi-search` 推 top-3 候选让用户选 |

---

## 存储

```
~/.claude/projects/C--Users-Administrator/memory/wisdom/
├── INDEX.md                      ← 主索引（auto-regen）
├── wisdom-principle-{id}.md      ← 原则类（如 karpathy-simplicity）
├── wisdom-mm-{id}.md             ← Mental Model（如 second-order）
├── wisdom-heuristic-{id}.md      ← 决策启发式（如 5-whys, premortem）
├── wisdom-case-{id}.md           ← 案例模式
├── wisdom-sci-{id}.md            ← 科研方法学
├── wisdom-personal-{id}.md       ← 个人 lessons（敏感）
└── application_logs/             ← 每次 apply 的反馈日志
    └── {timestamp}_{wisdom-id}_{rating}.md
```

频次反馈：每次 apply 后用户给 good/ok/bad 评分，写入 `application_logs/`。`daozhi-search` 排序时按"近 30 天 application × 评分"加权。

---

## 与 funnel/skill_route.py 的集成

`skill_route.py` 的 Layer 5c 已加入 `recommend_daozhi()`。当 query 含**用户决策触发词集合**：
- 「道」「术」「智」「智慧」「法」
- 「本质」「原则」「架构」「思路」
- 「怎么办」「怎么处理」「该怎么做」「如何决定」
- "decision" "principle" "framework" "approach"

→ 自动 surface top-5 候选 + 一句话适用理由。用户决定要不要走 daozhi-apply。

**不打扰原则**：纯查询 / 执行类任务不触发。
