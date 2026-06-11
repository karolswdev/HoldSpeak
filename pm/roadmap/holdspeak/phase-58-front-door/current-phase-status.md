# Phase 58 — The Front Door (positioning + the user-facing docs, revised)

**Status:** scaffolded (0/6). Opened 2026-06-11 on user direction, right
after Phase 57 closed (PR #44): *"a proper phase. Where we also revise WHAT
we are saying, so that we can be explicit around how to 'sell' this product
to our community."* The user fixed the three positioning decisions directly:
**lead angle "one copilot, two modes"**, **audience: developers**,
**comparisons: name names, honestly**.

**Last updated:** 2026-06-11 (scaffolded — the corpus measured: vocabulary
already clean (Phase 51 + per-phase humanizer passes), em-dashes pervasive
in pre-Phase-55 text (PLUGIN_AUTHORING 82, the typing guide 28, README 0),
no comparison section anywhere, the README's feature story stops around
Phase 48. The doc locks that pin content are mapped (plugin count, Qlippy
guarantees, links/images, vocab guard).)

## The thesis — why this phase

The docs grew feature by feature; each section is honest, but nobody ever
decided what HoldSpeak's story IS and told it consistently. The repo's
front door (README) under-sells the product it documents, there is no
honest comparison for the "why not X?" reader, and the older corpus
carries the strongest single AI tell (em-dash saturation) plus no voice
guard. One positioning canon + one full revision pass + one guard fixes
all of it, permanently.

## Goal

A positioning canon every user-facing doc aligns to; a README that pitches
"one copilot, two modes" to developers with honest named comparisons; every
guide re-framed (a why-lede, canonical feature names, the humanizer voice,
zero em/en dashes); a drift guard so none of it regresses. The pitch stays
as honest as the product.

## Scope

- **In:** `docs/internal/POSITIONING.md` + CLAUDE.md canon entry
  (HS-58-01); README.md + docs/README.md (HS-58-02); the core guides
  (HS-58-03); the developer/ops docs (HS-58-04); the dash/AI-vocab/
  canonical-name guard (HS-58-05); closeout (HS-58-06).
- **Out:** new product features; website/social assets beyond the repo;
  rewriting internal docs (docs/internal stays technical); changing any
  documented behavior or honest limit; video/demo production.

## Exit criteria (evidence required)

- The canon exists, is project canon (CLAUDE.md), encodes the user's three
  decisions, and every pillar carries shipped proof points; the canonical
  feature-name table is declared. (HS-58-01)
- README leads with both modes, carries the named honest comparison
  section (date-stamped, both directions), keeps the plugin-count lock +
  quickstart/platform/trust content, and lands ≈ today's length;
  docs/README.md aligned. (HS-58-02)
- Every core guide and every developer/ops doc: a why-lede, canonical
  names, humanizer-clean, zero em/en dashes in prose; doc locks green
  throughout; pinned phrases handled deliberately. (HS-58-03, HS-58-04)
- The guard locks dashes-zero + AI-vocab + canonical-name consistency
  over the user-facing corpus, proven both ways. (HS-58-05)
- Fresh-eyes render/link pass; before/after metrics; full suite green;
  `final-summary.md`; BACKLOG + README flips; PR merged on green.
  (HS-58-06)

## Invariants

- **The pitch is as honest as the product** — no claim a guide or test
  cannot back; comparisons state the other tool's strengths too.
- **Meaning preserved**: no documented fact, command, or honest limit is
  dropped.
- **Docs-and-test only**: zero behavior changes.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-58-01 | The positioning canon | backlog | none |
| HS-58-02 | README.md, the front door | backlog | HS-58-01 |
| HS-58-03 | The core guides | backlog | HS-58-01 |
| HS-58-04 | The developer + ops docs | backlog | HS-58-01 |
| HS-58-05 | The guard | backlog | HS-58-02..04 |
| HS-58-06 | Closeout: fresh-eyes pass + final-summary + PR | backlog | HS-58-01..05 |

## Where we are

Scaffolded. Next is **HS-58-01 — the positioning canon**: the keystone doc,
built strictly on the user's three decisions.
