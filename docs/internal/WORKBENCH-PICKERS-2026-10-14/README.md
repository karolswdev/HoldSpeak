# Workbench pickers

The owner accepted the shared Settings sheets, then rejected the browser-native
menus throughout the product. This release replaces the popup in the shared
choice species and adopts the remaining raw face. One component concern;
base91275406b; no owner visual acceptance inferred.

## What changed

The visible native select still owns labels, focus, form values, required and
disabled state, defaults/reset and native input/change events. Pointer or key
activation opens the library's square Workbench listbox instead of the browser
popup. Paper rows show the current check, a separate active highlight and
unavailable ghost states. Long lists scroll; labels wrap; the portal inherits
its owner's theme and stays in the viewport. Phone control/option targets use
the existing device44px rule in global.css; no new media-rule exception.

Arrows, Home/End and type-ahead move the active row; Enter/Space commits one
change. Escape cancels inside the window; Tab leaves; outside actions remain
usable. Unchanged parent renders preserve the selection in progress; actual
value/roster/disabled changes end the stale popup. The legacy Signal Select
uses the same core. Button moved unchanged into its own library module to
avoid a circular import; the scanner recognizes only the two exact new
implementation paths and still rejects lookalike face paths. No ceilings rose.

The source [census](AUDIT.md) found46 CycleGadget callsites, one legacy Select
and one raw Thread enum. The Thread enum now composes CycleGadget, preserving
its blank sentinel, string values, required label and existing Submit writer.
All48 active-source callsites inherit the shared core; this does not mean
all48 faces were walked live. No backend route or form writer changed.

[Brief](BRIEF.md), [canvas](canvas/index.html), [kit implementation](KIT.md),
[library contract](../../../web/src/desk/surface/contract.md) and independent
[finished source review](REVIEW.md) hold the exact design and API. Root read
corrected canvas1440/393 before product build. Review found a real lifecycle
bug: closing on React child identity dismissed menus during unrelated renders.
One red regression and semantic snapshot correction/recheck resolved it.
The final source verdict is RATIFY, not Muad'Dib's check.

## Verification

Focused kit41/3files, adoption65/3files and exact scanner7 pass. Red logs prove
nine missing-popup failures initially, two scanner registry failures before
correction and one parent-render dismissal before its fix. Collection and
run tails are named in KIT.md and AUDIT.md. Frontend TypeScript and production
build pass. Final combined quick GREEN:3880web /708affected Python /107desk sweeps (two existing xfails) /17canon guards. Build and final frontend TypeScript pass. Capability docs check passes10outputs; graph join retains14existing subtype notes. Logs: `.tmp/workbench-pickers/quick-final/`, `quick-final-console.log` and `types-final.log`. The sweep warning is the existing Python invalid-escape warning. Canvas files are outside quick selection; root rendered/read them separately.

Root production walks `live-final-{1440,393}` each pass13 states in isolated
HOME/DB with actual source and bundle provenance. They cover Language open,
long-list ends/type-ahead, actual pointer and keyboard saves, Escape no-PUT,
Tab, outside Add symbol, failed save/Retry, Wake action, Meetings summary and
actual JSON export save. Production gallery proves disabled options cannot
commit and keyboard traversal skips them. Nine-point hit ownership is true;
phone owner172x44 and options192x44. No page errors or body overflow. Root
read open/active/disabled and export screenshots at both widths.

Two earlier manual runs were rig failures, retained: an outside checkbox was
correctly obscured by the popup, then an outdated engine-navigation assumption
waited for a retired Table tab. Neither is called a product failure or pass.
The corrected rig uses a visible outside action and the current Meetings face.
A graph invocation with --headless was blocked because this rig uses that
flag for no-browser protocol walks. Corrected face cases omit that flag.
Graph face cases pass1440 and native-touch393 through the actual option and settings writer. Initial predicates held at0.938/0.950s; terminal outcomes settled at1.110/1.119s. Root read before/after shots and isolated DB provenance separately. Final quick counts above are from the completed run.

## Limits

No script changes the owner's real settings or desk DB. Real desktop/mobile
assistive technology, physical Safari/iOS devices, speech, OS hardware and
external dispatch remain unverified. Existing API/ref/default/reset behavior
is covered at the native boundary; no active multiple/size-listbox callsite
was found and those keep their native listbox behavior. Owner judges the
new feel on the normal local desk after deployment. Broad visual audit is
the owner's next requested pass; this release does not claim every surface
is polished. The existing compact Calendar chooser limitation remains open.
