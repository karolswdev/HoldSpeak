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

## Design direction (grounded in a live drive, 2026-07-21)

Driven headed: the moment `Record meeting` fires — before a word is
spoken, `00:00`/`0 segments` — the face already shows a four-cell
`connected/00:00/0/recording` stat strip, a "Bookmark" section with an
"Optional label" input + "Add bookmark" button, an "Intent routing"
preset `<Select>` defaulted to "Balanced," and a "Preview route"
`<textarea>` with helper copy. All of it renders at the FIRST instant,
not after some threshold — the working-posture failure is immediate.

1. **One verb, display step, alone at the top.** Stop/Start is the
   only thing that renders above the fold at idle-and-just-started;
   everything else in this story's scope earns its place only once
   it's needed (rule below). No `MetricStrip`-shaped four-cell grid —
   it's the literal thing convicted; replace `connected/00:00/0/
   recording` with ONE composed facts line at secondary-step type
   (`--desk-surface-detail-size`), e.g. "Connected · 00:00 · This
   device."
2. **Transcript as `SurfaceStream`.** Reuse `SurfaceStream` /
   `SurfaceStreamEntry` (`Surface.tsx:375-455`) — the same shape the
   Journal wing already rides — for the live transcript, not a bare
   "Listening for speech" placeholder div with nothing around it.
3. **Bookmark is a `SurfaceStreamEntry` hover verb, not a form.** Kill
   the standalone "Bookmark" section (label + input + button) entirely.
   Marking a moment is a verb that appears on the transcript stream
   itself at the point in time it marks (hover/press reveals it, per
   composition rule 3); naming it happens inline afterward on the
   entry, never in a pre-filled form waiting above the transcript.
4. **Intent routing preset + Preview route die on this face or move
   behind a gear door.** `LiveCore.tsx` has no `door`/`doorOpen` wings
   split today (unlike `DictationCore.tsx`'s `Configure dictation`
   door, `wings.tsx:70-76`) — add one if this plumbing survives at
   all; the working posture (AGENT_BRIEF §3) does not carry
   configuration knobs on its headline face regardless of load state.
5. **Deferred plugin jobs table (`total jobs`/`queued jobs`/`running
   jobs`/`failed jobs`/`queued due jobs`/`scheduled retry jobs`) is
   raw wire in the glass (Article VI) — same defect class as
   HS-102-06's pipeline dump.** Either fold it behind the gear as a
   diagnostics disclosure, or compose it as one honest line
   ("processing 2 of 3 · Process pending") — never six labeled numbers
   in a grid on the working face.

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
