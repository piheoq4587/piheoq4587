---
chain-tag: paper:claim-integrity
chain-type: curated-view
member-count: 8
default-mode: pipeline
installed-by: codex
installed-at: 2026-05-22
---

# Chain: `paper:claim-integrity`

用于论文、标书、幻灯片、综述、审稿回复中的 claim、引用、证据强度和内部一致性核查。

## 触发词

- claim 是否站得住 / 证据是否支持
- 引用核查 / reference integrity / citation drift
- 过度宣称 / claim strength / 证据等级
- 投稿前检查 / reporting guideline / STROBE / PRISMA / CONSORT / TRIPOD
- 手稿前后矛盾 / 图文不一致

## 成员 skill

- `paper-to-claim-verifier`
- `reference-integrity-checker`
- `claim-strength-calibrator`
- `consistency-checker-across-manuscript`
- `reporting-guideline-compliance-checker`
- `contradictory-findings-resolver`
- `result-reliability-checker`
- `evidence-level-ranker`

## 调用建议

短句 claim 核查优先 `paper-to-claim-verifier`；整篇手稿终稿检查优先 `consistency-checker-across-manuscript` + `reporting-guideline-compliance-checker`。
