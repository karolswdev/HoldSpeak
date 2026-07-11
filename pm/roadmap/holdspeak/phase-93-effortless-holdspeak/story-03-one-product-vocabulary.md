# HS-93-03 — One professional product voice

- **Project:** holdspeak
- **Phase:** 93
- **Status:** in progress — shared contract, full-client census, production
  remediation, and automated verification complete; owner/physical-device copy
  review pending
- **Depends on:** HS-93-01
- **Unblocks:** HS-93-04, HS-93-07, HS-93-08
- **Owner:** unassigned

## Problem

Phase 92 added a canonical registry, but primary client copy still mixes legacy
nouns and generic verbs with marketing, storytelling, mascot voice, and
explanatory prose. A registry is not convergence until the production product
speaks professionally and consistently.

## Scope

- **In:** Implement `copy-contract.md`; inventory and rewrite rendered
  primary-client strings across React and flagship Swift; expand the controlled
  census;
  change saved/live capability, destination, boundary, state, review,
  authorization, execution, and recovery copy; consequence-specific buttons;
  remove promotional, cinematic, quest-like, anthropomorphic, patronizing, and
  redundant operational prose; compatibility exceptions limited to SDK, wire,
  migration, marketing pages, and advanced diagnostic contexts; cross-client
  fixture, screenshot, and owner read-through review.
- **Out:** Renaming internal classes for aesthetics, deleting compatibility
  aliases, or flattening deliberate platform-native wording.
- **Paths:** product-language/trust/operation registries and guards, Web routes,
  AppShell, RuntimeDocs, Desk/History/Qlippy/Mission Control, flagship Swift root,
  Queue/Review/Desk proposal surfaces, docs and UAT wording.

## Acceptance criteria

- [x] The primary-client census fails on `Agent Desk` for Coder sessions,
      product-facing Profile/Recipe/Chain drift, paired-as-local wording, bare
      `pending`, and consequential generic verbs without adjacent commitment.
- [x] A copy inventory classifies every primary-journey string as label, state,
      supporting line, detail, error/recovery, or deliberate marketing/SDK
      exception; unused and redundant strings are deleted rather than rewritten.
- [x] Web and Swift use Persona for saved behavior, Coder session for a live
      process, Runs on for placement, and named boundary language for this
      device, paired device, private endpoint/node, and external service.
- [x] Web and Swift render Secure, Normal, and YOLO as the product posture labels
      while versioned adapters preserve current `safe`, `neutral`, and `yolo`
      wires; no UI calls the posture an inference Profile.
- [x] Review, approval, grant/arm, execution, and completion states are distinct;
      every button that can execute or queue an effect names the consequence and
      destination.
- [x] Operational React and Swift copy contains no promotional claim, cinematic
      or quest framing, mascot banter, faux urgency, congratulations, narrative
      filler, or paragraph that duplicates visible state/actions.
- [ ] Every forced-failure string names what failed, what was retained, the
      destination when relevant, and the next valid action without apology,
      jokes, or generic reassurance.
- [x] Compatibility and SDK exceptions are enumerated and versioned; a new
      exception requires an explicit reason rather than a broad path exclusion.
- [ ] Owner copy review completes the ten primary journeys on Web/iPhone/iPad
      with zero misunderstood noun, state, destination, or commitment.

## Test plan

- **Unit:** Python/Vitest/Swift registry fixtures, rendered-string census, copy
  exception allow-list, and failure-copy structure tests;
  exact commitment-label tests across proposal and steering surfaces.
- **Integration:** route DTO and UI tests proving the same reason/commitment text
  reaches Web and Swift; documentation drift guard.
- **Manual / device:** Read every ten-journey surface on production React,
  iPhone, and iPad without repository context; mark unclear, promotional,
  theatrical, patronizing, anthropomorphic, or redundant copy as blocking, then
  predict each action and compare the actual receipt.

## Notes / open questions

Generic `Open` remains valid for a non-consequential view when the adjacent
subject is unambiguous. The census targets ambiguity and filler, not the English
language. Professional copy does not require a sterile visual product.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.
