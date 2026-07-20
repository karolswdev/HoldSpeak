# HS-102-06 — Speech Settings: one composed face

- **Project:** holdspeak
- **Phase:** 102
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-102-07

## The owner's words (the bar)

> "The 'Speech Settings' is an absolute joke - a cacophony of tiles,
> panes, forms, form groups and so on." (two screenshots attached to
> the charter — the Speak window's gear face)

## Problem

The Speak window's gear face (`web/src/pages/cores/DictationCore.tsx`,
the configure wing) is the worst surviving pre-canon surface, and the
owner's screenshots convict it line by line:

- **Raw wire in the glass** (Article VI): "PIPELINE READINESS —
  pipeline enabled false / max total latency ms 600 / backend auto";
  "RESOLVED DELIVERY — id browser / confidence 0.78 / source hints /
  runs 0 / budget ms 600". Key-value dumps of internal state, not
  composed truth.
- **Warning boxes as furniture**: "Dictation pipeline is disabled."
  and "Project KB file is missing." float as bordered banners rather
  than honest states WITH their remedy at the point of decision.
- **Form-group cacophony**: PROJECT SCOPE (bare input + "Use
  project"), KNOWLEDGE and INSTRUCTIONS as two giant empty textareas
  each with an orange "Save knowledge" / "Save instructions" button
  (canon rule 1 outlaws exactly this; the configuring archetype
  saves on change — HS-101 round 3 already killed Save buttons in
  Settings), DICTATION RUNTIME re-stating label-over-Select stacks
  (Backend / Runs on / Latency budget) that the round-5
  `RuntimeDestination` bespoke already owns in Settings.
- **Eyebrow-section tiling**: six ALL-CAPS sections in two ragged
  columns — tiles, not a face.

## Scope

- In: the gear face recomposed as ONE configuring posture (grouped
  setting rows, the settings-rail archetype where the groups earn
  it): readiness/delivery become composed, honest lines (what runs
  where, at what budget, and WHY — humanized, remedies inline where
  a state is off); Knowledge and Instructions become material that
  edits in place (the presented text is the interface; save on
  change through the same PUTs — no orange Save buttons); the
  runtime group either embeds the bespoke destination component or
  links the one Settings owner (never a third copy of the same
  knobs); correction memory / learning digest read as honest quiet
  facts. Mockup-grade before/after at both viewports is part of this
  story's eyes-first step.
- Out: the wire routes (unchanged); Settings' own bespoke components
  (round 5, keep); the Journal and Blocks wings (HS-101 B3/B4,
  shipped).

## Acceptance criteria

- [ ] Hands-first ledger recorded (headed, 1440 + 393; pipeline
      off AND on, project scoped AND not) before code.
- [ ] Zero raw wire keys or values in the glass: every fact reads as
      composed language; off/missing states carry their remedy.
- [ ] Zero Save buttons: knowledge/instructions edit in place on the
      presented material, save on change, whisper the state.
- [ ] The runtime knobs exist in exactly ONE composed place; this
      face embeds or links it, never re-states it as label stacks.
- [ ] The section-tile cacophony is gone: one configuring posture,
      groups at caption step, the geometry walk's interior
      assertions green on this face.
- [ ] Driven live on a staged hub: scope a project, edit knowledge
      in place, watch the save whisper, flip the pipeline state and
      see the face tell the truth; both viewports, all read.
- [ ] A named guard: the interior-canon guard grows a rule for this
      face (no raw wire keys; no Save-button forms).

## Test plan

- Web vitest; token gate; vocabulary + interior-canon guards
  (grown); geometry walk; the live drive on the staged hub, headed,
  both viewports.

## Evidence required

- The ledger; before/after at both viewports; the live-drive record;
  guard output.
