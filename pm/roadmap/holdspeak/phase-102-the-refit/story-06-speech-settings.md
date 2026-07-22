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

## Design direction (grounded in a live drive, 2026-07-21 — this face,
as it exists right now, confirms every line of the problem statement)

Driven headed against a fresh staged instance, the gear face renders,
verbatim: `PIPELINE READINESS — pipeline enabled: false, max total
latency ms: 600, backend: auto`; `RESOLVED DELIVERY — id: browser,
label: Browser, confidence: 0.78, source: hints, app name: Safari,
window title: <window title>, runs: 0, budget ms: 600`; two bordered
warning boxes ("Dictation pipeline is disabled." / "Project KB file is
missing.") with no remedy attached; a bare "Project root" input +
"Use project" button; and empty Knowledge/Instructions textareas. The
Settings app's own Appearance group (`/settings`, `Show Audio Meter` /
`History Lines` / `Theme`) — visible in the SAME session — already
demonstrates the target composition. Copy that shape; do not invent
a new one.

1. **`SurfaceGroup` + `SurfaceSettingRow` + `SurfaceToggle`
   (`Surface.tsx:299-373`) are already proven in this exact app.**
   Every remaining ALL-CAPS tile section on this face becomes groups
   built from those three components — the six-tile cacophony dies by
   reuse, not by a new layout system.
2. **Compose the two raw dumps into honest sentences, field by
   field:**
   - `pipeline enabled: false` + `backend: auto` + `max total latency
     ms: 600` → one line: "Types automatically as you speak · off ·
     budget 600ms" with the state as a `SurfaceToggle` (flips the same
     PUT) and "Turn on" inline where it's off — not a separate warning
     box below.
   - `id/label/confidence/source/app name/window title/runs/budget
     ms` → one composed line, e.g. "Last typed into **Safari** via the
     browser bridge · 78% confidence," with the raw fields (id, source,
     runs, budget) behind a `Disclosure` (already imported in
     `settingsBespoke.tsx:18`) for anyone who needs the wire values —
     never on by default.
3. **"Dictation pipeline is disabled." / "Project KB file is missing."
   carry their remedy AT the point of the state**, inline in the
   composed sentence from rule 2 (a "Turn on" / "Create it" verb right
   there) — delete the standalone bordered banners entirely.
4. **Knowledge and Instructions become `EditInPlace`
   (`Surface.tsx:591`).** The presented text IS the interface; commit
   on blur/Enter through the same PUT the current Save buttons call.
   Delete both orange "Save knowledge" / "Save instructions" buttons —
   HS-101 round 3 already set this precedent for Settings; this face
   was the one still missing it.
5. **The DICTATION RUNTIME group (Backend / Runs on / Latency budget)
   embeds `RuntimeDestination` (`settingsBespoke.tsx:139`) or links to
   Settings' existing owner of that same component — it does not
   re-state the same three knobs as a third label-over-`<Select>`
   stack.** If HS-102-01 lands first, this story consumes whatever
   `ProfilesCore.tsx` composition that story ships instead of
   `RuntimeDestination` directly — one owner, never three copies of
   the same control.
6. **PROJECT SCOPE's bare "Project root" input + "Use project" button
   becomes one `SurfaceSettingRow`** with the project path as
   `EditInPlace` text and "Use project" as the row's inline verb, not
   a two-element form floating under its own eyebrow.

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
