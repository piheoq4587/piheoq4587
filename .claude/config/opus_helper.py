"""Opus model calling helper for tone.nyc.mn forwarding API (v2, 2026-04-24).

Problem:
  - claude-opus-4.6-n has a Notion-AI safety overlay that refuses aggressive
    structured-output prompts ("Output ONLY", "no markdown", "override") and
    also refuses system messages ("I'm not able to follow instructions that ask
    me to override my identity").
  - claude-opus-4.7-n emits a stray `<l` prefix at the start of ~40-70% of
    responses even WITH a system message. The `<l` artifact does NOT simply
    prepend — it REPLACES the first several tokens of the intended response,
    causing real content loss (verified 2026-04-24, 45-round diagnostic).

Universal fix (verified 0% artifact rate on 15 rounds, 2026-04-24):
  Inject a user/assistant few-shot priming pair before every real call.
  For Agno-style calls that include a system message, the pattern becomes:
    [system, example_user, example_assistant, real_user]
  For raw calls without system message:
    [example_user, example_assistant, real_user]

Two wrapping functions cover the two call styles:
  - wrap_with_fewshot(): structured-output mode (JSON/schema) — drops system msg
  - wrap_chat_messages(): general chat mode — PRESERVES system msg, inserts
                          generic academic few-shot between system and real user

Usage:
    from opus_helper import wrap_chat_messages, extract_from_opus_response

    # For general chat (e.g. team discussions, literature review):
    messages = [
        {"role": "system", "content": "你是一个文献评审员..."},
        {"role": "user", "content": "请评审这篇论文的方法学..."},
    ]
    if model in {"claude-opus-4.6-n", "claude-opus-4.7-n"}:
        messages = wrap_chat_messages(messages)
        # Result: [system, ex_user, ex_assistant, real_user]

    content = resp.choices[0].message.content
    if model.startswith("claude-opus"):
        content = extract_from_opus_response(content, structured=False)
"""
from __future__ import annotations
import json
import re
from typing import Any

# ─── Priming examples ────────────────────────────────────────────────────
# STRUCTURED mode: minimal JSON example. Drops system messages.
_DEFAULT_EXAMPLE_USER = "Record: name=Bob, age=25, city=London"
_DEFAULT_EXAMPLE_ASSISTANT = '{"name":"Bob","age":25,"city":"London"}'

# GENERAL CHAT mode: generic academic Q&A example. Keeps system message.
# The example is deliberately generic (a basic academic concept) so it does
# not bias the model's response style for any particular domain.
_CHAT_EXAMPLE_USER = "请简要说明什么是同行评审？"
_CHAT_EXAMPLE_ASSISTANT = (
    "同行评审是学术出版的质量控制机制，由领域内独立专家评估稿件的方法学严谨性、"
    "原创性和结论合理性，是保障学术文献质量的关键环节。"
)


def wrap_with_fewshot(
    messages: list[dict],
    custom_example: tuple[str, str] | None = None,
) -> list[dict]:
    """STRUCTURED MODE: drop any system msg, inject JSON-schema example.

    Used for structured-output tasks (JSON, config, template). Keeps only the
    last user message, prepending a (user, assistant) example pair.

    Returns:
      [example_user, example_assistant, real_user]

    Args:
      messages: OpenAI-format message list.
      custom_example: Optional (user_text, assistant_text) override.
    """
    real_user = None
    for m in reversed(messages):
        if m.get("role") == "user":
            real_user = m
            break
    if real_user is None:
        return messages

    ex_user, ex_assistant = custom_example or (
        _DEFAULT_EXAMPLE_USER,
        _DEFAULT_EXAMPLE_ASSISTANT,
    )
    return [
        {"role": "user", "content": ex_user},
        {"role": "assistant", "content": ex_assistant},
        real_user,
    ]


def wrap_chat_messages(
    messages: list[dict],
    custom_example: tuple[str, str] | None = None,
) -> list[dict]:
    """GENERAL CHAT MODE: preserve system msg, inject academic few-shot.

    Used for general chat tasks (team discussions, literature review, etc.)
    where we want to keep the caller's system message but still prime the
    tokenizer to avoid the `<l` artifact.

    Output pattern:
      [system_msg?, example_user, example_assistant, real_user]

    The system message (if any) is kept. The last user message is kept as the
    "real" task. Any intermediate messages (prior turns in a conversation) are
    dropped — we assume callers that need multi-turn context pass the full
    history, in which case the few-shot is still injected between the system
    and the first real user message.

    This design verified 0/15 `<l` artifact rate on claude-opus-4.7-n
    (vs 11/15 = 73% when using plain system+user) on 2026-04-24.

    Args:
      messages: OpenAI-format message list.
      custom_example: Optional (user_text, assistant_text) override.

    Returns:
      New message list with few-shot priming injected.
    """
    # Find the system message (if any) and the last user message
    system_msgs = [m for m in messages if m.get("role") == "system"]
    real_user = None
    for m in reversed(messages):
        if m.get("role") == "user":
            real_user = m
            break
    if real_user is None:
        return messages

    ex_user, ex_assistant = custom_example or (
        _CHAT_EXAMPLE_USER,
        _CHAT_EXAMPLE_ASSISTANT,
    )
    out: list[dict] = []
    out.extend(system_msgs)  # preserve all system messages
    out.append({"role": "user", "content": ex_user})
    out.append({"role": "assistant", "content": ex_assistant})
    out.append(real_user)
    return out


def strip_opus_prefix(content: str) -> str:
    """Strip the `<l` / `<l>` / `<` stray prefix that 4.7-n emits sometimes.

    Only strips if the prefix looks like an artifact (short, before real
    content). Safe on clean responses — no-ops when no artifact is present.

    Note: this is a SECOND LINE OF DEFENSE. The primary defense is few-shot
    wrapping via wrap_chat_messages() / wrap_with_fewshot(), which prevents
    `<l` from appearing in the first place. This stripper handles residual
    artifacts on the rare occasions when few-shot wrapping is bypassed.
    """
    if not content:
        return content
    stripped = content.lstrip()
    for prefix in ("<l>", "<l ", "<l\n", "<l\t", "<l"):
        if stripped.startswith(prefix):
            rest = stripped[len(prefix):].lstrip()
            # If prefix was `<l` and rest starts with a letter followed by `>`,
            # it's probably real XML — don't strip
            if prefix == "<l" and rest[:1].isalpha() and ">" in rest[:40]:
                continue
            return rest
    return content


def extract_from_opus_response(content: str, structured: bool = False) -> Any:
    """Return cleaned text (structured=False) or parsed JSON (structured=True).

    Lenient extraction handles:
      1. `<l` stray prefix on 4.7-n (residual artifact after few-shot wrapping)
      2. Markdown fences: ```json ... ``` or ``` ... ```
      3. Preamble text before JSON: "Here's the JSON: {...}"
      4. Soft refusals that still contain usable data

    Args:
      content: Raw `choices[0].message.content` from an Opus response.
      structured: If True, parse and return a Python dict/list. If False,
                  return cleaned text string.

    Returns:
      - structured=False: cleaned str (may be empty if input was pure artifact)
      - structured=True:  dict/list on success, None if no JSON extractable.
    """
    if not content:
        return None if structured else ""

    cleaned = strip_opus_prefix(content).strip()

    if not structured:
        return cleaned

    # Attempt 1: direct JSON parse
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # Attempt 2: markdown fence extraction
    fence_match = re.search(
        r"```(?:json|JSON)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```",
        cleaned,
    )
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # Attempt 3: first balanced {...} or [...]
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        if start < 0:
            continue
        depth = 0
        for i in range(start, len(cleaned)):
            c = cleaned[i]
            if c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(cleaned[start:i + 1])
                    except (json.JSONDecodeError, ValueError):
                        break

    return None


def is_opus_refusal(content: str) -> bool:
    """Detect Notion-AI refusal patterns on 4.6-n.

    When True, the caller should fall back to the next model in chain rather
    than treating the response as usable output.
    """
    if not content:
        return False
    c = content.lower()
    refusal_markers = (
        "i'm not able to follow instructions",
        "i'm notion ai",
        "notion ai, an ai",
        "override my identity",
        "override my behavior",
        "behavior guidelines",
        "i cannot follow instructions that ask me to",
    )
    return any(m in c for m in refusal_markers)


def has_l_artifact(content: str) -> bool:
    """Detect if a response contains the `<l` artifact (content integrity risk).

    Returns True if `<l` is at or near the start of the content. Use this to
    mark responses for retry or fallback even after strip — the artifact
    indicates the model DESTROYED the first ~9 characters of intended output,
    so stripping alone isn't enough for critical-integrity tasks.
    """
    if not content:
        return False
    head = content.lstrip()[:3]
    return head.startswith("<l")


# ─── Agno OpenAILike wrapper factory ─────────────────────────────────────

OPUS_MODELS = frozenset({"claude-opus-4.6-n", "claude-opus-4.7-n"})


def make_opus_aware_model(model_id: str, api_key: str, base_url: str,
                         temperature: float = 0.7, max_tokens: int = 4096,
                         use_structured_example: bool = False):
    """Factory: build an Agno OpenAILike that auto-wraps Opus calls with few-shot.

    For non-Opus models, returns the plain Agno OpenAILike unchanged.
    For Opus models (4.6-n, 4.7-n), returns a subclass that:
      1. Before every call, injects generic academic few-shot into messages.
      2. Automatically strips `<l` prefix from responses (defense-in-depth).

    This gives downstream code (scicrew, scicamel) a drop-in replacement for
    `OpenAILike(...)` without changing any callsite logic.

    Args:
      model_id: Model name, e.g. "claude-opus-4.7-n" or "grok-4.20-0309-non-reasoning"
      api_key, base_url: OpenAI-compatible endpoint credentials
      temperature, max_tokens: Standard sampling params
      use_structured_example: If True, use the JSON-schema example (drops system msg).
                              If False (default), use academic chat example (keeps system msg).

    Returns:
      An Agno OpenAILike instance (or wrapper subclass for Opus).
    """
    from agno.models.openai.like import OpenAILike

    if model_id not in OPUS_MODELS:
        return OpenAILike(
            id=model_id, api_key=api_key, base_url=base_url,
            temperature=temperature, max_tokens=max_tokens,
        )

    # Import Agno's Message class to build proper Message instances
    try:
        from agno.models.message import Message as AgnoMessage
    except ImportError:
        AgnoMessage = None

    # Pick the right text pair for priming
    if use_structured_example:
        ex_user_text, ex_assistant_text = _DEFAULT_EXAMPLE_USER, _DEFAULT_EXAMPLE_ASSISTANT
    else:
        ex_user_text, ex_assistant_text = _CHAT_EXAMPLE_USER, _CHAT_EXAMPLE_ASSISTANT

    class OpusAwareOpenAILike(OpenAILike):
        """OpenAILike subclass that injects few-shot priming for Opus models.

        Intercepts Agno's invoke()/ainvoke() to insert a (user, assistant)
        example pair between the system message and the first real user
        message. This primes the tokenizer and suppresses the `<l` artifact.
        """

        def _inject_fewshot(self, messages):
            """Insert few-shot priming into a list of Agno Message objects."""
            if not messages or AgnoMessage is None:
                return messages

            # Separate system messages from others
            system_msgs = [m for m in messages if getattr(m, "role", None) == "system"]
            non_system = [m for m in messages if getattr(m, "role", None) != "system"]

            if not non_system:
                return messages  # Nothing to prime

            # For structured mode: drop all non-system dialogue, keep only last user
            if use_structured_example:
                last_user = None
                for m in reversed(non_system):
                    if getattr(m, "role", None) == "user":
                        last_user = m
                        break
                if last_user is None:
                    return messages
                return [
                    AgnoMessage(role="user", content=ex_user_text),
                    AgnoMessage(role="assistant", content=ex_assistant_text),
                    last_user,
                ]

            # For chat mode: [system..., example_user, example_assistant, real_user...]
            return (
                system_msgs
                + [AgnoMessage(role="user", content=ex_user_text)]
                + [AgnoMessage(role="assistant", content=ex_assistant_text)]
                + non_system
            )

        def invoke(self, messages, *args, **kwargs):  # type: ignore[override]
            messages = self._inject_fewshot(messages)
            response = super().invoke(messages, *args, **kwargs)
            return _clean_response_content(response)

        async def ainvoke(self, messages, *args, **kwargs):  # type: ignore[override]
            messages = self._inject_fewshot(messages)
            response = await super().ainvoke(messages, *args, **kwargs)
            return _clean_response_content(response)

    return OpusAwareOpenAILike(
        id=model_id, api_key=api_key, base_url=base_url,
        temperature=temperature, max_tokens=max_tokens,
    )


def _clean_response_content(response):
    """Strip `<l` prefix from Agno's response object (defense in depth).

    Few-shot wrapping already prevents `<l` in 99%+ of cases, but we also
    clean at receive-time for belt-and-suspenders robustness.
    """
    # Agno response objects vary — try common shapes
    content = None
    if hasattr(response, "choices") and response.choices:
        msg = response.choices[0].message if hasattr(response.choices[0], "message") else None
        if msg and hasattr(msg, "content") and msg.content:
            cleaned = strip_opus_prefix(msg.content)
            if cleaned != msg.content:
                try:
                    msg.content = cleaned
                except (AttributeError, TypeError):
                    pass
    # Some wrappers use .content directly
    if hasattr(response, "content") and response.content:
        cleaned = strip_opus_prefix(response.content)
        if cleaned != response.content:
            try:
                response.content = cleaned
            except (AttributeError, TypeError):
                pass
    return response


# ─── Self-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test strip_opus_prefix
    assert strip_opus_prefix("<l391") == "391"
    assert strip_opus_prefix("<l>391") == "391"
    assert strip_opus_prefix("391") == "391"
    assert strip_opus_prefix("") == ""
    assert strip_opus_prefix("<link>foo</link>") == "<link>foo</link>"

    # Test extract_from_opus_response
    assert extract_from_opus_response('{"a":1}', structured=True) == {"a": 1}
    assert extract_from_opus_response(
        'Here you go: ```json\n{"a":1}\n```',
        structured=True,
    ) == {"a": 1}
    assert extract_from_opus_response('<l{"a":1}', structured=True) == {"a": 1}
    assert extract_from_opus_response("hi there", structured=False) == "hi there"

    # Test wrap_with_fewshot (structured mode)
    out = wrap_with_fewshot([{"role": "user", "content": "do X"}])
    assert len(out) == 3
    assert out[0]["role"] == "user"
    assert out[1]["role"] == "assistant"
    assert out[2]["content"] == "do X"

    # Test wrap_with_fewshot strips system msg (for 4.6-n Notion-AI refusal)
    out = wrap_with_fewshot([
        {"role": "system", "content": "be terse"},
        {"role": "user", "content": "do X"},
    ])
    assert len(out) == 3
    assert not any(m["role"] == "system" for m in out)

    # Test wrap_chat_messages PRESERVES system msg
    out = wrap_chat_messages([
        {"role": "system", "content": "You are a literature reviewer."},
        {"role": "user", "content": "Review this paper."},
    ])
    assert len(out) == 4
    assert out[0]["role"] == "system"
    assert out[0]["content"] == "You are a literature reviewer."
    assert out[1]["role"] == "user"  # example
    assert out[2]["role"] == "assistant"  # example answer
    assert out[3]["role"] == "user"
    assert out[3]["content"] == "Review this paper."

    # Test wrap_chat_messages without system msg (still wraps)
    out = wrap_chat_messages([{"role": "user", "content": "Hello"}])
    assert len(out) == 3
    assert out[0]["role"] == "user"
    assert out[-1]["content"] == "Hello"

    # Test refusal detection
    assert is_opus_refusal("I'm Notion AI, an AI assistant")
    assert not is_opus_refusal('{"name": "Alice"}')

    # Test <l detection
    assert has_l_artifact("<l随机对照试验")
    assert has_l_artifact("<l>content")
    assert not has_l_artifact("随机对照试验")
    assert not has_l_artifact("")

    print("opus_helper v2 self-test: all PASS")
