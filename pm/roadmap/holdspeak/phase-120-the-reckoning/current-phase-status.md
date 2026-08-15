# Phase 120 — The Reckoning

**Status:** done (11/11).

**Last updated:** 2026-08-06.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call. This follows the standing Opus->Terra->Orchestrator
pipeline.

## What we're building

Phase 115 ("The Polish") swept 73 violations across ~30 surfaces. It
made the desk look born from one OS. But it swept breadth, not depth.
Phases 116-119 shipped ambitious new capability — the Workbench, the
Hopper, click-to-toggle mic, seed revision — and each left visual debt
in its wake. Meanwhile, older primitives (directories, chains,
decisions) shipped with placeholder shells that were never finished.

This phase is the reckoning. Four Opus scouts audited every surface in
the codebase. Terra verified the findings and caught what the scouts
missed. The result: two CRITICALs (surfaces that render as blank
voids), 19 BAD violations (broken visual language, stale labels, raw
emoji, inline-styled admin panels), and 15+ MINOR papercuts (dead CSS,
sub-pixel borders, orphaned classes). The owner triggered this audit
because the Workbench Agent surfaces are "abhorrently bad." They're
the lead story, but they're not alone.

Three pillars:

1. **Workbench reforge.** The workbench agent surfaces — dashboard
   cards, config strip, item cards, inlet composer, template picker —
   get the craft they deserve. Missing CSS rules, invisible status
   signals, dead legacy CSS, emoji where sprites belong.

2. **Finish what was started.** Directory pullouts that open to void,
   chain pullouts that show UUIDs, decision editors that use raw
   `<textarea>`, a constitutional context page that looks like a
   different app, mic labels that say "Hold to..." when the mic is
   click-to-toggle, a disabled DEFAULTS button that advertises
   unfinished work.

3. **One material language.** Presence page running pre-Signal
   material, session pullouts with emoji icons, recipe editors with
   native `<select>` controls, workbench canvas with hardcoded hex
   colors. Every surface converges on the Signal Workbench grammar:
   sprites, tokens, desk gadgets, beveled/etched depth.

## Why this phase exists

1. **The workbench gap.** The Workbench shipped functional but ugly.
   The inlet composer's CSS classes don't exist. Pending items have no
   visual presence. Priority P1 looks identical to P5. The dashboard's
   "needs attention" signal is an 8px dot. The template picker uses
   platform emoji. 97 lines of dead agent-rail CSS ship in production.
   The owner saw it and said "absolutely abhorrently incredibly bad."
   (Article VIII — native-grade craft.)

2. **The void gap.** Opening a Directory shows nothing — no name, no
   members, no empty state. Opening an unknown primitive kind shows
   nothing — no feedback, no explanation. These are CRITICALs: the
   user clicks a real object and gets a blank window.
   (Article VI — honest by construction.)

3. **The label gap.** Five+ components still say "Hold to speak" /
   "Hold to fill" / "Hold to answer" when Phase 119 shipped
   click-to-toggle. The labels teach users the wrong interaction.
   (Article IV — voice as input.)

4. **The material gap.** The Presence page is a circular orb with a
   glow halo on a rounded card — pre-Signal material. The workbench
   canvas uses hardcoded `#0b0c10`. Session pullouts render `🙋`/`🤖`.
   The constitutional context core is built entirely with inline
   `style={{}}`. These surfaces belong to different apps than the desk.
   (Article VIII — native-grade craft; Article II — one primitive
   contract.)

## Method

- Workbench first. The owner's trigger was the workbench surface.
  Story 01 ships first so the owner sees the thing they hated improve
  before anything else.
- Dead ends fixed early. Stories 02-03 fix the blank shells (directory,
  fallback, chain, repo issues, defaults button). These are actual
  broken paths, not polish.
- Labels swept atomically. Story 04 is a repository-wide sweep of mic
  labels — every component, one story, no stragglers.
- Material convergence batched by concern. Stories 05-09 each target a
  specific class of violation (admin panels, editors, emoji, chrome,
  runtime faces) so fixes compose cleanly.
- The walk proves everything together. (Article IX — proof over claim.)

## Dependency graph

```
01 workbench reforge ──┐
02 open objects      ──┤
03 chains readable   ──┤
04 mic labels        ──┤
05 constitutional    ──┤
06 editors material  ──┤
07 sprite law        ──┤
08 no dead ends      ──┤
09 chrome repair     ──┤
10 runtime faces     ──┤
                       └──→ 11 the walk
```

## Stories

### The trigger

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | Workbench agents reforged | Why do the workbench surfaces look unfinished? | done |

### The voids

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 02 | Open objects must speak | Why does opening a directory show nothing? | done |
| 03 | Chains are readable | Why do chain steps show UUIDs instead of names? | done |

### The labels

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 04 | Browser mic means toggle | Why do labels still say "Hold to..." when mic is click-to-toggle? | done |

### The material

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 05 | Constitutional context joins the desk | Why does the context editor look like a different app? | done |
| 06 | Editors share one material | Why do some editors use raw `<textarea>` while others use DeskEditor? | done |
| 07 | Sprite law, no emoji | Why do some surfaces use platform emoji instead of sprites? | done |

### The chrome

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 08 | No dead ends | Why does the Repo Issues tab say "pending" and the DEFAULTS button stay disabled? | done |
| 09 | Window chrome repair | Why are footer classes orphaned and the close button a naked "x"? | done |

### The convergence

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 10 | Runtime faces match the desk | Why does the Presence page look pre-Signal and the canvas bypass tokens? | done |

### The proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 11 | The walk | Does every surface feel like one OS? | done |

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-120-01 | Workbench agents reforged | done | [story-01](story-01-workbench-agents-reforged.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-120-02 | Open objects must speak | done | [story-02](story-02-open-objects-must-speak.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-120-03 | Chains are readable | done | [story-03](story-03-chains-are-readable.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-120-04 | Browser mic means toggle | done | [story-04](story-04-browser-mic-means-toggle.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-120-05 | Constitutional context joins the desk | done | [story-05](story-05-constitutional-context-joins-the-desk.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-120-06 | Editors share one material | done | [story-06](story-06-editors-share-one-material.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-120-07 | Sprite law, no emoji | done | [story-07](story-07-sprite-law-no-emoji.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-120-08 | No dead ends | done | [story-08](story-08-no-dead-ends.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-120-09 | Window chrome repair | done | [story-09](story-09-window-chrome-repair.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-120-10 | Runtime faces match the desk | done | [story-10](story-10-runtime-faces-match-the-desk.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-120-11 | The walk | done | [story-11](story-11-the-walk.md) | [evidence-story-11](./evidence-story-11.md) |

## Where we are

All 11 stories done. Four Opus scouts audited, Terra verified,
ten Terra builders implemented, ten Opus verifiers confirmed — all
passed on first attempt. Owner walked it. ~30 files modified, 1
deleted, 1 created. Zero regressions (typecheck green on every story).
