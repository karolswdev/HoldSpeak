# Phase 47 — Project Knowledge: Legible & Inviting — Final Summary

**Status:** CLOSED (6/6). Opened and closed 2026-06-07.
**Branch:** `phase-47-project-kb-legibility`. **PR:** to `main`, merged on green CI.

## Why this phase

While reviewing the Phase-46 docs, the user said: *"I struggle to understand the
'project KB' ... and I feel like many users will also struggle. It's not only
about documentation, but also the UI/UX, and the way to present it."* The Phase-46
docs pass had itself gotten the concept wrong (it defined "project KB" as the
`.hs/` files). HoldSpeak had a genuinely useful "teach the copilot about this
project" capability hidden behind jargon, a confusing two-tab split, bare editors,
and zero discovery. This phase made it **legible**, **inviting**, and
**discoverable**, without changing pipeline behavior.

## What shipped

- **HS-47-01 — The model.** Settled one mental model and recorded it
  (`decision-concept-and-naming.md`): **project knowledge = Facts (the
  `project.yaml` `kb:` map, stamped in verbatim by `kb-enricher`, no LLM) +
  Context (the `.hs/` files, read by the optional `project-rewriter`)**. Renamed
  the jargon half: the `/dictation` "Project KB" tab is now **"Project Facts"**;
  "Project Context" kept. On-disk names, config keys, and `{project.kb.*}`
  placeholders unchanged. Glossary updated.
- **HS-47-02 — Teach on the surface.** Each surface gained a what/why/worked-example
  explainer (Facts shows a `{project.kb.stack}` substitution; Context shows a
  rewrite being shaped) and an inviting empty state with a one-click starter.
  Static markup toggled by JS to keep scoped CSS; screenshot-verified; focus-safe.
- **HS-47-03 — Guided setup.** A guided panel on the Context surface takes a fresh
  repo to working dictation with no file editing: a confirm-gated `.hs/` starter
  set and the user-requested **copiable, repo-aware "draft my `.hs/` with your
  coding agent" prompt** (Claude/Codex draft on your machine; you review in the
  tab). A new additive `project_facts_context` starter block consumes a fact so it
  is demonstrable; `scripts/dogfood_project_knowledge.py` proves it end to end.
- **HS-47-04 — Discovery.** An ambient, dismissible, focus-safe `#kn-nudge` bar
  above the tabs shows only when a detected project has no knowledge and routes
  into the guided flow. Durable per-project + global dismissal (localStorage);
  readiness gained an additive `project_context` existence signal (no new
  detection path).
- **HS-47-05 — Docs.** The Intelligent Typing guide now documents both halves
  correctly ("§5. Set Up Project Knowledge", with the previously-undocumented facts
  mechanism and a worked example); the index, `DICTATION_COPILOT.md`,
  `USER_GUIDE.md`, and the `dictation-runtime` web doc reconciled (the last also
  wrongly called KB enrichment an LLM step; fixed).
- **HS-47-06 — Closeout.** Before/after screenshots, a repeatable screenshot
  script, a green dogfood, this summary, and the PR.

## The user's idea, folded in

Mid-phase the user asked for a copiable prompt that has the user's own coding agent
generate good `.hs/` files. It was recorded as a decision and built as a
first-class path in HS-47-03 (`buildAgentPrompt`): repo-aware, one-click copy,
lists the files to author with a worked example, drafting stays local, review
happens in the tab before it takes effect.

## Invariants held

- **Behavior-preserving.** The `kb-enricher` substitution and `project-rewriter`
  rewrite are unchanged; the only pipeline addition is one optional, safe-by-default
  starter block. Pipeline tests green throughout.
- **Local-first & focus-safe.** Every new surface is local; the nudge is
  dismissible and never steals focus (the dictation bundle keeps zero `.focus()`).
- **Honest.** Facts vs context are described accurately everywhere; "no LLM" /
  "optional LLM stage" stated where true.
- **No file churn.** On-disk names and config keys unchanged.

## Verification

- Full suite: **2372 passed, 17 skipped** (`--ignore=tests/e2e/test_metal.py`).
- Dogfood: `scripts/dogfood_project_knowledge.py` → PASS (a fact reaches output,
  zero hand-editing, no mic).
- Doc guards 8/8; `npm run build` clean; **0** `_built/` tracked across all six
  commits.
- New tests: the guided-flow substitution regression, the explainer + empty-state
  markers, the repo-aware prompt, the discovery nudge + its readiness signal.

## Per-story evidence

| Story | Evidence |
|---|---|
| HS-47-01 | [evidence-story-01.md](./evidence-story-01.md) |
| HS-47-02 | [evidence-story-02.md](./evidence-story-02.md) |
| HS-47-03 | [evidence-story-03.md](./evidence-story-03.md) |
| HS-47-04 | [evidence-story-04.md](./evidence-story-04.md) |
| HS-47-05 | [evidence-story-05.md](./evidence-story-05.md) |
| HS-47-06 | [evidence-story-06.md](./evidence-story-06.md) |
