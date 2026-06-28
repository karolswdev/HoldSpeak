# HSM-20-04 — The forms + screens at compact width (connect, settings, sheets, the hold-bar teleprompter)

- **Project:** holdspeak-mobile
- **Phase:** 20
- **Status:** done (sim) — connect Port/Token stack + the iPhone hold-bar teleprompter + coder-card
  clamps shipped. The action-sheet/editor **scrim → rising-sheet reframe** is carried to a focused
  follow-up (those sheets already fit 390pt; the reframe is a larger, riskier no-modal polish best
  walked on device). Device walk = 20-05.
- **Evidence:** `evidence-story-04.md`.
- **Depends on:** 20-01 (`DeskCamera` + `laneWidth`).
- **Unblocks:** nothing downstream.
- **Owner:** unassigned

## Problem

The non-desk screens inherit iPad widths and rows. The companion connect screen packs Port + Token
two-up at a fixed maxWidth (`CompanionShellApp.swift:651–653`, inside `maxWidth: 560`); the
agent/chain editors are 560/740 modals (`DeskAgents.swift:618/906`); the action sheets are
460-wide; and the iPhone dictation surface has a **dedicated vision beat** (the HOLD BAR
teleprompter, `EXPERIENCE-VISION-2026-06-27.md:65`) that does not exist yet.

> **CORRECTION to the parity audit / status doc:** the unwrapped Port+Token row is at
> `CompanionShellApp.swift:651–653`, **not** `MeetingCaptureApp.swift:1641` (that line is unrelated).

## The design

1. **Connect screen (lane):** stack Port and Token vertically (or make Port flexible) below
   `camera == .lane`; clamp the `maxWidth: 560` container via `laneWidth`. Keep every field's
   speak-to-fill mic (credentials/ports stay paste/number by design).
2. **The agent/chain editors** (`DeskAgents.swift` `AgentEditor` 560×740, `ChainEditor` 560, member
   picker 420): clamp via `laneWidth` and reframe the dim-scrim as the hand-built rising sheet on
   lane (consistent with 20-02). The builder fields keep their mics.
3. **The action sheets** (`DioSendCard`/`DioActSheet`/`DioRunTargetSheet`/`DioRouteSheet`,
   460/440-wide) — if not already reframed in 20-02, clamp + rising-sheet them here.
4. **The iPhone HOLD-BAR teleprompter** (the vision's signature dictation moment): the dictation
   mic promotes to a persistent **bottom-edge hold bar** (accent-gradient capsule, thumb zone) on
   the dictate screen; press-and-hold reflows to a **bottom-up** single-column teleprompter that
   fills from the bar ("you said" muted nearest the thumb, "→ Cursor" full weight above, destination
   + egress as one pill at the top). **No dim toward the bar** (a dim is a scrim); the bar's
   elevation + the rising stack carry focus. Release commits (`.medium` haptic, `.success` on land);
   "trace ›" pushes a full screen with a working back control.
5. **Settings + the two sanctioned full-screen sheets** (a recording, settings) stay as full-screen
   destinations — the no-modal law governs *primitive editing*, not these (vision §4.3 "honest
   scope"). Just verify they fit 390pt.

## Scope

- **In:** the connect Port/Token stack; clamping + rising-sheet the agent/chain editors and action
  sheets; the iPhone hold-bar teleprompter; verifying settings/full-screen sheets at 390pt.
- **Out:** the desk lane (20-02); the capture canvas (20-03).

## Proof

- iPhone sim: connect stacks cleanly; editors fit; the hold-bar teleprompter reflows bottom-up with
  no dim; every field keeps its mic; the egress pill is present (never prose).
- `swift test` + both sim builds green. Device walk = 20-05.
</content>
