# Phase 51 — Public-Docs Hygiene

**Status:** IN PROGRESS (2/5). Opened 2026-06-07 on user direction, right after
Phase 50 closed + merged (PR #35). Net-new from a between-phases conversation
(captured as [project backlog](../BACKLOG.md) candidate H): a cheap, release-facing
follow-on now that the gate is down and strangers can install from the public repo.

**Last updated:** 2026-06-07 (HS-51-02 done: the scrub. All 6 in-scope guides plus
the optional asset readme are rewritten into product-tense; the in-scope leak grep
(case-insensitive) is now empty, doc guards green (75 passed), `MIR-01`/`DIR-01`
intact. A case-insensitive re-grep before scrubbing caught 5 lowercase-only leaks
the HS-51-01 grep missed, so the HS-51-03 guard must be case-insensitive. The
`humanizer` skill was run over all 15 rewrites (no AI tells, no new dashes). Next:
HS-51-03 (the guard).)

## The thesis — why this phase

**Phase 50 cut the release gate, but the public surface still reads like an internal
artifact.** A stranger who installs HoldSpeak from the repo opens the docs and finds
the project's own roadmap vocabulary staring back. Grounded in the live tree
(`grep -rInE 'HS-[0-9]{2}|Phase[ -][0-9]+|PMO|closeout|the current roadmap'` over
`README.md` + `docs/`, minus `docs/internal` and `docs/evidence`):

- **`docs/CONNECTOR_DEVELOPMENT.md`** narrates itself by phase: "Phase 9 shipped the
  first three connectors; phase 11 ...", "Phase 13 additions", "the current
  roadmap". A user does not know what a phase is.
- **`docs/DEVICE_PROTOCOL.md`** carries story IDs in a protocol table ("Periodic
  tick during meeting (HS-17-05)", "HS-17-08 / HS-17-13") and phase-relative TLS
  posture ("Phase 14 is plain `ws://`", "Phase 15's tunnel layer").
- **`docs/INTELLIGENT_TYPING_GUIDE.md`** cites "the HS-19 closeout" as the source of
  a known-good profile.
- **`docs/RELEASING.md`** points at "the Phase 50 evidence".
- The root **`README.md` is already clean** (only legitimate `actuator` product
  nouns), so the leak is in the deeper guides, not the front page.

The vocabulary means nothing to a new user and reads as half-finished. The fix is
small, mechanical, and exactly the kind of thing that should ship right after a
release gate.

## Goal

Make the user/operator-facing docs read like a product: strip internal
roadmap/process vocabulary (`Phase NN`, `HS-NN-NN`, `PMO`, "closeout", "the current
roadmap"), rewrite phase-relative claims into product-tense so the meaning survives
for a reader who has never heard of a phase, keep legitimate product nouns
(`actuator`) and named architecture specs (`MIR-01`/`DIR-01`), and lock the clean
state with a doc-drift guard plus a codified rule so the next phase cannot
reintroduce the leak. Docs-and-test only; no product behavior changes.

## Scope

- **In:** the leak inventory + vocabulary policy (HS-51-01); the scrub of
  user/operator-facing docs (HS-51-02); a roadmap-vocabulary doc-drift guard scoped
  to user-facing docs (HS-51-03); the rule codified in `DOCS_STYLE.md` (HS-51-04);
  closeout (HS-51-05).
- **Out:** the PMO roadmap corpus (`pm/roadmap/**`), `docs/internal/**`, and
  `docs/evidence/**` — frozen history, kept verbatim, never scrubbed or scanned; any
  product/code/behavior change; renaming product nouns or the `MIR-01`/`DIR-01`
  specs; restructuring the docs (Phase 46 did the lift, this is a vocabulary pass).

## Exit criteria (evidence required)

- A written leak inventory classifying every offending line as banned vs keep, and a
  fixed user-facing-vs-internal scope. (HS-51-01)
- Every banned reference gone from user/operator-facing docs, rewritten into
  product-tense; product nouns + spec names untouched; doc guards green. (HS-51-02)
- A roadmap-vocabulary guard in `test_doc_drift_guard.py`, scoped to user-facing docs
  only (not `docs/internal/`, not `docs/evidence/`), green on the clean tree, with a
  non-vacuous sanity test. (HS-51-03)
- A "no roadmap vocabulary in user-facing docs" rule in `DOCS_STYLE.md`. (HS-51-04)
- A dogfood proving the guard catches a planted violation and passes clean; full
  suite green; `final-summary.md`; phase CLOSED; PR to `main` merged on green;
  BACKLOG candidate H flipped to shipped. (HS-51-05)

## Invariants

- **Never touch the internal corpus.** `pm/roadmap/**`, `docs/internal/**`,
  `docs/evidence/**` keep their phase/story vocabulary; the guard does not scan them.
- **Rewrite, don't amputate.** A phase reference that carries real meaning is
  reworded into product-tense, not deleted into a dangling clause.
- **Behavior-preserving.** No code path, capture, dictation, plugin, synthesis, or
  routing change. Docs + one test file only.
- **Product nouns survive.** `actuator`, `connector`, `MIR-01`, `DIR-01` stay.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-51-01 | Leak inventory + vocabulary policy | done | none |
| HS-51-02 | Scrub user-facing docs (phase-relative -> product-tense) | done | HS-51-01 |
| HS-51-03 | Lock it: roadmap-vocabulary doc-drift guard | not started | HS-51-02 |
| HS-51-04 | Docs: codify the rule in DOCS_STYLE.md | not started | HS-51-02, HS-51-03 |
| HS-51-05 | Closeout: dogfood + final-summary + PR | not started | HS-51-01..04 |

## Where we are

2026-06-07, on the `phase-51-public-docs-hygiene` branch. HS-51-01 (inventory) and
HS-51-02 (scrub) are done: the 6 in-scope guides now read in product-tense, the
in-scope leak grep is empty, doc guards are green, and the `humanizer` skill cleared
all 15 rewrites. Next is HS-51-03 (the doc-drift guard that locks the clean state,
**case-insensitive** per the lowercase leaks the first grep missed), then HS-51-04
(the `DOCS_STYLE.md` rule) and HS-51-05 (closeout). Read
[`AGENT-BRIEF.md`](./AGENT-BRIEF.md) and [`leak-inventory.md`](./leak-inventory.md)
first.
