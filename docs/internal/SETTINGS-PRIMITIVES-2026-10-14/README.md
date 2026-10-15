# Shared Settings primitives — 2026-10-14

Owner direction: the Voice form still looked vanilla. Build a reusable native
component foundation and apply it broadly. Workbench stays. Base22de063e3,
one feature branch and release. The owner rejected the previous visual pass;
this record does not infer acceptance from a canvas or green checks.

## What changed

| Shared species | New composition |
| --- | --- |
| GadgetGroup | Opt-in inset control sheet, named heading, bounded action footer |
| GadgetRow | Explicit standard, short and full value widths |
| CheckGadget | Real labelled checkbox with visible On/Off and one native target |
| GadgetTable | Head-derived field labels when the window is narrow |
| SurfaceColumns | Balanced bounded preference columns, one column when narrow |
| GadgetDivider | Native etched divider inside a sheet |

[API contract](../../../web/src/desk/surface/contract.md) lives beside the
shared code. The implementation extends existing species; native controls and
form values stay with their current owners. Voice, Meetings, Rhythm, Sounds,
People and System adopt the pattern. Local inherited form rules no longer
compete with the shared sheets. Module headers use existing pixel sprites.

The native canvas uses the real frame, wings, controls and footer. Root read
empty/populated1440/393 renders, corrected paper material and floating value
columns, then settled the build. [Brief](BRIEF.md), [adoption audit](ADOPTION-AUDIT.md),
[canvas and primitive proposal](canvas/README.md), [kit implementation](audit-kit.md)
and [adoption implementation](ADOPTION-BUILD.md) retain the exact sequence.

## Producer-backed usability correction

The first real Voice walk failed: Add symbol immediately sent a blank entry
and the real validator returned400. Focused regression also proved the invalid
array could contaminate an unrelated language write in the same debounce batch.
Incomplete symbols now stay in a local buffer with a Draft fact; valid arrays
enter the existing revision-aware writer. The buffer survives unrelated
accepted writes, failures, newer edits and Back. It clears only when the
authoritative value matches and the same path has no pending/failed write.
Comparison follows the actual producer: spoken/attachment normalization,
literal symbol preserved, including a space. There is no shared form-state
framework, new endpoint, or replacement writer. Incomplete rows are local
to the current Settings instance; refreshing cannot persist an invalid row.

The [finished source review](REVIEW.md) found one concrete full-width CSS
specificity collision. Its one correction/recheck is RATIFY, source only.
Root also measured and corrected duplicate host/content padding, cycle label
tracking, wrapped multi-control rows and a nested TTS action strip. This is
an independent Sol review, not Muad'Dib's check or owner visual acceptance.

## Final checks and actual observations

Final combined quick **GREEN:3650web /651affected Python /107desk sweeps
(two existing xfails) /15canon guards**. Production build and frontend
TypeScript pass. Logs: `.tmp/settings-primitives/quick-final/` and its console.
The sweep's warning is the existing invalid Python escape in type_floor_rig.py.
Capability docs check passes10outputs; graph join check retains14existing
subtype notes. The canvas is outside the production quick selection; root
rendered and read its four states separately before implementation.

Focused proof: kit25passed after5red regressions and one corrective run;
adoption88passed across6files; actual-symbol correction42passed after2red
regressions. Final normalization expressions were verified by the real
producer walks and final combined check, not an unrun worker claim.

Actual isolated production walks and root inspection:

- `voice-corrected-1440`:8states pass, real completed symbol save, keyboard
  checkbox, unrelated write during incomplete entry, refused save/Retry, armed
  Forget. `voice-final-393`:8states pass, explicitly records no PUT during Add
  and partial entry, and nine-point ownership for Add, check, Retry and Forget.
- `voice-normalization-393`:8states pass; outer spaces in spoken phrase and a
  literal-space symbol normalize through the real route and clear Draft.
- `layout-final-{1440,393}`: full text wells equal their slots414/303px;
  standard picks remain190/172px. AFTER EVERY MEETING measures136.8px inside
  available156/138px, so it fits. No horizontal overflow or page errors.
- Remote Enable and credential creation are real isolated producer writes.
  The rig has no remote MCP listener, so its address is a declared read-leaf
  substitution for layout. No remote connection is claimed. TTS installed/
  missing-model is also a declared controlled read for layout only; no model
  download or speech gesture occurs. Root read both controlled-state shots.
- All module/wing arrivals, calendar rename/preservation, refusal/Retry and
  newest-edit Retry are captured. `modules-final-1440` retains17states then
  fails at the existing empty native chooser; `modules-final-393` returns18
  rig states, but root does not treat its weak chooser visibility predicate
  as a closed chooser face. The source and runtime limitation is below.
- Production graph calendar-save cases pass1440/393; root read before/after
  shots, initial predicate and settled terminal separately. Each observation
  names source22de063e3dirty, actual bundle and an isolated HOME/DB.

## Open observations

The existing compact Calendar chooser can render no controls when a source
is already in use and native discovery has no candidates/permission action
or receipt. CalendarCard hides URL entry for inUse; compact CalendarFrame
also omits the old Card state. This was not changed by the primitive build.
It is tracked as existing P2 in pm/STATUS.md; native chooser completion is
not claimed. Meetings Add feed remains the explicit URL entry.

Owner live visual acceptance, real native calendar/key/microphone behavior,
remote MCP connection, speech/model quality and external dispatch remain
unverified. The normal owner's desk is not used for scripted write tests.
