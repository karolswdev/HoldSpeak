# HSM-21-05 — Docs + the walk rider

- **Project:** holdspeak-mobile
- **Phase:** 21
- **Status:** in-progress — the docs half is DONE (README's companion paragraph carries
  the one-badge trust surface; ARCHITECTURE names `EgressScope` + the shared posture
  mapping; doc guard 18/18) and the rider is STAGED press-play at
  [`HSM-21-WALK-RIDER.md`](./HSM-21-WALK-RIDER.md) (H1–H3, ~5 minutes on the staged couch
  session). PASS×3 closes this story and the phase.
- **Depends on:** 21-01…21-04 (documents what shipped; the rider verifies it).
- **Unblocks:** phase close (the honesty checks ride the owner's staged couch session).
- **Owner:** unassigned

## Problem

Every phase gets its own documentation story, and this phase's device verification
should not cost a separate session — the couch session (18-06 + 19-07 walks) is already
staged.

## The design

1. **Entry points current:** README / ARCHITECTURE / SECURITY where the egress story is
   told — the one `EgressScope` grammar across surfaces, the Swift guard joining the
   voice guard, the GitHub readiness truth.
2. **`HSM-21-WALK-RIDER.md`**: three honesty checks appended to the couch session —
   H1 a connector primitive's pullout wears Cloud (and a plain note wears On device);
   H2 the shell dictate receipt wears the amber `Local + <host>`; H3 the trust chip
   states the hub's real posture (flip actuators and watch it change).
3. **Screenshots current** per story.

## Scope

- **In:** entry-point docs, the rider doc, screenshot inventory.
- **Out:** running the rider (the owner's hands).

## Test plan

- Doc guards green (`uv run pytest -q tests/unit/test_doc_drift_guard.py`).
- The rider validated press-play against a live local hub.
