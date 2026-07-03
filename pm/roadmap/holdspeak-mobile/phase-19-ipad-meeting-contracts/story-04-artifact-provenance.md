# HSM-19-04 — Artifact provenance: the confidence ring + sources

- **Project:** holdspeak-mobile
- **Phase:** 19
- **Status:** in-progress — **built, wired, and sim-proven** (PR #159: `ConfidenceRing` +
  the artifacts card in `CompanionShellApp.swift`, over `meetingArtifacts(meetingId:)` from
  PR #151/`3544fc1`; screenshot `screenshots/confidence-ring-ipad.png`). Remaining: the
  evidence trail + the story flip.
- **Depends on:** `HTTPDesktopClient+Artifacts.swift`; hub route
  `GET /api/meetings/{id}/artifacts` (`holdspeak/web/routes/meetings/insights.py:117`).
- **Unblocks:** Phase 20's compact pass and Phase 21's honesty work both build on this
  render.
- **Owner:** unassigned

## Problem (as audited — now closed in code)

`Models.swift` carried `confidence` and `sources` and the iPad render dropped both: the
machine's certainty and the "synthesized from" trail were invisible. The audit's deeper
question — does the iPad ever read the hub's persisted `/artifacts`? — is answered: it does
now, via `meetingArtifacts`, no longer relying solely on changeset sync.

## What shipped

1. **The confidence ring** (`ConfidenceRing`, `CompanionShellApp.swift:46`): the synthesis
   confidence as a banded filled arc (≥0.75 green / ≥0.5 amber / low red); a nil confidence
   renders dimmed, never invented.
2. **Sources on the card**: "Synthesized from transcript · decision" — the provenance trail
   as a compact line, plus the status pill (accepted / needs review / rejected).
3. **Wired end to end**: tapping a desktop meeting loads artifacts + aftercare together
   (`loadArtifacts`, `CompanionShellApp.swift:175`).

## Design notes locked by this story

- The desk app's local `ReviewUI` artifacts intentionally carry **no ring**: handwritten
  notes are confidence-1.0 by construction; a ring there would be decoration, not honesty.
  Hub-provenance rendering is the Companion shell's job.
- `/api/all-action-items` remains unread from Swift — named, deliberately out (no iPad
  surface consumes the cross-meeting rollup yet).

## What closes the story

The evidence file quoting the shipped code + the sim screenshot, and the phase-status flip.
Real-metal verification joins the 19-07 walk.

## Test plan

- `swift test` green (`*ClientTests` cover the artifacts decode incl. the raw-ISO timestamp
  posture from the EQ-W6 metal audit).
- Sim proof: `HS_SHELL_DEMO=artifacts` (three confidences banding green/amber/red) —
  already committed as `screenshots/confidence-ring-ipad.png`.
