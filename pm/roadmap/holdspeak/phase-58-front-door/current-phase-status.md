# Phase 58 — The Front Door (positioning + the user-facing docs, revised)

**Status:** in-progress (5/6). Opened 2026-06-11 on user direction, right
after Phase 57 closed (PR #44): *"a proper phase. Where we also revise WHAT
we are saying, so that we can be explicit around how to 'sell' this product
to our community."* The user fixed the three positioning decisions directly:
**lead angle "one copilot, two modes"**, **audience: developers**,
**comparisons: name names, honestly**.

**Last updated:** 2026-06-11 (**HS-58-05 done: the voice guard.** Four
new tests over the user-facing corpus (prose only, code blocks exempt):
dashes-zero with a verbatim-UI-quote allowlist, the AI-vocab tells (tuned
live: the "not just" pattern was narrowed to the tic forms after flagging
two legitimate logical uses), the canonical-name bans, and a
both-ways seeded-violations proof. The Phase-51 vocab pattern widened to
single-digit phases (the live HS-9-03 find). DOCS_STYLE.md documents the
rules. Suite **2645 passed, 17 skipped** (+4).
**HS-58-04 (prior): the developer + ops
docs.** The extend-it corpus revised: contributor-pitch ledes on
PLUGIN_AUTHORING ("the highest-leverage way to make HoldSpeak yours…
mostly the prompt you wish your meetings produced") and
CONNECTOR_DEVELOPMENT ("teach it… without forking the runtime"); 101
prose dashes removed across six files (example code exempt per the
canon), every replacement hand-chosen; no contract/protocol/schema fact
altered. Locks green; suite 2641. **HS-58-03 (prior): the core guides.** All
eight user-flow guides revised against the canon: why-ledes (the
five-minute promise, the say-vs-meant gap, "a meeting should end with
decisions, not a recording"), canonical names in prose, 70 em/en dashes
removed with hand-chosen replacements (the one survivor is a verbatim UI
quote the canon exempts — a first-pass edit of it was caught by grepping
the real `journal.js` string and restored). Bonus find: an `HS-9-03`
vocab leak in the Firefox guide that Phase 51's two-digit pattern misses
(fixed; guard widening → HS-58-05). Locks green; suite 2641.
**HS-58-02 (prior): README.md, the front
door.** The hero IS the canon's one-liner; "The two modes" gives Dictate
and Meet equal billing and carries the post-48 surface the old README
missed (voice commands, pre-briefing, recording AND transcript import,
aftercare, facets); the pillars tightened to the canon's four; **the
comparison section the repo never had** (named tools, both directions,
date-stamped, closed by our own trade-offs); Qlippy as the delight beat
with the never-acts guarantee; Contributing now pitches building ON
HoldSpeak. docs/README.md hero aligned. Zero dashes, plugin-count lock
green, 238 lines. Full suite 2641 passed, 17 skipped.
**HS-58-01 (prior): the positioning canon.**
`docs/internal/POSITIONING.md` fixes the story on the user's three
decisions (recorded verbatim as non-relitigable): the one-copilot-two-modes
one-liner, four pillars each with shipped proof points, the named
competitive frame (OS dictation / local Whisper apps / AI dictation
services / Talon / raw tooling — both directions, as-of-dated,
architecture-level), the canonical feature-name table with banned
synonyms, and the voice rules (humanizer standard, no-dash, the honesty
bar, why-ledes, developer register). CLAUDE.md lists it as source canon,
binding every future phase. Doc slice green (the vocab guard correctly
does not scan internal docs); full suite 2641 passed, 17 skipped.
Earlier: scaffolded — the corpus measured: vocabulary
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
| HS-58-01 | The positioning canon | done | none |
| HS-58-02 | README.md, the front door | done | HS-58-01 |
| HS-58-03 | The core guides | done | HS-58-01 |
| HS-58-04 | The developer + ops docs | done | HS-58-01 |
| HS-58-05 | The guard | done | HS-58-02..04 |
| HS-58-06 | Closeout: fresh-eyes pass + final-summary + PR | backlog | HS-58-01..05 |

## Where we are

**HS-58-01 → HS-58-05 shipped 2026-06-11.** The story is told everywhere
and locked against decay. Next is **HS-58-06 — closeout**: the fresh-eyes
render pass, before/after metrics, final-summary, PR merged on green.
