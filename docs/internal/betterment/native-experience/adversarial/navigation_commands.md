# navigation_commands

Job: Navigate by Go, menu, Dock, palette and shared commands.  Baseline:
`main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430).  Reviewer task:
`review_navigation_commands`.  Evidence class: active source, representative
assertions, and viewed 1440/393 shell captures; no tests, live Desk/API calls,
provider/native actions, or owner acceptance.  Anchors are baseline-specific
and may drift.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The whole job is: choose a Go/menu/Dock/palette/key/voice entry; resolve the
application, object, or project identity and scope; focus, restore, or open
the right window; report an unavailable target; then return without losing
focus, selection, draft, or prior work. The manifest supplies projections and
Go rows (`web/src/desk/applications.ts:558-669`); the registry supplies Go's
focus-or-restore path (`web/src/desk/verbRegistry.ts:705-752`). The brief's
“identical” scope/context requirement is too broad: a front-window object,
selected desk object, and configured voice macro are different contracts.
Assertions cover registry derivation and Go at both widths
(`web/src/desk/__tests__/verbRegistry.test.ts:130-167`,
`web/src/desk/__tests__/menus.app.test.tsx:269-316`), not voice/context
recovery.

FINDINGS:

1. **P1 — contextual availability is declared but not consistently enforced.**
   Menus, object menus, and keys check/refuse `v.ghost(ctx)`
   (`web/src/desk/components/DeskMenuBar.tsx:327-409`,
   `web/src/desk/objectMenu.ts:127-153`, `web/src/desk/keymap.ts:133-147`).
   Voice exposes `VoiceIntentDef.ghost` (`web/src/desk/voice/grammar.ts:1-8`),
   but `routeVoiceIntent` returns the first local match without evaluating it
   (`web/src/desk/voice/intentRouter.ts:74-80`); the editor's “Select text
   first” guard is bypassed (`web/src/desk/voice/grammars/editor.ts:3-18`).
   The demonstrated gap is proposal availability; effect-time guards remain consumer-specific. The editor grammar is used by retained `NoteEditor`, not the normal Thought document (`web/src/desk/pullouts/editors/NoteEditor.tsx:171-176`). Cost: an unavailable command can be offered for confirmation; a malformed active-note edit was not observed. This fails Tenet
   3. Correction: evaluate voice guards before proposing and assert refusal or
   dictation recovery for absent context.

2. **P1 — context ownership must be specified, not flattened.** Object-menu
   targeting prefers the front-window object, then desk selection
   (`web/src/desk/components/DeskMenuBar.tsx:80-99`); keyboard and palette use
   selected IDs (`web/src/desk/keymap.ts:112-115`,
   `web/src/desk/components/DeskToolShelf.tsx:512-517`). Cost: the current difference can act on a surprising object, while forcing every global and local command into one scope can also be wrong. Current routing is evidence, not accepted native behavior. This fails Tenets 3 and
   5. Correction: define a target policy per command scope: the same object command from the same active view should resolve consistently by menu and shortcut; global navigation and an explicitly targeted palette action may differ. Assert a front/selection disagreement without enshrining today’s inconsistency.

3. **P1 — voice macros and contextual proposals need separate contracts.**
   Configured macros exact-match and auto-fire saved actions; `desk_verb` has a closed enum alongside other configured local action kinds
   (`holdspeak/config/ui.py:34-40,72-75`; `holdspeak/dictation_runner.py:61-75`);
   contextual proposals use confidence and explicit confirmation
   (`web/src/desk/components/MicButton.tsx:250-293`). Cost: “voice parity” may
   create a second command bus or auto-fire a proposal. This fails Tenets 1 and
   3. Correction: share target/outcome/receipt metadata but keep consent,
   confirmation, cancellation, and recovery distinct.

4. **P2 — the audit does not close the navigation loop.** Dock handles
   running/minimized/closed states (`web/src/desk/components/window/Dock.tsx:390-457`)
   and aliases preserve scope (`web/src/desk/applications.ts:656-669`), but
   missing targets, stale scope, return focus, and retry are unspecified. Cost:
   arrival may work while resumption fails. This fails Tenets 3, 6, and 7.
   Correction: name trigger, identity, scope, terminal outcome, receipt, and
   return for each surface.

## Convergence

Converge with `desktop_workspace`/`windows` on compositor identity, front
authority, focus, minimize, and restore; `objects_pullouts` on semantic refs
and front context; `settings` on parked aliases and composed scope;
`projects_room`/`drawers` on direct targets; and `feedback` on refusals and
receipts. `voice_commands` consumes shared labels/outcomes, not contextual
selection. Keep Go, Dock, and palette as projections with different discovery
jobs: one visual surface would impose explorer ceremony on the fast path and
weaken phone Go. Do not add a parallel registry.

## User experience

The 1440 capture shows a quiet Workbench/Dock fast path; 393 shows Go as the
compact navigator and the same manifest-shaped Dock
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/desk-1440.png`,
`desk-393.png`). Source suggests good craft: one manifest, one registry,
direct opening. Improve pleasure by keeping the named target visible, making
refusal reasons actionable, and returning focus predictably. Captures
do not prove transitions, accessibility, latency, or owner delight.

CONDITIONS: Add the context table; split macro versus proposal behavior; define
identity/scope/availability/refusal/receipt/return; and cover the voice guard
before calling this audit implementation-ready.

MISSED:

1. Front-window object differs from selected icon (highest wrong-target cost).
2. Existing minimized app versus a stale alias or parked row.
3. Voice no-match, unavailable target, confirm-cancel, and return to dictation.
4. Phone Go and desktop Go reaching the same scoped project or drawer.

TUESDAY: The simple Go/Dock/palette path looks fast, but the audit is not yet a
reliable promise that every entry lands on the right scoped work and returns.

## Acceptance challenges

1. With Today already minimized, activate it from Go and Dock; both focus one
   window, preserve its scope, and return focus to the initiating work after
   close.
2. Select object A while a front window represents object B. Exercise the same object command by menu and keyboard against its declared active-view target. A deliberately global/selection command may name A explicitly; no entry silently changes the target or mutates the other object.
3. On 393, open a project from Go; on 1440, open the same project from the
   palette. Both converge on one project-scoped window, and a parked alias
   names its Settings wing rather than a dead surface.
4. Say a contextual command with its required context absent, cancel a
   proposal, and repeat as dictation. No action fires; with context present,
   one confirmed action emits one receipt and returns to the prior work.

UNKNOWN: No tests were executed; no live Desk/API/provider/native walk,
performance or accessibility measurement, focused transition capture, or
owner observation was performed. The viewed captures are visual references,
not acceptance evidence.
