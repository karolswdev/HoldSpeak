# Phase 1 — The Mechanics

**Last updated:** 2026-07-09 (HSU-1-03 shipped: the scenario contract +
the feature ledger (255 keys, every phase mapped) + coverage math + the
7-scenario smoke pack; 3/6)

## Goal

Build the UAT rig itself — the conductor that hosts HoldSpeak on this
Mac under controlled conditions and reachable by the devices, the
induction engine (config decks good and bad, desk seeding, and named
**idempotent state recipes** with verify probes — repeatable worlds,
not stumbled-into ones), the **three-surface** scenario contract
(web / iPad / iPhone, verdict per surface, honest `n/a`) with an
enumerated feature ledger, the guided website that walks a human
through a pack and captures per-surface verdicts — from the device's
own browser too — and the debrief + triage protocol that turns a
sitting into backlog-ready findings — proven by one real smoke-pack
sitting run end to end by the owner across all three surfaces.

## Scope

- **In:** the `uat/` harness (conductor process, run lifecycle, run
  DB, LAN reachability for device sittings), the induction engine
  (config decks, seed manifests, idempotent state recipes with verify
  probes, mesh-node spawn/kill), the three-surface scenario YAML
  contract + loader + validation, `uat/features.yaml` v1 (the ledger
  seeded from the holdspeak phase index, per-surface applicability
  columns, `unknown` honest), one smoke pack (~6–8 scenarios incl. at
  least one deliberately-bad deck and one three-surface scenario),
  the React+Vite guided site with per-surface verdict capture usable
  from the devices' browsers, the debrief packet generator
  (per-surface scores, cross-surface splits first-class), the joint
  triage protocol, harness docs, the live closing sitting. Absorbing
  the dogfood substrate (isolated `_home` recipe, fixture generators,
  mock repos, transcripts).
- **Out:** the exhaustive capability inventory (Phase 2 — The
  Inventory); full scenario coverage of the product (Phase 3); any
  change to HoldSpeak product behavior (the harness drives the
  product through its existing CLI/config/API surface only — a
  product bug found here becomes a *finding*, not a fix in this
  phase); device-side state induction beyond hub-synced state (a
  Phase 2 inventory question); CI automation of sittings (a sitting
  is human by definition); packaging/publishing the harness.

## Exit criteria

- [ ] `uv run python -m uat.conductor` serves the guided site on a
      pinned local port (LAN-optable for device sittings); a run
      boots an isolated HoldSpeak with a chosen deck, health-checked,
      logs captured, torn down cleanly, and reports pairing facts a
      device app can use.
- [ ] At least five decks exist including two deliberately bad ones,
      and a scenario can assert the product *fails honestly* under
      them.
- [ ] The shipped state recipes apply idempotently and verify via
      probes read back through product routes — incl.
      `meeting-just-ended-open-actions` yielding a real meeting with
      a real open action.
- [ ] The scenario contract is validated by tests with the surface
      axis enforced (explicit applicability, `n/a` requires a
      reason); `uat/features.yaml` v1 enumerates the shipped surface
      with every holdspeak phase mapped and three applicability
      columns; the smoke pack loads clean.
- [ ] The guided site walks a pack step by step, captures
      pass/fail/partial/skip + note + screenshot **per (step,
      surface)** into the run DB, works from an iPhone-width browser
      over LAN, and survives a mid-sitting product restart.
- [ ] A finished sitting generates a debrief packet (markdown + JSON,
      per-surface scores + coverage %, cross-surface splits rendered
      as one finding); the triage protocol doc defines the joint
      review and the BACKLOG feed format.
- [ ] The closing sitting: the owner runs the smoke pack live on this
      Mac end to end — the three-surface scenario sat on web, iPad,
      and iPhone with ≥1 verdict cast from a device — the debrief is
      generated, and at least one finding is triaged through the
      protocol.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSU-1-01 | The conductor: hosted runs | done | [story-01](./story-01-the-conductor.md) | [evidence-01](./evidence-story-01.md) |
| HSU-1-02 | The induction engine: decks, seeds, state recipes | done | [story-02](./story-02-the-induction-engine.md) | [evidence-02](./evidence-story-02.md) |
| HSU-1-03 | The scenario contract + the feature ledger | done | [story-03](./story-03-scenario-contract-and-coverage.md) | [evidence-03](./evidence-story-03.md) |
| HSU-1-04 | The guided site | backlog | [story-04](./story-04-the-guided-site.md) | — |
| HSU-1-05 | The debrief + the triage protocol | backlog | [story-05](./story-05-the-debrief.md) | — |
| HSU-1-06 | Docs + the first sitting | backlog | [story-06](./story-06-docs-and-first-sitting.md) | — |

## Where we are

**HSU-1-03 is done (2026-07-09).** The scenario contract and the feature
ledger live under `uat/conductor/contract/`. **The ledger**
(`uat/features.yaml`) enumerates 255 capabilities as stable keys, each with
its per-surface applicability (`yes|no|unknown`), the holdspeak phases that
shipped it, needed recipes, and priority — plus a `phase_map` pinning
**every** holdspeak phase 0–87 to its covering keys or an explicit
`internal/no-uat-surface` marker (20 internal/refactor phases carry the
marker, honestly). It is seeded from the Phase-2 directory's 255 rows by
`uat/tools/build_ledger.py` (which *proposes*; the committed YAML is canon,
freshness-checked in CI). **The contract** (`scenarios.py`) loads/validates
scenarios with named `ERROR <path>: <issue>` errors, enforces the surface
axis (default all-yes, opt out only with `{n/a: reason}`), and resolves
per-(step, surface) applicability. **Coverage math** (`coverage.py`/ledger)
is exact per surface and overall, excluding retired, counting `unknown`
distinctly. **The smoke pack** (`uat/scenarios/smoke/`, 7 scenarios) proves
the whole vocabulary: both golden decks' postures, both bad decks, a
three-surface desk walk, an honest per-surface `n/a`, and a mid-run mesh
kill. Conductor API: `/api/features`, `/api/packs`, `/api/packs/{pack}`.
65 local tests. Next: HSU-1-04 (the guided site).

---

**HSU-1-02 is done (2026-07-09).** The induction engine lives under
`uat/conductor/induction/`: five **decks** (`golden-local`, `golden-43`,
`bad-endpoint`, `no-model`, `mesh-node` — each round-tripped through the
product's own `Config.load` so they can't rot), **seed manifests** applied
through the product's public routes (`/api/notes`, `/api/kbs`,
`/api/meetings/import`) with deterministic ids so re-seeding upserts, a
**probe** layer that reads state back through product `GET` routes, a
**mesh NodeManager** (real `holdspeak mesh serve` workers as their own
process groups), and the **recipe** engine: YAML recipes composing
deck + seeds + actions, closed by a verify probe, **idempotent by
probe-first contract** (apply checks the probe; already-satisfied is a
no-op), with `includes:` composition and cycle refusal at load. Seven
smoke recipes ship (`fresh-desk`, `seeded-desk`, `intel-endpoint-dead`,
`first-run-no-model`, `meeting-just-ended-open-actions`, `mesh-node-alive`,
`mesh-node-just-died`). Proven: `seeded-desk` idempotent (twice, no dupes);
`bad-endpoint` degrading honestly (runtime-test + doctor both name the dead
port, <5s); a recipe verify-failure raising loudly; **live on `.43`** — a
real meeting with an open action from real intel, and the mesh node
spawn→live→kill→offline lifecycle read through `/api/profiles`. 44 local
tests + 2 `.43`-gated. Next: HSU-1-03 (the scenario contract + feature
ledger).

---

**HSU-1-01 is done (2026-07-09).** The conductor exists: a standalone
FastAPI app (`uv run python -m uat.conductor`, pinned port 8799) that
boots `holdspeak web --no-open` as a managed subprocess under a fresh
isolated HOME (`uat/_runs/<run_id>/home/`, the dogfood `_home` recipe
ported to `uat/conductor/home.py`), polls the auth-exempt `/health`
route until up, captures the product's stdout/stderr per run, and tears
it down by process-group (SIGTERM→SIGKILL) with no orphans. Restart-
with-a-different-overlay is a first-class verb. LAN binding mints the
run its own web auth token and reports pairing facts. The run DB
(sqlite, `uat/_runs/uat.db`) lands its full schema here (runs,
scenario_executions, step_verdicts, findings) though verdict *writes*
arrive in HSU-1-04. The subprocess boundary is grep- **and** clean-
import-enforced (`tests/uat/test_no_holdspeak_import.py`). Proven by 20
harness tests incl. a real-boot integration test that boots, health-
checks, restarts, and tears down an actual HoldSpeak. Next: HSU-1-02
(the induction engine — decks, seeds, recipes).

---

Scaffolded 2026-07-08 from the owner's direct ask: a robust UAT
harness that forces a real human sitting — a guided website with
scenario scripts and per-step feedback capture, powerful enough to
host the server, flip good/bad configurations, and seed the desk.
Amended the same day, pre-build, on the owner's second direction:
(a) **three-surface UAT** — nearly every scenario aims at web, iPad,
and iPhone with a verdict per surface and `n/a` honest; (b) **the
induction engine** — decks/seeds generalized into named idempotent
state recipes with verify probes, so the protocol is repeatable; (c)
**Phase 2 re-chartered as The Inventory** (the joint capability
census), pushing the coverage pack to Phase 3. Decisions locked at
scaffold: standalone conductor (not an in-product route), absorb +
supersede the Phase-67 dogfood harness, coverage enumerated from the
git/phase record, mechanics + one smoke pack only. Next: HSU-1-01.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The conductor grows a second product (auth, users, deploy) instead of staying a dev rig | medium | Localhost-only, no auth, run DB is a local sqlite; scope "Out" list enforced at review | Any story adding harness features no scenario needs |
| Seeding via product APIs couples the harness to route churn | medium | Seed through the same public routes the web UI uses; contract tests pin the few routes used | A product route rename silently breaking seeds with no failing harness test |
| Bad decks bitrot as the config schema moves | medium | Decks are validated against `Config.load` round-trip in tests | A deck that no longer produces the failure its scenario asserts |
| The human sitting never happens and the rig joins PROTOCOL.md on the shelf | medium | The closing story IS the sitting; the phase cannot close without it | Phase open >2 weeks with 5/6 done |

## Decisions made

| Date | Decision | Reason | Authority |
|---|---|---|---|
| 2026-07-08 | Standalone conductor process, never an in-product route | The harness must boot/kill/reboot the product under bad configs; it cannot live inside the process under test | owner + agent |
| 2026-07-08 | Absorb and supersede dogfood (Phase 67) | One harness, no drift; the guided site replaces the fillable PROTOCOL.md | owner |
| 2026-07-08 | Coverage ledger derived from the phase index + git history | "We have git" — the shipped surface is enumerated from the record, not from memory | owner |
| 2026-07-08 | Phase 1 = mechanics + one smoke pack | Prove the rig on a thin vertical slice before authoring at scale | owner |
| 2026-07-08 | Story prefix `HSU`, code home `uat/` | Consistent with HS/HSM siblings; harness never ships in the package | owner |
| 2026-07-08 | Three surfaces (web/iPad/iPhone) are the default target of every scenario; verdicts per surface; `n/a` needs a stated reason | "Literally nearly all of the tests should aim for those three targets" — owner, directly | owner |
| 2026-07-08 | States are induced by named idempotent recipes with verify probes, never staged by hand | "Induce specific states, for a more idempotent, repeatable protocol" — owner, directly | owner |
| 2026-07-08 | Phase 2 = The Inventory (the joint capability census + charter); the coverage pack moves to Phase 3 | The matrix must exist before scenarios are authored at scale — "really, really big material" | owner |
| 2026-07-09 | Recipe idempotency is **probe-first**: apply evaluates the verify probe; if the world already holds it is a verified no-op, else it stages then re-verifies. Seeds carry deterministic ids so the staging path upserts, never duplicates | One mechanism gives both idempotency and self-verification; matches the RECIPE-WORKLIST "applied twice = same verified state" contract | agent (HSU-1-02) |
| 2026-07-09 | Mesh liveness is read through `GET /api/profiles` `mesh_liveness` (a meshNode profile registered per node), the product's own hub-side heartbeat view — not `/api/mesh/info` (identity-only) | The relay claim stamps last-seen hub-side; `/api/profiles` is the public read that surfaces it, so the harness verifies through a real product route | agent (HSU-1-02) |

## Decisions deferred

| Decision | Trigger | Default |
|---|---|---|
| Whether dogfood's files physically move under `uat/` or are imported in place | HSU-1-01 implementation | Import/reuse in place; move only what the conductor must own |
| Speak-to-fill mic on the site's note fields (needs a transcriber; the product under test may be down) | HSU-1-04 | Ship typed notes first; mic rides the host product's transcribe route when it is up, degrades honestly when not |
| Whether a sitting can drive a remote mesh node on another machine | Phase 2 scenario needs | Phase 1 spawns local `mesh serve` processes only |
