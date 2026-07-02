# Phase 75 — Preview Before It Types: final summary

- **Closed:** 2026-07-02 — **5/5 stories**, open-to-close same day.
- **Branch:** `phase-75-preview-before-type` (merged to `main` by PR).
- **Why:** backlog candidate M (owner-sourced, parked since the post-P53
  review) — see the finished text before it types; the P60 wake grammar
  generalized to hold-key dictation.

## What shipped, in one paragraph

An opt-in mode (`dictation.preview_before_type`, Settings → Voice; off by
default with the off-path LOCKED byte-identical by test): a finished
dictation journals its pipeline pass and then ARMS instead of types — one
one-shot server-minted token, a `dictation_preview` broadcast, and a
shell-level card visible on EVERY route (the desk front door included;
the QueueHud idiom, keyboard-first, the P60 badge label as the only trust
copy). **Type it** commits through the normal typing path;
**Discard**/Escape burns; agent-reply sessions never preview (the
companion answer flow stays immediate); the first-dictation milestone
marks on delivery, not on arm. The routes carry `/api/dictation/wake/
type`'s security contract verbatim.

## Two real bugs the phase's own tests caught

1. **The loader dropped the knob** (`Config.load`'s explicit dictation
   constructor) — the toggle would save, echo `true`, and silently revert
   on every restart. Caught by the round-trip test, fixed in-commit.
2. The manifest guard fired on the card's new call sites (working as
   designed; regenerated).

## The closeout walk (HS-75-05)

Real mixin verbs behind the routes, a capturing typer, one browser
session on `/`: a REAL pipeline pass armed the card (nothing typed while
armed — asserted), Type it delivered the EXACT text to the typer, a
second pass discarded and delivered nothing, pathname stayed `/`. The
**mic-in-hand pass is the owner's real-metal leg**, recorded up front in
the scaffold.

## Numbers

Suite **3088 passed, 37 skipped** at close (+8 this phase); doc guards
85; two new routes on the manifest.
