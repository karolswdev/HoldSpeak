# Phase 42 — First-Run Delight & Daily Confidence — Final Summary

- **Phase opened:** 2026-06-06
- **Phase closed:** 2026-06-06
- **Stories shipped:** 8 (HS-42-01 … HS-42-08)

## Goal — was it met?

Original promise:

> A user goes from fresh clone to a **verified first dictation** — with visible
> privacy/trust state and **zero file editing** — inside one guided local cockpit,
> held to a measurable time-to-first-dictation (TTFD) headline.

**Yes — proven by an all-in-app, zero-file-edit dogfood** (`scripts/dogfood_first_run.py`):

```
1. launch → /setup interactive: 1.13s
2. one primary action: "Set a valid local model path (…)"
   guided first-dictation steps shown
3. model assistant test: ✓ Basic voice typing — no LLM runtime configured…
4. first dictation: It worked — text landed in your app. You're all set.
   durable milestone set (by the runtime on a real dictation): True
5. returning user → dashboard (no nag)
6. config.json hand edits: NONE (zero file editing)

TTFD-to-ready: 1.13s · all-in-app, zero file edits · DOGFOOD OK
```

The one un-automatable step is literally speaking into a mic — everything up to
and through the in-app "✓ It worked" confirmation is exercised here, and the
real-app magic-moment was separately proven live (HS-42-04: a `dictation_typed`
broadcast → the success banner + transcript). The real-mic stopwatch on a
physical device remains a manual capture (hardware-gated, the same posture as the
metal/spoken-e2e suites).

## What shipped (by story)

| Story | Outcome |
|---|---|
| HS-42-01 | The **setup-state contract** — `GET /api/setup/status`, an **adapter** over `collect_doctor_checks()` (1:1, drift-guarded) + readiness + egress + presence, cheap via `skip_network`; the durable **`first_run` milestone** (`db.milestones`, survives restart). |
| HS-42-02 | **Global settings completion** — the interim "consolidating / History → Settings" drawer retired into a real shell-level **`/settings`** page; the gear links to it; save round-trip proven live. |
| HS-42-03 | The **welcome / `/setup`** route (brand hero · dynamic headline · progress · one primary action · needs-attention list · ready grid · Privacy/Presence cards) + a **`/` first-run guard** (redirect only when `first_run\|blocked` — never nag) + a **CLI launch nudge**. |
| HS-42-04 | The **guided first dictation** — steps + readiness row + **live WS feedback** ("✓ It worked — text landed in your app" + transcript) + a fallback ladder; the **`FIRST_DICTATION_SUCCESS` milestone** set at the real dictation-success points (`first_run` flips false). |
| HS-42-05 | The **ambient Trust & Privacy chip + panel** — a persistent shell posture chip (Local only · Configured endpoint · Writes need approval · Needs attention) opening a full "what can leave this machine?" panel. |
| HS-42-06 | The **runtime model setup assistant** — the four backend choices (Basic · MLX · GGUF · OpenAI-compatible) with copyable installs + a one-click **Test my runtime** (injectable, time-boxed preflight). |
| HS-42-07 | **Presence onboarding** — a guided step with an honest per-platform tier, the focus invariant, copyable enable commands, and a faithful inline HUD preview. |
| HS-42-08 | **Closeout** — this summary, the TTFD dogfood, docs leading with the guided path, README/HANDOVER, doc-guards, PR. |

## Exit criteria — final state

- [x] Fresh launch exposes `/setup` without docs; a healthy returning user is
      **not** nagged (the dogfood's step 5).
- [x] `/api/setup/status` is an **adapter over `collect_doctor_checks()`** — a
      test proves every doctor `FAIL` surfaces (HS-42-01).
- [x] `first_run` is a durable milestone that survives relaunch (HS-42-01/04).
- [x] A guided first-dictation proves the **real external-app** path (live WS
      magic-moment); the real-mic frame is hardware-gated.
- [x] Privacy/egress state is visible **ambiently** (the shell TrustChip).
- [x] Global settings live at a real surface; **no live copy says "consolidating"
      / "History → Settings"** (guarded by a test).
- [x] Runtime model setup has guided basic/local/GGUF/OpenAI-compatible paths;
      the advanced `/dictation` cockpit remains.
- [x] Desktop presence is discoverable + accurately tiered per platform.
- [x] Restrained PixelLab (one brand mark + status glyphs/preview).
- [x] All optional features off ⇒ default local-first + byte-identical.
- [x] **TTFD captured** (the dogfood: 1.13s to a guided ready state, zero file
      edits); docs lead with the guided path; `final-summary.md`; README → done.

## Verification

- Full suite **2306 passed, 16 skipped** at close (2283 at HS-42-01; +~120 across
  the phase). Every story added committed tests; no real network/LLM call in the
  default suite; **0** `holdspeak/static/_built/` files tracked.
- Screenshots (in `evidence/`): `settings_page` · `setup_page` · `setup_guided` ·
  `setup_first_dictation_done` · `setup_dictation_success_live` · `trust_local` ·
  `trust_cloud` · `setup_model_assistant` · `setup_presence_onboarding`; the TTFD
  transcript in `first_run_dogfood.txt`.

## Notes

- **Arrival, not capability** — the phase added no new intelligence; it made the
  existing depth feel coherent, safe, and delightful, and deleted the interim
  shell debt.
- The deterministic transcription proof remains the existing `core_path_smoke`
  CI test (the fixture WAV lives in `tests/`, not the installed package), so the
  production first-dictation uses the user's real speech.
