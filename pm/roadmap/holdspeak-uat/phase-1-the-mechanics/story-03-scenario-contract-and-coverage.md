# HSU-1-03 — The scenario contract + the feature ledger

> **Superseded contract notice:** This story accurately records protocol v1.
> Protocol v2 forbids its default-all-yes `surfaces` model and instead requires
> one explicit implementation target plus compatible explicit form factors.
> See `uat/AUTHORING.md`; do not author new scenarios from the schema below.

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** done
- **Depends on:** HSU-1-02
- **Owner:** agent

## Problem

The scenario is the unit of UAT, and it needs a contract: what world
to stage (deck + seeds + nodes), what to tell the human to do, what
they should expect, and what verdict to collect. Just as important:
scenarios must cite *which shipped feature they cover*, against an
enumerated ledger of everything the 90 phases actually delivered — the
owner's standing point: **we have git; coverage is derived from the
record, not remembered.** Without the ledger, a green sitting proves
only that we tested what we happened to think of.

## Scope

- In:
  - **The scenario contract** — `uat/scenarios/<pack>/<nn>-<slug>.yaml`:
    `id`, `title`, `features: [ledger keys]`, `recipes` (the HSU-1-02
    state recipes that stage the world — decks/seeds ride inside
    them), **`surfaces`** (the three-target rule: default
    `{web: yes, ipad: yes, iphone: yes}`, overridable per scenario
    *and per step* with `n/a: <reason>` — a surface is opted OUT with
    a stated reason, never silently absent), ordered `steps` (each:
    `do` — the instruction to the human, `expect` — the honest pass
    bar, optional `where` — the product route/screen to open),
    optional `mid_run` actions the conductor performs between steps
    (apply a recipe, restart with another deck, kill a node — the
    HSU-1-01/02 verbs), and `teardown`. Loader + validation with
    named, greppable errors. A step's expected verdict count = its
    applicable surfaces.
  - **The feature ledger, v1** — `uat/features.yaml`: the shipped
    capabilities enumerated as stable keys (e.g. `dictation.pipeline`,
    `meetings.import.transcript`, `desk.steering.arm`,
    `mesh.relay`, …), each entry naming the holdspeak phase(s) that
    shipped it and carrying a per-surface applicability column
    (`web/ipad/iphone: yes|no|unknown` — `unknown` is honest and
    expected at v1). Built by walking `pm/roadmap/holdspeak/README.md`'s
    phase index (with git history as the tiebreaker for what survived
    later phases), reviewed by hand — the derivation script
    (`uat/tools/build_ledger.py`) proposes, the committed YAML is
    canon. Retired features are marked `retired`, not deleted. **v1
    is the mechanical seed**: Phase 2 (The Inventory) owns making it
    exhaustive and resolving every `unknown`; this story owns the
    format and the derivation.
  - **Coverage math** — given a pack (or a finished sitting), compute
    features covered / total live features, **per surface and
    overall**; exposed via the conductor API for HSU-1-04/05 to
    render.
  - **The smoke pack** — `uat/scenarios/smoke/`: 6–8 scenarios proving
    the rig's whole vocabulary: a dictation-surface walk on
    `golden-local`, a meeting round-trip on
    `meeting-just-ended-open-actions`, a desk walk over `seeded-desk`
    **declared three-surface** (the same seeded primitives checked on
    web, iPad, and iPhone), one `bad-endpoint` honest-failure
    scenario, one `no-model` first-run-truth scenario, one mesh-node
    scenario with a mid-run `mesh-node-just-died`, and at least one
    step carrying an honest per-surface `n/a` with its reason.
- Out: rendering (HSU-1-04), verdict storage semantics (HSU-1-04),
  the exhaustive inventory (Phase 2), full-coverage pack authorship
  (Phase 3 — the matrix will make the gap list explicit).

## Acceptance criteria

- [x] The contract is schema-validated; a malformed scenario fails
      load with a named error naming the file and field
      (`ERROR <path>: <issue>`, `test_scenarios.py`).
- [x] Every scenario must cite ≥1 ledger key that exists and ≥1
      recipe that exists; an unknown key or recipe fails validation.
- [x] Surface rules enforced: every scenario resolves to an explicit
      per-surface applicability; `n/a` without a reason fails
      validation; a step with every surface `n/a` fails too.
- [x] `uat/features.yaml` exists with every holdspeak phase (0–87 —
      the record's actual span) mapped to at least one ledger entry or
      an explicit `internal/no-uat-surface` marker — no phase silently
      absent — and every entry carrying the three applicability columns
      (`unknown` allowed at v1). Seeded from the directory's 255 rows by
      `uat/tools/build_ledger.py` (proposes; the committed YAML is canon,
      freshness-checked in `test_build_ledger.py`).
- [x] Coverage math is exact and tested, per surface and overall
      (covered, uncovered, retired excluded, `n/a` and `unknown`
      handled distinctly — `test_ledger.py`).
- [x] The smoke pack (7 scenarios) loads clean, cites real ledger keys
      and recipes, and exercises: both golden decks' postures
      (`seeded-desk`/`fresh-desk` + `meeting-just-ended-open-actions`),
      both bad decks (`intel-endpoint-dead`, `first-run-no-model`), a
      three-surface scenario, an honest `n/a` with reason, and one
      mid-run conductor action (the mesh kill).
- [x] Tests green under `uv run pytest -q tests/uat/` (65 local +
      2 `.43`-gated).

## Test plan

- Unit: schema validation (positive + negative fixtures), ledger
  integrity (keys unique, phases exhaustive), coverage math.
- Integration: load the smoke pack end to end; dry-run a scenario's
  staging (deck applied, seeds applied, nodes up) without a human.
- Manual / device: the pack is *sat through* in HSU-1-06.

## Notes / open questions

- `expect` lines are written against POSITIONING canon voice: honest
  pass bars ("the badge reads local", "doctor names the dead
  endpoint"), never marketing.
- The ledger doubles as the Phase-2 work generator: its `unknown`
  applicability cells and thin domains ARE the inventory's worklist,
  and after Phase 2 the uncovered keys ARE Phase 3's scenario backlog.
