# Phase 107 — Close the Side Doors — FINAL SUMMARY

**Census delta: 38 debt → 15 debt.** Audited baseline 40 total /
2 covered / 38 debt; close 21 total / 3 covered / 3 exempt / 15 debt.
**Dictation did not get slower:** the kernel's admission price is
~25 ms per typed act (~2.7% of the owner-perceived path), disclosed,
measured by interleaved A/B, and accepted by the owner with the
baseline re-pinned. The owner's sitting passed — verdict verbatim:
**"I complete the sitting - all of it works!"**

## What shipped (7/7, PRs #399-#405 + the closing commit)

- **HS-107-01** — dictation's commit boundary as a pinned contract
  (`docs/internal/DICTATION_COMMIT_BOUNDARY.md`): five paths + T03,
  each with effect, commit point, authority basis cited to
  `operation_policy.py:238`, receipt shape, exemptions. Zero
  rerouting; baseline latency on real metal.
- **HS-107-02** — all ten typing sites: T03/T04 via `process.input@1`
  (the encoder gap closed as driver adaptation), D01-D07 via the new
  `desktop.type_text@1` clause-4 fast path, D08 eliminated as dormant
  with a named refusal. Receipts record the act, never the content.
- **HS-107-03** — subprocess triage: C01/C04 through
  `subprocess.exec@1` (argv immutable at admission, payload-swap
  proven dead, ONE decision per act), C02/C03/C05 argued as reads
  with principal + named read authority; `agent:untrusted` running
  `gh` refused by name.
- **HS-107-04** — egress triage: the charter's "11 migratable"
  honestly corrected to 7; seven migrated through `external_egress@1`
  (destination in every receipt, the desk badge journal-fed);
  transcription latency untouched (−0.08%).
- **HS-107-05** — the independent audit demoted EIGHT rows the
  migration stories claimed (T01/T02 and C02/C03/C05 → mixed;
  N10-N12 disputed), corrected the Phase 106 baseline to 2/40, and
  gave every remaining row a machine-asserted closing condition.
  Demotions were the story working.
- **HS-107-06** — the audited number at both doc entry points, a
  drift guard pinning docs ↔ ledger, and the cooperating-code
  narrowing UNCHANGED in strength: coverage changed, containment did
  not.
- **HS-107-07** — the eight-beat machine session as one rerunnable
  command; the owner drove it and passed it 8/8 under his ruled
  baseline.

## The owner's rulings (all riders chartered or resolved, none absorbed)

1. **N10-N12 are exempt computation** — clause-5 exemption
   re-ratified; the HS-107-05 clause-1 challenge resolved by the
   Constitution's sole interpreter. Debt 18 → 15.
2. **Configured wake actions are armed by their configuration** —
   clarifying note added to Article IV.2; defaults still arm.
3. **The ~25 ms admission price is accepted** — baseline re-pinned to
   the kernel path, session-noise bands stated in code, deltas beyond
   them still fail by name.

## The ledger

Operation types now registered: eight — the Phase 106 six plus
`subprocess.exec@1` and `external_egress@1`; `desktop.type_text@1`
joined as the fifth driver. The kernel spine was **byte-unchanged
across the entire phase** (`git diff --exit-code` over
broker/admission/journal/model/executor: exit 0 at every story and at
close). Article XI clause 2 is now materially true for the typing,
subprocess, and egress families of cooperating code; clause 6
**remains in force** over 15 debt sites — five mixed (T01/T02
tmux routes, C02/C03/C05 principal defaults), nine bypass and one
dormant raw-desktop primitive — and self-repeals only at an empty
register, which is RFC §5b confinement's job.

## Remainders → BACKLOG candidate Y

§5b confinement + A01-A10; T01/T02 universal kernel routing;
C02/C03/C05 mandatory principals; the second userland program; the
process window; the generic liveness seam; the CI blind spot
(`tests/e2e/test_live_bus.py` skips without Playwright + a bundle).

## Suites at close

Full suite 4308 passed (only the two known pre-existing UAT
failures: build-ledger staleness, voice-notes 502 copy); web chain
green (354/354, build clean); all doc/voice/vocabulary/census guards
green (49 passed post-ruling).
