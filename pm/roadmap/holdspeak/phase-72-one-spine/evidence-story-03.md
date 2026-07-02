# Evidence — HS-72-03 — One name per concept: untangle "companion"

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## What moved (the manifest diff is exactly these eleven routes)

- **The coder session picker** → `/api/coders/*` (paths renamed in place in
  `holdspeak/web/routes/system.py`): `status`, `select`, `dismiss`, `pin`,
  `clear-stale`.
- **The desk actuator relay** → `/api/desk/actuators/{slack,webhook,github}/
  {propose,{proposal_id}/decision}`, extracted from `meetings.py` (which
  shrank **1,855 → 1,460 lines**) into the new
  `holdspeak/web/routes/desk_actuators.py`, registered in
  `routes/__init__.py` + `web_server.py`.
- **The shared lifecycle helpers** (`proposal_to_dict`,
  `actuator_result_event`, `execute_slack_proposal`,
  `execute_webhook_proposal`, `execute_github_proposal`, `_GITHUB_RUNNER`)
  were closures inside `build_meetings_router`; they now live at module
  level in `holdspeak/web/routes/actuator_shared.py` (ctx passed
  explicitly), called by BOTH routers — the seam the one-actuator-lifecycle
  story builds on. Handler bodies byte-identical; `meetings.py` keeps thin
  local bindings so its call sites and behavior are unchanged.
- `_COMPANION_MEETING_ID` + the repo regex moved with the relay,
  unchanged — killing the sentinel is the next story's job, not this
  rename's.

## Callers moved in the same commit (no shims, nothing released)

- **Swift:** `HTTPDesktopClient.swift` (4 picker paths → `api/coders/*`),
  `DeskDioramaStage.swift` (`DeskHostLink` propose/decision →
  `api/desk/actuators/\(target)/…` — the earlier exploration claim that the
  Swift client never calls the relay was WRONG; it does, and moved),
  doc comments in `Providers.swift` + `CompanionBoard.swift`.
- **Web:** `companion-desk.js`, `companion-app.js`, `desk-app.js`
  (`refreshCoders`), page comments in `companion.astro` / `desk.astro`.
- **Docs (factual path):** `AGENT_HOOK_INSTALL.md`.
- **Tests:** `test_web_server.py` (picker), the three relay suites
  (`test_web_companion_{slack,webhook,github}.py` — paths + the
  `_GITHUB_RUNNER` patch target now on `actuator_shared`).

## Verification artifacts

- **Manifest diff = exactly the moved routes:** 11 removed
  (`/api/companion/*`), 11 added (5 `/api/coders/*` + 6
  `/api/desk/actuators/*`), route count constant at 229. The regenerated
  consumer tags on the NEW paths are extracted from the real call sites —
  cross-surface proof the clients actually call the renamed routes.
- Zero grep hits for `api/companion` outside the manifest history and the
  new module's "was" docstring.
- Rename-affected suites: **128 passed** (relay slack/webhook/github +
  `test_web_server` + api-surface) + **16 passed** (github relay after the
  patch-target import fix).
- `swift test`: **394 passed, 0 failures** (the renamed client + the
  CompanionBoard seam).
- App target: `gen-meeting-capture.rb`, then the documented toolchain
  workaround (`scripts/patch-llm-macro.sh <dd> <proj> <scheme>` to sever the
  LLM.swift macro, then `xcodebuild -sdk iphonesimulator -derivedDataPath
  <dd> -disableAutomaticPackageResolution -skipMacroValidation`) →
  **BUILD SUCCEEDED**. Two failed attempts recorded honestly: a plain build
  hits the LLM.swift macro gate, and `-skipMacroValidation` alone still dies
  on the swift-syntax `_SwiftSyntaxCShims` break — the patch script is
  load-bearing, exactly as its header documents.
- Web: `npm run build` green (19 pages); **route pre-flight 2 passed** —
  every page (including `/companion` and `/desk`, which fetch
  `/api/coders/status` on load) renders with zero page errors against the
  renamed routes.
- Full python suite at ship: **3058 passed, 37 skipped, 0 failures**
  (Playwright restored to the venv, so the route pre-flight runs again).

## Acceptance criteria — re-checked

- [x] "Companion" no longer names an API concept; the picker is
      `/api/coders/*`, the relay is `/api/desk/actuators/*`.
- [x] Swift client + web callers + tests moved in the same commit; no
      aliases, no redirects.
- [x] Manifest diff shows exactly the moved routes and nothing else.
- [x] Byte-identical handler behavior (bodies moved verbatim; all
      pre-existing relay/picker tests pass with only path/patch-target
      edits).

## Deviations from plan

- **The interactive Simulator screenshot** (the coder board walked against
  the renamed routes on a live hub) was replaced by three cheaper proofs
  that together cover the same claim: the app compiles for the Simulator,
  the package's board tests pass against the renamed client seam, and the
  regenerated manifest's `ios` consumer tags on the new paths are extracted
  from the real Swift call sites. An interactive device/Simulator walk
  lands with the phase closeout's owner walk.
- The story scaffold predicted the web `/companion` page "presents the
  coder board" label work; the page copy already says Agent Desk/coders —
  only comments needed updating. No label changes shipped.

## Follow-ups

- HS-72-04: kill `_COMPANION_MEETING_ID` via the owner-typed proposal
  origin; `actuator_shared.py` is the seam it extends into the one
  lifecycle service.
- The picker status route also reports desk connector config
  (`connectors.slack_configured` etc.) — a residual conflation inside the
  coders status payload; noted for HS-72-04/10 to place properly.
