# HS-36-04 — Dynamic, digression-heavy multi-topic spoken-e2e

- **Project:** holdspeak
- **Phase:** 36
- **Status:** not-started
- **Depends on:** none (independent of the UI stories; pairs well with them)
- **Unblocks:** HS-36-05 (its rich output is the closeout showcase)
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
  - Same harness as the existing scenarios: `say` (multi-voice) → per-line wav →
    Whisper → transcript segments → real `.43` `PluginHost` (deferred queue drained) →
    `synthesize_and_persist` → temp SQLite → `MeetingWebServer` → Playwright screenshot.
  - **Structural, noise-tolerant assertions** (the real LLM is non-deterministic and
    the input is intentionally messy): a long transcript is produced; the pipeline
    completes without error; a **rich** artifact set results — assert **≥3 distinct
    artifact types** are produced (don't pin exact types), and that real signal survived
    the noise (e.g. at least one action item *or* decision *or* risk artifact present).
    Never assert exact wording.
  - Opt-in identical to the others (`HOLDSPEAK_SPOKEN_E2E=1`; module-skips otherwise).
- **Out:**
  - Changing the router/plugins to handle noise "better" — this is a *test*, not a
    behavior change. If it reveals a real routing weakness, file a follow-up; don't
    fix it inside this story.
  - Asserting a specific set of artifact types (that would make a deliberately
    non-deterministic test flaky).

## Acceptance criteria

- [ ] A new opt-in spoken-e2e scenario with a long, digression-heavy, multi-topic,
      multi-speaker script exists in `tests/e2e/test_spoken_meeting_e2e.py`.
- [ ] Assertions are structural + noise-tolerant: long transcript, no pipeline error,
      **≥3 distinct artifact types**, and at least one "signal" artifact (action item /
      decision / risk) — no exact-wording or exact-type-set assertions.
- [ ] Opt-in/module-skip matches the existing scenarios; default suite green without
      the opt-in.
- [ ] **Verified once for real against `.43`** — run output captured; the rich artifact
      set is the showcase fixture for the closeout screenshot.

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
