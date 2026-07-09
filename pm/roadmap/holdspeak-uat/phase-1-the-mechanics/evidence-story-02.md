# Evidence - HSU-1-02

- **Story:** HSU-1-02 - The induction engine: decks, seeds, state recipes
- **Status:** done
- **Date:** 2026-07-09

## What shipped

`uat/conductor/induction/` — decks, seed manifests, probes, a mesh NodeManager,
and the recipe engine:

- **5 decks** (`uat/decks/`): `golden-local`, `golden-43`, `bad-endpoint`,
  `no-model`, `mesh-node`. Each round-trips through the product's own
  `Config.load` in `test_decks.py` so it can't drift from the schema. The
  conductor writes the sparse overlay as JSON; it never imports `Config`.
- **Seed manifests** (`uat/seeds/`): notes/KBs/meetings applied through the
  product's public routes (`/api/notes`, `/api/kbs`, `/api/meetings/import`)
  with deterministic ids — re-seeding upserts, never duplicates.
- **Probes** (`probes.py`): every assertion reads state back through a product
  `GET` route (notes/KBs, meetings-with-open-actions, setup runtime-test,
  setup readiness, `/api/profiles` mesh liveness, subprocess `doctor`).
- **Mesh nodes** (`nodes.py`): real `holdspeak mesh serve` workers as their own
  process groups, spawned/killed by name.
- **Recipes** (`recipes.py`): YAML composing deck + seeds + actions, closed by a
  verify probe. **Idempotency is probe-first**: apply evaluates the probe; an
  already-satisfied world is a verified no-op, else it stages then re-verifies
  (a failure raises `RecipeVerifyError` naming the missed assertion). `includes:`
  composition with cycle refusal at load.
- **7 smoke recipes**: `fresh-desk`, `seeded-desk`, `intel-endpoint-dead`,
  `first-run-no-model`, `meeting-just-ended-open-actions`, `mesh-node-alive`,
  `mesh-node-just-died`. Conductor API: `GET /api/decks`, `GET /api/recipes`,
  `POST /api/runs/{id}/recipes/{name}`, `POST/DELETE /api/runs/{id}/nodes`.

## `.43` live proofs (LAN-gated; run 2026-07-09)

These recipes need the `192.168.1.43` llama.cpp endpoint. They self-skip in CI
(no LAN); proven live here.

**Mesh node lifecycle** — `test_mesh_node_lifecycle` spawns a real worker, the
hub reports it **live** via `/api/profiles` mesh_liveness, SIGINT tears the group
down, and the hub flips it to **offline**:

```text
tests/uat/test_induction_integration_43.py::test_mesh_node_lifecycle
1 passed in 128.94s (0:02:08)
```

**Meeting intel → real open action** — `test_meeting_recipe_yields_a_real_open_action`
imports `dogfood/transcripts/pylon-incident.vtt` on `golden-43`, drains the
deferred-intel queue (`POST /api/intel/process`) so real intel runs on `.43`, and
verifies ≥1 open action through the product's own `/api/meetings` history route
(the transcript names "Priya owns the headroom alert, Wei owns the synthetic ACME
CI test…" — real extraction, not a DB fake):

```text
tests/uat/test_induction_integration_43.py::test_meeting_recipe_yields_a_real_open_action
1 passed in 196.54s (0:03:16)
```

## Proof

### Captured run — 2026-07-09T07:17:01Z

- **Command:** `uv run pytest -q tests/uat/ --ignore=tests/uat/test_induction_integration_43.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9a591b5939542abdb06aed7a50e11204ac1c81e8

```text
............................................                             [100%]
44 passed in 11.87s
```
