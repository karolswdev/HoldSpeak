# HS-47-03 — Guided setup flow (fresh repo → working)

- **Project:** holdspeak
- **Phase:** 47
- **Status:** backlog
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
  - A **"you're set" confirmation** that shows the next step (enable the rewrite
    stage if they want context-based rewriting; try a dry-run) and links the dry-run.
  - Reuse the existing project-root detection + the KB/`.hs/` write primitives
    (`project_kb.py`, the project-doc-suggestion apply path) — no new write
    mechanism.
- **Out:** discovery/nudge (HS-47-04); explainer/empty-state visuals (HS-47-02);
  pipeline behavior. This story is the *create-it-without-editing-files* path.

## Acceptance criteria
- [ ] From a detected project with no project knowledge, the flow scaffolds a
      working starter (`.hs/` + `project.yaml` KB) entirely from the UI, with an
      explicit review/approve step before writing.
- [ ] After the flow, a dry-run shows project knowledge actually affecting output
      (a `{project.kb.*}` value stamped, or `.hs/` context shaping a rewrite).
- [ ] Proven by a **dogfood** (fresh temp project → guided flow → working dictation,
      zero hand-editing), provable without a mic.
- [ ] No silent writes; behavior-preserving; tests + `npm run build` green.

## Test plan
- Unit/integration: the scaffold writes the expected files; the apply path reuses
  the approved-write semantics; `uv run pytest -q -k "dictation or project"`.
- Dogfood: a script (mirroring `scripts/dogfood_*.py`) drives the flow end-to-end on
  a temp repo and asserts the resulting dry-run reflects the seeded knowledge.

## Notes / open questions
- Mirror the Phase-42/43 dogfood pattern (`scripts/dogfood_*.py`) for the proof.
- Decide whether the flow is a dedicated route/panel or an inline wizard within the
  surfaces — settle during build, favouring the lightest thing that hits the AC.
