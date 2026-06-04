# HS-36-04 — Dynamic, digression-heavy multi-topic spoken-e2e

- **Project:** holdspeak
- **Phase:** 36
- **Status:** done (2026-06-04). Evidence: [evidence-story-04.md](./evidence-story-04.md).
- **Depends on:** none (independent of the UI stories; pairs well with them)
- **Unblocks:** HS-36-05 (the BEFORE baseline + repro for the routing fix)
- **Owner:** unassigned

## Problem

Both existing spoken-e2e scenarios are **clean, scripted** meetings that march
topic-by-topic (product/architecture/delivery; incident/comms). Real meetings are
messy — people open with small talk, digress mid-thought, interrupt, double back
("wait, what were we saying?"), drop an action item in passing, and cover several
unrelated things in one session. We have **no** e2e that models that. Two gaps result:

1. **Pipeline robustness is untested against noise** — can transcription → multi-intent
   routing → the plugin chains still pull real signal (decisions, action items, risks)
   out of a conversation full of tangents and chit-chat?
2. **The artifact UI is only ever exercised with tidy, sparse output.** A realistic
   meeting fires *several* intent chains at once and produces a dense, varied set of
   artifacts — exactly the material needed to stress-test and screenshot the new
   "elevated" artifact cards (HS-36-01/02/03): many types on one screen, long cells,
   overflow, copy-all.

This story adds a third spoken-e2e: one long, dynamic, human-sounding meeting.

## Scope

- **In:**
  - A new scenario in `tests/e2e/test_spoken_meeting_e2e.py` (e.g.
    `test_spoken_dynamic_meeting_end_to_end`) with a **long, multi-speaker script** that
    deliberately models real speech: opening small talk / a digression (broken coffee
    machine, weekend), drift into a genuine product or planning topic, an interruption,
    an offhand tangent, a real **decision** reached messily, **action items** dropped in
    passing ("I'll poke at that", "can someone ping infra"), a **risk** raised as an
    aside, a callback to an earlier thread, and a "anyway, where were we" reset — so the
    conversation spans **several intents** (and several plugin chains fire).
  - **Drive the REAL MIR routing path**, not a hardcoded chain. Unlike the existing two
    scenarios (which execute a fixed plugin list over the whole transcript), this one
    routes through the actual pipeline — `say` → Whisper → transcript segments →
    `process_meeting_state` (build_intent_windows → score → select_active_intents →
    dispatch per window) → `synthesize_and_persist` → temp SQLite → `MeetingWebServer` →
    Playwright. This is essential: only the real routing path exhibits the dilution
    weakness, so it's what makes the before/after meaningful.
  - **Capture the BEFORE screenshot.** With the *current* (pre-HS-36-05) routing, render
    `/history` for this meeting and save `evidence/dynamic_meeting_before.png` — the
    baseline showing intents diluted away / a sparse artifact set. (HS-36-05 captures the
    AFTER on the same script.)
  - **Structural, noise-tolerant assertions** (the real LLM is non-deterministic and
    the input is intentionally messy): a long transcript is produced; the pipeline
    completes without error; **≥1 artifact** results. Deliberately **loose** — this
    scenario's job is to *expose* how much the old routing drops, not to assert richness
    (that's HS-36-05's bar). Record the produced intents/artifacts in the run output so
    the before/after is quantifiable. Never assert exact wording or an exact type set.
  - Opt-in identical to the others (`HOLDSPEAK_SPOKEN_E2E=1`; module-skips otherwise).
- **Out:**
  - The routing *fix* — that's HS-36-05. This story builds the messy meeting + drives
    the real routing + captures the BEFORE baseline. It may legitimately show a sparse /
    intent-dropping result; that's the point.
  - Asserting a specific set of artifact types (that would make a deliberately
    non-deterministic test flaky).

## Acceptance criteria

- [ ] A new opt-in spoken-e2e scenario with a long, digression-heavy, multi-topic,
      multi-speaker script exists in `tests/e2e/test_spoken_meeting_e2e.py`.
- [ ] The scenario routes via the **real** `process_meeting_state` MIR path (windowing +
      scoring + dispatch), not a hardcoded chain.
- [ ] Assertions are structural + noise-tolerant: long transcript, no pipeline error,
      ≥1 artifact — no exact-wording or exact-type-set assertions (richness is HS-36-05's
      bar, not this one's).
- [ ] The **BEFORE** screenshot (`evidence/dynamic_meeting_before.png`) + the run's
      produced intents/artifacts are captured against the current routing, for the
      before/after comparison.
- [ ] Opt-in/module-skip matches the existing scenarios; default suite green without
      the opt-in.
- [ ] **Verified once for real against `.43`** — run output captured.

## Test plan

- `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s \
   tests/e2e/test_spoken_meeting_e2e.py::test_spoken_dynamic_meeting_end_to_end`
  (dangerouslyDisableSandbox to reach `.43`) — passes; ≥3 artifact types; rich output.
- Default `uv run pytest -q --ignore=tests/e2e/test_metal.py` — module-skips, suite green.

## Notes / open questions

- Keep the script genuinely messy but keep *some* real substance in it, or the run can
  legitimately produce too few artifacts — tune the script (not the assertions) until a
  real `.43` run reliably clears ≥3 types.
- This is the meeting to screenshot for HS-36-05 (many cards, varied types) — it best
  demonstrates the overflow fix + card density.
- If the messy input exposes a genuine routing/transcription weakness, record it as a
  follow-up (candidate for a future hardening phase), per the "Out" scope.
