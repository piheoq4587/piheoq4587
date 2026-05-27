# Global behavioral guidelines

These apply to ALL Claude Code sessions in this repository.

## 📁 Skills System (Cloud Edition)

Skills are located in `.claude/skills/`. Core components:
- `task-router` — Universal routing for all non-trivial tasks
- `daozhi` / `daozhi-search` / `daozhi-apply` / `daozhi-distill` — Wisdom management
- `daoshu` — Classical text framework extraction
- `_chains/` — Pre-built skill chains
- `_taxonomy/` — Domain classification

## 🔀 Universal Task Routing (ALWAYS-ON)

**Rule**: For any non-trivial task (≥2 steps, cross-domain, unclear tool choice), **always invoke `task-router` first**.

### Decision Flow

```
User Request → Single-step/tool-clear? → Yes → Execute directly
                                      → No  → Call task-router → Get plan → Execute
                                                                    ↓
                                              Steps ≥5 or Domains ≥3? → Yes → Spawn orchestrator
                                                                      → No  → Execute plan step-by-step
```

### Mandatory Trigger Conditions

Default to task-router. Any of these conditions triggers routing:
- Task ≥ 2 steps
- Crosses ≥ 2 domains
- Contains entity ID mapping (gene/disease/drug/PDB/PMID...)
- Contains open-ended verbs ("帮我"/"分析"/"调研"/"找"/"做"/"复刻"/"修复"/"检查")
- Uncertain which tool/skill/chain to use
- User didn't explicitly name a tool

### Skip Routing Only For (5 types)

1. **Greetings** — "你好"/"hi"/"早安"
2. **Common knowledge** — "今天星期几"/"3+5="
3. **Single-tool explicit query** — User specified tool for single lookup
4. **Simple file/command ops** — "ls"/"git status"/"删掉这个文件"
5. **Status queries** — "你装了什么 skill?"/"manifest 内容?"

## ☯️ Ti-Yong Protocol (Wisdom-First)

**4-Layer Loop** (for substantial tasks):

```
Layer 0 体 (Wisdom-First Inquiry — ask: 本质? 最短路径? 验证标准?)
  ↓
Layer 1 道 (Strategy Selection — choose: single-shot/parallel-N/serial/compare/reflect)
  ↓
Layer 2 用 (Skill Execution — task-router STRICT 5-Phase)
  ↓
Layer 3 反哺 (Reflect & Distill)
  ↓ back to Layer 0
```

## 🔬 Zero-Hallucination Protocol

For ANY research task:
- ALL citations MUST come from tool results in THIS conversation
- If search returned no results, say so — NEVER fall back to training data
- Self-check before responding: every citation traces to a tool call

## Coding Discipline (Karpathy Guidelines)

1. **Think before coding** — state assumptions; surface ambiguity; ask when unclear
2. **Simplicity first** — minimum code that solves the problem; no speculative abstractions
3. **Surgical changes** — touch only what request requires; match existing style
4. **Goal-driven execution** — define verifiable success criteria before implementing

## 📦 Installed Skills (41 total)

### Core System
- `task-router` — Universal task routing
- `daozhi` / `daozhi-search` / `daozhi-apply` / `daozhi-distill` — Wisdom management
- `daoshu` — Classical frameworks
- `agentmemory-bridge` — Memory integration
- `knowledge-synthesis` — Knowledge synthesis

### Research & Analysis
- `literature-search` — Literature search
- `perplexity-search` — Web search
- `drug-discovery-search` / `drugbank-search` / `drug-interaction-checker` — Drug research
- `health-trend-analyzer` — Health analysis
- `nlp-text-analyzer` — Text analysis
- `empirical-analysis-python` — Python analysis

### Development
- `git-commit-smart` — Smart commits
- `gitnexus-cli` / `gitnexus-pr-review` / `gitnexus-refactoring` / `gitnexus-exploring` — Git tools
- `finishing-a-development-branch` — Branch completion
- `e2e-test-framework` — Testing
- `overnight-dev` — Background development
- `infrastructure-as-code-generator` — IaC

### Content & Visualization
- `baoyu-translate` / `baoyu-diagram` / `baoyu-url-to-markdown` — Translation & diagrams
- `baoyu-compress-image` / `baoyu-image-cards` / `baoyu-infographic` / `baoyu-slide-deck` / `baoyu-markdown-to-html` — Content creation
- `diagram-design` — Diagram design
- `normalize-format` — Format normalization

### Reflection & Planning
- `reviews-retros-reflection` — Retrospectives
- `extract-thread-spine` — Thread extraction
- `goal-analyzer` — Goal analysis
- `meeting-insights-analyzer` — Meeting analysis
- `information-architecture` — IA design
- `medical-device-mdr-auditor` — MDR audit

## Usage

To use a skill, refer to it by name in your request or ask me to route your task.

Example triggers:
- "用 task-router 分析这个任务"
- "帮我翻译这段文字" (auto-routes to baoyu-translate)
- "画个架构图" (auto-routes to diagram-design or baoyu-diagram)
- "分析这篇论文" (auto-routes through literature-search + knowledge-synthesis)
