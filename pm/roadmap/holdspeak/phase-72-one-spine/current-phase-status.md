# Phase 72 — One Spine (cross-surface cohesion)

**Status:** open — scaffolded 2026-07-02, 0/10 (HS-72-07 cut same day;
10 live stories).

**Last updated:** 2026-07-02 (**opened + scaffolded** from a deep architectural
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

- [ ] JSON Schemas exist for all 10 sync kinds + the ChangeSet envelope, and
      all three surfaces validate against them in their own test suites; a
      deliberate one-surface drift fails the guard (HS-72-01).
- [ ] A committed, generated API-surface manifest with per-route consumers;
      snapshot tests fail on undeclared routes and on Swift calls to
      undeclared paths (HS-72-02).
- [ ] "Companion" means exactly one thing; the coder picker and the desk
      actuator relay live on their own prefixes, with the Swift client and
      web callers moved in the same story (HS-72-03).
- [ ] One propose→approve→execute implementation; the sentinel meeting row is
      gone; proposals carry an owner-typed origin (HS-72-04).
- [ ] The shadow modules/orphans are renamed or removed; suite + route
      pre-flight green (HS-72-05).
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
| HS-72-01 | The primitive contract, machine-checked | HIGH | todo | — |
| HS-72-02 | The API surface, declared | HIGH | todo | — |
| HS-72-03 | One name per concept: untangle "companion" | HIGH | todo | 02 |
| HS-72-04 | One actuator lifecycle | HIGH | todo | 03 |
| HS-72-05 | Retire the shadows | MED | todo | — |
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
