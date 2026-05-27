---
chain-tag: bio:mechanism-validation
chain-type: curated-view
member-count: 4
default-mode: pipeline
installed-by: codex
installed-at: 2026-05-22
---

# Chain: `bio:mechanism-validation`

用于把组学、机制、通路、靶点、细胞状态或临床关联发现推进到可验证的功能实验和转化证据链。

## 触发词

- 机制验证 / 补强实验 / 阻断救援
- 从相关性到因果性
- 细胞实验 / 动物实验 / organoid / xenograft
- validation ladder / functional validation

## 成员 skill

- `mechanism-to-validation-planner`
- `animal-and-cell-validation-planner`
- `validation-strategy-designer`
- `translational-study-blueprint`

## 调用建议

默认先用 `mechanism-to-validation-planner` 定义待验证 claim 和验证阶梯，再用 `animal-and-cell-validation-planner` 落到模型、扰动、readout 和工作量分档。
