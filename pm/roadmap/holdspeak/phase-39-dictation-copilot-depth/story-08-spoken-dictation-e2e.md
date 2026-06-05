# HS-39-08 — Real spoken→enriched dictation e2e + demo

- **Project:** holdspeak
- **Phase:** 39
- **Status:** done
- **Depends on:** HS-39-01
- **Unblocks:** HS-39-07 (closeout reuses this as the headline before/after)
- **Owner:** unassigned

## Problem

Everything in HS-39-01/02/03 was proven with **injected fake runtimes** — no
real LLM had ever touched the new code. That's a real gap: three features
stacked up with zero real-endpoint validation, and the phase's "might" (rough
speech → a precise, project-grounded coding task) was never actually *shown*.
Added mid-phase on direct user request: a **real** spoken→enriched e2e against
a live OpenAI-compatible endpoint, over a fixture project with real `.hs/`
context + code, with a beautiful before/after, **and committed as a permanent
(gated) test**.

## Scope

- In:
  - A realistic fixture project `tests/fixtures/dictation_demo_project/` —
    `.hs/{context,instructions,memory,terms}.md` (a double-entry payment
    ledger "ledgerline") + a `pyproject.toml` + real `src/ledgerline/**` code.
  - A reusable demo `scripts/dictation_enrichment_demo.py` — `run_enrichment()`
    drives the **real** pipeline (multi-pass project-rewriter) via
    `build_pipeline` over an `openai_compatible` runtime, and `render()` prints
    a Signal-styled before→after (SPOKEN → ENRICHED → context-preservation
    suggestion + stats). Runnable standalone (`uv run python scripts/…`).
  - A gated e2e `tests/e2e/test_dictation_enrichment_e2e.py` — runs only when
    `HOLDSPEAK_DICTATION_E2E_BASE_URL` + `_MODEL` point at a reachable endpoint
    (auto-skips otherwise, like the spoken-meeting e2e); asserts the enrich
    happened, `.hs` context loaded, and the task is grounded in project
    specifics (`ledger_entries` / `idempotency_keys` / double-entry / …).
  - A committed plain-text capture under `evidence/`.
- Out:
  - `say`→Whisper front-end (the "spoken" is a realistic raw-dictation string;
    the Whisper path is covered by the spoken-meeting e2e + the HS-32-04 smoke).
  - Running against a hosted-CI LLM (a LAN/self-hosted endpoint is required;
    hosted CI skips — see Notes).
  - Asserting exact LLM text (output varies; assertions are structural).

## Acceptance criteria

- [x] Fixture project with `.hs/` context + code resolves via the real
      `detect_project_for_cwd` and loads `instructions/context/memory/terms`. —
      e2e asserts `result.hs_files` includes `memory` + `instructions`.
- [x] `run_enrichment()` drives the real multi-pass project-rewriter through an
      `openai_compatible` runtime and returns before/after + suggestion + stats.
- [x] The e2e auto-skips with no endpoint (hosted-CI safe) and **passes against
      a real endpoint** — verified on `.43` (`Qwen3.5-9B-UD-Q6_K_XL.gguf`):
      `1 passed in 15.07s`.
- [x] Enriched output is substantially richer (≥1.5×) and grounded in project
      specifics, not generic prose (≥2 grounding markers). — assertions + the
      committed capture (446 → ~2.4k chars).
- [x] A beautiful before→after renders to stdout; a plain capture is committed
      under `evidence/dictation_enrichment_demo.txt`.

## Test plan

- Gated e2e (real): `HOLDSPEAK_DICTATION_E2E_BASE_URL=… HOLDSPEAK_DICTATION_E2E_MODEL=… uv run pytest -s tests/e2e/test_dictation_enrichment_e2e.py`.
- Skip path (CI): `uv run pytest -q tests/e2e/test_dictation_enrichment_e2e.py` → skipped.
- Hermetic suite unaffected: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → e2e skips.

## Notes / open questions

- **"Our CI test" caveat (honest):** a LAN/self-hosted-LLM test cannot run in
  hosted GitHub CI — there's no endpoint there, so it skips (green). It runs for
  real wherever the endpoint is reachable: the author's machine, or a
  self-hosted runner with `HOLDSPEAK_DICTATION_E2E_*` set. This mirrors the
  existing opt-in spoken-meeting e2e tests exactly.
- Demo uses `stages=["project-rewriter"]` + `rewrite_passes=2` (the most
  visually dramatic path). Corrections (HS-39-02) + model-assisted detection
  (HS-39-03) are unit-proven; a future pass could weave them into the same demo.
- Added mid-phase per user request; the phase grew 7→8 stories. HS-39-07
  closeout remains the finale and will reuse this capture as the headline
  before/after.
