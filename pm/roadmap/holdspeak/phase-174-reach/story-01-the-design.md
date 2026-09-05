# HS-174-01 — The design

- **Project:** holdspeak
- **Phase:** 174
- **Status:** done
- **Depends on:** Phase 173 merged
- **Unblocks:** HS-174-02, HS-174-03, HS-174-04, HS-174-06, HS-174-07, HS-174-09
- **Owner:** unassigned

## Problem

Every face in 174 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
Reach introduces three new face regions (the remote badge on the
pipeline observer, the credential scope face in Settings, the third
connector's Door card) and modifies the egress chip vocabulary. Without
artboards these cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - The remote EGRESS badge (the badge on every remote MCP read in the
    pipeline observer; the badge vocabulary: local, local+cloud, cloud,
    remote — the new "remote" state; Article III:2).
  - The credential scope face in Settings (the owner mints a scoped
    credential: identity, palette subset, TTL, revoke; the row shows
    active credentials with last-used, expiry, and the palette chip).
  - The third connector's Door card (the same Door grammar as GitHub
    and Jira: the source row with in-world pickers, default Watches,
    the provider chip; the Connections face in Settings with one state
    and one verb per tool).
  - The .43 runner status row (the pipeline observer shows the remote
    runner's last-run, receipts, and the connection state).
  - The LAN companion notification (the push payload shape: count only
    by default, Article III; the companion's notification face).
- Out: implementation; new library species (use existing ones).

## Acceptance criteria

- [x] Artboards at 1440 + 393 on the ratified shell for every new face
      region (Article IX.2; UX-CANON.md rule E.1).
- [x] Counsel reads the artboards before the owner (UX-CANON.md rule
      E.1).
- [x] The owner's word on the canvas (Article IX.4).
- [x] No prose in the artboards (Article VII.1; UX-CANON.md rule A.3).
- [x] Every artboard uses at least three type steps (UX-CANON.md rule
      C).
- [x] The remote badge artboard shows the "remote" egress state
      (Article III:2).
- [x] The credential scope artboard shows OWNER is never a remote
      principal (Article XI:4).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The "remote" egress badge: is it a new color or a variation of the
  existing egress chip? Propose a new semantic token (the existing chip
  has local/cloud/local+cloud; "remote" is a fourth state: the call
  crosses the network but stays on the owner's infrastructure). The
  owner decides on the canvas.
