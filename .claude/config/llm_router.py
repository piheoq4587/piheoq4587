"""Central LLM router. Single source of truth for model/endpoint/chain config.

All Skills, MCPs, and downstream programs (scicrew, scicamel, researchclaw,
scisuper) should import this module instead of hardcoding model names, base
URLs, or fallback chains.

When config needs to change (key rotated, new model added, chain reordered):
edit ~/.claude/config/llm_config.json — that's it. Every caller picks up the
change automatically on next invocation (config is re-read each call).

Public API:
  get_endpoint() -> dict          # {base_url, api_key} from env
  get_chain(role="default") -> list[str]   # model fallback chain (cooldown-aware)
  get_model_meta(model) -> dict   # {supports_tools, needs_fewshot, max_prompt_kb, ...}
  needs_fewshot(model) -> bool    # whether to wrap with opus_helper
  call_llm(messages, role="default", **kwargs) -> str   # cascade-fallback HTTP call
  make_agno_model(role="default", model_id=None)        # Agno OpenAILike (Opus-aware)

Example use in a Skill:
  import sys, os
  sys.path.insert(0, os.path.expanduser("~/.claude/config"))
  from llm_router import call_llm, make_agno_model

  reply = call_llm([{"role":"user","content":"hi"}], role="tool_capable")
"""
from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path
from typing import Any

# ─── Config paths ─────────────────────────────────────────────────────────
_CONFIG_DIR = Path.home() / ".claude" / "config"
_CONFIG_PATH = _CONFIG_DIR / "llm_config.json"
_ENV_PATH = _CONFIG_DIR / "api-credentials.env"

# Ensure opus_helper is importable (it lives next to this file)
if str(_CONFIG_DIR) not in sys.path:
    sys.path.insert(0, str(_CONFIG_DIR))


# ─── Lazy loaders ─────────────────────────────────────────────────────────
def _load_env() -> None:
    """Load api-credentials.env into os.environ (idempotent)."""
    if not _ENV_PATH.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_PATH, override=False)
    except ImportError:
        # Fallback: manual parse
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _load_config() -> dict:
    """Read llm_config.json fresh every call (so edits take effect immediately)."""
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Central LLM config missing: {_CONFIG_PATH}\n"
            f"Expected at ~/.claude/config/llm_config.json"
        )
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# In-memory cooldown state (per-process; survives within a session)
_COOLDOWN_STATE: dict[str, float] = {}


# ─── Public API ───────────────────────────────────────────────────────────
def get_endpoint(reload_env: bool = True) -> dict:
    """Return {base_url, api_key} from env (re-loaded by default)."""
    if reload_env:
        _load_env()
    cfg = _load_config()
    ep = cfg["endpoint"]
    base = os.getenv(ep["base_url_env"]) or ep.get("default_base_url")
    key = os.getenv(ep["api_key_env"]) or ""
    return {"base_url": base, "api_key": key}


def get_model_meta(model: str) -> dict:
    """Return metadata dict for a model (or empty dict if unknown)."""
    return _load_config()["models"].get(model, {})


def needs_fewshot(model: str) -> bool:
    """True if the model requires opus_helper few-shot wrapping (4.7-n, 4.6-n)."""
    return bool(get_model_meta(model).get("needs_fewshot", False))


def supports_tools(model: str) -> bool:
    """True if model can call OpenAI-style functions/tools via this proxy."""
    return bool(get_model_meta(model).get("supports_tools", False))


def is_disabled(model: str) -> bool:
    """True if model is marked disabled in config (skip during fallback)."""
    return bool(get_model_meta(model).get("disabled", False))


def needs_direct_answer_guard(model: str) -> bool:
    """True if model needs the Gemini direct-answer guard prepended (avoids self-intro)."""
    return bool(get_model_meta(model).get("needs_direct_answer_guard", False))


# Gemini direct-answer guard text (per LLM_PROXY_MODEL_ROUTING_PORTING_GUIDE_2026-05-06 §8)
_GEMINI_GUARD = "直接完成下面任务；不要自我介绍，不要确认指令，不要询问我还需要什么。"


def _apply_direct_answer_guard(messages: list[dict]) -> list[dict]:
    """Prepend the Gemini guard sentence to the last user message."""
    msgs = [dict(m) for m in messages]
    for i in range(len(msgs) - 1, -1, -1):
        if msgs[i].get("role") == "user":
            content = msgs[i].get("content", "")
            if isinstance(content, str) and _GEMINI_GUARD not in content:
                msgs[i]["content"] = f"{_GEMINI_GUARD}\n\n{content}"
            break
    return msgs


def list_roles() -> list[str]:
    """Return all defined role names."""
    return [k for k in _load_config()["roles"].keys() if not k.startswith("_")]


def get_policy(name: str, default: Any = None) -> Any:
    """Lookup a policy value (cooldown_ttl_seconds, request_timeout_seconds, ...)."""
    return _load_config().get("policies", {}).get(name, default)


def get_chain(role: str = "default") -> list[str]:
    """Return model fallback chain for a role, with disabled models removed
    and cooled models moved to tail.

    Unknown roles fall back to 'default'. Returns [] if neither defined.
    """
    cfg = _load_config()
    raw_chain = cfg["roles"].get(role) or cfg["roles"].get("default") or []
    if not raw_chain:
        return []

    models_meta = cfg.get("models", {})

    # Skip disabled models
    chain = [m for m in raw_chain if not models_meta.get(m, {}).get("disabled", False)]

    # Apply cooldown reordering
    now = time.time()
    active, cooled = [], []
    for m in chain:
        if _COOLDOWN_STATE.get(m, 0) > now:
            cooled.append(m)
        else:
            active.append(m)
    return active + cooled


def mark_cooldown(model: str, reason: str = "") -> None:
    """Mark a model for cooldown (TTL from policy). Auto-applied by call_llm."""
    ttl = int(get_policy("cooldown_ttl_seconds", 900))
    _COOLDOWN_STATE[model] = time.time() + ttl


def _is_cooldown_error(err_text: str) -> bool:
    t = (err_text or "").lower()
    return (
        "429" in t
        or "model_cooldown" in t
        or "cooling down" in t
        or "rate limit" in t
        or ("ssl" in t and "eof" in t)
    )


# ─── Direct HTTP call with cascade fallback ────────────────────────────────
def call_llm(
    messages: list[dict],
    role: str = "default",
    structured: bool = False,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    timeout: int | None = None,
    tools: list[dict] | None = None,
) -> str:
    """High-level: try chain in order, return first successful content string.

    For Opus models, automatically wraps with opus_helper few-shot.
    Raises RuntimeError only if ALL models in chain fail.
    """
    from openai import OpenAI

    ep = get_endpoint()
    chain = get_chain(role)
    if not chain:
        raise RuntimeError(f"No models defined for role '{role}'")

    timeout = timeout or int(get_policy("request_timeout_seconds", 120))
    client = OpenAI(api_key=ep["api_key"], base_url=ep["base_url"], timeout=timeout)

    last_err = None
    for model in chain:
        try:
            msgs = list(messages)

            # Apply few-shot wrapping for Opus models
            if needs_fewshot(model):
                try:
                    from opus_helper import wrap_chat_messages, wrap_with_fewshot
                    msgs = (wrap_with_fewshot if structured else wrap_chat_messages)(msgs)
                except ImportError:
                    pass  # graceful degrade

            # Apply Gemini direct-answer guard if model needs it
            if needs_direct_answer_guard(model):
                msgs = _apply_direct_answer_guard(msgs)

            kwargs = {
                "model": model,
                "messages": msgs,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            # Only attach tools if the model supports them AND caller provided them
            if tools and supports_tools(model):
                kwargs["tools"] = tools

            resp = client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message
            content = (msg.content or "").strip()

            # Tool-call path: when caller passed tools and model returned tool_calls,
            # serialize the tool_calls as JSON so the caller can dispatch.
            tool_calls = getattr(msg, "tool_calls", None)
            if tools and tool_calls:
                serialized = []
                for tc in tool_calls:
                    serialized.append({
                        "id": getattr(tc, "id", None),
                        "type": getattr(tc, "type", "function"),
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    })
                return json.dumps({"tool_calls": serialized, "content": content}, ensure_ascii=False)

            # Post-process Opus output (strip <l artifact, parse JSON if structured)
            if needs_fewshot(model):
                try:
                    from opus_helper import extract_from_opus_response, is_opus_refusal
                    if is_opus_refusal(content):
                        last_err = f"{model}: opus refusal"
                        continue
                    extracted = extract_from_opus_response(content, structured=structured)
                    if structured:
                        return extracted  # dict/list
                    if extracted:
                        content = extracted
                except ImportError:
                    pass

            if not content:
                last_err = f"{model}: empty response"
                continue
            return content

        except Exception as e:
            err_text = str(e)
            last_err = f"{model}: {err_text[:200]}"
            if _is_cooldown_error(err_text):
                mark_cooldown(model, err_text[:120])
            continue

    raise RuntimeError(f"All models in chain '{role}' failed. Last error: {last_err}")


# ─── High-value combo (lead + critique + final synthesis) ──────────────────
def call_llm_combo(
    messages: list[dict],
    max_tokens: int = 4000,
    critique_count: int = 2,
    temperature: float = 0.5,
    timeout: int | None = None,
) -> str:
    """High-value non-tool route: lead model + N critique models + final synthesizer.

    Pipeline:
      1. Lead model (role='lead_synthesis') drafts initial answer.
      2. critique_count models from role='cross_check' independently critique.
      3. role='lead_synthesis' produces final synthesis incorporating critiques.

    Use for grant ideas, scientific judgement, high-stakes reasoning.

    Args:
      messages: original user prompt (OpenAI message list).
      max_tokens: per-call cap.
      critique_count: how many cross-check critiques to gather (1-3).
      temperature: sampling temperature for lead/critique calls.
    """
    if critique_count < 1:
        critique_count = 1
    if critique_count > 3:
        critique_count = 3

    lead_chain = get_chain("lead_synthesis")
    cross_chain = get_chain("cross_check")
    if not lead_chain:
        raise RuntimeError("No models defined for role 'lead_synthesis'")

    # Step 1: lead draft
    draft = call_llm(messages, role="lead_synthesis",
                     max_tokens=max_tokens, temperature=temperature, timeout=timeout)

    # Step 2: gather critiques from distinct cross-check models
    critique_text = ""
    distinct_critics = [m for m in cross_chain if m not in (lead_chain[:1])][:critique_count]
    if not distinct_critics and cross_chain:
        distinct_critics = cross_chain[:critique_count]

    user_prompt_text = ""
    for m in messages:
        if m.get("role") == "user":
            user_prompt_text = m.get("content", "")
            break

    for i, model_name in enumerate(distinct_critics, 1):
        try:
            crit_msgs = [{
                "role": "user",
                "content": (
                    f"Original task:\n{user_prompt_text}\n\n"
                    f"Draft answer to critique:\n{draft}\n\n"
                    "Please give a rigorous, specific critique: list factual errors, "
                    "missing evidence, logical gaps, and concrete improvement suggestions. "
                    "Keep it under 400 words."
                )
            }]
            chain_for_critic = [model_name] + [m for m in cross_chain if m != model_name]
            critique = ""
            for cm in chain_for_critic:
                try:
                    critique = call_llm(crit_msgs, role="cross_check",
                                        max_tokens=600, temperature=0.4, timeout=timeout)
                    break
                except Exception:
                    continue
            if critique:
                critique_text += f"\n--- Critique {i} ({model_name}) ---\n{critique}\n"
        except Exception:
            continue

    # Step 3: final synthesis
    final_msgs = [{
        "role": "user",
        "content": (
            f"Original task:\n{user_prompt_text}\n\n"
            f"Initial draft:\n{draft}\n\n"
            f"Critiques:\n{critique_text}\n\n"
            "Produce the FINAL improved answer. Address every valid critique, "
            "preserve the draft's strengths, and write in clear prose."
        )
    }]
    return call_llm(final_msgs, role="lead_synthesis",
                    max_tokens=max_tokens, temperature=temperature, timeout=timeout)


# ─── Agno model factory ────────────────────────────────────────────────────
def make_agno_model(role: str = "default", model_id: str | None = None,
                    temperature: float = 0.7, max_tokens: int = 4096):
    """Build an Agno OpenAILike for the head model in a role's chain.

    For Opus models, returns OpusAwareOpenAILike (auto few-shot at invoke time).
    For others, returns plain OpenAILike.

    Args:
      role: Role name (default/tool_capable/synthesis/...). Used if model_id=None.
      model_id: Explicit model name (overrides role).
    """
    ep = get_endpoint()
    if model_id is None:
        chain = get_chain(role)
        if not chain:
            raise RuntimeError(f"No models defined for role '{role}'")
        model_id = chain[0]

    if needs_fewshot(model_id):
        from opus_helper import make_opus_aware_model
        return make_opus_aware_model(
            model_id=model_id,
            api_key=ep["api_key"],
            base_url=ep["base_url"],
            temperature=temperature,
            max_tokens=max_tokens,
            use_structured_example=False,
        )

    from agno.models.openai.like import OpenAILike
    return OpenAILike(
        id=model_id,
        api_key=ep["api_key"],
        base_url=ep["base_url"],
        temperature=temperature,
        max_tokens=max_tokens,
    )


def apply_to_env(role: str = "tool_capable", complex_role: str = "synthesis") -> None:
    """Export the role's chain as PRIMARY_MODEL/FALLBACK_MODEL_1..3 env vars.

    Useful for programs that drive their chain off env vars (scicamel).
    Call this once at startup; existing values in os.environ are NOT overwritten.

    Args:
      role: Role whose chain populates PRIMARY_MODEL / FALLBACK_MODEL_1..3
      complex_role: Role for COMPLEX_PRIMARY_MODEL / COMPLEX_FALLBACK_MODEL_1..3
    """
    _load_env()
    for prefix, r in [("", role), ("COMPLEX_", complex_role)]:
        chain = get_chain(r)
        names = [f"{prefix}PRIMARY_MODEL"] + [f"{prefix}FALLBACK_MODEL_{i}" for i in range(1, 4)]
        for name, model in zip(names, chain[:4]):
            os.environ.setdefault(name, model)


# ─── Self-test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Config:    {_CONFIG_PATH}")
    print(f"Env file:  {_ENV_PATH}")
    ep = get_endpoint()
    print(f"Endpoint:  {ep['base_url']}  (key {'set' if ep['api_key'] else 'MISSING'})")
    print(f"\nDefined roles:")
    for r in list_roles():
        print(f"  {r:25s} -> {' -> '.join(get_chain(r))}")
    print(f"\nPolicies:")
    cfg = _load_config()
    for k, v in cfg.get("policies", {}).items():
        print(f"  {k}: {v}")
    print(f"\nModels metadata:")
    for m, meta in cfg["models"].items():
        flags = []
        if meta.get("disabled"): flags.append("DISABLED")
        if meta.get("supports_tools"): flags.append("tools")
        if meta.get("needs_fewshot"): flags.append("fewshot")
        if meta.get("needs_direct_answer_guard"): flags.append("guard")
        kb = meta.get("max_prompt_kb", "?")
        print(f"  {m:35s} [{', '.join(flags) or 'plain':24s}]  max={kb}KB")
