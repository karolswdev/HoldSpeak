# Phase 74 — The Run Story, Completed: final summary

- **Closed:** 2026-07-02 — **5/5 stories done**, same-day open-to-close.
- **Branch:** `phase-74-run-story` (merged to `main` by PR).
- **Why it existed:** Phase 73's two recorded hub follow-ups — a run's
  output evaporated with the HTTP response, and the run emitted no frames.

## What shipped, in one paragraph

Ask an agent (or run a chain/workflow) anywhere and the answer is now a
REAL primitive: schema v6 makes artifacts owner-typed (nullable
meeting_id + origin meeting|run, the v5 rebuild recipe, Phase-50
backup-then-apply proven by a facsimile-upgrade test), all three run
routes persist their output with capability lineage and answer with
`artifact_id`, the sync pull gains the run-born lane while the wire keeps
`meeting_id` a plain string (the iPad's non-optional decode unmoved), the
routes broadcast honest `intel_status` frames (running → ready | error,
scope-tagged, ONE bracket per chain, no fabricated tokens — locked by
test), and the desk closes the loop: `runCapability` refreshes and marks
the landed artifact NEW, so the answer MATERIALIZES on the stage wearing
the beat, opens to the model's words with `via <capability>` lineage, and
files into a zone like anything else. The theater plays with zero client
wiring — the one-bus architecture held.

## The closeout walk (HS-74-05, real metal)

One session on `/` against the REAL `.43` endpoint: ask the Owl → the
frames captured `[running, ready]` on the page → the model's `'walked'`
materialized wearing the beat → opened to via-Owl lineage → filed into
the Answers zone through the real membership PUT (the DB row asserted).
`location.pathname` stayed `/` after every beat; zero page errors.

## The numbers

- Suite: **3080 passed, 37 skipped** (3071 at open + 9 new); doc guards
  85; every fired guard (schema snapshot, sync stub, two response pins,
  the voice guard on my own draft) updated honestly in-commit.
- Three real-metal `.43` runs across the phase, each with an
  instruction-following check.

## Findings for the future

1. Run-born artifacts carry `origin='run'` and NULL meeting_id in the DB
   but `""` on every serialized surface — keep it that way; the iPad's
   `meetingId: String` is non-optional.
2. The run routes still return the full output inline; the artifact is
   additive. If outputs get big, pagination lives on the artifact side.
3. The iPad's desk does not yet MATERIALIZE run artifacts with a beat
   (they arrive via sync as ordinary artifacts) — a candidate HSM story.
