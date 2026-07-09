# HSU-1-02 — Decks, seeds, and the mesh

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSU-1-01
- **Owner:** unassigned

## Problem

A UAT scenario is only meaningful if it starts from a *described*
world: a known configuration (sometimes deliberately broken — "does it
fail honestly?" is half of trust) and a known desk (notes, KB,
recipes, a meeting in history — not whatever was lying around). Today
config permutation means hand-editing `config.json` and desk state
means clicking. Both must become declarative inputs to a run.

## Scope

- In:
  - **Decks** — named config permutations under `uat/decks/*.yaml`,
    each a sparse overlay the conductor merges over defaults and
    writes as the run HOME's `config.json` before boot
    (`Config.load()` round-trip validated in tests so decks can't rot
    silently). Ship at least five: `golden-local` (everything local,
    the POSITIONING default), `golden-43` (intel on the
    `192.168.1.43` llama.cpp, the dogfood tier-2 posture),
    `bad-endpoint` (intel pointed at a dead port — features must
    degrade honestly, never hang), `no-model` (no Whisper model
    available — first-run/doctor surfaces must tell the truth), and
    `mesh-node` (a runtime profile targeting a named mesh node the
    conductor controls).
  - **Seed manifests** — `uat/seeds/*.yaml` describing desk/context
    state; the conductor applies one after boot **through the
    product's own public routes** (the same `/api/desk/*` the web UI
    calls: notes, KB, recipes; meetings via the transcript-import
    route with dogfood's committed `.vtt`/`.txt` fixtures) so seeding
    exercises real product surface and a seeded object is
    indistinguishable from a user-made one. Auth via the run HOME's
    own web token.
  - **Mesh hands** — the conductor spawns/kills local
    `holdspeak mesh serve` worker processes attached to a run (same
    managed-subprocess machinery as HSU-1-01), so a scenario can stage
    "the node is alive" and "the node just died" mid-sitting.
  - Conductor API: `GET /api/decks`, `POST /api/runs/{id}/seed`,
    `POST /api/runs/{id}/nodes` + `DELETE /api/runs/{id}/nodes/{name}`.
  - **Dogfood absorption, part 2**: reuse the transcript/meeting
    fixtures (and `make_fixtures.py` where audio is wanted); nothing
    re-authored that dogfood already renders.
- Out: scenario files referencing decks/seeds (HSU-1-03), UI
  (HSU-1-04), remote-machine nodes (deferred, Phase 2), new fixture
  *content* beyond what the smoke pack needs.

## Acceptance criteria

- [ ] Each shipped deck round-trips through `Config.load` in tests;
      `bad-endpoint` and `no-model` boot a product that *runs* and
      reports its condition (doctor/UI state), not a crash-loop.
- [ ] A seed manifest materializes: ≥2 notes, ≥1 KB entry, ≥1 recipe,
      ≥1 imported meeting — verified back through product `GET`
      routes, not by poking the product DB directly.
- [ ] Seeding a run twice is idempotent or refuses loudly (no silent
      duplicate desks).
- [ ] A run can spawn a named local mesh node, see it live from the
      product side, kill it, and see the product report it offline.
- [ ] Tests green under `uv run pytest -q tests/uat/`.

## Test plan

- Unit: deck overlay/merge, manifest parsing, idempotency keys.
- Integration: boot `golden-local`, apply the smoke seed, read desk
  state back via product routes; boot `bad-endpoint` and assert doctor
  reports the dead intel endpoint (no `.43` needed — the bad deck
  points at a local dead port).
- Manual / device: mesh-node death observed live rides HSU-1-06.

## Notes / open questions

- Decks are *overlays*, not full configs — the product's defaults stay
  the single source of truth and decks state only their delta.
- Seeding through public routes is a deliberate coupling: if a route
  rename breaks seeding, that is a real cross-surface break we want a
  failing harness test to catch (risk table in the phase doc).
