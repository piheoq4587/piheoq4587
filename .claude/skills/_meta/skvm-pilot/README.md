# SkVM Pilot Meta-Skill (引导脚本，非正式 skill)

SkVM 本身是外部工具（[arXiv:2604.03088](https://arxiv.org/abs/2604.03088), [GitHub](https://github.com/SJTU-IPADS/SkVM)，npm: `@ipads-skvm/skvm@0.1.5`）。本目录只放部署引导脚本和决策矩阵，不复刻 SkVM 进本地 skill 库。

## ⚠️ 重要：SkVM 0.1.5 不支持 Windows (2026-05-24 验证)

实测 `npm i -g @ipads-skvm/skvm` 在 Windows-x64 上失败：
```
skvm postinstall: unsupported platform win32-x64.
Supported: darwin-arm64, darwin-x64, linux-x64, linux-arm64.
```

**当前可选方案**：
1. **等 SkVM 出 Windows 二进制**（最稳妥，但不知何时）
2. **用 WSL2** 在 Windows 里跑 Linux SkVM（中等成本）
3. **从源码 build**: clone https://github.com/SJTU-IPADS/SkVM 自己编译（高成本）
4. **延后 Phase 3**: 用现有 Funnel v1.2 + LLM Router v3 已经覆盖 SkVM 论文 ~70% 价值（路由 + 模型 fallback），可以接受暂时不上 SkVM

## SkVM 是什么

把 skill 当成"代码"、把 LLM+Harness 当成"异构处理器"，提供 AOT 编译 + JIT 优化 + 跨平台运行时。

- **Author**: SJTU IPADS (Chen Haibo's team)
- **Tested**: 118K+ skills × 8 LLMs × 3 Harnesses
- **Reported gains**: 40% token ↓ / 3.2x speed / 19-50x latency ↓
- **License**: open source per arXiv paper

## 部署步骤

1. 跑 `skvm_pilot.cmd` (双击或 cmd 里执行) —— interactive，每步等用户确认
2. 跑完后查 `~/.claude/projects/C--Users-Administrator/skvm-profile/` 下报告
3. 看 metric 决定下一步

## 决策矩阵（试点完看这表）

| 指标 | 阈值 | 结论 |
|---|---|---|
| Token reduction | ≥20% | 试点成功 → 扩到 50 skill 全量 profile |
| Latency improvement | ≥5x | 同上 |
| Cross-CLI consistency variance | <5% | 同上 |
| Token reduction | <10% | 部分撤回，只对高 ROI 类 skill 用 |
| Latency improvement | <2x | 同上 |
| 任何 skill 跑崩 | ≥1 | 完全撤回，反馈给 SkVM 作者 |

## 与本地 stack 的关系

```
用户 query
   │
   ▼
Funnel v1.2 (skill_route.py) ← 选哪个 skill
   │
   ▼
LLM Router v3 (llm_router.py) ← 选哪个 LLM
   │
   ▼
SkVM Runtime (新加这层)        ← 选定后如何最优跑
   │
   ▼
真实 LLM 调用
```

三者互补不替代。

## 撤回条件（用户严格模式 v2.0）

- 5 个试点 skill 中 ≥3 个 token / 延迟 **恶化** → 撤回
- 任何关键 skill (task-router / Funnel / daozhi-distill) 跑崩 → 撤回
- profile 全量成本超 $50 → 暂停，找最贵部分撤回

## 重要：不要把 SkVM 自己当 skill 装

SkVM 是工具链，不是 skill。它的输出（编译后的 skill 变体）会写到 `~/.local/share/skvm/` 之类的位置，与 `~/.gemini/skills/` canonical 路径**不冲突**。Funnel 仍然路由到 canonical，SkVM Runtime 在执行环节做一层 translation。
