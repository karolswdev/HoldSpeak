# HS-45-04 — Replay: prove it learned

- **Project:** holdspeak
- **Phase:** 45
- **Status:** done
- **Depends on:** HS-45-01, HS-45-02
- **Owner:** Claude (Opus 4.8)
- **Evidence:** [evidence-story-04.md](./evidence-story-04.md)

## Problem
The copilot learns (corrections, KB, config), but the user never *sees* it get
better — a past utterance can't be re-run through the now-tuned pipeline. The
"it's learning me" promise stays abstract. Replay makes it tangible: take a real
stored utterance, run it through the **current** pipeline, and show before → after.

## Scope
- **In:**
  - `POST /api/dictation/journal/{id}/replay` — re-runs the stored **transcript**
    of a journal entry through the **current** pipeline in **dry-run mode**
    (no typing), returning the new routing / final text / per-stage latency.
  - A **before/after diff** vs the original journal entry (old block/target/final
    → new), surfaced as a **"Replay"** action on each Journal entry (HS-45-02).
  - **Opt-in re-insert:** an explicit, focus-safe action to *type* the improved
    result into the active target (default **preview-only**; insert is a separate
    deliberate click, never automatic).
  - The satisfying loop: correct an utterance (HS-45-03) → replay it → watch the
    routing change to the corrected target. This is the phase's "it learned"
    payoff.
- **Out:** bulk replay; auto/scheduled replay; replaying audio (we replay the
  stored transcript, not re-transcribe — no mic, and the transcript is the
  durable artifact).

## Acceptance criteria
- [x] `POST /api/dictation/journal/{id}/replay` re-runs the stored transcript
      through the current pipeline (dry-run) and returns new routing + final text
      + latency, without typing anything.
- [x] The Journal shows a per-entry **Replay** action rendering before → after
      (old vs new block/target/final).
- [x] After a correction (HS-45-03) targeting an utterance's gist, replaying that
      utterance demonstrably routes to the corrected target — a test asserts the
      changed outcome (offline, via the target-correction nudge).
- [x] Re-insert is **opt-in + focus-safe** — preview by default; a deliberate
      **Copy improved result** (clipboard) is the re-insert primitive. *OS-typing
      re-insert is deferred:* no web→typer seam exists and typing into the active
      app from a background web click is the exact focus-steal vector this phase
      forbids; the story permits preview-only ("preview alone already proves the
      learning"). Decision recorded in the phase status.
- [x] Replay never mutates the original journal row (a fresh dry-run, `journal=None`);
      suite green; `(cd web && npm run build)` succeeds; **0** `_built/` tracked.

## Test plan
- Unit / API: replay endpoint returns a fresh pipeline result for a stored
  transcript; a correction recorded between the original run and the replay
  changes the routed target. `uv run pytest -q -k replay`.
- Integration: dry-run (records entry) → correct → replay → assert before/after
  diff shows the corrected routing.
- Page-content: the Replay action + before/after markup.
- Live (Playwright): `evidence/replay_before_after.png` (an utterance replayed
  after a correction, showing the changed routing).
- Manual / device: n/a (transcript replay needs no mic).

## Notes / open questions
- **Re-insert scope** — default preview-only; gate the actual typing behind an
  explicit opt-in click, focus-safe. Confirm during build whether insert is in
  scope for v1 or deferred to a follow-up (preview alone already proves the
  learning).
- Replay uses the same dry-run pipeline entry point used elsewhere, so it
  inherits project-root detection + the current config/corrections automatically.
