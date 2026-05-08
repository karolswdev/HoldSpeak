# HS-14-08 - Phase 14 Exit + DoD + Protocol Docs + Cross-Network Deferral

- **Project:** holdspeak
- **Phase:** 14
- **Status:** done
- **Depends on:** HS-14-01, HS-14-02, HS-14-03, HS-14-04, HS-14-05, HS-14-06, HS-14-07
- **Unblocks:** phase 15
- **Owner:** unassigned

## Problem

Phase 14 closes when the substrate is documented, regression-clean,
and the cross-network deferral is recorded with explicit hand-off
to phase 15. This story is the discipline gate, not new functional
work.

## Scope

- **In:**
  - `docs/DEVICE_PROTOCOL.md` covering: handshake JSON,
    auth/PSK, control message types, audio frame format,
    server-to-device status messages, inbound device events,
    close codes, and a worked end-to-end example (handshake →
    start → 3 PCM frames → stop → status messages).
  - `pm/roadmap/holdspeak/README.md`: phase index updated —
    phase 14 status flips to `done`, phase 15 row added with
    `not-started` status pointing at the cross-network theme,
    "Last updated" bumped, "Current phase" pointer moves to
    phase 15.
  - `phase-14-aipi-lite-devices/final-summary.md` per the
    `roadmap-builder.md` template: goal recap, exit criteria
    final state with evidence links, story table, surprises +
    lessons, handoff to phase 15.
  - Full regression sweep: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
    green at ≥ phase-13 baseline (1406 / 13 skipped).
  - `current-phase-status.md` frozen — no further edits after
    phase close (per PMO contract §6).

- **Out:**
  - Any phase-15 work (cross-network reach, multi-SSID, public
    URL, tunnels). Phase 15's `current-phase-status.md` is
    written at phase 15 open, not here.
  - Designer-handoff screenshots — phase 14 is API-only with
    no UI surface; this is recorded in the final-summary
    "Surprises and lessons" with the explicit reasoning.

## Acceptance Criteria

- [x] `docs/DEVICE_PROTOCOL.md` exists and includes a working
  example.
- [x] All HS-14-01..07 stories show `Status: done` in their
  story files with paired `evidence-story-{n}.md` files.
- [x] `final-summary.md` exists, follows the template, and
  records the cross-network deferral with the trigger.
- [x] Regression sweep
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` green at
  ≥ phase-13 baseline. **1520 passed / 5 skipped** vs. the
  1406 / 13 baseline; 2 pre-existing pre-phase-14 failures
  documented in evidence.
- [x] `pm/roadmap/holdspeak/README.md` reflects phase 14 done
  + phase 15 not-started.

## Test Plan

- Unit / integration: full regression as above.
- Manual: re-run the AIPI-Lite end-to-end (voice-type a
  sentence; run a 5-min meeting with one device participating;
  long-press during meeting → bookmark visible in saved
  transcript). Capture the saved transcript JSON snippet for
  evidence.

## Notes

- Per PMO-CONTRACT.md §1: the regression command output goes
  in `evidence-story-08.md`, not summarized.
- The "no UI in phase 14" decision (recorded in the phase
  current-phase-status.md "Out" list) means designer-handoff
  is genuinely n/a here. The final-summary records that
  reasoning so a future agent doesn't re-litigate it.
- The cross-network handoff line in the final-summary should
  name what assumptions phase 14 baked in that phase 15
  needs to re-examine: TLS termination point, PSK rotation
  semantics under reconnects, tunnel-vs-direct addressing,
  per-device labels persisting across network changes.
