# HSM-16-03 — The desktop hub surface for organization

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** todo
- **Depends on:** HSM-16-02 (the entities + policy).
- **Unblocks:** HSM-16-05 (wire), HSM-16-04 (the web reads the same store).
- **Owner:** unassigned

## Problem

For organization to flow, something must be the **hub** — the canonical store the iPad and the web both
reconcile against. That is the desktop (the Mac server: `holdspeak/web_server.py` + the runtime). Today
it has no concept of Desk directories or knowledge bases.

## Scope

- **In:**
  - A canonical, persisted store on the desktop for `Directory` / `KnowledgeBase` / `Membership`
    (reuse the existing DB seam; additive tables/collection).
  - The sync surface: `GET`/`POST` (or extend the existing dictation/companion API family) so a paired
    device can **pull** the current organization ChangeSet and **push** its local changes — the
    transport for HSM-16-05. Authorization via the existing pairing token (`HTTPDesktopClient`).
  - Honors the egress + approval contract (Phase 15): organization is local-by-default mesh data;
    nothing leaves the user's devices.
- **Out:** the iPad/web clients (16-05/16-04); rendering. Keep it to the store + endpoints + tests.

## Acceptance criteria

- [ ] The desktop persists directories, KBs, and memberships canonically (survives restart).
- [ ] A pull endpoint returns the organization ChangeSet; a push endpoint applies a device's changes
      under the 16-02 conflict policy; both behind the pairing token.
- [ ] Python tests cover persistence + push/pull + a conflict reconcile, run via `uv run pytest -q`.

## Test plan

- `uv run pytest -q` for the new routes + store (create/list/push/pull/reconcile). A pull-after-push
  round-trip returns the merged set; an unauthorized call is refused.
