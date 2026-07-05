# HSM-16-05 — Wire the mesh: organization flows back and forth

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** done (2026-07-04 resume survey — pre-paid: the Phase-23-04 10-kind push→pull round-trip matrix carries kb/directory/membership byte-faithful, golden-pinned on both sides of the wire; live merges proven in the 22-01/22-04 DeskSync passes)
- **Depends on:** HSM-16-02 (model), HSM-16-03 (hub), HSM-16-04 (web surface).
- **Unblocks:** HSM-16-06 (proof).
- **Owner:** unassigned

## Problem

The pieces exist in isolation: the iPad has a local org store, the desktop is the hub, the web has a
Desk. Nothing connects them. This story makes a knowledge base (or directory, or classification)
created on **any** surface appear on the **others**.

## Scope

- **In:**
  - The iPad reconciles its `@AppStorage` organization against the desktop hub (pull on open / pair,
    push on change) via `HTTPDesktopClient` + the HSM-16-02 reconcile policy. The local `hs.desk.*`
    maps become a projection of the synced entities (id-keyed).
  - The web Desk reads/writes the **same** hub store, so it and the iPad converge.
  - **Layout stays local** (per the phase taxonomy): positions/modes/spill are not pushed; only
    organization (containers + membership) syncs.
  - Sensible sync triggers (on foreground / on pair / on change) — not a chatty poller; reuse the
    Phase-15 mesh plumbing where it fits.
- **Out:** real-time live push (a later story if wanted); content sync (already Phase 10). Conflict
  policy is 16-02's — this story applies it, doesn't redefine it.

## Acceptance criteria

- [ ] Create a KB on the iPad → after sync it exists on the desktop and appears on the web Desk (and
      vice-versa), with the same id and members.
- [ ] Classify a meeting into a KB on one surface → the membership shows on the others after sync.
- [ ] A delete/rename reconciles deterministically per HSM-16-02 (no duplicate or zombie containers).
- [ ] Desk layout is provably NOT synced (arrange on iPad, the web keeps its own arrangement).

## Test plan

- Cross-surface integration: scripted push from a fake device → desktop → pull on another → identical
  org set (Python side). On-device: the proof in HSM-16-06 is the real-metal confirmation.
