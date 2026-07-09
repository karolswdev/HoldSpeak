# HSU-3-02 — Cloud-egress card + per-card egress probe

- **Project:** holdspeak-uat
- **Phase:** 3
- **Status:** backlog
- **Depends on:** none
- **Owner:** unassigned

## Problem

Every egress-badge beat today opens a local note and asserts "local" — the
falsifiable **cloud flip** (a card whose content leaves, named target and all)
is walked on no surface (`PROTOCOL-COVERAGE.md` §3.4). The re-eval also flags a
directory-vs-product mismatch: the directory promises a *per-card* pill, but the
web `egressBadge()` may be one global chrome pill. This story stages a real
cloud-egress card and probes its egress honestly — or records the mismatch.

## Scope

- In:
  - A recipe `egress-cloud-card`: drive an actuator to a pending proposal with a
    real named cloud target (the meetings `aftercare/file-issue` seam, or a
    desk/webhook connector), off-by-default flow turned on for the run.
  - A probe `egress_names_target` (per-card if the product exposes it): the
    card/proposal's egress reads cloud with its target named, no prose. If the
    product's badge is global chrome, a probe `egress_scope_is` reading the
    global scope, and a **ledger note** recording the per-card mismatch.
  - Flip pack-d/07 (egress cloud-flip) + pack-d/11 + pack-a/04
    (`trust.egress.cloud-meeting-intel` OFF/ON) to staged beats.
- Out: actually firing the egress (an unapproved proposal never egresses — that
  invariant is already the close of pack-a/04); any product change to make the
  badge per-card (that would be a *finding*, not this story).

## Acceptance criteria

- [ ] `egress-cloud-card` stages a proposal whose egress names a cloud target,
      queued + unexecuted.
- [ ] A probe reads the egress truth through a product route (per-card if
      available; else the global scope + a recorded mismatch note).
- [ ] The unblocked scenarios carry real verdicts, and the local-vs-cloud
      contrast (a local note stays local; the card reads cloud) is machine-checked.

## Test plan

- Integration: create the proposal, probe its egress, assert unexecuted; the
  local control note reads local.
- Manual/device: n/a.

## Notes / open questions

- Read the meetings `aftercare/file-issue` + `export/slack` routes and the
  proposal egress shape; confirm whether egress is per-card or chrome-global on
  web before asserting.
