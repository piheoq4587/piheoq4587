---
name: daozhi-apply
description: |
  输入(智慧 id + 问题),按该智慧的 operations 步骤分析问题,输出结构化分析。
  完成后请用户给 good/ok/bad 评分,写入 application_logs/ 让道智库越用越聪明。
  触发词: 「用 wisdom-X 分析 Y」「apply X to Y」「用二阶效应看这个决策」「以 occam-razor 拆解」
tags: [km:memory-distill, think:decision-matrix]
---

# 道智应用 · Apply Wisdom to Problem

## Phase A1 · 接收输入

需要两样:
1. **wisdom id**（如 `wisdom-mm-second-order`）或 dao 名（如 `dao-laozi-wuwei`）
2. **problem**（用户的实际困境 / 决策 / 待分析事项）

如缺其一 → 询问补充，**不假设**。

## Phase A2 · 加载智慧全文

`Read ~/.claude/projects/C--Users-Administrator/memory/wisdom/{wisdom_id}.md`

或对古文道：`Read ~/.gemini/skills/{dao_name}/SKILL.md` + 引用其 references/

加载内容包括:
- short-frame（一句话用法）
- operations（步骤）
- applicability + counter-indication
- examples

## Phase A3 · 严格按 operations 执行

**关键**: 不能跳步,不能用其他 wisdom 串味。

输出格式:

```
应用 wisdom: {wisdom_id}
对问题: {problem 简短复述}

步骤 1 · {operations[0]}
  → 在你的问题里这是: ...
  → 我看到: ...
  → 中间结论: ...

步骤 2 · {operations[1]}
  → 在你的问题里这是: ...
  ...

...

综合结论:
  - 根据 {wisdom name} 这个框架,你的问题该被理解为: ...
  - 建议的行动: ...
  - **但注意**: 这个 wisdom 的 counter-indication 是 {...}
    如果你的实际情况更接近 counter-indication → 请考虑换一个 wisdom

参考 examples:
  - 类似情景 1: ...
  - 类似情景 2: ...
```

## Phase A4 · 反馈请求

末尾追加:

```
---
本次应用质量如何?
  · good — 这个智慧确实切中要害,以后类似问题继续推
  · ok — 部分有用但不完美
  · bad — 不太适用,以后该问题少推这个

(你给的评分会写到 ~/.claude/projects/.../memory/wisdom/application_logs/ 让 daozhi-search 重排序)
```

用户给评分后,跑:
```bash
python ~/.gemini/skills/_chains/_scripts/log_usage.py \
    daozhi-apply --rating {good|ok|bad} \
    --task "{wisdom_id} on {problem_summary}"
```

并写一行到 `application_logs/{ISO_timestamp}_{wisdom_id}_{rating}.md` 含完整 problem + analysis + rating + 理由（如有）。

## Phase A5 · 多 wisdom 并用模式

当用户说"用 X+Y+Z 智慧一起分析":
1. 对每个 wisdom 独立跑 Phase A1-A3,不互相参考
2. 最后做 synthesis 步骤:
   - **一致区**: X 和 Y 给出相同结论 → 这是高置信度结论
   - **冲突区**: X 说 A, Z 说非 A → 列出冲突 + 说明各自合理的场景边界
   - **互补区**: X 看一个面,Y 看另一个面 → 整合
3. 综合反馈请求改成: "X 和 Y 哪个更切题,还是综合最好?"

这是 SKILL_INVOCATION_PROTOCOL §15.3 多 skill cross-application 在 daozhi 上的具体实现。
