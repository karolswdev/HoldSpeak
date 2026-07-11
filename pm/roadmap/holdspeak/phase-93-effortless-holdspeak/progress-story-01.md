# HS-93-01 progress record — Three obvious starts

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `1e6a28f3`<br>
**After build:** current Phase-93 working tree; no commit identity claimed<br>
**Acceptance status:** in progress — automated and simulator evidence is not
owner or physical-device acceptance.

## Visible subtraction

| Measure | Before | After |
|---|---:|---:|
| Global Web navigation destinations | 9 | 5: Desk, Dictation, Meetings, Studio, Settings |
| Simultaneous Web create-type controls | 5 | 1 Create entry |
| Choices behind Create | permanently exposed | Note, Zone, Knowledge, Persona, Workflow, each with task copy |
| Fresh-Desk daily starts | two central links, five create chips, separate Record orb | Dictate, Record, Create; no duplicate Record orb |
| Moved advanced Web routes reachable from the Desk | no shared entry | Tools/search shelf with Workflow editor, Personas/Coder sessions, Runs on, Commands, Cadence, Activity |
| Native first-use create controls | three permanent iPad chips / three-choice iPhone menu | one five-choice Create menu on both layouts |

No deep route was removed. The existing spatial Desk, selection, object
pull-outs/inspectors, Persona rail, live Coder presence, attention, receipts,
keyboard object actions, and direct manipulation remain in place.

## Captures

The two before captures were already present from the exact baseline commit.
The after Web captures come from `npm run shots` against the production Vite
build. The native captures come from fresh simulator installs of the generated
flagship `HoldSpeakMobile` app.

| Surface | Before | After |
|---|---|---|
| Web desktop arrival | [before](./evidence/hs-93-01/before-web-desktop.png) | [after](./evidence/hs-93-01/after-web-desktop.png) |
| Web compact arrival | [before](./evidence/hs-93-01/before-web-compact.png) | [after](./evidence/hs-93-01/after-web-compact.png) |
| Web Create disclosure | five permanent controls in the before arrival | [one five-choice menu](./evidence/hs-93-01/after-web-create.png) |
| Web advanced-tool discovery | five advanced routes in global navigation | [Desk Tools/search shelf](./evidence/hs-93-01/after-web-tools.png) |
| iPhone native arrival | not captured on the exact baseline | [iPhone 17 Pro simulator](./evidence/hs-93-01/after-iphone-simulator.png) |
| iPad native arrival | not captured on the exact baseline | [iPad Pro 13-inch simulator](./evidence/hs-93-01/after-ipad-simulator.png) |

Simulator captures are supplementary only. They are not credited as physical
iPhone/iPad evidence.

## Interaction and accessibility locks

- Web Dictate and Record are direct links; Create is a keyboard-operable ARIA
  menu with Escape, arrow, Home, End, outside-click, and focus-return behavior.
- The Tools shelf opens by button or `Control/Command-K`, focuses search, keeps
  all moved deep links, searches Desk objects and Zones, and opens the existing
  object inspector or Zone view.
- Compact Web keeps all three starts and every Create choice visible without
  hover or drag.
- Native Dictate and Record are semantic Buttons. Create is a native Menu with
  five named actions. Workflow opens the focused Workbench; Persona opens its
  builder; Note, Knowledge, and Zone retain their existing Desk creation paths.
- The old native first-use architecture lesson and record-only coaching were
  removed. `Agent Desk`, `Your live agents`, and `ON-DEVICE · LOCAL MESH` were
  also removed from the touched fallback arrival surface.

## Verification completed

```text
cd web && npm run check
React architecture guard passed (93 source files)
TypeScript: passed
Vitest: 19 files, 125 tests passed
Vite production build: passed
```

```text
.venv/bin/python -m pytest -q \
  tests/unit/test_phase93_arrival_contract.py \
  tests/unit/test_native_first_words_contract.py \
  tests/unit/test_desk_locks.py \
  tests/integration/test_web_built_mount.py \
  tests/integration/test_web_setup_route.py \
  tests/integration/test_web_welcome_wizard.py
28 passed
```

```text
swift test --package-path apple
534 tests passed, 9 skipped, 0 failures

ruby apple/scripts/gen-meeting-capture.rb
xcodebuild -project apple/build/HoldSpeakMeetingCapture.xcodeproj \
  -scheme HoldSpeakMobile -configuration Debug \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath apple/build/phase93-derived \
  -skipMacroValidation -disableAutomaticPackageResolution \
  CODE_SIGNING_ALLOWED=NO build
Xcode 26.5: BUILD SUCCEEDED
```

The screenshot rail was repaired during this run. It previously requested
trailing-slash URLs under Vite's asset base, causing every advertised non-root
capture to silently render the Desk. It now boots the production bundle once
and moves through canonical BrowserRouter paths before capture. Create and Tools
states are captured on desktop and compact Web.

The full Playwright route-preflight lane is not credited green here. Its
product-boot wait remained unbounded after the first case in this environment,
so the run was stopped rather than represented as successful. The bounded route
shell tests above and direct production captures passed; repairing that wider
preflight wait remains part of the phase verification-rail work.

## Evidence still required before done

- Owner first-glance explanation and moved-tool discovery walk on the exact
  production build.
- Keyboard-only Web walk, including Create and every moved tool.
- Physical iPhone and iPad VoiceOver/action walk and captures.
- Exact committed build provenance after the implementation is committed.
- HS-91-10 dependency closure or an explicit owner-authorized sequencing
  disposition.

No story checkbox is closed by this file. The missing observations are phase
gates, not paperwork to infer from automated results.
