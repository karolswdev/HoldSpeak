# Phase 138 — The People Ledger: final summary

**Closed:** 2026-08-17 (close-out branch `phase-138-close`).
**Verdict chain:** revival counsel RATIFY-WITH-CONCERNS (pre-merge, should-fix
applied in `36807f20`) → fresh close counsel RATIFY-WITH-CONCERNS, no
blockers (S1 fixed before the final flip). Owner sitting pending.

## What shipped

An encrypted, local-only relationship ledger for a technical leader: AES-256-GCM
envelope store in its own sidecar SQLite (`holdspeak/people/`), key held only by
an allow-listed native credential store; manual relationships, notes-only 1:1s
with shared-intent agenda and leader-private prep; requests with explicit
request→commitment transition; commitments projected in memory into
Follow-through with source-dispatched verbs; a singleton Desk People surface
with readiness gates and factual trust badges; default-off People MCP family;
commitment execution into Workbench with satisfaction history.

The implementation landed on main via the PR #459 revival (merged `2c50c2da`,
CI all green, full suite 6000/0). This phase's close-out flipped every story on
gate-captured evidence.

## The proof

- 258 focused tests across the story flips (crypto/AAD, custody allow-list,
  policy hard-refusals, store fail-closed, no-leaks raw-byte sweeps, service
  lifecycle, follow-through regression, routes, MCP, web).
- HS-138-06 attended walk (`scripts/people_walk_full.py`): **55 PASS / 0 FAIL /
  11 shots** — walk-scoped real Security-framework keychain, full lifecycle,
  restart decrypt, missing-key fail-closed + restore + recovery, zero plaintext
  sentinels in DB/WAL/SHM/log bytes, loopback-only network, desktop + narrow,
  zero console errors. Evidence keeps all three captures as provenance (a
  false-positive check → an honest fail → the strict pass).

## Judgment calls held for the sitting

1. **Trust-facts amendment** (story-04, visible): `This device only` →
   `Local storage`; the Send-to-Workbench verb carries a `Workbench model`
   egress badge at the point of decision. Counsel ruled the old claim false;
   owner may overrule.
2. **Walk-scoped keychain**: the walk proves custody on a keychain created
   inside the isolated HOME via the real `security` CLI — the owner's login
   keychain is deliberately untouched. Ruled as satisfying the native-backend
   bar; recorded for the owner's awareness.
3. **Open ledger** (status doc): revival L1–L4 (MCP boundary prose, silent
   empty People cards on a broken sidecar, no dev-only keystore seam, no
   Constitution citations in source) + close CL2/CL3/CL5 (productLanguage
   `local_only` constant reuse risk; Info-lens `Sync: This device only` is true
   and retained; commitment-inspector CycleGadget overlaps the
   Send-to-Workbench label at narrow column widths).

## Pointers

- Status + ledgers: `current-phase-status.md`
- Walk evidence: `evidence-story-06.md`, shots in `assets/walk/`
- Security docs: `docs/PEOPLE_SECURITY.md`, `docs/SECURITY.md` §People
