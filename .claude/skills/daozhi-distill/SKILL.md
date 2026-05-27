---
name: daozhi-distill
description: |
  从现代材料(论文/案例/决策日志/个人经验/书籍 quote)蒸馏成结构化"智慧"条目并存入道智库。
  与 daoshu(古文)互补 — 这个 skill 专门处理非古文源。
  输出 wisdom-*.md 到 ~/.claude/projects/.../memory/wisdom/ 并自动 update INDEX.md。
  触发词: 「蒸馏这段」「提炼智慧」「从这个材料提原则」「distill principle」「extract wisdom」「成 wisdom 条目」
tags: [km:memory-distill, dao:dao-distillation]
---

# 道智蒸馏 · Modern Material → Wisdom Entry

## Phase D1 · 接收材料

用户提供：
- 论文段落 / abstract
- 决策日志 / 复盘
- 个人 lesson（"上次我从 X 学到 Y"）
- 书籍 quote / 心智模型描述
- 经验总结

→ 直接读，不假设训练记忆里有相同内容。

## Phase D2 · 5 维拆解

| 维度 | 问题 |
|---|---|
| **核心声明** | 这段材料想说什么 1 句话原则？ |
| **底层公理** | 哪些假设是必要的？哪些不是？ |
| **适用条件** | 什么场景下这个原则成立？什么时候反而错？ |
| **操作步骤** | 用这个原则该怎么具体做（5-8 步）？ |
| **反模式** | 看起来像但其实不是的常见误用？ |

## Phase D3 · 分类（决定 wisdom-*-{id} 的中间字母）

| 类型 | 字母 | 示例 |
|---|---|---|
| 原则 principle | `principle` | karpathy-simplicity, occam-razor |
| 心智模型 mental-model | `mm` | second-order, survivorship-bias |
| 决策启发式 | `heuristic` | 5-whys, premortem, fermi |
| 案例模式 | `case` | "类似 X 项目失败因为 Y" |
| 科研方法学 | `sci` | falsifiability, claim-evidence-chain |
| 个人 lesson | `personal` | 个人特定 lessons (敏感) |

## Phase D4 · frontmatter 模板

```yaml
---
id: wisdom-{type}-{slug}
type: {principle|mental-model|heuristic|case|sci|personal}
name: {中文名}
english-name: {英文名 / 别名}
source: {作者/书/论文/出处 + 如可能附 DOI 或 URL}
domains: [decision, research, eng, ...]
triggers:
  - {自然语言关键词 1}
  - {自然语言关键词 2}
  - ...
applicability:
  - {场景 1}
  - {场景 2}
counter-indication:
  - {不该用的场景 1}
  - {不该用的场景 2}
short-frame: {一句话用法概要}
operations:
  - {步骤 1}
  - {步骤 2}
  - ...
examples:
  - {例 1}
  - {例 2}
related: [{相关 wisdom id 列表}]
created: {YYYY-MM-DD}
---
# {中文名}

（正文：详细说明 + 关键 quote + 反例 + 何时该用何时不该）
```

## Phase D5 · 写入 + 更新 INDEX

1. 写到 `~/.claude/projects/C--Users-Administrator/memory/wisdom/wisdom-{type}-{slug}.md`
2. 跑 INDEX update（追加新条目到 By Type / By Domain / By Trigger 三个交叉表）
3. 同步备份到 `OneDrive\备份skill及道智\memory-v2\wisdom\`（如启用了自动备份）

## Phase D6 · 三重验证

- ✓ 触发词集合 ≥3 个不同自然语言表述
- ✓ Operations 步骤可由不熟悉的人直接执行
- ✓ Counter-indication 至少 1 个（避免变成"万能"伪框架）

如缺任一 → 提示用户补充，**不强写**。
