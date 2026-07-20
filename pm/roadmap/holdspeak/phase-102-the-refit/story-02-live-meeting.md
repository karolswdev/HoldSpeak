# HS-102-02 — Live Meeting: a working face

- **Project:** holdspeak
- **Phase:** 102
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-102-07

## The owner's words (the bar)

> "'Live Meeting' window is honestly a design and usability joke."

## Problem

The round-7 inventory already convicted this face and it shipped no
fix: `web/src/pages/cores/LiveCore.tsx` is a plumbing dashboard
wearing a WORKING posture's clothes. Before any meeting runs, the
person meets wire stats (Connection / Duration / Segments / Room as
a stat strip), a "Bookmark" SurfaceSection with an "Optional label"
label+input stack, an "Intent routing" preset Select, and a
"Preview route" TEXTAREA — developer plumbing, visible at the
moment the person just wants to hit Record. The working posture rule
(AGENT_BRIEF §3): one generous column, the verb huge, chrome silent.

## Scope

- In: `LiveCore.tsx` recomposed to the working posture. The face
  leads with the ONE verb (Start / Stop, huge, display step) and the
  live transcript as the material (the script composition, like the
  meeting detail's transcript); duration/segments as one quiet facts
  line (round-6 phrasing), never a stat-tile strip; Bookmark becomes
  a moment verb ON the transcript (mark now; name it inline
  afterward — no pre-filled form); intent routing preset and the
  Preview-route textarea fold behind the gear (configuring posture)
  or die on this face; the meeting-details fields (Title/Tags)
  appear quietly only when there is something to save (the round-7
  drop-well grammar). Mockup-grade before/after is part of this
  story's eyes-first step.
- Out: capture/recorder wire routes (unchanged); the Record wing of
  Meetings (HS-102-04); the recording orb/bar indicator (shipped,
  system moments).

## Acceptance criteria

- [ ] Hands-first ledger recorded (headed, 1440 + 393, idle AND
      mid-recording states) before the first code change.
- [ ] Idle face: the verb leads at display step; zero wire stats,
      zero forms, zero textareas visible.
- [ ] Recording face: the transcript IS the material (script
      composition, time gutter), one quiet facts line; Bookmark is a
      verb on the moment, not a form section.
- [ ] Plumbing (routing preset, preview route) lives behind the gear
      in a configuring posture, or is gone from this window.
- [ ] Driven live on a staged hub: start → speak (or seeded frames)
      → bookmark a moment → stop → the meeting materializes; both
      viewports, all screenshots read.
- [ ] A named guard: a walk leg (or geometry assertion) pins the
      idle face — no `Field`/textarea/stat-strip renders before
      recording starts.

## Test plan

- Web vitest; token gate; vocabulary + interior-canon guards;
  geometry walk; the live start→bookmark→stop drive on the staged
  hub, headed, both viewports.

## Evidence required

- The ledger; before/after at both viewports; the live-drive record;
  guard output.
