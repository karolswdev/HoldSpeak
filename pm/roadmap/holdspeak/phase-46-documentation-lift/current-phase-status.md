# Phase 46 — Documentation Excellence & the 10-Second Hook

**Status:** PLANNING (0/6). Opened 2026-06-06 on user direction ("a dedicated
phase that will guide us through scaffolding/updating documentation … the main
README is too low on cool facts of the app, and slightly too large and
repetitive. People love the graphics, so that stays … other documentation files
probably also need a big lift").

**Last updated:** 2026-06-06 (phase scaffolded; HS-46-01 — the doc truth audit —
is the entry point; you reimagine on top of truth, not vibes).

## The thesis — why this phase

**The product outgrew its docs.** Thirteen phases shipped since the last
dedicated documentation pass (Phase 33, OSS readiness) — the journal + replay,
the moment-of-truth, actuators I/II, desktop presence, the first-run wizard, the
config cockpit, persistent memory. The README and guides have accreted, not been
composed. Verified against the live tree:

- **The README sells like a spec sheet, not a product.** 205 lines that open
  with a competent one-liner and then list features. No 10-second hook, no "why
  this is different," and the best stories (it *learns you*; your **voice** now
  gets the afterlife your **meetings** do; 14 real LLM plugins; 100% local) are
  buried or missing. The user's read: *too low on cool facts.*
- **It repeats itself.** "What it does", "Intelligence Pipeline", and "Meeting
  intelligence plugins" re-describe overlapping ground; the pre-release status is
  stated twice; the AIPI-Lite companion gets two long paragraphs for an optional
  device. The user's read: *slightly too large and repetitive.*
- **The graphics are great — and underused.** The pixellab art (logo, workflow
  map, operator-loop GIF, AIPI device) is a genuine asset. **It stays.** But the
  *app itself* is never shown — there are zero real UI screenshots in the README
  or guides, despite a beautiful journal, `/history`, cockpit, and presence HUD.
- **The guides have drifted + lack one voice.** 4,677 lines across 13 docs
  (`PLUGIN_AUTHORING` 808, `INTELLIGENT_TYPING_GUIDE` 668, `MEETING_MODE_GUIDE`
  601, …), written across many phases with different tone, structure, and
  freshness. Some claims likely drifted from live code; the index
  (`docs/README.md`, 64 lines) is a list, not a map.

This phase gives the documentation the same lift the product got: a README that
**hooks in ten seconds** (cool facts up, graphics kept, repetition cut, depth
linked out), real **screenshots of the actual app**, one consistent **voice +
structure** across every guide, and a **truth pass** so nothing is overstated or
stale.

## Goal

Make the documentation worthy of the product: a README that hooks in ten seconds
and sells what's genuinely cool (honestly), and a docs set that is **accurate,
consistent, visually rich, and easy to navigate** — every shipped capability
discoverable and represented, the graphics kept, the bloat gone.

## Scope

- **In:** a **doc truth audit** + drift fix (claims vs live code); a **bold
  README reimagining** (10-second hook · cool-facts highlights · all graphics
  kept · capability matrix · 60-second start · depth linked out · materially
  shorter); a **docs voice & structure system** (a short style guide + the
  standard page skeleton applied across every guide) + an elevated, scannable
  **docs index**; a **visual lift** (real UI screenshots across the guides via
  the existing Playwright scripts + a repeatable capture home); a **coverage &
  discoverability** sweep (a feature → doc matrix; every shipped capability —
  journal/replay/actuators/presence/wizard — sold and linked); a **closeout**
  (link-check + doc-drift green, before/after, `final-summary.md`, PR).
- **Out:** code/feature changes (docs only — if a doc reveals a real bug, file
  it, don't fix it here); new pixellab asset generation (reuse the existing art +
  real screenshots); reference-doc rewrites beyond voice/accuracy unless trivial;
  translating docs; a hosted docs site.

## Exit criteria (evidence required)

- A doc audit lists every live doc with its drift findings; the factual errors
  are fixed; counts/flags/keys/route-names match live code. (HS-46-01)
- The README hooks in ten seconds (a real hook + a cool-facts highlights strip),
  keeps **every** existing graphic, cuts the repetition, links depth out, and is
  **materially shorter** (target ~130–150 lines); before/after captured. (HS-46-02)
- A docs style guide exists and the standard page skeleton is applied across the
  user-facing guides; `docs/README.md` is a scannable journey-grouped map. (HS-46-03)
- Real UI screenshots of the actual app appear in the README + the key guides,
  captured by a repeatable script under `docs/assets/screenshots/`. (HS-46-04)
- A feature → doc matrix proves every shipped capability is documented + linked;
  no shipped feature is undiscoverable; nothing overstated. (HS-46-05)
- Doc-drift + dangling-link guards green; before/after; `final-summary.md`;
  phase CLOSED; PR to `main`. (HS-46-06)

## Invariants

- **Honest, not hype.** Cool facts must be *true* — pre-release status stays
  clear; no cloud-sync / always-on claims that contradict the local-first
  posture; "100% local" only where literally true (the LLM endpoint you point at
  is yours). Bold framing, accurate substance.
- **Graphics stay.** The pixellab art is an asset and is preserved; screenshots
  are additive.
- **Docs only.** No source/behavior changes; the suite is incidental (doc guards
  + link-check + a clean `npm run build` for any screenshot capture).
- **Grounded.** Every claim is checked against live code (the repo's standing
  doc-truth rule); the audit (HS-46-01) is the foundation the rest builds on.
- **Reproducible visuals.** Screenshots come from a committed capture script (no
  hand-pasted one-offs), so they can be refreshed when the UI changes.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-46-01 | Doc truth audit & drift fix | backlog | [story-01-doc-truth-audit.md](./story-01-doc-truth-audit.md) | — |
| HS-46-02 | The README, reimagined (the 10-second hook) | backlog | [story-02-readme-reimagined.md](./story-02-readme-reimagined.md) | — |
| HS-46-03 | Docs voice & structure system + elevated index | backlog | [story-03-voice-and-structure.md](./story-03-voice-and-structure.md) | — |
| HS-46-04 | Visual lift — real screenshots across the guides | backlog | [story-04-visual-lift.md](./story-04-visual-lift.md) | — |
| HS-46-05 | Coverage & discoverability (feature → doc matrix) | backlog | [story-05-coverage-discoverability.md](./story-05-coverage-discoverability.md) | — |
| HS-46-06 | Closeout — before/after + guards + PR | backlog | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

Phase scaffolded off `main` (post Phase-45 + the journal-UI fix, PRs #23/#24) on
branch `phase-46-documentation-lift`. Nothing written yet. **HS-46-01** (the
truth audit) is the foundation — you reimagine on top of an accurate picture, not
vibes. Sequence: 01 → (02, 03) → (04, 05) → 06.

## Active risks

- **Over-selling a pre-release.** Bold framing can drift into hype. Mitigation:
  the honesty invariant + the truth audit gate; keep the pre-release banner.
- **Screenshot staleness.** Hand-captured screenshots rot. Mitigation: a
  committed capture script (reuse the `scripts/screenshot_*.py` pattern) so
  visuals are reproducible.
- **Scope creep into a rewrite of everything.** 4,677 lines of docs. Mitigation:
  the truth pass is accuracy + voice + structure + visuals — not a line-by-line
  rewrite of reference material; deep rewrites are out unless a doc is actively
  misleading.
- **Doc↔feature drift recurring.** Mitigation: the feature → doc matrix
  (HS-46-05) + the existing doc-drift guard; consider extending the guard.

## Decisions made (this phase, from user)

- **README: bold reimagining** — lead with the wow / cool facts, cut hard for
  punch (~130–150 lines), keep every graphic, move depth (the plugin table, the
  AIPI prose, the config block) to linked docs.
- **Visuals: real UI screenshots** — add live product screenshots via the
  existing Playwright scripts; reuse the pixellab art as-is (no new generation).
- **Scope: README + a truth/voice pass on all docs** — comprehensive: fix drift,
  unify voice/structure, elevate the index across the whole user-facing set.

## Decisions deferred

- **Cool-facts home** — README hero highlights vs a dedicated `HIGHLIGHTS`/"Why
  HoldSpeak" doc vs both; settle in HS-46-02/05 (default: a README highlights
  strip + the index map; a dedicated doc only if it earns its place).
- **Reference-doc depth** — how far the voice/structure pass goes into the
  dev/reference docs (`PLUGIN_AUTHORING`, `CONNECTOR_DEVELOPMENT`,
  `DEVICE_PROTOCOL`); settle in HS-46-03 (default: accuracy + a consistent
  skeleton, not a rewrite).
