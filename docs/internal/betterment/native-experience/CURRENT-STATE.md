# Current state: native-feeling HoldSpeak in the current React stack

**Audit date:** 2026-10-23  
**Baseline:** `main` `787c55c8096f746b06a4c8d5d42ae48ef5c1fe20` (PR1428)

This is a read-only source audit, not a new architecture or a technology
migration. Line anchors below are against the baseline and can drift after
merges.

## Executive readout

The React stack already has the right native-grade seams: one Desk route,
one window/compositor owner, a reusable surface kit, a single document keymap,
and one microphone authority. The strongest reuse path is therefore to tighten
those seams and their proof. A second UI framework or a rewrite would violate
Tenets 3 and 5 by adding interfaces before the owner has used the first one.

The main risks are not raw component count. They are contract escape hatches,
split material ownership, and browser proof that stops short of WebKit. The
most concrete current seam is the narrow Room wing selector: the production
code folds tabs into a menu, but a live helper still assumes a tab exists.

## Framework graph (observed source facts)

```
BrowserRouter/AppShell -> DeskApp/DeskChrome -> SurfaceWindows
  -> DeskWindowFrame -> window registry + compositor (plane/z/geometry/WAAPI)
Feature core -> surface barrel -> Surface/Gadget/Pattern + feature CSS
MicButton -> micStreamSession/pendingVoice -> controlled field or editor
/presence -> React PresencePage; optional native host embeds /presence
```

- The route model has only Desk, Welcome, and Presence as real routes;
  legacy product paths deep-link into Desk windows (`web/src/routes.tsx:1-6,
  20-29,43-85`). `AppShell` is deliberately a thin main/ambient shell
  (`web/src/components/AppShell.tsx:8-25`). This is a good OS boundary: the
  Desk owns coexistence while deep links remain entry points.
- `DeskWindowFrame` owns drag/resize/raise/close, opener focus restoration,
  Escape, and the non-modal window contract (`web/src/desk/components/DeskWindow.tsx:1104-1121,1181-1230`).
  `useCompositor` is the single plane/z and FLIP-like WAAPI arrangement owner
  (`web/src/desk/compositor/useCompositor.ts:1-12,182-222`). Reuse this seam;
  do not introduce feature-level window physics.
- `desk/surface` explicitly provides the supported barrel (`web/src/desk/surface/index.ts:1-2`),
  with Surface, Gadget, Reading, Composer, Wing, and voice species
  (`web/src/desk/surface/index.ts:41-90,118-150,192-208`). The contract
  records real consumers and correctly warns that a reference specimen is not
  proof of a complete production journey (`web/src/desk/surface/contract.md:38-61`).

## Findings by native boundary

**Shell, focus, and keyboard — strength with one narrow-width gap.** The
single ref-counted key binder ignores typing, repeat, default-prevented, and
IME-composing events (`web/src/desk/keymap.ts:133-184`). The compositor and
window focus rules already share explicit authorities. However,
`useCoreWings` publishes a `SurfaceWings` node (`web/src/pages/cores/core-hooks.tsx:40-69`),
and `SurfaceWings` deliberately folds when measured head allocation is too
small (`web/src/desk/surface/wings.tsx:74-109`). The folded form is a
`StripMenuButton`, not a tab (`web/src/desk/surface/stripMenu.tsx:104-193`).
The Room helper still does `get_by_role("tab", name="History")`
(`tests/e2e/test_room_glass.py:1511-1517`). The current full-tape handoff
reports new Room[393] timeouts at this helper (`tests/e2e/test_room_glass.py:1514,2116`).
Inference: a newly folded head likely exposed a stale selector, not that the
Room data path is broken. Coverage currently has synthetic fold geometry but no
live 393 assertion that opens the folded menu and chooses History
(`web/src/desk/surface/__tests__/wings.test.tsx:68-100`).

**Surface, material, and CSS — strong kit, incomplete ownership.** Generated
tokens define semantic/component layers, the light material, focus ring, and
12px floor (`web/src/styles/tokens.css:1-18,160-223`). Shared host selectors
own common rhythm and the 68-character reading measure
(`web/src/desk/surface/contract.md:63-70`; `web/src/desk/surface/surface.css:5331-5399,5425-5437`);
the earlier `surface.css:298-365` range is generic columns/split layout, not
the shared-host rule itself.
The escape hatch is recurring private imports despite the barrel contract:
Settings and Room directly import `desk/surface/Surface`, `gadgets`, and other
private modules (`web/src/pages/cores/SettingsCore.tsx:22-68`; `web/src/features/project-room/ProjectRoomCore.tsx:6-86`).
This is contract drift, not prima-facie broken behavior: converge imports when
an active component is already being touched, not with a bulk rewrite. Active
Review still carries raw date/text inputs explicitly marked for redesign
(`web/src/features/project-room/review/ReviewPosture.tsx:103-118,276-288`).
The apparently similar Zone raw controls are not an active consumer: the store
now says no live door opens a Zone and keeps the primitive for parked code/tests
(`web/src/desk/store/compositorSlice.ts:359-365`; `web/src/desk/compositor/hubWindows.ts:511-512`).
The remaining raw controls inside the shared gadget implementation are a small
exception set (Stepper, table add, and TransportKey)
(`web/src/desk/surface/gadgets.tsx:552-577,690-704,825-840`); treat them as
explicit species decisions, not dead-code migration.

**Voice, text selection, IME, and pending state — real foundations, uneven
field semantics.** `micSession` keeps one AudioWorklet-backed session, gates
holds against open mic, and releases the device after idle (`web/src/lib/micSession.ts:1-18,186-220`).
`StringGadget` and `PadGadget` put the mic beside native fields and protect
late callbacks with a latest-writer ref (`web/src/desk/surface/gadgets.tsx:262-360,363-470`).
Pending audio has IndexedDB plus a page-memory fallback (`web/src/lib/pendingVoice.ts:13-16,39-110`);
text drafts persist synchronously where adopted (`web/src/lib/durableDraft.ts:68-100`).
IME guards exist in the global keymap and field handlers. Selection-aware
editor commands use CodeMirror ranges (`web/src/desk/components/DeskEditor.tsx:209-235,300-340`),
but generic dictation in NoteEditor appends to the body rather than sharing one
selection/caret insertion primitive (`web/src/desk/pullouts/editors/NoteEditor.tsx:50-58,172-183`).
That is a focused reuse opportunity, not a reason to replace CodeMirror.

**Native presence boundary — currently broken and kept off.** `/presence` is a
small React card, not a Desk window (`web/src/pages/PresencePage.tsx:14-35`;
route `web/src/routes.tsx:20-28`). The source mechanism can host that same URL
in a non-activating macOS NSPanel/WKWebView, with compositor-dependent Linux
tiers (`holdspeak/desktop_presence_cocoa.py:3-16,426-485`;
`holdspeak/desktop_presence.py:358-414`). The setting is config-backed,
persistent through `/api/settings`, and has live start/stop plumbing
(`holdspeak/config/device.py:23-38`; `web/src/pages/cores/SettingsCore.tsx:304-307,1540-1575,2269-2294`;
`holdspeak/web_runtime.py:358-414`). Owner evidence on 2026-10-23 marks the
native Presence rendering broken. At the owner's request, Astra terminated
the identified renderer and verified that the overlay was gone and
`presence.enabled=false` was persisted and applied live. The rendering root cause is
unverified. Keep it off until repaired, closeable, and backed by a fresh capture
proof. The owner screenshot/local untracked evidence path is not present in
this audit worktree, so this note does not invent one. Documentation/comment
drift remains at `holdspeak/web_runtime.py:219-222`, which still describes
env-only enablement while code passes the config flag.

## Verification and performance limits

The browser evidence is meaningful: the desk sweep fences fit, readable text,
contrast, overlap, raw buttons, hit targets, motion, and egress at 1440/393
(`tests/e2e/test_desk_sweep.py:26-58`), and component glass runs Chromium and
Firefox with screenshots and geometry (`tests/e2e/test_components_glass.py:293-344`).
No live (non-parked) `webkit.launch` or WebKit browser project/configuration
appears in the source census; a parked test reference is not live coverage.
WebKit is therefore unknown, not failed. Screenshots are evidence artifacts,
not a demonstrated pixel-diff gate. The compositor has motion timing but no
runtime frame/long-task telemetry (`web/src/desk/compositor/useCompositor.ts:182-222`);
the bundle script reports bytes and checks chunk/maps, with no byte budget
(`web/scripts/check-bundle.mjs:12-32`). This audit ran no benchmark or live
walk; perf claims beyond these fences are unmeasured.

Root read the completed local tape artifacts and compared failed-test names:

- Current: `/Users/karol/dev/tools/wt-main-tape-modernize-all-20261023/.tmp/delivery/tape/summary.json`, exact main `787c55c80`: 12 Python and nine browser failures, web baseline and strict Firefox timing green.
- Prior: `/Users/karol/dev/tools/wt-main-tape-richer-icons-20261022/.tmp/delivery/tape/summary.json`, main `62358b671`: 13 Python and nine browser failures.

The new observed failures are three Room[393] fold-selector cases and one
scheduled-microphone case whose cause this research does not establish.
Other failures recur or no longer fail in the compared run. This is a
run-to-run set difference, not proof of causal regression or repair. The
selector source is at `tests/e2e/test_room_glass.py:1514,2116`. Logs are local
untracked artifacts; this record captures the observed facts without claiming
a fresh rerun. The browser note separately records root's three-engine
capability probes; WebKit application tasks and performance remain unproved.

## High-value changes (reuse, no parallel framework)

1. Make a shared fold-aware test helper that accepts either tab or strip-menu
   choice, and add one live 393 Room walk; preserve `SurfaceWings` semantics.
2. Add one shared caret/selection insertion adapter for `MicButton` consumers;
   keep field dictation, editor commands, and IME guards explicit.
3. When active Settings/Room components are touched, use the surface barrel and
   reduce private imports; converge Review's marked raw fields into gadget
   species. Leave retired ZoneWindow parked and retain native input types for
   passwords/files/radios.
4. Define CSS ownership at the shared-host seams before touching feature CSS;
   move only repeated layout/material rules, not a giant stylesheet rewrite.
5. Add WebKit runs for the compact fold, focus return, mic-disabled state, and
   one visual assertion; retain Chromium/Firefox coverage and 1440/393 shots.
6. Add optional compositor marks (arrange, raise, settle) and long-task/frame
   sampling behind diagnostics, so “native-grade” performance becomes observed.
7. Keep Presence disabled while the renderer is broken; identify the root cause,
   then capture close, enable/disable persistence, renderer-unavailable, and
   focus-safety proof before re-enabling it. Align comments/docs afterward.

These changes serve Tenets 1, 3, 5, 6, and 7: fewer competing interfaces,
clearer recovery, and an OS-like Desk the senior architect can use on Tuesday.
Tuesday answer today: the shell is credible; the 393 fold selector and
cross-browser proof still need one focused pass before calling it native-grade.
