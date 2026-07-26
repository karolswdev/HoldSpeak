# Phase 103 — Foundations & Borrowed Fire — final summary

**CLOSED 7/7, 2026-07-25.** Chartered from a four-agent adversarial
research pass (three analysts on `ViuGiaLai/researchmind`, one blind
audit of HoldSpeak's own Desk); most findings rejected, and what
survived skepticism shipped:

- **HS-103-01** — session restoration: the desk remembers its open
  windows (`hs.desk.open-windows`); the audit's second finding
  (`resetLayout()` stale geometry) honestly reported
  not-reproducing, pinned by a regression test.
- **HS-103-02** — the voice guard reads the glass: a dash-in-prose
  rule over rendered strings surfaced 33 offenders where the audit
  named 3; all recomposed; a shared scan-helper false-positive fixed.
- **HS-103-03** — grounding verification: a dependency-free lexical
  entailment scorer on Ask-AI; an adversarial real-metal proof (true
  bullet unflagged, fabricated bullet flagged) through the real UI.
- **HS-103-04** — endpoint health: a thread-safe circuit breaker at
  the two named call sites; `holdspeak doctor` names open circuits;
  18ms fail-fast proven live.
- **HS-103-05** — the steering demo recipe: the flagship feature
  provable on demand by composing existing UAT primitives.
- **HS-103-07** — the AI chat surfaces (chartered mid-sitting by the
  owner's own verdict): a screenshot survey found the real defect —
  a repeating egress/receipt clutter bug breaking line-wrap on every
  reply — fixed, plus turn-entrance motion, a warmer empty state,
  and shared send-press feedback.
- **HS-103-06** — closeout: machine proof, per-story drift-check,
  retrospective, and TWO owner sittings. The first (07-22) held the
  phase open and chartered HS-103-07; the second (07-25) accepted:
  "I accept," verbatim in [evidence-story-06](./evidence-story-06.md).

## Final machine state (on merged main, 2026-07-25)

The failure family every evidence file in this phase documented as
pre-existing (stale API-surface manifest + four refit-stale
assertions) was paid on PR #367's repair commit and re-verified:
pytest 4148 passed / 37 skipped / zero unrelated failures; web tsc +
vitest 318/318 + build + tokens gate clean; all guards green.

## Handoffs and riders

- **Parked, not committed** (recorded in the charter's decisions):
  researchmind's governance-as-data policy engine; the academic-
  domain features.
- **The sitting-loop lesson**: machine-checkable acceptance criteria
  structurally cannot see felt-craft gaps; the owner's sitting is a
  first-class gate (HS-103-07 exists because of it). Phases 105/104
  carry sitting-loop closeouts by construction.
- **Next**: the roadmap pointer moves to
  [Phase 105 — Workbench](../phase-105-workbench/current-phase-status.md);
  Phase 104 (Borrowed Fire II) follows; the kernel phases charter
  from `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md` (its §8
  prerequisites may ride earlier as riders — the effect census
  inventory is already parked under `proposals/`).
