# Plan: Migrate watsonx calls from `generate_text` to `chat` API

## Overview

The `ibm/granite-4-h-small` model is a chat-native, instruction-tuned model that does
**not** respond meaningfully through the legacy `/ml/v1/text/generation` endpoint
(routed via `generate_text()`). Calls to that endpoint return only whitespace.

IBM watsonx.ai itself emits a deprecation warning pointing to `/ml/v1/text/chat`.

This plan migrates both the production service and the diagnostic test script to use
`ModelInference.chat()` with proper `system` + `user` message roles.

**Scope:**
- `src/backend/app/services/ai_service.py` — `WatsonxAdapter` class and `_build_prompt`
- `src/backend/test_watsonx_adapter.py` — diagnostic test script

**Non-goals:**
- No changes to prompt content or `_SYSTEM_MESSAGE`
- No changes to `_parse_llm_response`, mock fallback, or any other logic
- No dependency version changes

---

## Sub-Task 1 — Update `WatsonxAdapter.complete()` to use `chat()`

**Status:** [x] done

### Intent
Replace the deprecated `generate_text()` call in `WatsonxAdapter.complete()` with
`ModelInference.chat()`, passing the prompt as structured `system` + `user` messages
so `ibm/granite-4-h-small` (and other chat-native models) respond correctly.

### Expected Outcomes
- No `WatsonxAPIWarning` deprecation warning when `complete()` is called.
- The model returns a non-empty, structured JSON string.
- The `_parse_llm_response` parser receives real content and produces a valid `CaseAnalysis`.

### Todo List
1. Split `_build_prompt(text: str)` into two parts so `complete()` can receive them
   separately — **or** (simpler) change `complete()` to accept `(system: str, user: str)`
   and update the single call-site in `_watsonx_analysis()`.
   - Chosen approach: keep `_build_prompt` for backward-compat, but add a new
     `_build_messages(text: str) -> list` helper that returns
     `[{"role": "system", "content": _SYSTEM_MESSAGE}, {"role": "user", "content": <case text block>}]`.
2. Change `WatsonxAdapter.complete(prompt: str)` to `complete(messages: list)`.
3. Replace the `self._model.generate_text(...)` call with:
   ```
   response = self._model.chat(messages=messages, params={...})
   return response["choices"][0]["message"]["content"]
   ```
   Keep the same `params` keys (`max_new_tokens`, `temperature`, `repetition_penalty`).
4. Update `_watsonx_analysis()` to call `_get_adapter().complete(_build_messages(text))`
   instead of `_get_adapter().complete(_build_prompt(text))`.
5. Keep (or remove) the now-unused `_build_prompt()` helper — leave it in place to
   avoid breaking anything else; it is harmless.

### Relevant Context
- File: `src/backend/app/services/ai_service.py`
- `WatsonxAdapter.complete` — lines 952–975
- `_build_prompt` — line 1508
- `_watsonx_analysis` call-site — line 1670
- `_SYSTEM_MESSAGE` constant — line 1031 (already a clean system prompt string)
- `_parse_llm_response` — line 1520 (no changes needed here)

---

## Sub-Task 2 — Update `test_watsonx_adapter.py` to use `chat()`

**Status:** [x] done

### Intent
Make the diagnostic test exercise the same API path (`/ml/v1/text/chat`) that
production code now uses, so it gives a truthful signal about whether the model
is reachable and responding.

### Expected Outcomes
- No deprecation warning when the test runs.
- `MODEL RESPONSE:` prints `TEST` (or similar non-empty text).
- The test can be re-run at any time to validate credentials + model health.

### Todo List
1. Replace the `model.generate_text(...)` block with:
   ```python
   response = model.chat(
       messages=[
           {"role": "system", "content": "You are a helpful assistant."},
           {"role": "user", "content": "Return only the word: TEST"},
       ],
       params={"max_new_tokens": 20, "temperature": 0.0},
   )
   text = response["choices"][0]["message"]["content"]
   print("\nMODEL RESPONSE:")
   print(repr(text))
   ```
2. No other changes needed.

### Relevant Context
- File: `src/backend/test_watsonx_adapter.py`
- `model.generate_text` call — lines 40–46
- `print` output — lines 48–49

---

## Implementation Notes

- `ModelInference.chat()` returns a dict. The generated text lives at
  `response["choices"][0]["message"]["content"]`.
- The `params` dict keys accepted by `chat()` are the same as `generate_text()`
  (`max_new_tokens`, `temperature`, `repetition_penalty`).
- Both sub-tasks are independent and can be done in either order.
- Run `python test_watsonx_adapter.py` from `src/backend/` after Sub-Task 2 to
  confirm the model responds before implementing Sub-Task 1.
