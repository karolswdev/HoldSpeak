# HSU-2-01 — The UAT charter

- **Project:** holdspeak-uat
- **Phase:** 2
- **Status:** backlog
- **Depends on:** none (needs only Phase 1's HSU-1-03 ledger format to reference)
- **Owner:** unassigned

## Problem

"UAT" means nothing until it is written down for *this* product. The
owner's standing claim is parity across three surfaces — the iPad,
the iPhone, and the web desk; that parity IS the experience HoldSpeak
is building. UAT is the instrument that holds the product to that
claim, and the charter is where the instrument's rules are set, once,
jointly, so every sitting after it means the same thing.

## Scope

- In: `uat/CHARTER.md`, jointly authored (agent drafts, owner amends
  and approves — the approval is recorded in the doc header), stating:
  - **What UAT is here** — a human sitting with the real product on
    real metal, guided and recorded; what it is not (agent
    self-verification, unit/e2e suites, seeded sim demos — those
    already exist and don't count as a sitting).
  - **The parity frame** — the three surfaces (web desk / iPad /
    iPhone) are the claimed parity set; nearly every scenario aims at
    all three; a cross-surface verdict split is a **parity break**,
    a first-class finding class of its own; `n/a` is legitimate only
    with a stated reason and is itself reviewable (an `n/a` the owner
    disagrees with is a roadmap gap, not a test gap).
  - **Verdict semantics** — what pass / fail / partial / skip each
    mean, precisely enough that two sittings by different moods agree.
  - **Honesty rules** — timestamps are evidence; no proxy sittings
    (the agent never casts a surface verdict); states are induced by
    recipes, never staged by hand; a broken staging is a harness
    finding, recorded, never worked around silently.
  - **The cadence** — when sittings happen (per release cut at
    minimum; after any phase that touches a must-test capability),
    and roles: the owner sits, the agent stages, reads, and triages.
  - **The finding lifecycle** — pointer to `uat/TRIAGE.md`
    (HSU-1-05) and the BACKLOG feed.
- Out: the inventory content (HSU-2-02..04), harness behavior changes
  (the charter documents the rig Phase 1 built; a rule the rig cannot
  enforce yet becomes a rider, named in the charter).

## Acceptance criteria

- [ ] `uat/CHARTER.md` exists and covers every bullet above; the
      parity frame names the three surfaces explicitly as the claimed
      parity set.
- [ ] Owner approval recorded in the doc (date + the owner's own
      amendments visible in the git history, not just an agent draft
      rubber-stamped).
- [ ] The charter and the shipped rig agree: every rule is either
      enforced by Phase 1's mechanics or explicitly named as a rider.
- [ ] Cross-references resolve: TRIAGE.md, the ledger, the scenario
      contract's surface rules.

## Test plan

- Unit: n/a — a canon doc.
- Integration: n/a.
- Manual / device: the owner's read-and-amend pass IS the test.

## Notes / open questions

- The charter's sitting-shape rules are pre-drafted in
  [`../PROTOCOL-NOTION.md`](./PROTOCOL-NOTION.md) (beat spine,
  control-vs-treatment, honest-failure close, per-surface capture) —
  distilled from the walks that already worked. The charter formalizes
  those into canon; this story does not re-derive them.
- The charter is UAT-side canon; if it ever contradicts
  `docs/internal/POSITIONING.md`, positioning wins and the charter
  updates.
