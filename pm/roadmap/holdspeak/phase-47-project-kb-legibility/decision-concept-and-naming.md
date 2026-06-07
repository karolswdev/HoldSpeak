# HS-47-01 decision — the project-knowledge model and its names

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Status:** decided. This is the model every other Phase-47 surface presents.

## The decision in one line

HoldSpeak's "teach the copilot about this project" capability is named
**Project knowledge**, and it has two parts: **Facts** (the deterministic KB)
and **Context** (the optional rewrite guidance). On-disk file names and config
keys do not change.

## The model

**Project knowledge** is the umbrella: what HoldSpeak knows about the project you
are dictating into. It is made of two parts that do different jobs.

**Facts** (was "Project KB").
- What it is: a set of key/value entries you maintain.
- What it does: the default `kb-enricher` stage stamps each value into a block
  template verbatim wherever a `{project.kb.<key>}` placeholder appears.
- The promise: exact, deterministic, no model involved. A fact comes out byte
  for byte the way you wrote it.
- On disk: the `kb:` map in `<repo>/.holdspeak/project.yaml`.
- Default path: yes. `kb-enricher` is in the default dictation pipeline.

**Context** (stays "Project Context").
- What it is: short Markdown notes about the project (instructions, background,
  workflows, targets, ignore rules).
- What it does: the optional `project-rewriter` stage reads them so the rewrite
  model phrases things the way this project expects.
- The promise: guidance, not substitution. It shapes a rewrite; it is not copied
  in verbatim and it only runs when you turn the rewrite stage on.
- On disk: the `.hs/` Markdown folder in the repo.
- Default path: no. The rewrite stage is opt-in.

The one-sentence relationship, used consistently across UI and docs:

> Facts are exact values stamped into your dictation. Context is background the
> rewrite model reads. Facts need no model; Context uses the optional rewrite
> stage.

## Why these names

"Project KB" was the problem. "KB" is jargon, and "knowledge base" collides head
on with the umbrella idea of project knowledge: the half was wearing the name of
the whole. That is exactly why the Phase-46 docs pass mistook the KB for the
`.hs/` files. Renaming the half to **Facts** frees **Project knowledge** to mean
the whole, and "Facts vs Context" carries the actual distinction a user needs:
exact values versus background guidance.

"Project Context" already described the `.hs/` files accurately and was never the
source of the confusion, so it stays. Changing only the one jargon label keeps
churn low while fixing the real legibility break.

## On-disk decision: keep everything

`.holdspeak/project.yaml` (the `kb:` map), the `.hs/` folder, the config keys,
the stage names (`kb-enricher`, `project-rewriter`), and every `{project.kb.*}`
placeholder stay exactly as they are. This is a presentation change. A rename on
disk would force a migration, break existing repos and placeholders, and buy
nothing the framing does not already buy. The placeholder syntax stays
`{project.kb.<key>}` because that is the contract block authors already write
against; the UI simply explains that those are your "facts."

## What this story changes

Labels and copy only, no behavior:
- The `/dictation` tab "Project KB" becomes "Project Facts".
- Both tab headers and ledes are rewritten to name the umbrella and state the
  relationship, so the two tabs read as one capability with two parts.
- The readiness card and a few JS-rendered strings that said "Project KB" now say
  "Project Facts".
- The `DOCS_STYLE.md` glossary entry records the umbrella plus both labels so UI
  and docs stay in lockstep.

The explainer panels, teaching empty states, guided setup, and discovery nudge
are later stories (HS-47-02 onward). This story settles the model and applies the
names.
