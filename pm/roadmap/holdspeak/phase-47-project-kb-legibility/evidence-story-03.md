# Evidence — HS-47-03: Guided setup flow (fresh repo → working)

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-47-project-kb-legibility`.

## What shipped

A detected project with no knowledge can now go to working project-aware
dictation from the UI, with no file editing, and the headline user request landed:
a copiable prompt that has your own coding agent draft the `.hs/` context.

### The guided setup panel (Context surface)

`#hs-setup` (static markup, toggled by JS so its scoped CSS applies) is launched
from the Context empty state's new "Set up project knowledge" button. It has two
authoring paths plus a hand-off:

- **Use a starter set** (`#hs-setup-starter`): creates a small, well-formed `.hs/`
  set (`instructions.md`, `context.md`, `terms.md`) with fill-in prompts. A
  `holdspeakConfirm` dialog lists exactly which files will be written first (the
  explicit review/approve step); nothing is saved silently; the user edits each
  file afterward. Reuses the existing `PUT /api/dictation/project-hs` write path.
- **Draft with your coding agent** (`#hs-setup-copy-prompt`): the user-requested
  feature. A one-click-copy, repo-aware prompt (`buildAgentPrompt`) that names the
  detected repo + root, lists the `.hs/` files to author, gives a worked example,
  and asks the agent to report what it wrote so the user can review in the Context
  tab. Drafting happens on the user's own machine (their Claude/Codex); HoldSpeak
  never calls a model here.
- **"You're set" hand-off** (`youreSetHtml`): after creating facts or a context
  starter, a success line routes into the dry-run via a delegated
  `[data-section-jump]` link.

### The connective tissue: a fact-consuming starter block

Facts had nothing referencing them out of the box, so a dry-run could not show a
fact taking effect. Added an **additive** starter block template
`project_facts_context` (`_helpers.py`) whose template appends
`Project stack: {project.kb.stack}`. The placeholder stays unresolved (and the
injection is skipped) until the user fills in the `stack` fact, so it is safe by
default and behavior-preserving. This is what makes the guided flow demonstrably
"work."

### Facts side

The Facts empty state's "Use starter facts" already scaffolds
`.holdspeak/project.yaml`; its success message now routes to the dry-run and tells
the user to fill a value and add the `project_facts_context` block.

## Proof — the dogfood

`scripts/dogfood_project_knowledge.py` drives the same HTTP endpoints the browser
calls, against a fresh temp repo (only a `pyproject.toml`), with the test suite's
deterministic stub runtime standing in for the local model (no mic, no LLM):

```
1. detected project: ledgerline (anchor: pyproject.toml)
2. created starter facts -> .../ledgerline/.holdspeak/project.yaml
3. set fact   stack = 'Rails 7 + Postgres 16'
4. added block 'project_facts_context' (references {project.kb.stack})
5. scaffolded context -> .hs/ ['context.md', 'instructions.md', 'terms.md']
6. dry-run utterance: 'help me refactor the payments module'
   stages: ['intent-router', 'kb-enricher']
   final text: 'help me refactor the payments module\n\nProject stack: Rails 7 + Postgres 16'
PASS: the fact 'Rails 7 + Postgres 16' reached dictation output with zero file editing.
```

## Tests run

- New: `test_project_facts_context_starter_block_stamps_a_fact`
  (`test_web_dry_run_api.py`) is the CI regression behind the dogfood;
  `test_dictation_context_has_guided_setup_and_agent_prompt` and
  `test_agent_prompt_is_repo_aware_and_lists_the_hs_files`
  (`test_web_dictation_cockpit.py`) assert the panel + the repo-aware prompt.
- Targeted: `uv run pytest -q -k "dictation or doc_drift or link or dry_run or blocks_api"`
  → **403 passed, 5 skipped**.
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2370 passed, 17 skipped** (exit 0).
- Build: `(cd web && npm run build)` clean; bundle carries `hs-setup` +
  `buildAgentPrompt` + the panel markup; **0** `_built/` tracked.
- Screenshot-verified: the guided panel renders (header + Close, the two authoring
  cards, the agent prompt in a scrollable block) with the scoped CSS applied.

## Acceptance criteria

- [x] Scaffolds a working starter (`.hs/` + `project.yaml` KB) from the UI with an
      explicit review/approve step; no hand-editing.
- [x] A dry-run shows a `{project.kb.*}` value stamped (the `project_facts_context`
      block).
- [x] Proven by a dogfood, no mic.
- [x] A copiable, repo-aware "draft with your coding agent" prompt; generation
      stays local, review before it takes effect.
- [x] No silent writes; behavior-preserving; tests + build green; 0 `_built/`.
