# Evidence — HS-47-01: Concept & naming reconciliation

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-47-project-kb-legibility`.

## What shipped

The settled model that every other Phase-47 surface presents, plus the label and
copy changes that apply it. No pipeline behavior changed.

### The decision

`decision-concept-and-naming.md` records the canonical model and the rationale:

- **Project knowledge** is the umbrella: what HoldSpeak knows about the repo you
  dictate into. It has two parts.
- **Facts** (was "Project KB"): the `kb:` map in `.holdspeak/project.yaml`. The
  default `kb-enricher` stage stamps each value into a block template verbatim via
  `{project.kb.<key>}` placeholders. Deterministic, no LLM, on the default path.
- **Context** (stays "Project Context"): the `.hs/` Markdown folder, read by the
  optional `project-rewriter` LLM stage. Guidance for a rewrite, opt-in.
- **On-disk: keep everything.** File names, config keys, stage names, and the
  `{project.kb.*}` placeholder syntax are unchanged. A rename would force a
  migration and break existing repos and placeholders for no gain the framing does
  not already deliver. This is a presentation change.

Why "Facts": "KB" / "knowledge base" was the jargon, and it collided with the
umbrella idea (the half wore the whole's name), which is exactly how the Phase-46
docs pass mistook the KB for the `.hs/` files. Renaming the half to "Facts" frees
"Project knowledge" to mean the whole, and "Facts vs Context" carries the real
distinction: exact values versus background guidance.

### Applied changes (labels + copy only)

`web/src/pages/dictation.astro`:
- Tab `section-kb` label: "Project KB" → **"Project Facts"** (id + `data-section`
  unchanged, so JS and tests that key off `kb` are untouched).
- `view-kb` header "Project knowledge base" → "Project facts"; lede rewritten to
  name the umbrella, state the no-LLM verbatim-stamp promise, and keep the
  placeholder + `project.yaml` reference.
- `view-kb` panel header "Knowledge-base entries" → "Fact entries".
- `view-hs` lede rewritten to state it is the other half of project knowledge and
  how it differs from Facts (guidance the rewrite model reads, opt-in stage).
- Readiness lede: "project KB" → "project facts".

`web/src/scripts/dictation-app.js` (runtime-rendered strings):
- Readiness card label "Project KB" → "Project Facts".
- Button "Create starter KB" → "Create starter facts".
- Toast "Created starter Project KB." → "Created starter project facts."
- Delete-confirm body/scope copy de-jargoned ("knowledge base file" → "project
  facts file").
- Code identifiers (`loadKB`, `createStarterKB`, the `kb` section id, comments)
  left as-is by design: on-disk/internal names do not change.

`docs/internal/DOCS_STYLE.md`: the glossary entry now records the "Project
knowledge" umbrella plus both UI labels, states facts-vs-context, and pins the
unchanged on-disk names so UI and docs stay in lockstep.

### Deferred docs page

`web/src/pages/docs/dictation-runtime.astro` still says "Project KB enrichment".
That is a docs page, owned by HS-47-05 (docs alignment), so it is intentionally
left for that story rather than touched here.

## Tests run

- Targeted (story test plan): `uv run pytest -q -k "dictation or doc_drift or link"`
  → **367 passed, 5 skipped** (the page-content assertions updated to "Project
  Facts" / "Project Context" pass against the freshly built bundle).
- Build: `(cd web && npm run build)` → 12 pages built, clean. The new label is
  present in `holdspeak/static/_built/`; **0** `_built/` files tracked by git.
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2365 passed, 17 skipped** (exit 0). Pipeline tests green; behavior
  preserved.

## Acceptance criteria

- [x] A recorded decision states the canonical model, the names, and the
      on-disk-rename call (with rationale) — `decision-concept-and-naming.md`.
- [x] The `/dictation` labels/headers/ledes reflect the settled model; the two
      tabs read as one capability with a stated relationship.
- [x] UI labels and the `DOCS_STYLE.md` glossary agree; no surface implies the KB
      does what context does or vice-versa.
- [x] Behavior unchanged (labels/copy only); page-content + pipeline tests green.
