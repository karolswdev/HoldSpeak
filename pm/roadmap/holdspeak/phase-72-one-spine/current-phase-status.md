# Phase 72 — One Spine (cross-surface cohesion)

**Status:** open — 5/10 (HS-72-01..05 done 2026-07-02; HS-72-07 cut;
10 live stories).

**Last updated:** 2026-07-02 (**HS-72-05 done** — the shadow modules
renamed (recorder + tracker), wire names kept, orphans deleted, /activity
on Studio. Earlier: **HS-72-04 done** — one actuator lifecycle:
schema v5 owner-typed proposals, the sentinel meeting dead, the rebuild
migration proven against a real v4 DB, `decide_proposal` the single
decision path with four thin route callers. Earlier: **HS-72-03 done** — "companion" untangled:
the coder picker at `/api/coders/*`, the desk relay at
`/api/desk/actuators/*` in its own router, the shared lifecycle helpers in
`actuator_shared.py`, all callers moved in the same commit; the manifest
diff is exactly the eleven routes. Earlier: **HS-72-02 done** — the API
surface is a declared, committed artifact: 229 routes with
call-site-derived consumers (44 iOS / 151 web), five snapshot tests, both
drift directions proven red. Earlier: **HS-72-01 done** — the primitive contract is
machine-checked: 8 kind schemas + the ChangeSet envelope + one golden fixture,
three guards (hub pytest / Swift fixture round-trip / validate.py), the
three-way kind-set lock, four real drifts caught on the first pass. See
"Where we are". Earlier same day: **opened + scaffolded** from a deep architectural
analysis of all three surfaces, run 2026-07-02 against the post-Phase-71 tree:
the Python hub (~63k lines, 13 routers), the web flagship (19 pages), and the
Apple app (4-layer SPM package + the 34-file `App/MeetingCapture` module).
Eleven stories authored; branch `phase-72-one-spine` on open.)

## The thesis

Phases 69–71 closed the *felt* gap between the surfaces: same tokens, same IA,
same world. The analysis shows the *structural* gap is still open. The product
is one product in three bodies, and its spine — the names, the wire contracts,
the lifecycles, the module shapes — is held together by prose and habit:

- The primitive contract exists as **four hand-synchronized shapes per kind**
  (Swift `Contracts`, Swift `App/` records with hand-written bridges, Python
  `db/primitives.py`, TS `primitives.ts`), reconciled only by
  `THE_PRIMITIVE_FRAMEWORK.md` prose. `sync.py` keeps `SYNC_KINDS` in lockstep
  with the mobile enum **by comment**. The `contracts/schemas/` dir covers the
  meeting domain (9 schemas) and none of the 10 kinds that actually sync.
- **"Companion" names three unrelated concepts** on one URL prefix: the coder
  session picker (`holdspeak/web/routes/system.py:151+`), the desk actuator
  relay (`holdspeak/web/routes/meetings.py:1202+`), and — in the docs — the
  iPad app itself.
- The **actuator propose→approve→execute lifecycle is implemented twice**; the
  desk copy fabricates a sentinel meeting row (`_COMPANION_MEETING_ID`,
  `meetings.py:1200,1235`) because proposals are modeled as strictly
  meeting-scoped when two real callers have no meeting.
- **`meetings.py` regrew into a god-module** (1,855 lines) past the watch item
  (1,525) and the module budgets `docs/ARCHITECTURE_BACKEND_RUNTIME.md` set
  after Phase 63.
- **Shadow modules / orphans** invite mis-patching and confusion:
  `holdspeak/meeting.py` (actually the recorder) beside `meeting_session/`;
  `runtime_activity.py` beside `runtime/activity.py`; a logger named
  `dictation_runtime` inside `dictation_runner.py:28`; orphaned
  `web/src/scripts/companion-app.js`; dead `/design/check`; the nav-orphaned
  `/activity` page duplicating the dictation cockpit's activity surface.
- The web runs **two parallel live-event systems** (`runtime-bus.js` opens a
  second `/ws` beside `dashboard-app.js`'s owned socket) and still carries
  three pre-Phase-54 monoliths (`history.astro` 3,400 / `desk.astro` 1,732 /
  `live.astro` 1,383, plus their 1,4–1,8k-line scripts).
- **The API surface is undeclared.** 12 of 13 routers hardcode full paths
  per-decorator; which routes the iPad consumes is discoverable only by
  grepping Swift; `docs/ARCHITECTURE.md:165-189` undercounts the real iPad
  client by roughly half (it also drives agents, chains, activity nudges,
  blocks, journal, learning digest, meeting start/stop and import).

Phase 72 replaces each prose seam with a machine-checked one. It is the
structural layer the Equilibrium feature-parity program (HSM 18–23) stands on,
and deliberately owns **none** of Equilibrium's feature gaps (see Scope Out).

## Scope

- **In:** the eleven stories below — the machine-checked primitive contract,
  the declared API surface, the companion untangle, one actuator lifecycle,
  the shadow sweep, the meetings-router split, the `/history` decomposition,
  one live bus, the iPad storing Contracts natively, the honest docs, the
  closeout. Touches `holdspeak/`, `web/src/`, `apple/`,
  `pm/roadmap/holdspeak-mobile/contracts/`, `docs/`.
- **Out:** every Equilibrium-owned gap (iPad dictation/meeting feature clients
  → HSM 18/19; iPhone size class → 20; egress honesty → 21; `graph_json` → 22;
  mobile schema safety + sync live-merge → 23); voice macros' immediate
  dispatch and Slack's inline approve→execute (by design, Phases 52/61); the
  `gen-*.rb` flatten-at-build (by design — SwiftPM cannot emit a signed iOS
  app); `desk.astro` decomposition (fresh Phase-71 code — watch item, not
  debt yet); moving iPad desk persistence off `@AppStorage` into SQLite
  (HSM 23 territory); any new user-facing feature.

## Exit criteria (evidence required)

- [x] JSON Schemas exist for all 10 sync kinds + the ChangeSet envelope, and
      all three surfaces validate against them in their own test suites; a
      deliberate one-surface drift fails the guard (HS-72-01 — proven red
      both ways, outputs in the evidence).
- [x] A committed, generated API-surface manifest with per-route consumers;
      snapshot tests fail on undeclared routes and on Swift calls to
      undeclared paths (HS-72-02 — both directions proven red, outputs in
      the evidence).
- [x] "Companion" means exactly one thing; the coder picker and the desk
      actuator relay live on their own prefixes, with the Swift client and
      web callers moved in the same story (HS-72-03 — manifest diff =
      exactly the eleven moved routes; zero stale grep hits).
- [x] One propose→approve→execute implementation; the sentinel meeting row is
      gone; proposals carry an owner-typed origin (HS-72-04 — the v4→v5
      rebuild proven against a real old-shape DB, backup asserted).
- [x] The shadow modules/orphans are renamed or removed; suite + route
      pre-flight green (HS-72-05 — the wire frame names deliberately kept;
      proven by the web-runtime frame assertions).
- [ ] `meetings.py` split under the module budget with a byte-identical route
      table (HS-72-06).
- [x] ~~`/history` decomposed to the Phase-54 pattern~~ (HS-72-07 **cut** —
      superseded by the 2026-07-02 owner decision to migrate interactive
      surfaces to React; decomposing the Astro monolith in place is wasted
      motion. Discharged, not done.)
- [ ] One `/ws` consumer on the web; the second socket is gone; every shell
      widget still fires (HS-72-08).
- [ ] The iPad's desk records embed the `Contracts` types (bridges deleted);
      golden fixtures round-trip in Swift tests; Simulator proof (HS-72-09).
- [ ] `docs/ARCHITECTURE.md` matches the measured reality; API surface doc
      linked; voice + mermaid guards green (HS-72-10).
- [ ] Full python suite, web build, Swift build + tests, tri-surface contract
      validation, route manifest, route pre-flight — all green in one closeout
      run; `final-summary.md` written (HS-72-11).

## Stories

| Story | Title | Priority | Status | Depends on |
|-------|-------|----------|--------|------------|
| HS-72-01 | The primitive contract, machine-checked | HIGH | **done** (8 kind schemas + ChangeSet envelope + golden fixture; three guards — pytest over a real pull, Swift fixture round-trip, validate.py; three-way kind-set lock; 4 real drifts caught: tombstone payloads (fixed), missing updated_at (tolerant decoders), lossy agent fields (locked, follow-up), the baseURL decode bug (fixed); drift proven red both ways; see [evidence](./evidence-story-01.md)) | — |
| HS-72-02 | The API surface, declared | HIGH | **done** (generated manifest `docs/api-surface.json` + `docs/API_SURFACE.md`: 229 routes, consumers from real call sites — 44 iOS / 151 web; 5 snapshot tests incl. clients-only-call-served-routes; both drift directions proven red; doc guards green; see [evidence](./evidence-story-02.md)) | — |
| HS-72-03 | One name per concept: untangle "companion" | HIGH | **done** (picker → `/api/coders/*`; relay → `/api/desk/actuators/*` in new `desk_actuators.py`; shared lifecycle helpers promoted to `actuator_shared.py`; `meetings.py` 1,855→1,460; all Swift/web/test callers moved same commit; manifest diff = exactly the 11 routes; suites 128+16, swift 394/0, sim BUILD SUCCEEDED (patched toolchain), pre-flight green, full suite 3058; see [evidence](./evidence-story-03.md)) | 02 |
| HS-72-04 | One actuator lifecycle | HIGH | **done** (schema v5: owner-typed `origin` + nullable `meeting_id`; the sentinel meeting dead in code+data+queries; rebuild migration proven against a real v4 DB with backup asserted; `decide_proposal` = the ONE lifecycle, 4 routes thin; wire schema+fixture updated; 123+99 affected tests green; see [evidence](./evidence-story-04.md)) | 03 |
| HS-72-05 | Retire the shadows | MED | **done** (meeting.py→meeting_recorder.py, runtime_activity.py→activity_tracker.py, all importers; wire/API names untouched — the frame tests caught the too-broad first sweep; logger fixed; companion-app.js + /design/check deleted; /activity on Studio; 97+8 tests, 18 pages; see [evidence](./evidence-story-05.md)) | — |
| HS-72-06 | Split the meetings god-module | MED | todo | 03, 04 |
| HS-72-07 | The meetings archive, decomposed | MED | **cut** (superseded by the 2026-07-02 web stack decision — `/history` migrates to React in a later phase instead of being decomposed in place; see the story file) | — |
| HS-72-08 | One live bus on the web | MED | todo | — |
| HS-72-09 | The iPad speaks Contracts natively | HIGH | todo | 01 |
| HS-72-10 | Docs: the honest map (the docs story) | MED | todo | 01–09 |
| HS-72-11 | Closeout: the one-spine proof | HIGH | todo | 01–10 |

Build order: **01 → 02** (the contract, then the declared surface) → **03 →
04 → 06** (the hub chain: names → lifecycle → split) with **05** any time and
**07 / 08** in parallel on the web → **09** (after 01) → **10** (docs) →
**11** (closeout).

## Where we are

**2026-07-02 — HS-72-05 done (5/10).** The shadows are gone.
`holdspeak/meeting.py` (the live recorder, not dead code) is
`meeting_recorder.py`; `runtime_activity.py` is `activity_tracker.py`;
every importer, patch target, and internal-doc reference moved. The
load-bearing subtlety: the `runtime_activity` WebSocket FRAME and the
`_set_runtime_activity` methods are wire/API names consumed by web + iPad
and were deliberately kept — the first sweep renamed them too and the
web-runtime frame assertions failed instantly (the tests doing their job);
the API names were reverted, module references kept. The
`dictation_runner` logger stops calling itself `dictation_runtime`.
Orphans deleted (`companion-app.js`, `/design/check` — built-mount probes
repointed to the kept gallery and `/dictation`); `/activity` gains its
honest Studio card, ending its nav-orphan state. Proofs: rename slice 97
passed; web build 18 pages (down one, the dead page); built-mount +
pre-flight 8 passed; full suite 3061 passed with exactly one failure: the
HS-72-02 manifest guard flagging this story's page deletion — regenerated,
guard 5/5 (the declared-surface loop closing on its first organic drift).
Next: HS-72-06 (split the meetings god-module — now 1,460 lines after
03/04).

**2026-07-02 — HS-72-04 done (4/10).** The actuator lifecycle is ONE
implementation and the sentinel meeting is dead. Schema v5 makes proposals
owner-typed (`origin` meeting|desk, CHECK-constrained; `meeting_id` null
exactly when desk); the v≤4 upgrade runs the documented SQLite rebuild
inside the Phase-50 backup-then-apply path — sentinel-attached rows
re-typed to `origin='desk'` with NULL meeting_id (ids preserved, audit
intact), the fake `companion` meeting deleted, the `list_meetings`
exclusion removed — proven end-to-end against a real v4-shaped database in
the new `test_db_actuator_origin.py` (backup file asserted; the facsimile
initially read as v5 because `INSERT OR REPLACE` on the version PK adds a
second row — the test now clears the table first, a trap worth knowing).
`actuator_shared.decide_proposal` is the single decision lifecycle; the
meeting route and the three desk routes are thin callers, with Slack's
approve-executes-inline consent model expressed as an `executors` entry
rather than an inline branch. The wire gains `origin` (additive); the
proposal schema's `additionalProperties: false` caught it immediately —
the HS-72-01 guard working in anger — and the schema + fixture were
updated deliberately. Snapshot regenerated with the identical no-op
normalizer. Proofs: affected slice 123 passed; all actuator/proposal/
qlippy files 99 passed; validate.py green; full suite 3062 passed, 37
skipped.
Next: HS-72-05 (retire the shadows) or HS-72-06 (split the meetings
god-module) — 06 is now much smaller after 03/04.

**2026-07-02 — HS-72-03 done (3/10).** "Companion" no longer names an API
concept. The coder session picker lives at `/api/coders/*` (renamed in
place in `system.py`); the desk actuator relay lives at
`/api/desk/actuators/{slack,webhook,github}/*` in the new
`desk_actuators.py` (extracted from `meetings.py`, which shrank
**1,855 → 1,460 lines**); and the shared propose→approve→execute helpers —
previously closures inside `build_meetings_router` — are module-level in
`actuator_shared.py`, called by both routers (the exact seam HS-72-04
extends into the one lifecycle service). Every caller moved in the same
commit: the Swift client (including `DeskHostLink`'s relay calls — the
scaffold's belief that Swift never called the relay was wrong), the web
scripts, the docs path, and every test (incl. the `_GITHUB_RUNNER` patch
target, now on `actuator_shared` per the Phase-63 rule). Proofs: the
regenerated manifest diff is exactly the eleven moved routes with consumer
tags re-extracted from the real call sites (cross-surface proof the
clients call the new paths); rename-affected suites 128+16 passed;
`swift test` 394/0; the Simulator app BUILD SUCCEEDED via the full documented toolchain
workaround (`patch-llm-macro.sh` severs the LLM.swift macro, then
`-derivedDataPath` + `-disableAutomaticPackageResolution` +
`-skipMacroValidation` — flag-only attempts still die on the swift-syntax
break); web build + route pre-flight green (Playwright was found
missing from the venv after the earlier extras churn and restored — the
`dev` extras group carries it). Residual finding recorded: the coders
status payload still reports desk connector config (`connectors.*`) — a
conflation inside the payload, noted for 04/10. Next: HS-72-04 (one
actuator lifecycle — kill the sentinel meeting).

**2026-07-02 — HS-72-02 done (2/10).** The API surface is a declared,
committed artifact. `scripts/gen_api_surface.py` enumerates the REAL
assembled app (the pre-flight's own construction, so nothing hides) and tags
every route with its consumers, extracted from the real call sites
(`apple/Sources` + `apple/App` Swift literals with `\(…)`-interpolation
wildcards; `web/src` js/ts/astro literals with `${…}` wildcards and
truncated-interpolation prefix fragments). The measured surface:
**229 routes — 44 iOS-consumed, 151 web-consumed** (the hand-written
ARCHITECTURE description undercounts the iPad by half; HS-72-10 will link
the artifact instead). Five snapshot tests hold it: committed manifest ==
live app, committed markdown == manifest, clients-only-call-served-routes,
non-vacuity pins, and an extractor canary. Calibration caught real
generator traps (FastAPI's WS class is `APIWebSocketRoute` — a naive check
silently dropped `/ws`; Swift log strings leaking as paths). Both drift
directions proven red and reverted. Doc-drift guard 15/15 over the
generated markdown; api-surface tests 5/5; full suite green at ship.
Deviation: the cosmetic `APIRouter(prefix=…)` conversion skipped (recorded
in the evidence). Next: HS-72-03 (untangle "companion") — its rename proof
is now a manifest diff showing exactly the moved routes.

**2026-07-02 — HS-72-01 done (1/10).** The primitive contract is machine-checked.
Eight kind schemas + the ChangeSet envelope landed beside the existing
meeting-domain schemas, with one shared golden fixture consumed by all three
guards: the hub pytest validates a REAL `/api/sync/pull` (one row per kind +
a tombstone) against the schemas and locks the kind set three ways (hub
`SYNC_KINDS` == the schemas' `x-sync-kind` set == Swift `SyncKind`, parsed
from source); `swift test` decodes + round-trips the fixture through the
canonical coder; `validate.py` adds the key-never-syncs negative. The first
enforcement pass caught four real drifts — the hub emitting full values on
tombstones (fixed, one line, against its own documented rule), Swift
requiring an `updated_at` the hub never emits for seven kinds (a hub-pulled
KB could never have decoded; tolerant decoders added), `Agent.manual_context`/
`use_zone_context` silently lossy through hub sync (locked in the schema,
follow-up filed), and `RuntimeProfile.baseURL` unable to decode off the wire
at all under `convertFromSnakeCase` (explicit coding key). Deliberate drift
proven red in both directions and reverted. validate.py 20/20; contract+sync
pytest 21 passed; full `swift test` 394 passed / 0 failures; full python
suite 3051 passed, 38 skipped. SERIALIZATION-CONTRACT gained §12 (enforcement). Next:
HS-72-02 (the API surface, declared).

**2026-07-02 — opened + scaffolded.** Authored from a four-track architectural
analysis (hub / web / Apple / PMO state) run against the post-Phase-71 tree.
Headline findings verified in-tree before authoring: the `/api/companion/*`
triple overload (`system.py:151+` vs `meetings.py:1202+`), the
`_COMPANION_MEETING_ID` sentinel (`meetings.py:1200,1235`), `meetings.py` at
1,855 lines, `holdspeak/meeting.py` being the live recorder (NOT dead code —
imported by five `meeting_session/` modules + `main.py:439`; the remediation
is a clarifying rename, not deletion), `companion-app.js` orphaned
(`companion.astro` loads `companion-desk.js`), `/design/check` and `/activity`
with zero inbound links, and `contracts/schemas/` holding 9 meeting-domain
schemas but none for the primitive kinds. Eleven stories authored. Next: an
agent starts HS-72-01 (the schemas + tri-surface validation) on this branch
under the PMO gate.

## Active risks

| Risk | Mitigation | Stop signal |
|------|------------|-------------|
| Route renames strand the paired iPad app | Swift client + web callers + tests move in the same commit; nothing is released on the Apple side, no compat shims | Any grep hit for an old `api/companion` path in `apple/` or `web/src` after HS-72-03 merges |
| Module splits break patch targets (the Phase 63 lesson) | After any split, grep tests for the old dotted path; route table proven byte-identical via the HS-72-02 manifest | A test patching `holdspeak.web.routes.meetings.<name>` fails, or the manifest snapshot diff is non-empty when the story claims identity |
| The actuator `origin` migration violates the Phase-50 schema matrix | Additive column + `SCHEMA_VERSION` bump + the 4-way matrix tests re-run | The newer-DB-on-older-build refusal test goes red, or a backup is not taken before apply |
| Web decomposition silently unstyles JS-rendered DOM (the standing Astro gotcha) | `<style is:global>` discipline + screenshot-verify every decomposed surface | A class present in the built bundle that does not visually apply in the screenshot |
| The Swift record refactor regresses the desk | Golden-fixture round-trip tests + full `xcodebuild` + Simulator screenshots; owner device walk at closeout | Desk objects fail to render, drag, or persist on the Simulator walk |
| Scope magnetism toward Equilibrium features | The Out list names the owning HSM phase for every adjacent gap | A story diff adds a feature client (facets, aftercare, import, egress) instead of structure |

## Decisions made

- **The phase lives in the `holdspeak` roadmap** (Phase 72), not
  `holdspeak-mobile`: the hub is the backbone and most of the diff is hub +
  web; Phase 71 set the precedent for a `holdspeak` phase touching `apple/`.
- **"Coder" is the canonical name** for the session-picker concept — the
  Primitive Framework already distinguishes `agent` (persona) from `coder`
  (live session); the picker routes follow the noun.
- **Structural cohesion here, feature parity in Equilibrium.** Every adjacent
  feature gap is explicitly routed to its owning HSM phase in Scope Out.
- **`holdspeak/meeting.py` is renamed, not deleted** — verification showed it
  is the live recorder layer.

## Decisions deferred

- The final home of the `/activity` admin surface (default in HS-72-05: link
  it from the Studio index; the owner may prefer folding domains/connectors
  admin into Settings).
- `desk.astro` (1,732 lines) decomposition — fresh Phase-71 code; becomes a
  watch item with a density-guard ceiling, not a story.
- ~~Consolidating the two JS-loading conventions~~ — **resolved by the
  2026-07-02 owner decision** (Phase 73 re-scaffold): interactive surfaces
  are React + Vite islands; document pages stay Astro; no new Alpine. The
  `?raw`+`new Function` pattern dies with each surface's migration, desk
  first.
