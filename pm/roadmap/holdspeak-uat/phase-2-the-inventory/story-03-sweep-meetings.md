# HSU-2-03 — Inventory sweep: meetings

- **Project:** holdspeak-uat
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HSU-2-01
- **Owner:** unassigned

## Problem

Meeting intelligence is the product's deepest vertical — capture
through synthesis through follow-through — and its surface story is
genuinely three-way (the iPad records meetings on-device; the web desk
reviews and acts; the iPhone carries the result). No single artifact
enumerates what a sitting should hold it to.

## Scope

- In: the meetings domain inventoried into `uat/features.yaml` — at
  minimum the territory of: live capture (hub and on-device),
  device/remote audio ingest, meeting import (audio and transcript,
  web + CLI), MIR routing + segment probing, the 14 plugins + plugin
  packs + per-project enablement, artifact rendering (cards,
  copy-as-markdown, mermaid), meeting history + facets + search,
  aftercare (open/decided/changed, moment jump, follow-up draft),
  actuators end to end (propose → approve → execute, GitHub/webhook/
  Slack, audit), exports, re-processing the archive, and the
  cross-surface meeting lifecycle (recorded on iPad → intel on the
  hub → reviewed on web → visible on iPhone). Row format, method, and
  verification discipline identical to HSU-2-02 (per-surface
  applicability verified on the real surface; record-vs-product
  discrepancies become finding rows).
- Out: ranking (HSU-2-05), scenario authoring (Phase 3), building
  recipes, fixing anything found.

## Acceptance criteria

- [ ] Every HS/HSM phase whose subject is in this domain is mapped to
      ≥1 ledger row or explicitly marked internal — checked by a
      domain phase-list in the story evidence.
- [ ] Zero `unknown` surface cells remain in this domain; contested
      cells carry verification notes/screenshots.
- [ ] Every row names its required state recipe(s); the
      meeting-shaped ones (imported-with-artifacts, aftercare-open,
      proposal-pending) explicitly reconciled against the HSU-1-02
      smoke recipes.
- [ ] The cross-surface lifecycle rows exist (they are the parity
      claim at its most end-to-end).
- [ ] Ledger validation green.

## Test plan

- Unit: ledger validation suite green on the grown file.
- Integration: n/a.
- Manual / device: the surface-verification pass, incl. one real
  on-device-recorded meeting traced to the web desk and the iPhone.

## Notes / open questions

- **Starting map:** [`directory/20-meetings.md`](./directory/20-meetings.md)
  — 42 capabilities pre-seeded by the sweep. This story verifies the
  map on device and reconciles it into the ledger; the trust/egress
  meeting rows also live in
  [`directory/40-trust-and-egress.md`](./directory/40-trust-and-egress.md).
- Actuator rows must carry their consent framing (off by default,
  approval audited) into the scenario hints — a UAT scenario that
  suggests weakening a gate is wrong by construction.
