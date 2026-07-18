# Issue 01 — LLM Model Deprecation Warning

## Status

`open` — low priority, non-blocking

## Description

On server startup, NVIDIA AI Endpoints emits the following warning:

```
UserWarning: Model meta/llama-4-scout-17b-16e-instruct on endpoint
https://integrate.api.nvidia.com/v1 is deprecated and may be removed
in a future release.
```

The model still works today. If NVIDIA removes it, all LLM calls will fail silently or raise at runtime.

## Root Cause

The model name is **hardcoded** as a string literal in `backend/app/graph/tools/llm.py`:

```python
# app/graph/tools/llm.py — current (bad)
llm = ChatNVIDIA(
    model="meta/llama-4-scout-17b-16e-instruct",   # ← hardcoded
    ...
)
```

If the model is removed or renamed, every agent that calls `llm.invoke()` or `llm.with_structured_output()` will break simultaneously.

## Fix

Move the model name to an environment variable so it can be swapped without a code change.

**`backend/.env`** — add:
```
NVIDIA_MODEL=meta/llama-4-maverick-17b-128e-instruct
```

**`backend/.env.example`** — document it:
```
NVIDIA_MODEL=meta/llama-4-maverick-17b-128e-instruct
```

**`backend/app/graph/tools/llm.py`** — update:
```python
llm = ChatNVIDIA(
    api_key=os.getenv("NVIDIA_API_KEY"),
    model=os.getenv("NVIDIA_MODEL", "meta/llama-4-maverick-17b-128e-instruct"),
    temperature=0.2,
    top_p=0.7,
)
```

The `os.getenv("NVIDIA_MODEL", "...")` default means the app still works if `.env` is missing the key — it falls back to the new default.

## Candidate Replacement Models

| Model | Notes |
|---|---|
| `meta/llama-4-maverick-17b-128e-instruct` | Llama 4, actively supported, likely successor |
| `meta/llama-3.3-70b-instruct` | Stable, widely used, higher quality |
| `nvidia/llama-3.1-nemotron-70b-instruct` | NVIDIA-tuned, good for structured output |

## Acceptance Criteria

- [ ] `NVIDIA_MODEL` env var added to `.env.example` with a non-deprecated default
- [ ] `llm.py` reads model name from env var with a fallback
- [ ] Deprecation warning no longer appears on startup
- [ ] All agents still return valid structured output after the swap

## Related Files

- [`app/graph/tools/llm.py`](../backend/app/graph/tools/llm.py)
- [`backend/.env.example`](../backend/.env.example)