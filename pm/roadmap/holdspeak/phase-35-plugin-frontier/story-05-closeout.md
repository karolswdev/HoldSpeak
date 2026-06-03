# HS-35-05 — Phase closeout + final-summary

- **Status:** not-started.

## Goal

Close Phase 35 cleanly: confirm the plugin system is now externalizable end-to-end
(authoring guide true + linked, packs discoverable, per-project enable/disable
working, incident/comms e2e covered) and write the phase `final-summary.md`.

## Scope

- **Routing invariants** — the 14 built-ins still register + route identically
  (chain constants unchanged); the pack/enable layers sit around them.
- **Doc truth** — `docs/PLUGIN_AUTHORING.md` matches the shipped pack/enable
  surface; doc link-check green; README plugin section points at the public guide.
- **Suite + ruff** — `uv run pytest -q --ignore=tests/e2e/test_metal.py` green; new
  modules (`plugin_sdk`, `plugin_pack_loader`, `plugin_packs/`) ruff-clean.
- **`final-summary.md`** — what shipped, decisions (incl. actuators deferred to
  Phase 36), state at close; flip the project README phase row → `done` and refresh
  the HANDOVER pickup pointer (teeing up Phase 36 — Actuators).

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- Manual: a clean-clone reader can follow `docs/PLUGIN_AUTHORING.md`; a fixture user
  pack loads.

## Done when

- [ ] Built-in routing unchanged; pack + enable/disable + e2e all green; ruff-clean.
- [ ] `final-summary.md` written; project README phase row = `done`; HANDOVER
      refreshed (Phase 36 — Actuators teed up).
