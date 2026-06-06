# Evidence — HS-42-06 — Runtime model setup assistant

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

## What shipped

A guided model-setup assistant on `/setup` so a newcomer reaches a working
intelligent-typing runtime without understanding backends — with a one-click
"Test my runtime".

### The self-test — `holdspeak/setup_runtime.py`

`probe_runtime(dictation_cfg, *, http_get=None)` tests the configured runtime and
returns `{ok, status, backend, detail}`, never raising:

- **pipeline disabled → `basic`** (no LLM runtime needed; voice typing works).
- **mlx / llama_cpp →** `resolve_backend` (the existing resolver, raising
  `RuntimeUnavailableError` → `unavailable`) then a **model-path-exists** check
  (`missing_model` / `unconfigured` / `ok`).
- **openai_compatible →** a **time-boxed GET `{base_url}/models` preflight** via
  an **injectable** `http_get` (`unreachable` / `error` / `ok`), so the default
  suite makes no real outbound call.

`runtime_choices()` is the static reference for the four guided choices.
`POST /api/setup/runtime-test` runs it over `Config.load().dictation`.

### The assistant UI — `web/src/pages/setup.astro` + `setup-app.js`

An "Intelligent typing (optional)" card (`#runtime`) with a 2×2 grid of the four
choices — **Basic voice typing · Local Apple Silicon (MLX) · Local GGUF
(llama.cpp) · OpenAI-compatible endpoint** — each showing what it affects, what
it needs, and a **copyable install command** (click-to-copy with a "✓ copied"
state). A **"Test my runtime"** button calls the endpoint and shows a green/red
result; an **"Advanced runtime settings"** button links into the existing
`/dictation` Runtime cockpit (the assistant guides, it doesn't replace it).

## Verification

- **Live (Playwright):** clicking "Test my runtime" on a default config returned
  **"✓ Basic voice typing — no LLM runtime configured. Hold, speak, release works
  as-is."** Screenshot: [`evidence/setup_model_assistant.png`](./evidence/setup_model_assistant.png).
- The endpoint reads the current config; the OpenAI preflight is opt-in (only on
  the test click) and time-boxed.

## Tests run

```
uv run pytest -q tests/unit/test_setup_runtime.py
→ 8 passed   (ruff clean)
```

- basic (pipeline off) → `basic`; local missing/ready/unavailable; openai
  reachable (asserts the `/models` URL) / unreachable / unconfigured; the four
  choices cover basic/mlx/llama_cpp/openai_compatible. All with injected seams —
  **no real network call, no model load**.

Full suite: see the HS-42-06 commit message.

## Acceptance criteria

- [x] Each of the four choices shows extra + needs + scope + a copyable install
      command; a Test button gives a clear pass/fail result.
- [x] Endpoint preflight is opt-in (only on test) + time-boxed and degrades
      gracefully (`unreachable`/`error`, never hangs the UI); covered incl. a
      failure case.
- [x] The advanced Runtime cockpit remains reachable (the "Advanced runtime
      settings" link to `/dictation`) and unchanged.
- [x] Bundle rebuilt; only `web/src` committed; a screenshot of the assistant.
- [x] Default suite green; no real network call in the default suite (preflight
      injected/mocked).
