# HS-105-04 - Info on everything — the inspectable desk

- **Project:** holdspeak
- **Phase:** 105
- **Status:** done
- **Depends on:** HS-105-01
- **Unblocks:** HS-105-07
- **Owner:** unassigned

## The reference (the bar)

Workbench's "Information…" worked on ANY icon and showed the whole
truth: the image, size, dates, protection bits, the comment, and —
the forward-thinking part — TOOLTYPES: per-object key-value
configuration, right there, user-editable. Every object on the
machine was inspectable and configurable through one uniform
surface. That is the mindset to replicate: not a properties dialog
per feature, but ONE Info surface derived from the primitive
contract, so inspecting anything feels like inspecting everything.

## Problem

The desk's objects have no uniform "what does the system know about
you" surface. Identity, lineage, size, egress posture, receipts,
and per-object configuration are scattered across cards, settings
surfaces, or nowhere. An OS you cannot ask "what is this, exactly?"
keeps secrets — and a per-kind properties panel would fossilize
into snowflakes within two phases.

## Recipe

1. **One Info card, contract-derived.** A new pull-out (`Info`),
   opened from the right-click menu and the verb registry on EVERY
   primitive kind, composed entirely from contract-declared
   sections — a kind never hand-builds its Info; it declares, the
   surface derives (Article II, enforced by a census).
2. **The universal sections** (every kind, always):
   - **Identity:** kind, name (EditInPlace — rename lives here too),
     id, created/modified.
   - **Lineage:** what made it (the Phase-74 run-born chain, the
     drop source once HS-105-02 lands, import provenance), each
     ancestor openable.
   - **Footprint:** honest size/counts (chars, facts, members,
     artifacts — per kind's declared measure).
   - **Posture:** the egress badge where the object can cause runs
     (a recipe's destination, a profile's endpoint) — the SAME badge
     component, never a restatement.
   - **Receipts:** the object's recent acts (runs it grounded,
     steers it rode into, proposals it raised), newest first,
     capped, each openable.
3. **Tooltypes — per-object configuration as data.** The contract
   grows a per-kind declaration of its editable keys (a recipe's
   destination override, a zone's clean-up grid, a note's language
   hint …), rendered as a uniform key-value editor in Info. Rules:
   only keys the kind declares (no freeform), every edit through the
   object's existing update path (no second write path — census),
   values validated by the declared type. This is the story's
   forward-thinking core: configuration stops being a settings-page
   scavenger hunt and lives ON the object, uniformly.
4. **Read the glass discipline.** Everything renders as labels and
   values — no reassurance, no prose (the voice guard covers the new
   surface). Absent data renders as an honest absence, never a
   fabricated default.
5. **Snapshot into the spec.** The Info schema (universal sections +
   per-kind declarations) is written into the contract area as a
   spec artifact — this surface is likely the single richest page of
   the future Swift spec, so it is authored as one from day one.

## Out of scope

- Editing CONTENT from Info (bodies are edited in place in their
  cards — HS-101 canon); permissions/protection bits (no multi-user
  model exists); any settings-page removal (dedup later, once Info
  proves itself).

## Acceptance

- Info opens on every primitive kind on a seeded desk; the census
  proves derivation (no kind-specific Info component exists).
- Rename via Identity, a tooltype edit on at least two kinds (one
  recipe, one zone), each landing through the existing update paths
  and surviving reload.
- Lineage on a run-born artifact walks to its run; Receipts on a
  grounded note lists the real run from the staged walk.
- Voice guard green; both viewports.

## Test plan

- **Unit:** section derivation per kind; tooltype validation +
  refusal; the write-path census.
- **Integration:** rename + tooltype edits round-tripping; receipts
  query.
- **Live (evidence):** the headed walk on a staged hub with real
  lineage present, screenshots read.

## Chef's notes

- Fight every urge to special-case a kind "just this once." The
  first snowflake voids the story's reason to exist; if a kind
  cannot express its need through a declared section, the contract
  is what grows, deliberately.
- Receipts is the section that makes Info feel ALIVE rather than
  archival — it is also the natural landing pad for Phase 104's
  session/gate receipts later. Leave its query shape general.
