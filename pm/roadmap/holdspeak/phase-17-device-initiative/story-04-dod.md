# HS-17-04 — DoD: Protocol-Doc Consolidation + Final-Summary + Phase Exit

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-17-01, HS-17-02, HS-17-03
- **Unblocks:** AIPI-Lite phase 4 close (AIPI-4-05 / AIPI-4-06 become unblocked once HS-17 ships)
- **Owner:** unassigned

## Problem

Close phase 17: consolidate `docs/DEVICE_PROTOCOL.md`'s phase-17 additions, write the final-summary, flip the parent README's phase index, and surface the AIPI-Lite-phase-4 unblock signal so the device-side roadmap can pull the trigger on AIPI-4-05 / AIPI-4-06.

## Scope

### In

- `docs/DEVICE_PROTOCOL.md` consolidation:
  - "Frame types" section lists `device_health` + `query` alongside the existing handshake / status / event frame types.
  - Each new frame has: schema (Pydantic-style), example JSON, field semantics, error-handling notes.
  - Version note: phase-17 additions are backwards-compatible (no breaking changes to existing frames); document the version bump if the doc has versioning.
- `final-summary.md` per `~/dev/HoldSpeak/pm/roadmap/roadmap-builder.md` §2.5:
  - Goal recap + yes/no/partial.
  - Exit criteria final state with evidence links.
  - Stories shipped table.
  - Stories cut or deferred.
  - Surprises + lessons.
  - **Handoff to AIPI-Lite phase 4** (this is the load-bearing handoff): name the bridge-side stories now unblocked (AIPI-4-05, AIPI-4-06), point at the wire schemas, point at the integration tests as the contract.
  - Final asset/test posture.
- Parent README updates:
  - `Last updated` bumped.
  - Phase 17 row → `done`.
  - Current-phase pointer moves to whatever's next (HS-15 if not started; HS-16 if HS-15 already started/done; the user picks).
- `current-phase-status.md` frozen — no more edits after phase close.
- AIPI-Lite roadmap handoff note: record the exact unblock signal for `~/dev/esp32/AIPI-Lite-Voice-Bridge/pm/roadmap/aipi-lite/phase-4-active-device/current-phase-status.md` so AIPI-4-05 + AIPI-4-06 can move from `blocked` → `backlog` in the AIPI-Lite repo's own PMO flow. This HoldSpeak story documents the signal; it does not require a cross-repo edit to pass.

### Out

- Any new functionality. This is a close-out story, not a feature story.
- Migration tooling for older AIPI-Lite firmware (phase-17 additions are backwards-compatible by design; nothing to migrate).
- Backporting `device_health` / `query` to pre-HS-14 versions. There are no pre-HS-14 versions of this substrate.

## Acceptance Criteria

- [ ] `docs/DEVICE_PROTOCOL.md` lists both new frame types in the "Frame types" section, with schema + example + semantics.
- [ ] `evidence-story-{01,02,03}.md` files exist for each of the substrate + UI stories.
- [ ] `final-summary.md` written per `roadmap-builder.md` §2.5 — every required section present; handoff section explicitly names AIPI-4-05 / AIPI-4-06 as now-unblocked.
- [ ] Parent README phase index row 17 → `done`; `Last updated` bumped.
- [ ] `current-phase-status.md` frozen with a "phase closed" notice at the top + a pointer to `final-summary.md`.
- [ ] AIPI-Lite unblock signal documented clearly: AIPI-4-05 + AIPI-4-06 may be flipped `blocked` → `backlog` in the AIPI-Lite repo once that repo is touched. If the AIPI-Lite repo is available in the same working session, coordinate a separate PMO-compliant edit there; do not make it a HoldSpeak acceptance gate.
- [ ] `pytest -q` (or HoldSpeak's documented test command) reports no regressions; full integration suite green.
- [ ] PMO contract certification clean (`.tmp/CONTRACT.md` boxes all `[x]`).

## Test Plan

- **Methodology compliance** per `roadmap-builder.md` §5.6:
  - Every story file has `Status: done` with paired `evidence-story-{n}.md`.
  - Final-summary follows §2.5 sections.
  - Parent README + current-phase-status updated.
- **Functional regression:** existing HS test suite green; the `device_audio_ws` integration tests added in HS-17-01 / 02 stay green.
- **Manual:** read `docs/DEVICE_PROTOCOL.md` end-to-end as a "fresh user implementing a new device" simulation; note any frictions.

## Notes

- **Cross-repo handoff coordination.** Flipping AIPI-4-05 / AIPI-4-06 from `blocked` → `backlog` in the AIPI-Lite repo is a separate working-tree change in a separate repo, with its own PMO contract certification. Recording the unblock signal here keeps the audit trail honest without making another repo's status file a HoldSpeak gate.
- **Final-summary handoff section is the load-bearing part.** Anyone reading HS-17's final-summary should walk away knowing: (a) what shipped, (b) what's now possible that wasn't before, (c) what AIPI-Lite-side stories are now unblocked + where to find them. The wire schemas are the contract; point at them explicitly.
- **No protocol-doc versioning** unless `DEVICE_PROTOCOL.md` already has it. AIPI-2 was permitted to land `extra="forbid"` Pydantic models that *implicitly* version by rejecting unknown fields; the doc itself is the human-readable canon and doesn't need a separate version number for additive changes.
