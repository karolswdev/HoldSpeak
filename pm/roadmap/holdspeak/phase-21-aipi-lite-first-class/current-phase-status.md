# Phase 21 — AIPI-Lite First-Class Integration

**Last updated:** 2026-05-24 (HS-21-01 closed: AIPI-Lite tree imported under `aipi-lite/`).

## Goal

Make AIPI-Lite a first-class part of the HoldSpeak repository so firmware,
bridge, protocol, and companion UX work can be developed and reviewed together.

## Scope

### In

- Import the AIPI-Lite firmware and bridge source tree under `aipi-lite/`.
- Preserve local runtime config on disk while keeping secrets ignored.
- Document the import source and working-tree state.
- Update HoldSpeak roadmap/source canon so AIPI-Lite is part of the product tree.

### Out

- Repackaging the bridge as a HoldSpeak Python package.
- Firmware flashing or live device verification.
- New protocol behavior.
- Cross-network transport work.

## Exit criteria

- [x] AIPI-Lite firmware and bridge source exist under `aipi-lite/`.
- [x] `aipi-lite/secrets.yaml` and `aipi-lite/bridge.env` are ignored by Git.
- [x] Import provenance is documented.
- [ ] Follow-up developer workflow is defined: run tests, flash firmware, and operate bridge from the unified checkout.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-21-01 | Import AIPI-Lite tree | done | [story-01-import-aipi-lite-tree.md](./story-01-import-aipi-lite-tree.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-21-02 | Unified AIPI developer workflow | backlog | — | — |

## Where we are

The AIPI-Lite working tree has been imported under `aipi-lite/`, including the
current firmware, bridge, tests, docs, roadmap, and local uncommitted source
changes from the prior sibling checkout. Local config files remain available on
disk but ignored. Next pickup is HS-21-02: define and validate the unified
developer workflow.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Secrets accidentally tracked | medium | Root `.gitignore` and `aipi-lite/.gitignore` ignore `secrets.yaml` and `bridge.env`; verify with `git check-ignore`. | `git status` shows local config as staged/untracked. |
| Imported AIPI history loses provenance | low | `aipi-lite/IMPORT.md` records source path, branch, HEAD, and dirty files. | Future work cannot explain where imported code came from. |
| Two PMO roadmaps diverge | medium | Keep AIPI roadmap imported for history, but use HoldSpeak Phase 21 for unified-repo integration work. | Same story is updated in both places without an explicit handoff. |

## Decisions made

- 2026-05-24 — **Use `aipi-lite/` as the first-class directory.** The name is short, product-aligned, and clearly owns device-side firmware/bridge work.
- 2026-05-24 — **Keep local config on disk but ignored.** `secrets.yaml` and `bridge.env` may exist locally inside the import, but must not be tracked.

## Decisions deferred

- Whether to preserve the old sibling repo as an archive or retire it.
- Whether to package `aipi-lite/bridge` as an installable HoldSpeak extra.
- Whether the AIPI roadmap should remain nested or be folded into the HoldSpeak roadmap after this transition.
