# HS-42-06 — Runtime model setup assistant

- **Project:** holdspeak
- **Phase:** 42
- **Status:** backlog
- **Depends on:** HS-42-01
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The runtime page has the controls, but model/backend setup is still expert-shaped:
a newcomer must understand backends, extras, model paths, and endpoints before
reaching a working state.

## Scope

- In:
  - A guided assistant (inside Setup or the Runtime tab) with four clear choices:
    **Basic voice typing only · Local Apple Silicon (MLX) · Local GGUF/llama.cpp ·
    OpenAI-compatible endpoint.** Each shows: the required install extra, the model
    path/endpoint, whether it affects dictation / meeting intel / both, a **Test**
    button with a clear result, and copyable install/setup commands **only when
    needed**.
  - An opt-in, time-boxed **endpoint preflight** for the OpenAI-compatible choice
    (the deferred network call from HS-42-01).
  - The assistant **links into** the advanced Runtime cockpit and never removes the
    advanced fields.
- Out:
  - New backends or model formats.
  - Auto-downloading models.

## Acceptance criteria

- [ ] Each of the four choices shows extra + path/endpoint + scope + a Test button
      with a clear pass/fail result; copyable commands appear only when needed.
- [ ] Endpoint preflight is opt-in + time-boxed and degrades gracefully on failure
      (routes to a fix, never hangs the UI); covered by tests incl. a preflight
      failure.
- [ ] The advanced Runtime cockpit remains reachable and unchanged.
- [ ] Bundle rebuilt; only `web/src` committed; a screenshot per backend choice.
- [ ] Default suite green; no real network call in the default suite (preflight
      injected/mocked).

## Test plan

- Unit/integration: choice → validation; endpoint preflight success + failure
  (injected client).
- Frontend: `cd web && npm run build && npm run shots`.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Reuse the existing `/api/settings` GET/PUT + `DictationPipelineConfig` /
  `LLMRuntimeConfig` validation; the assistant is a guided front-end over them.
