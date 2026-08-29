# HS-150-03 — The chief-of-staff overlay (person_sections)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** done
- **Depends on:** HS-150-01
- **Unblocks:** HS-150-06
- **Owner:** unassigned

## Problem

The Brief is persisted, person-blind, absent on first load, leaks
a raw path into a persisted item, and wears receipt-verbs on
human items (the walk's joy judgment, verbatim in the audit).

## Scope

### In (settled-design D3 + D4)

- **The counsel's structural law:** `person_sections` is composed
  by a standalone `compose_person_overlay(...)` at the ROUTE/MCP
  adapter layer AFTER the observed methods return — the
  MondayBrief dataclass NEVER carries it; generate()/_load_brief()
  stay person-free BY CONSTRUCTION (this kills the
  pipeline_events observer path and the briefs/latest resource
  path in one move). Per relationship-with-signal: next linked
  1:1, THEY-OWE count + stalest age (board by aliases), YOU-OWE
  count, agenda backlog; L2 honesty when the sidecar is closed.
  Pins: the write-count spy on the three brief tables AND a
  pipeline_events content check (no person content in
  result_summary after a full generate+get cycle with People
  present) AND an asdict(MondayBrief) shape pin (no
  person_sections field, ever).
- MCP gate discipline: person_sections absent when People access
  is off; shared_intent-only contents (the 149 F6 pattern).
- The manager's verbs on person items: "Add to 1:1 agenda" (the
  real people.agenda authority) and "Open person"; receipt items
  keep their verbs.
- D4 folds: BriefLane's no-brief state leads with the act
  (Generate — the joy pattern), never null; persisted receipt
  details become summary-level (raw paths never enter
  monday_brief_items — a hygiene pin).
- Shots: the person sections populated, the BriefLane first-load
  state, both widths.

### Out

- Persisting ANY person content (forbidden); regeneration
  semantics; the full Brief beautify (ledger).

## Acceptance criteria

1. With people + a linked 1:1 + mapped delegations: the brief
   response carries person_sections with all four signals; the
   brief TABLES gain zero person rows (the pin).
2. Access-off MCP → person_sections absent; a planted
   leader_private never appears.
3. "Add to 1:1 agenda" from a person item lands in the person's
   agenda through the real authority.
4. First-load BriefLane shows the act; the path-leak pin holds.

## Test plan

monday_brief_service collector/overlay tests + the write-count
pin + the MCP gate pin (planted private) + hygiene pin;
BriefView/BriefLane component tests; live shots.
