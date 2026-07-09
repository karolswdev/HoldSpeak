# HSU-2-02 — Inventory sweep: input & intelligence

- **Project:** holdspeak-uat
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HSU-2-01
- **Owner:** unassigned

## Problem

The daily-driver half of the product — everything between a held key
(or a wake word, or a tapped mic) and text landing somewhere — has
grown across ~30 phases and three surfaces, and no single artifact
enumerates it. This sweep turns that record into ledger rows.

## Scope

- In: the input & intelligence domain inventoried into
  `uat/features.yaml` — at minimum the territory of: the dictation
  pipeline and its stages (blocks, target profiles, project
  KB/context, rewriting depth), correction memory and the visible
  learning loop (journal, digest, replay, the correction ritual),
  preview-before-type, wake word, languages + the spoken-symbol
  dictionary, voice command macros, activity pre-briefing, the
  transcribe-everywhere affordances (hold-to-talk on inputs across
  surfaces), and on-device transcription/models on the iPad/iPhone.
  For every row: stable key, shipping phase(s) (HS and HSM both),
  **per-surface applicability verified on the real surface where not
  obvious** (the web desk, the iPad app, the iPhone app — a
  screenshot for any contested cell), the state recipe(s) a scenario
  would need, and open questions flagged for the HSU-2-05 review.
- In: the method — walk the phase index + git history for the domain,
  cross-check the docs corpus, then verify on the live surfaces;
  where record and product disagree, the product wins and the
  discrepancy becomes a finding row.
- Out: ranking (HSU-2-05), scenario authoring (Phase 3), building the
  named recipes, fixing anything found.

## Acceptance criteria

- [ ] Every HS/HSM phase whose subject is in this domain is mapped to
      ≥1 ledger row or explicitly marked internal — checked by a
      domain phase-list in the story evidence.
- [ ] Zero `unknown` surface cells remain in this domain; every cell
      that was `unknown`/contested carries a verification note (and a
      screenshot where visual).
- [ ] Every row names its required state recipe(s), existing or
      needed (needed ones accumulate in the recipe worklist).
- [ ] Record-vs-product discrepancies recorded as finding rows, not
      silently reconciled.
- [ ] Ledger still validates (`uv run pytest -q tests/uat/` ledger
      tests green).

## Test plan

- Unit: ledger validation suite (from HSU-1-03) green on the grown
  file.
- Integration: n/a.
- Manual / device: the surface-verification pass on the real web
  desk, iPad, and iPhone.

## Notes / open questions

- Authored directly (the standing rule: no subagent fan-out for
  roadmap/PMO content); the surface checks need the real devices in
  hand.
