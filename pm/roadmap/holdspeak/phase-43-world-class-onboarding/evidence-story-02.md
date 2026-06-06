# Evidence — HS-43-02 — Model picker step

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-43-world-class-onboarding`
- **Owner:** unassigned

## What shipped

The wizard's Model step is now a real **selectable picker** (the last placeholder
is gone — every wizard step is real).

### The picker — `welcome.astro` + `welcome-app.js`

- A `role="radiogroup"` of four **selectable tiles**: **Basic voice typing · Local ·
  Apple Silicon (MLX) · Local · GGUF (llama.cpp) · OpenAI-compatible** — each with a
  filled-radio selected state (accent border + glow), the name, what it affects
  (Dictation / Dictation + meetings), and a short blurb. Distinct from the other
  steps (a selection grid).
- **Selecting a tile persists** via `PUT /api/settings` — Basic → pipeline off;
  the others → pipeline on + `dictation.runtime.backend` set.
- A **"Test my runtime"** button reuses the HS-42-06 `POST /api/setup/runtime-test`
  and shows a green/red result; the **copyable install command** for the selected
  backend appears beneath.

## Verification

- **Live (Playwright):** selecting the GGUF tile persisted `dictation.runtime.backend:
  "llama_cpp"` + `pipeline.enabled: true` **to disk**, and "Test my runtime"
  honestly reported *"✕ Backend 'llama_cpp' requires the 'llama-cpp-python'
  package…"* with the install command. Screenshot:
  [`wizard_model.png`](./evidence/wizard_model.png).

## Tests run

```
uv run pytest -q tests/integration/test_web_welcome_wizard.py   → passed
```

- `test_model_step_is_a_real_picker` — no placeholders remain; a radiogroup of the
  four backends; selection persists via `/api/settings`; the Test reuses the
  runtime-test endpoint.

Full suite: see the HS-43-02 commit message.

## Acceptance criteria

- [x] The Model step lets a user choose Basic/Local/Endpoint with a clear selected
      state + a one-click Test result; reuses the HS-42-06 endpoint; selection
      persists to config.
- [x] Distinct visual treatment (selection grid); reduced-motion safe; suite green.
