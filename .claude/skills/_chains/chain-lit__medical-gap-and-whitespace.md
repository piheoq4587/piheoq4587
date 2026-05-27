---
chain-tag: lit:medical-gap-and-whitespace
chain-type: curated-view
member-count: 5
default-mode: cascade+verify
installed-by: codex
installed-at: 2026-05-22
---

# Chain: `lit:medical-gap-and-whitespace`

用于医学选题是否饱和、是否仍有差异化空白、真实研究缺口、未满足临床需求、人群/方法缺口等任务。

## 触发词

- 研究空白 / gap / 缺口 / 创新点 / whitespace
- 方向是否饱和 / 题目是否拥挤 / 还有没有机会
- unmet clinical need / 临床痛点 / 临床需求
- 人群缺口 / 亚组不足 / 方法学缺陷

## 成员 skill

- `medical-topic-saturation-and-whitespace-checker`
- `medical-research-gap-finder`
- `unmet-clinical-need-extractor`
- `population-gap-detector`
- `method-gap-detector`

## 调用建议

先选 1 个主 skill 收敛问题；正式结论必须再走 Scite / PubMed / OpenAlex / WoS 等实时检索验证，不允许仅凭模型知识给 gap 结论。
