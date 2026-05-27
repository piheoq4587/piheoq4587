---
name: daozhi-search
description: |
  问题 → 适用智慧反向检索。输入用户的实际问题或决策困境，扫 memory/wisdom/INDEX.md
  并按 triggers/domains/applicability 三维匹配，输出 top-5 候选道智 + 一句话为什么适用。
  也可同时引用 dao-* 子 skill (古文道) — 跨库统一索引。
  触发词: 「这个问题用什么智慧」「智慧库有什么适用」「wisdom for this」「该用什么思路分析」「适合用什么 mental model」
tags: [km:memory-distill, think:decision-matrix]
---

# 道智反向检索 · Problem → Applicable Wisdom

## Phase S1 · 读 INDEX

读取 `~/.claude/projects/C--Users-Administrator/memory/wisdom/INDEX.md`。

INDEX 包含 3 交叉表：
- **By Type**: principle / mental-model / heuristic / case / sci / personal
- **By Domain**: research / decision / eng / paper / writing / ...
- **By Trigger Keyword**: {keyword → wisdom_id 列表}

## Phase S2 · 三维匹配

对用户的 problem 描述，按以下顺序打分：

1. **Trigger keyword 精确匹配** (权重 ×3)
   - problem 含 wisdom.triggers 任一关键词 → +3
2. **Domain 匹配** (权重 ×2)
   - problem 涉及 domain (decision/research/eng/...) → +2
3. **Applicability 模糊匹配** (权重 ×1)
   - problem 描述与 wisdom.applicability 文本语义相似 → +1
4. **频次 bonus** (权重 ×0.5)
   - 该 wisdom 近 30 天 application_logs/ 里被评 good 的次数 × 0.5
5. **Counter-indication 减分** (权重 ×-2)
   - problem 命中 wisdom.counter-indication → -2

最终按总分降序，取 top-5。

## Phase S3 · 输出格式

```
道智库适用候选 (按相关度排序):

1. wisdom-mm-second-order — 二阶效应
   理由: 你这个决策有多步连锁反应 (你提到"影响公司"+"长期")
   一句话: 不只问"会发生什么"，还问"然后会发生什么"
   去看完整: ~/.claude/projects/.../memory/wisdom/wisdom-mm-second-order.md

2. wisdom-heuristic-premortem — 事前剖析
   理由: 你说"想避免失败" — 经典 premortem 场景
   一句话: 假设这件事一年后失败了,想象都因为什么

3. dao-laozi-wuwei (古文道,跨引)
   理由: 你说"想干预但担心反效果" — 无为而治正合
   去看: ~/.gemini/skills/dao-laozi/

4. ...
5. ...

→ 想用哪个? 直接说"用 1 分析" / "用 1+2+3 都跑一遍对比" / "都跳过"
```

## Phase S4 · 不强推荐

- 如果 top-5 全部得分 <5 → 提示"没有强匹配，可能你的问题需要新蒸馏一个智慧"，并建议 `daozhi-distill`
- 如果用户说"都跳过" → 不强求，记录 problem 到一个 backlog（可作为未来 daozhi-distill 的输入）

## 与 funnel 集成

skill_route.py 的 Layer 5c 已经在做"轻量推荐"。daozhi-search **本 skill** 是"重量级正式检索"——用户明确叫起来时跑，输出比 Layer 5c 更详细的 top-5 + 全文路径。
