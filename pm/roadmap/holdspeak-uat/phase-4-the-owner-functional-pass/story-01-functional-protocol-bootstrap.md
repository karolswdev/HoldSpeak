# HSU-4-01 — Executable functional protocol + exact bootstrap

- **Project:** holdspeak-uat
- **Phase:** 4
- **Status:** done
- **Depends on:** HSU-3-02
- **Owner:** agent

## Problem

The harness has broad authored coverage but presents ten historical packs with
raw slugs, no coherent owner order, and no at-a-glance distinction between
automatic state, assisted preflight, and genuinely hands-on setup. Several
user-interface tests also ask the owner to manually manufacture meetings,
action states, and proposals that the conductor can create exactly.

**Protocol-v2 amendment (2026-07-09):** The original delivery counted
web/iPad/iPhone surface slots. The subsequent owner audit found that model could
substitute responsive React for Swift. Current execution requires one named
implementation target plus compatible form factors; the original counts remain
historical evidence, not the active denominator.

## Scope

- In:
  - An executable campaign manifest that composes canonical scenarios by
    reference and preserves their protocol snapshot/evidence boundary.
  - Seven owner-facing campaigns with purpose, duration, prerequisites,
    bootstrap split, and move-on gate.
  - `uat/FUNCTIONAL-PASS.md`: the actual execution protocol, usability bar,
    per-scenario loop, campaign stop gates, and explicit exclusions.
  - Exact local sync-staged meeting actions and proposal queues for aftercare,
    mobile proposal review, and Qlippy.
  - Guided-site usability changes that put numbered campaigns first and explain
    what is automatic versus physical/manual.
- Out:
  - Product fixes found by the sitting.
  - Human verdicts or physical-device claims.
  - Drift/schema/no-telemetry/token-attack hardening.

## Acceptance criteria

- [x] Campaign manifests resolve known scenario references in order, reject bad
      references/duplicates, validate like packs, and snapshot canonical assets.
- [x] The site leads with seven numbered functional campaigns and shows purpose,
      time, preflight, bootstrap split, and move-on gate before starting.
- [x] The owner protocol covers 85 functional scenarios / 484 observations and
      makes campaigns 1–5 the core pass.
- [x] Protocol v2 requalifies the executable pass as 90 scenarios / 327
      target-specific slots, separates React Desk from flagship Swift Desk, and
      forbids viewport evidence from satisfying native acceptance.
- [x] Exact aftercare and proposal fixtures stage one pending + one accepted
      action, one review proposal, and a two-card Qlippy queue through public
      product routes, idempotently and without executing a connector.
- [x] Harness/unit/site tests and a live local bootstrap integration are green.

## Test plan

- Unit/contract: scenario, recipe, pack, campaign, API, sitting, and debrief tests.
- Site: Vitest plus production build.
- Live local: apply the exact aftercare/proposal/Qlippy recipes to an isolated
  `golden-local` product and assert exact IDs/states/destinations plus idempotency.
- Manual/device: owner-gated in HSU-4-02/03, not claimed here.
