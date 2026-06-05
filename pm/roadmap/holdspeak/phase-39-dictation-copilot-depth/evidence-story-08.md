# Evidence — HS-39-08 — Real spoken→enriched dictation e2e + demo

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `tests/fixtures/dictation_demo_project/` (**new**) — `.hs/context.md` /
  `.hs/instructions.md` / `.hs/memory.md` / `.hs/terms.md`, `pyproject.toml`
  (name `ledgerline`), `src/ledgerline/ledger.py`, `src/ledgerline/api/charges.py`.
- `scripts/dictation_enrichment_demo.py` (**new**) — `run_enrichment()` +
  `render()` + `main()`; drives the real pipeline, prints the before/after.
- `tests/e2e/test_dictation_enrichment_e2e.py` (**new**) — gated e2e
  (env + reachability skip), structural assertions, prints `render()`.
- `pm/roadmap/holdspeak/phase-39-dictation-copilot-depth/evidence/dictation_enrichment_demo.txt`
  (**new**) — committed plain-text capture of a real `.43` run.

## Verification artifacts

- Real endpoint (`.43`, `Qwen3.5-9B-UD-Q6_K_XL.gguf`):
  `HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf uv run pytest -q tests/e2e/test_dictation_enrichment_e2e.py`
  → `1 passed in 15.07s`.
- Skip path (no endpoint): `uv run pytest -q tests/e2e/test_dictation_enrichment_e2e.py`
  → `1 skipped`.
- Hermetic full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → `2167 passed, 16 skipped` (the +1 skip vs HS-39-03 is this e2e).
- Ruff (`scripts/…` + the e2e) → `All checks passed!`.
- Demo capture (real `.43`): 446-char rambling dictation →
  ~2.4k-char project-grounded coding task citing `idempotency_keys`,
  `ledger_entries`, the double-entry invariant, integer minor units, and the
  real `src/ledgerline/**` paths — plus a `.hs/memory/*.md`
  context-preservation suggestion. See
  `evidence/dictation_enrichment_demo.txt`.

## Reality check — this is the FIRST real-endpoint validation of Phase 39

Until this story, HS-39-01/02/03 were all fakes. This is the first time the new
dictation code ran against the real `.43` model end-to-end, and it produced a
genuinely useful, project-grounded result. It de-risks the HS-39-07 closeout
(which will reuse this capture) and gives a permanent, re-runnable proof.

## Deviations from plan

- Added mid-phase (not in the original 7-story scaffold) on direct user
  request; phase grew 7→8. The "spoken" input is a crafted realistic
  raw-dictation string rather than `say`→Whisper (the Whisper front-end is
  already covered elsewhere); the enrichment — the valuable, LLM-dependent part
  — is fully real.

## Follow-ups

- Optionally weave corrections (HS-39-02) + model-assisted detection (HS-39-03)
  into the same demo for an all-features showcase.
- A self-hosted CI runner with `HOLDSPEAK_DICTATION_E2E_*` set would run this
  for real on every push; hosted CI will continue to skip it.
