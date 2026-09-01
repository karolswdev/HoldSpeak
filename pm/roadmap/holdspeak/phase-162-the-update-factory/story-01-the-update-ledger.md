# HS-162-01 - The update ledger: schema v70, revision pinning, the repo layer

- **Project:** holdspeak
- **Phase:** 162
- **Status:** done
- **Depends on:** -
- **Unblocks:** HS-162-02
- **Owner:** unassigned

## Problem

§8: update generation operates over an explicit Project revision and
review/source manifest; UPD-004 demands draft revisions that never
rewrite a published update. Nothing persists updates today.

## Scope

- **In:** schema v70 (additive): `project_updates` — id (pupd_
  prefix, deterministic per §4.1 where the inputs are stable),
  project_id, project_revision (PINNED at draft time), review_id
  (nullable — the manifest anchor), lifecycle
  (draft|published|superseded), draft_revision (int), body_md,
  claims_json (the structured claim metadata: claim text span →
  evidence refs/locators), source_manifest_json (what the draft SAW:
  observation/review/source ids + coverage caveats),
  generator (deterministic|model:<assignment>), created/updated/
  published_at, named-column INSERTs; repo layer with conn-accepting
  `*_in_transaction` variants; lifecycle law: publishing is
  revision+1 on the PROJECT (change row + ledger, one transaction);
  superseding an unaccepted draft replaces it (UPD-004), a published
  update is IMMUTABLE — regeneration creates a new draft.
- **Out:** drafting logic (02/03), routes (04), UI (05).

## Acceptance criteria

- [ ] v70 additive; reconcile green on a COPY of a real DB; fence/census suites stay green.
- [ ] UPD-004 as repo law under test: replace-unaccepted works; any write to a published row refuses typed.
- [ ] Revision pinning: a draft records the project_revision + manifest it was built over; tests prove the pin survives project mutation.

## Test plan

- **Unit:** tests/unit/test_project_updates_schema.py (+ repo truth tables).
