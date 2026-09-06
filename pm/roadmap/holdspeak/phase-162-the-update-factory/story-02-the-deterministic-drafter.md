# HS-162-02 - The deterministic drafter: the fallback ships first

- **Project:** holdspeak
- **Phase:** 162
- **Status:** done
- **Depends on:** HS-162-01
- **Unblocks:** HS-162-03
- **Owner:** unassigned

## Problem

UPD-003: a deterministic template fallback MUST remain available when
inference is unavailable. It ships FIRST — it defines the section
contract (UPD-001) and the claim schema (UPD-002) the model drafter
will be constrained to.

## Scope

- **In:** `ProjectUpdateService.draft_update(project_id,
  generator="deterministic")`: reads the Project room truth (items,
  changes, decisions, open review, observations with evidence links)
  over ONE pinned revision + manifest; emits editable Markdown with
  the UPD-001 sections — progress, decisions, risks/blockers,
  dependencies, next actions, and source-coverage caveats when any
  source is degraded/absent; EVERY factual sentence carries a claim
  entry resolving to ≥1 evidence ref/locator (the §4.1 refs the
  rooms already speak); zero prose without a locator — the
  deterministic drafter simply does not know how to lie. Persists
  via 01's repo (single transaction). Regenerate = supersede
  unaccepted draft (UPD-004).
- **Out:** model drafting (03), wire (04).

## Acceptance criteria

- [ ] Golden tests: a seeded room drafts the six sections with every claim carrying refs; the caveat section appears iff coverage is partial (ledger-honest).
- [ ] A room with nothing to say drafts the honest minimal update, not filler.
- [ ] Determinism: same room state ⇒ byte-identical draft (goldens pinned).

## Test plan

- **Unit:** tests/unit/test_update_drafter.py (goldens + claim resolution truth table).
