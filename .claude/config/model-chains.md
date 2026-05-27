# Model Chain Configuration (canonical)
Endpoint: `https://tone.nyc.mn/v1`. API key is loaded from `api-credentials.env`.
Revision 2026-05-07: user-requested Grok-first routing. All central router roles now place the two Grok models first:
```text
grok-4.20-0309-reasoning -> grok-4.20-0309-non-reasoning -> claude-opus-4.7-n -> gpt-5.5-n -> gemini-3.1-pro-n -> claude-opus-4.6-n
```
## Active roles
The source of truth is `llm_config.json`. Older programs that only read environment variables should use:
```text
PRIMARY_MODEL=grok-4.20-0309-reasoning
FALLBACK_MODEL_1=grok-4.20-0309-non-reasoning
COMPLEX_PRIMARY_MODEL=grok-4.20-0309-reasoning
COMPLEX_FALLBACK_MODEL_1=grok-4.20-0309-non-reasoning
RESEARCH_MODEL_PRIMARY=grok-4.20-0309-reasoning
RESEARCH_MODEL_FALLBACK_1=grok-4.20-0309-non-reasoning
```
## Model notes
- `grok-4.20-0309-reasoning`: first model for research/deep reasoning and structured outputs.
- `grok-4.20-0309-non-reasoning`: second model and fast fallback; OpenAI-compatible tool/function calling.
- `claude-opus-4.7-n` and `claude-opus-4.6-n`: later fallbacks only. Any new code that calls these through `https://tone.nyc.mn/v1` must use `opus_helper.py` (`wrap_chat_messages` / `wrap_with_fewshot`) before sending and `extract_from_opus_response` after receiving.
- No-suffix GPT aliases remain disabled unless a fresh live proxy test proves they work.
## Operational rules
1. Import `llm_router.py` where possible instead of hardcoding model names.
2. Treat timeout, connection reset, empty content, JSON parse failure, `429`, `model_cooldown`, or `cooling down` as fallback triggers.
3. Keep cooldown TTL at 900 seconds.
4. Do not print API keys in logs.
