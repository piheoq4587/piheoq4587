# 中心化 LLM 路由系统 — 使用指南

> 一处修改，全部生效。Key/URL/模型/链顺序变了，只改这一两个文件。

## 文件清单（中心配置目录 `~/.claude/config/`）

| 文件 | 用途 | 改动频率 |
|---|---|---|
| **`llm_config.json`** | 模型元数据 + 角色链定义 | 模型升级/换代时 |
| **`api-credentials.env`** | API key + base URL + 各种凭证 | key 轮换时 |
| `llm_router.py` | 路由器代码（一般不动） | 框架升级时 |
| `opus_helper.py` | Opus few-shot 包装（一般不动） | bug 修复时 |

---

## 三大常见修改场景

### 场景 1: 换 API Key

只改一处：`~/.claude/config/api-credentials.env`

```bash
OPENAI_API_KEY=sk-NEW_KEY_HERE
```

**所有 SciCrew/SciCamel/Skill/MCP 自动用新 key**（下次启动）。

### 场景 2: 换转发地址（tone.nyc.mn → 新代理）

改 `api-credentials.env` 同一处：

```bash
OPENAI_API_BASE=https://newproxy.com/v1
OPENAI_BASE_URL=https://newproxy.com/v1
```

不需要碰任何代码。

### 场景 3: 升级/替换模型（如 GPT-5.5 → GPT-5.6）

1. 改 `~/.claude/config/llm_config.json`：

```jsonc
"models": {
  "gpt-5.6": { "supports_tools": true, "needs_fewshot": false, "max_prompt_kb": 200 },
  "gpt-5.5": { ... },   // 保留作为 fallback 也可
  ...
},
"roles": {
  "tool_capable":   ["gpt-5.6", "grok-4.20-0309-non-reasoning", "gpt-5.4-mini"],
  "synthesis":      ["gpt-5.6", "grok-4.20-0309-non-reasoning", "gpt-5.4-mini"],
  ...
}
```

2. 同步 `api-credentials.env` 末尾的环境变量（scicamel 用）：

```bash
PRIMARY_MODEL=gpt-5.6
```

完成。SciCrew + Skills + scicamel 全部立即用 5.6。

---

## 角色制（不要写死模型名！）

调用方应该按**用途**选模型，不直接写 `model="gpt-5.5"`。

| 角色 | 用途 | 当前链 |
|---|---|---|
| `default` | 通用 | gpt-5.5 → grok-4.20 → gpt-5.4-mini |
| `tool_capable` | 需要调用工具的 agent | gpt-5.5 → grok-4.20 → gpt-5.4-mini |
| `synthesis` | 综合大 prompt 无工具 | gpt-5.5 → grok-4.20 → gpt-5.4-mini |
| `fast_cheap` | 短 prompt 快速响应 | gpt-5.4-mini → grok-4.20 → gpt-5.5 |
| `deep_reasoning_small` | ≤5KB prompt 深度推理 | claude-opus-4.7-n → 4.6-n → gpt-5.5 |

将来 GPT-5.6 来了，只改 `llm_config.json` 把每个角色的链头换成 `gpt-5.6` —— 不需要改任何调用代码。

---

## 各程序接入状态

| 程序 | 接入方式 | 你想换链时改什么 |
|---|---|---|
| **SciCrew** | `core/agno_engine.py` 直接 `import llm_router` | 只改 `llm_config.json` |
| **SciCamel** | 通过环境变量 `PRIMARY_MODEL`/`FALLBACK_MODEL_*` | 改 `llm_config.json` + `api-credentials.env`（同步两处）|
| **ResearchClaw** | 通过 YAML 配置文件 (LlmConfig dataclass) | 改 ResearchClaw 的 yaml |
| **SciSuper** | 通过 CrewAI ConeLLM + opus_helper 副本 | 通过 CrewAI 的配置 |
| **Skills (新写的)** | `from llm_router import call_llm` | 只改 `llm_config.json` |
| **MCP servers** | （如果用 LLM）`from llm_router import call_llm` | 只改 `llm_config.json` |

---

## 给 Skill / MCP / 临时脚本写代码示例

### 最简单：高层 API（自动 fallback）

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/config"))
from llm_router import call_llm

# 自动按 tool_capable 链 cascade，第一个失败自动换下一个
reply = call_llm(
    messages=[{"role": "user", "content": "你好"}],
    role="tool_capable",   # 或 "synthesis" / "fast_cheap" / "deep_reasoning_small"
    max_tokens=1000,
)
print(reply)
```

### Agno Agent（创建一个绑定路由模型的 agent）

```python
from llm_router import make_agno_model
from agno.agent import Agent

agent = Agent(
    model=make_agno_model(role="tool_capable"),  # 自动用 gpt-5.5
    tools=[...],
)
agent.run("...")
```

### 显式指定模型（绕过角色）

```python
from llm_router import make_agno_model
agent = Agent(model=make_agno_model(model_id="gpt-5.4-mini"))
```

---

## 如何为新 Skill 选择角色？

**决策树**：

1. **会用工具吗？**（爬网页、查数据库、查论文等）
   - 是 → `role="tool_capable"`（gpt-5.5）
   - 否 → 看下一步

2. **prompt 大小？**
   - >10KB（综合大量上下文）→ `role="synthesis"`（gpt-5.5）
   - 5-10KB → `role="default"`（gpt-5.5）
   - ≤5KB 且需要深度推理 → `role="deep_reasoning_small"`（4.7-n 优先）
   - ≤5KB 但只要快 → `role="fast_cheap"`（gpt-5.4-mini，4.6 秒响应）

3. **不确定？** → `role="default"` 永远不会错。

---

## 测试中心配置

```bash
# 自检：列出所有角色 + 模型 + 端点
python ~/.claude/config/llm_router.py

# 跑 SciCrew 连通性测试
cd ~/scicrew && .venv/Scripts/python.exe -c "from core.agno_engine import test_api; test_api()"
```

---

## 关键约束（实测 2026-04-25）

⚠️ **claude-opus-4.7-n 和 4.6-n 不能调用工具**——通过 tone.nyc.mn 转发后被 Notion-AI overlay 拦截。

⚠️ **Opus 模型只能处理 ≤5KB prompt**——超过会卡 10+ 分钟超时。

✅ **gpt-5.5 是当前最快的工具调用模型**（14KB+tool 场景 14 秒）。

✅ **gpt-5.4-mini 是最便宜的 fallback**（4.6 秒 ping）。

✅ **grok-4.20-0309-non-reasoning 是稳定备份**（17-22 秒）。

如果你之后发现某个新模型也能调用工具且速度更快，更新 `llm_config.json` 把它加到 `tool_capable` 链头即可。
