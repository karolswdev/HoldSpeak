# Phase 72 — Agent Brief (read this first)

**Phase 72 — One Spine (cross-surface cohesion).** Opened from a deep
architectural analysis of all three surfaces (Python hub, web flagship, Apple
app) on 2026-07-02. Phases 69–71 made the surfaces *feel* like one product;
this phase makes them *be* one product structurally. Today the product's spine
— its names, wire contracts, lifecycles, and module shapes — is held together
by prose documents and habit, not by anything a machine checks. Every one of
those prose seams has already drifted at least once.

## 0. Mission

One spine: one machine-checked primitive contract, one declared API surface,
one name per concept, one actuator lifecycle, no shadow modules, module budgets
restored, one live event bus on the web, and the iPad storing the Contracts
types natively instead of hand-mirroring them. Feature parity is NOT this
phase (that is the Equilibrium program, HSM 18–23); this phase is the
structural layer Equilibrium's features stand on.

## 1. The one thing you must not get wrong

**Byte-identical behavior everywhere the story does not explicitly change it.**
This is a cohesion phase, not a feature phase. Route renames, module splits,
and record refactors all carry the same failure mode: something that used to
work silently stops (the Phase 63 lesson: patch targets move; the Phase 53
lesson: a feature can be silently dead while all plumbing passes). Every story
must prove the before/after equivalence it claims — the route-manifest
snapshot, the full suite, screenshots for JS-rendered web DOM, a Simulator
build for Swift. When a story renames a route, the Swift client, the web
callers, and the tests move **in the same commit** — this repo ships both
sides of every seam, and nothing is released on the Apple side, so there are
no compat shims ever.

## 2. What the analysis found (the debt this phase retires)

Full detail in [`current-phase-status.md`](./current-phase-status.md). The
headlines, all verified against the tree on 2026-07-02:

1. **The primitive contract lives in prose ×4.** Each primitive kind exists as
   a Swift `Contracts` type, a Swift `App/` record with hand-written
   `toContract()`/`init(contract:)` bridges, a Python repository shape
   (`holdspeak/db/primitives.py`), and a TS shape (`web/src/lib/primitives.ts`)
   — reconciled only by `THE_PRIMITIVE_FRAMEWORK.md` saying "shapes match this
   doc byte-for-byte". `holdspeak/web/routes/sync.py` keeps `SYNC_KINDS` "in
   lockstep with the mobile/web SyncKind enum" — by comment. The
   `contracts/schemas/` dir has 9 JSON Schemas for the meeting domain and
   **zero** for the 10 primitive kinds that actually sync.
2. **"Companion" means three unrelated things** on one URL prefix: the coder
   session picker (`system.py:151+`), the desk actuator relay
   (`meetings.py:1202+`), and (in docs) the iPad app itself.
3. **The actuator lifecycle is implemented twice**, and the second copy
   fabricates a fake meeting row (`_COMPANION_MEETING_ID = "companion"`,
   `meetings.py:1200`) to satisfy a NOT NULL FK — a missing abstraction.
4. **`meetings.py` regrew into a god-module** (1,855 lines; the architecture
   doc flagged it as a watch item at 1,525 and set module budgets it now
   violates).
5. **Shadow modules and orphans**: `holdspeak/meeting.py` (the recorder,
   misleadingly named against `meeting_session/`), `runtime_activity.py` vs
   `runtime/activity.py`, a logger literally named `dictation_runtime` inside
   `dictation_runner.py`, `web/src/scripts/companion-app.js` (orphaned),
   `/design/check` (dead), `/activity` (a nav-orphaned duplicate surface).
6. **The web has two live-event systems** (`runtime-bus.js` opens a second
   `/ws` beside `dashboard-app.js`'s own socket) and three monolith pages
   (`history.astro` 3,400 / `desk.astro` 1,732 / `live.astro` 1,383) that
   never got the Phase-54 treatment.
7. **Nobody can say what the API surface is.** 12 of 13 routers hardcode full
   paths per-decorator; the iPad-vs-web consumer split is discoverable only by
   grepping Swift; `docs/ARCHITECTURE.md:165` undercounts the iPad client by
   roughly half.

## 3. What is deliberately NOT here (owned elsewhere — do not duplicate)

- iPad dictation/meeting **feature clients** → HSM 18/19.
- iPhone size-class work → HSM 20.
- Egress honesty (`.mixed`, hard-coded "On device") → HSM 21.
- Workbench `graph_json` round-trip → HSM 22.
- Mobile schema safety + sync live-merge → HSM 23.
- Voice macros staying immediate-dispatch, and Slack's inline approve→execute:
  **by design** (Phases 52/61) — do not "fix".

## 4. Rules that bite (repo conventions)

- PMO commit gate: write `.tmp/CONTRACT.md` fresh per commit (template in
  `pm/roadmap/PMO-CONTRACT.md`); one story per PR; evidence file ships in the
  same commit that flips a story to done.
- Tests: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (the metal file
  hangs without a mic). Web: edit `web/src`, `cd web && npm run build`; the
  `_built/` bundle is gitignored — commit source only. Astro scoped CSS never
  reaches JS-injected DOM — `<style is:global>` + screenshot-verify.
- Swift: `gen-meeting-capture.rb` COPIES sources — re-run after every `App/`
  edit; `swift test` does not build the App target; Simulator screenshots are
  the floor, an owner device walk is the bar.
- Patch targets live in the module that defines the symbol (Phase 63): after
  any split, grep the tests for the old dotted path.

## 5. Build order

**01 → 02** are the foundation (the contract, then the declared surface).
**03 → 04 → 06** is the hub chain (untangle names → one lifecycle → split the
god-module last, smallest). **05** any time. **07, 08** parallel on the web.
**09** after 01 (it consumes the schemas/fixtures). **10** after features,
**11** last.
