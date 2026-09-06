# HS-173-02 — The model drafter

- **Project:** holdspeak
- **Phase:** 173
- **Status:** done
- **Depends on:** HS-173-01
- **Unblocks:** HS-173-06
- **Owner:** unassigned

## Problem

The model drafter exists as `_draft_with_model`
(project_update_service.py:679) and is functional: it resolves a
deployment revision, builds a prompt from the deterministic claim
inventory, and invokes the inference runner. But the owner's desk has no
model assignment for the `project.update.draft` capability (the 170
concierge must land first), so it has never produced a real draft. The
arc says: "claims preserved, prose rewritten, unverified marked, the
egress chip on the draft."

## Scope

- In:
  - The model drafter rewrites the deterministic body_md into
    stakeholder-readable prose while preserving every Claim ref.
  - Unverified claims (where the model generated language not
    grounded in the deterministic inventory) are MARKED with the
    existing `UNVERIFIED_MARKER` (project_update_service.py:79,
    UPD-002).
  - The egress chip appears on the draft card whenever the model
    drafter is used (Article III: the model may be cloud-hosted).
  - The deterministic drafter remains the fallback: if the model
    is unavailable, the deterministic draft ships as-is with no
    unverified markers.
  - The draft is always editable before publish (Article IV: voice
    arms, it does not fire).
- Out:
  - Automatic publishing of model-drafted updates.
  - New claim types beyond the existing schema.
  - Changing the deterministic drafter's output.

## Acceptance criteria

- [x] The model drafter produces stakeholder-readable prose from the
      deterministic inventory; verified by a unit test with a seeded
      Room state.
- [x] Every factual sentence in the model output carries a Claim ref
      from the deterministic inventory; no invented refs.
- [x] Unverified claims are marked with `UNVERIFIED_MARKER`
      (Article VI).
- [x] The egress chip appears on the draft card when the model drafter
      is used; absent when the deterministic fallback is used.
- [x] The deterministic drafter is the fallback; model unavailability
      produces the deterministic draft, not an error.
- [x] The draft is editable before publish (Article IV).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k model_drafter`
  - Model drafter rewrites prose while preserving claim refs.
  - Unverified claims are marked.
  - Model unavailability falls back to deterministic.
  - Egress chip present on model draft, absent on deterministic.
- Integration: the rig boots a hub with a model assignment, drafts an
  update, and reads the output.
- Manual: the owner sees a model-drafted update on his desk.

## Notes / open questions

- The `_draft_with_model` already exists and is functional. This story
  is about making it produce stakeholder-quality prose (prompt tuning,
  output parsing via `_parse_model_output` at line 544) and wiring the
  egress chip. The heavy lifting may be prompt engineering.
