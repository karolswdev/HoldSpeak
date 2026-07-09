# HSU-1-02 — The induction engine: decks, seeds, state recipes

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSU-1-01
- **Owner:** unassigned

## Problem

A UAT scenario is only meaningful if it starts from a *described*
world — and only repeatable if that world can be induced on demand,
identically, a month apart. "Described" is more than a config file:
it is "a meeting just ended with three open actions", "the desk holds
these five primitives", "an agent pane is awaiting input", "the mesh
node just died". Today every one of those states is stumbled into by
hand. The induction engine makes them named, idempotent, verified
verbs of the conductor — the owner's requirement stated directly:
*specific harness logic to induce specific states, for a more
idempotent, repeatable protocol.*

## Scope

- In:
  - **Decks** — named config permutations under `uat/decks/*.yaml`,
    each a sparse overlay the conductor merges over defaults and
    writes as the run HOME's `config.json` before boot
    (`Config.load()` round-trip validated in tests so decks can't rot
    silently). Ship at least five: `golden-local`, `golden-43` (intel
    on the `192.168.1.43` llama.cpp), `bad-endpoint` (dead port —
    degrade honestly, never hang), `no-model`, `mesh-node`.
  - **Seed manifests** — `uat/seeds/*.yaml` describing desk/context
    state; applied after boot **through the product's own public
    routes** (the same `/api/desk/*` the web UI calls: notes, KB,
    recipes; meetings via the transcript-import route with dogfood's
    committed fixtures) so a seeded object is indistinguishable from
    a user-made one. Auth via the run HOME's own web token.
  - **State recipes** — `uat/recipes/*.yaml`, the composition layer
    and the story's center of gravity: a recipe names a world state
    and composes deck + seeds + **process/mesh actions** (boot,
    restart-with-deck, spawn/kill a local `holdspeak mesh serve`
    node) + **product actions** (run a pipeline via product API where
    one exists — e.g. import a transcript so intel produces real
    artifacts and open actions), and closes with a **verify probe**:
    assertions read back through product `GET` routes that the state
    actually holds. A recipe that cannot verify itself fails loudly.
    **Idempotency is the contract**: applying a recipe to a run twice
    converges to the same verified state (re-seed detection, not
    duplicate desks). Recipes compose (`includes:` other recipes);
    cycles refuse at load.
  - Ship the smoke set of recipes, at minimum: `fresh-desk`,
    `seeded-desk`, `meeting-just-ended-open-actions`,
    `intel-endpoint-dead`, `first-run-no-model`,
    `mesh-node-alive` / `mesh-node-just-died` (the died variant is a
    recipe with a mid-run action — the HSU-1-03 contract invokes it
    between steps).
  - Conductor API: `GET /api/decks`, `GET /api/recipes`,
    `POST /api/runs/{id}/recipes/{name}` (apply + verify; the
    response carries the probe results), `POST /api/runs/{id}/nodes`
    + `DELETE /api/runs/{id}/nodes/{name}`.
  - **Dogfood absorption, part 2**: reuse the transcript/meeting
    fixtures (and `make_fixtures.py` where audio is wanted); nothing
    re-authored that dogfood already renders.
- Out: scenario files referencing recipes (HSU-1-03), UI (HSU-1-04),
  remote-machine nodes (Phase 2 decides; local processes only here),
  device-side state induction (the iPad/iPhone apps sync from the
  hub — inducing hub state IS inducing their state; anything truly
  device-local is a Phase 2 inventory finding), new fixture *content*
  beyond what the smoke recipes need.

## Acceptance criteria

- [ ] Each shipped deck round-trips through `Config.load` in tests;
      `bad-endpoint` and `no-model` boot a product that *runs* and
      reports its condition, not a crash-loop.
- [ ] Every shipped recipe applies, **verifies via its probe**, and is
      idempotent: applied twice to one run, the probe passes both
      times and no duplicate state exists (asserted through product
      `GET` routes, never by poking the product DB).
- [ ] `meeting-just-ended-open-actions` yields a real meeting with ≥1
      open action visible via the product's own aftercare/history
      routes — real pipeline output, not a DB fake.
- [ ] A recipe with an unsatisfiable probe fails loudly, naming the
      failed assertion; a recipe cycle refuses at load.
- [ ] A run can spawn a named local mesh node, see it live from the
      product side, kill it, and see the product report it offline.
- [ ] Tests green under `uv run pytest -q tests/uat/`.

## Test plan

- Unit: deck overlay/merge, recipe parsing/composition/cycle refusal,
  idempotency keys, probe evaluation.
- Integration: boot `golden-local`, apply `seeded-desk` twice (probe
  green both, no dupes); apply `meeting-just-ended-open-actions` and
  read the open action back; boot `bad-endpoint` and assert doctor
  names the dead endpoint (local dead port — no `.43` needed).
- Manual / device: mesh-node death observed live rides HSU-1-06.

## Notes / open questions

- Decks are *overlays*, not full configs — the product's defaults stay
  the single source of truth and decks state only their delta.
- Inducing through public routes is a deliberate coupling: if a route
  rename breaks a recipe, that is a real cross-surface break we want a
  failing harness test to catch (risk table in the phase doc).
- Recipes needing real intel output declare `requires: intel` and are
  probed against `golden-43`; the smoke set keeps at least one fully
  local path so the rig demos without the LAN.
