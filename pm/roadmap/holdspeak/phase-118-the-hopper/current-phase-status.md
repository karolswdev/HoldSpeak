# Phase 118 — The Hopper

**Status:** in-progress (9/10). (Record corrected 2026-08-15 by HS-132-13:
the header said backlog (0/10) while the story table and the shipping
commits — 6522739b wave one 6/10, ab3acb44 wave two 8/10, 28cda81a story 05
9/10, all on main — show nine stories done. HS-118-10, the walk, remains
open and is a standing owner-sitting IOU.)

**Last updated:** 2026-08-05 (chartered, revised after Terra review).

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call. This follows the standing Opus→Terra→Orchestrator
pipeline.

## What we're building

The Workbench shipped in Phase 116 as a complete agent workspace —
conductor, memory, skills, constitutional context, templates, voice,
drop-to-work. It works. But it asks the user to fill in a form
before work can begin: pick an agent, type a title, set a priority,
attach grounding through a selector. That is too much ceremony for a
surface whose job is to eat mess and produce order.

This phase turns the Workbench from a workspace you configure into a
**hopper** you throw things at. The hopper has a mouth — the
**inlet** — that accepts anything: dropped desk objects, typed
instructions with `@`-referenced drawers, or spoken intent with
drawer names resolved from speech. Every path converges on the same
item shape: **grounding** (what to work on) + **instruction** (what
to do with it). The hopper digests items and produces desk-ready
primitives — not text blobs.

The three input paths:

1. **Drop + speak/type.** Drag a meeting, note, or zone onto the
   inlet. Grounding chips appear. Speak or type what you want done.
   Submit.
2. **Composer with @-references.** Type
   `summarize @Monday standup and compare with @last week's retro` —
   drawer names resolve to zone-grounded qualified refs via inline
   autocomplete.
3. **Voice-only.** Speak naturally into the inlet. Two-tier
   resolution: exact zone names resolve instantly (client-side
   substring match); paraphrased or contextual references resolve
   via a small local LLM configured as the workbench's resolver
   profile. Both tiers run concurrently. The model returns zone
   IDs validated against the catalog — hallucinations are dropped.
   Resolved refs appear as removable chips; the user confirms by
   submitting.

The output side evolves too: results mint as artifacts in a
`pending-review` state with full provenance. The owner triages each
output — accept, reject, or rework — before it becomes a real desk
object. The workbench proposes; the owner approves.

Two system-level foundations ship alongside the hopper:

- **Sprite states.** Every DeskPrimitive gains a state field and a
  sprite-state registry. The desk renderer looks up the active
  sprite variant by `(kind, state)`. This is not a workbench
  feature — it's an OS feature. A recording meeting, a processing
  workbench, a draft artifact all show different sprites. The
  backbone ships here; assets follow in a later phase.
- **Browser mic pipeline.** The browser mic (MicButton → Whisper)
  feeds the full dictation pipeline — corrections, learning loop,
  intent routing — not just raw transcription. The source differs;
  the pipeline doesn't.

## Why this phase exists

1. **The inlet gap.** The current composer is a form (title + body +
   priority + grounding selector). Forms are ceremony. The hopper
   needs a mouth that accepts anything in one gesture.

2. **The reference gap.** There is no way to name a desk object in
   text — no `@`-mention, no inline reference anywhere in the
   codebase. Grounding is attached through a panel, not through
   language.

3. **The voice resolution gap.** Voice grammars handle workbench
   commands (add-item, run, clear-done) but cannot resolve references
   to desk objects. Exact substring matching handles verbatim zone
   names, but natural speech paraphrases — "the research stuff" for
   a zone called "Research Notes" — can't be matched by a scanner.

4. **The hydration gap.** The conductor drops qualified refs from
   grounding — `_hydrate_item_grounding()` only reads `meeting_ids`
   and `artifact_ids`. The `refs` field is silently ignored. Zone
   refs that arrive via `@`-mention or voice resolution would vanish
   before the agent ever sees them.

5. **The output gap.** Results are plain strings. "Keep" is manual,
   per-item, loses egress provenance, and doesn't link back to the
   source item. No consent gate stands between auto-minted output
   and the desk. The workbench produces answers but not desk objects.

6. **The uniqueness gap.** Zone names aren't unique. Two zones can
   share a name. Voice resolution by name is impossible when the
   address is ambiguous.

7. **The sprite gap.** Desk primitives have one static sprite. The
   desk can't communicate state at a glance — a recording meeting
   looks identical to an idle one.

8. **The pipeline gap.** The browser mic returns raw Whisper
   transcription. The desktop hotkey mic returns corrected,
   pipeline-processed text. Same user, two quality tiers, depending
   on which mic they clicked.

## Method

- Every input path produces the same item shape: grounding refs +
  instruction body. No path is special-cased. (Article II — the
  DeskPrimitive contract.)
- Zone names are globally unique addresses. Ambiguity is a system
  error, not a user choice. DB-enforced, not application-checked.
  (Article VI — honest by construction.)
- Every text input can be spoken into. The browser mic is a
  first-class input source feeding the full dictation pipeline.
  Visible single-mic authority — only one mic owns the floor.
  (Article IV — voice as input.)
- Dropped objects become grounding chips, not items. The user states
  intent before work is created. The workbench never guesses intent.
  (Article VI — honest, not flattering.)
- Minted artifacts enter `pending-review`. The owner triages each
  output — accept, reject, or rework — before it becomes a desk
  object. Propose → approve → execute. (Article V — consent is the
  spine.)
- Every auto-mint is a consequential operation admitted through the
  kernel. The run receipt stamps the mint, the egress boundary, and
  the grounding lineage. (Article XI — kernel admission;
  Article III — honest egress.)
- Sprite states are a primitive-level contract. Every kind declares
  its state vocabulary; the renderer maps `(kind, state)` to a
  sprite variant. (Article II — DeskPrimitive contract;
  Article VIII — native-grade craft.)
- The walk proves on the real hub with real mic, real model, real
  viewport. Screenshots for static state, video/trace for animated
  transitions. (Article IX — honest proof.)
- The inlet replaces the composer. No coexistence, no toggle, no
  "advanced" mode. (Article VII — no prose, no chrome.)

## Dependency graph

```
01 uniqueness ──┐
02 hydration  ──┼──→ 04 @-refs ──→ 05 voice-drawer
03 inlet ───────┘

06 output minting ──→ 09 artifact triage

07 sprite states     (independent foundation)
08 browser mic       (independent foundation)

10 walk              (all)
```

## Stories

### The plumbing

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | Zone name uniqueness | How does voice know which drawer you mean? | backlog |
| 02 | Conductor ref hydration | Why do zone refs vanish before the agent sees them? | backlog |

### The inlet

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 03 | The inlet | How does work arrive at the hopper? | backlog |
| 04 | @-reference tokenizer | How does typed text name a desk object? | backlog |
| 05 | Voice drawer resolution | How does spoken text name a desk object — even by paraphrase? | backlog |

### The output

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 06 | Output minting | How do results become desk objects? | backlog |
| 09 | Artifact triage | How does the owner accept, reject, or rework output? | backlog |

### The foundations

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 07 | Sprite states | How does the desk show primitive state at a glance? | backlog |
| 08 | Browser mic pipeline | Why should the browser mic be second-class? | backlog |

### The proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 10 | The walk | Does every surface hold up on the real device? | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-118-01 | Zone name uniqueness | done | [story-01](story-01-zone-name-uniqueness.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-118-02 | Conductor ref hydration | done | [story-02](story-02-conductor-ref-hydration.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-118-03 | The inlet | done | [story-03](story-03-the-inlet.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-118-04 | @-reference tokenizer | done | [story-04](story-04-at-reference-tokenizer.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-118-05 | Voice drawer resolution | done | [story-05](story-05-voice-drawer-resolution.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-118-06 | Output minting | done | [story-06](story-06-output-minting.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-118-07 | Sprite states | done | [story-07](story-07-sprite-states.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-118-08 | Browser mic pipeline | done | [story-08](story-08-browser-mic-pipeline.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-118-09 | Artifact triage | done | [story-09](story-09-artifact-triage.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-118-10 | The walk | backlog | [story-10](story-10-the-walk.md) | -- |

## Where we are

Chartered. Revised after Terra review: constitutional grounding
corrected (Articles IV, V, IX, XI added), zone uniqueness made
DB-enforced, voice matching tightened to word-boundary, auto-minting
gated by consent (pending-review + triage), sprite states elevated
to system primitive, browser mic elevated to full pipeline. No work
started.
