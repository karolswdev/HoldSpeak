# HS-47-03 — Guided setup flow (fresh repo → working)

- **Project:** holdspeak
- **Phase:** 47
- **Status:** done
- **Depends on:** HS-47-01, HS-47-02
- **Unblocks:** HS-47-06
- **Owner:** unassigned

## Problem
Setting up project knowledge today means knowing to create `.hs/*.md` files by
hand and/or a `kb:` map in `.holdspeak/project.yaml` by hand — exactly the
"frig around with files" friction the cockpit phases removed elsewhere. There is
no guided path from a detected project to working project-aware dictation.

## Scope
- **In:**
  - A **guided setup flow** launched from the surfaces (and/or the empty state): for
    the detected project root, scaffold sensible defaults — a starter `.hs/`
    (instructions/context/workflows/targets/ignore) **and** a starter `project.yaml`
    `kb:` map — with the user reviewing/editing inline before it's written
    (respecting the "never writes without approval" invariant).
  - A **"draft with your coding agent" on-ramp** (user direction, 2026-06-07):
    a copiable, ready-to-paste prompt that asks the user's existing agent (Claude
    Code / Codex) to generate good starter `.hs/` context files for *this* repo,
    following HoldSpeak's conventions and common use cases (instructions, project
    background, workflows, target preferences, ignore rules), with a worked
    example baked in so the output is usable, not generic. One-click copy. The
    agent does the drafting on the user's own machine (no HoldSpeak LLM
    dependency, stays local), and anything written back into `.hs/` still goes
    through the approval-gated apply path. This hand-holds users who do not know
    what good context looks like; pair it with the "scaffold the defaults" path
    above so a user can either start from a template or have their agent author a
    tailored set.
  - A **"you're set" confirmation** that shows the next step (enable the rewrite
    stage if they want context-based rewriting; try a dry-run) and links the dry-run.
  - Reuse the existing project-root detection + the KB/`.hs/` write primitives
    (`project_kb.py`, the project-doc-suggestion apply path) — no new write
    mechanism.
- **Out:** discovery/nudge (HS-47-04); explainer/empty-state visuals (HS-47-02);
  pipeline behavior. This story is the *create-it-without-editing-files* path.

## Acceptance criteria
- [x] From a detected project with no project knowledge, the flow scaffolds a
      working starter (`.hs/` + `project.yaml` KB) entirely from the UI: Facts via
      "Use starter facts"; Context via the guided panel's "Create a starter set"
      (a confirm preview lists the files = explicit review/approve, then the user
      can edit each before/after). No hand-editing of files.
- [x] After the flow, a dry-run shows project knowledge affecting output: the new
      `project_facts_context` starter block stamps the `{project.kb.stack}` fact
      into the final text (proven by the dogfood + a CI regression test).
- [x] Proven by a **dogfood** (`scripts/dogfood_project_knowledge.py`): fresh temp
      project → facts + block + context via the same HTTP endpoints the UI calls →
      dry-run stamps the fact. No mic; the local model is stood in by the test
      suite's deterministic stub runtime.
- [x] The Context surface offers a copiable, repo-aware "draft with your coding
      agent" prompt (one-click copy); the prompt names this repo, lists the `.hs/`
      files to write, and carries a worked example. Generation stays on the user's
      machine; review happens in the Context tab before it takes effect.
- [x] No silent writes (the starter set is confirm-gated; the agent path is the
      user's own agent); behavior-preserving (the starter block is additive);
      tests + `npm run build` green; 0 `_built/` tracked.

## Test plan
- Unit/integration: the scaffold writes the expected files; the apply path reuses
  the approved-write semantics; `uv run pytest -q -k "dictation or project"`.
- Dogfood: a script (mirroring `scripts/dogfood_*.py`) drives the flow end-to-end on
  a temp repo and asserts the resulting dry-run reflects the seeded knowledge.

## Notes / open questions
- Mirror the Phase-42/43 dogfood pattern (`scripts/dogfood_*.py`) for the proof.
- Decide whether the flow is a dedicated route/panel or an inline wizard within the
  surfaces — settle during build, favouring the lightest thing that hits the AC.
