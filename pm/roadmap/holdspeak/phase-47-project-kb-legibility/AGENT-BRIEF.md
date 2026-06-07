# Phase 47 — Agent Brief (read this first)

You are picking up **Phase 47 — Project Knowledge: Legible & Inviting** for
HoldSpeak. This brief is self-contained: the mission, the exact code seams
(already mapped against the live tree), the rules of the road, and a per-story
definition of success. Read it, then read
[`current-phase-status.md`](./current-phase-status.md) and the story file you're
working. If this brief disagrees with the live status docs or the codebase, the
**codebase wins** — re-verify before trusting any line or number below.

---

## 0. Mission

HoldSpeak can teach the copilot about a project, and it's a genuinely useful
feature. Right now it's hidden behind jargon and a confusing split, so users
(including an attentive agent during the Phase-46 docs pass) cannot tell what it
is. Make it **legible** (a user gets it in seconds) and **inviting** (a user can
set one up from the UI without reading a guide or hand-editing files).

This is a **UX + onboarding** phase. It does **not** change pipeline behavior:
the `kb-enricher` substitution and the `project-rewriter` rewrite stay exactly as
they are. You are changing names, framing, explainers, empty states, a guided
flow, and discovery, not what the stages do.

---

## 1. The one thing you must not get wrong

"Project KB" is **overloaded**. There are two different mechanisms, and the docs
already conflated them once. Keep them straight:

- **Project KB** = the `kb:` key-value map in `<repo>/.holdspeak/project.yaml`.
  Its keys become `{project.kb.<key>}` placeholders that the **default
  `kb-enricher`** stage substitutes into a matched block's template. Deterministic,
  no LLM. UI tab: **"Project KB"** (`section-kb` in `/dictation`).
- **Project context** = the separate **`.hs/` Markdown folder**
  (`instructions` / `context` / `workflows` / `targets` / `ignore`), read by the
  **optional `project-rewriter`** LLM stage. UI tab: **"Project Context"**
  (`section-hs`).

Never write or imply that the KB is the `.hs/` files, or that `kb-enricher` reads
`.hs/`. (`DICTATION_COPILOT.md` has this right; the Intelligent Typing guide
historically did not.)

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md` §"Contract template"); `mkdir -p .tmp` first, the
  pre-commit hook validates and deletes it. A story flipping to `done` **must**
  ship its `evidence-story-{n}.md` in the same commit; **one** done-flip per
  commit. The phase-exit story needs `evidence-story-06.md` **and**
  `final-summary.md` in the same commit. The story Status line must be the
  list-item form `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates: the story header status,
  the phase `current-phase-status.md` (row + Last-updated + "Where we are"), the
  project `README.md` (phase row + Current-phase + Last-updated), and any canon
  doc the story touched.
- **One PR per phase, merged when CI green.** Work on a phase branch
  (`phase-47-project-kb-legibility` or `phase-47/hs-47-01-...`); at close, push +
  open a PR to `main` + merge with a merge commit when all four CI suites pass
  (Unit · Integration macOS · E2E macOS · Linux Smoke). Memory
  `feedback_merge_phases_via_pr`.
- **Tests actually run.** Flip a story to `done` only after running the relevant
  tests and reading the output. Full suite:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` (the metal file hangs
  without a mic). Type-check is not validation.
- **Behavior-preserving.** Off-by-default features stay byte-identical; the
  pipeline stages are untouched; pipeline tests stay green.
- **Write like a human.** The user is allergic to AI-flavored prose. In any doc
  or UI copy you add: **no em or en dashes**, no emoji-decorated bullets, no
  rule-of-three padding, no "not X but Y". Plain, varied, direct. (The
  `humanizer` skill is available; `docs/internal/DOCS_STYLE.md` is the voice
  authority and carries the project-KB glossary entry.)

---

## 3. The ground truth (code seams, already mapped)

UI (Astro; source in `web/src`, built bundle is **gitignored** under
`holdspeak/static/_built/` — run `(cd web && npm run build)`, Node ≥ 22.12, after
any `web/src` edit; page-content tests read the built JS):

- `web/src/pages/dictation.astro` — the tabbed cockpit. The two surfaces:
  - **Project KB** tab: button `section-kb` (line ~41); `<section id="view-kb">`
    (~430). Edits the `kb` mapping in `.holdspeak/project.yaml`; has a
    `kb-btn-starter` "Use starter" + `kb-btn-add` "New entry" + a `kb-rows` grid.
  - **Project Context** tab: button `section-hs` (line ~42); `<section id="view-hs">`
    (~457). Edits the repo-local `.hs/` files; has a suggestion panel +
    `hs-suggestion-path`.
- Client logic: `web/src/scripts/dictation-app.js` (the runtime DOM is rendered
  by JS — heed the scoped-CSS trap in §5).

Backend:

- `holdspeak/plugins/dictation/builtin/kb_enricher.py` — the default stage; pure
  `{project.kb.*}` template substitution, never the LLM. (`_PLACEHOLDER_RE`,
  `_lookup` dotted-name traversal.)
- `holdspeak/plugins/dictation/project_kb.py` — read / write / validate the
  `.holdspeak/project.yaml` `kb:` map (atomic-write; `KB_KEY_RE`).
- `holdspeak/plugins/dictation/project_root.py` — auto-detects the project root +
  lazily loads the kb dict for read-only consumption.
- `holdspeak/plugins/dictation/builtin/project_rewriter.py` — the optional LLM
  stage that uses `.hs/`.
- Web routes (`holdspeak/web/routes/dictation/`):
  - `kb.py` → `/api/dictation/project-kb*` (the KB read/write API).
  - `agent.py` → `/api/dictation/project-context`, `agent-context*`.
  - `project_docs` → `/api/dictation/project-hs`, `project-doc-suggestion*`
    (the `.hs/` editor + the approved-write/suggestion apply path — reuse this
    for any UI-driven `.hs/` write; HoldSpeak must never write `.hs/` silently).

Config defaults: dictation pipeline default stages are
`["intent-router", "kb-enricher"]` (so the **KB** is on the default path;
`project-rewriter`/`.hs/` is opt-in). `dictation.pipeline.enabled` defaults
`false`. See `holdspeak/config.py`.

Tooling you'll reuse:

- **Screenshots:** `scripts/screenshot_docs.py` (boots a real server over seeded
  state, no mic/LLM; writes to `docs/assets/screenshots/`). Mirror it for
  before/after captures of the surfaces.
- **Dogfood:** `scripts/dogfood_*.py` (e.g. `dogfood_wizard.py`,
  `dogfood_first_run.py`) — the pattern for HS-47-03's "fresh repo → working,
  zero file editing" proof.
- **UX:** the `ui-ux-pro-max` skill + the Phase-43/44 "Signal" language (ambient
  glow, eyebrow + display headline, contained pill navs, elevated rounded
  surfaces, reduced-motion-safe). Memory `project_phase30_ui_overhaul`,
  `feedback_high_ui_standards`.

---

## 4. Per-story definition of success

- **HS-47-01 — Concept & naming.** A recorded decision (under this folder or
  `docs/internal/`): the canonical model + names + the on-disk-rename call
  (default: keep `.holdspeak/project.yaml` + `.hs/` on disk, change presentation
  only). Apply the `/dictation` label/header/lede changes so the two tabs read as
  one capability with a stated relationship. Labels-and-copy only; behavior
  unchanged. Lead candidate: **"Project knowledge = Facts (KB) + Context"**. Don't
  bikeshed — decide, record, move on.
- **HS-47-02 — Explainer + empty states.** Each surface gets a what/why/example
  explainer (accurate per §1) and a teaching empty state with a one-click starter,
  at the Signal bar. No bare grid/textarea on first visit.
- **HS-47-03 — Guided setup flow.** From a detected project with no knowledge,
  scaffold a working starter (`.hs/` + `project.yaml` KB) from the UI with an
  explicit review/approve step (no silent writes), then a dry-run shows it
  affecting output. Prove with a dogfood (no mic).
- **HS-47-04 — Discovery nudge.** When a detected project lacks knowledge, an
  ambient, dismissible hint routes into the flow; durable per-project dismissal;
  a global off switch; never naggy; never steals focus.
- **HS-47-05 — Docs alignment.** Document **both** mechanisms correctly (KB =
  `project.yaml`; context = `.hs/`) in the Intelligent Typing guide, matching the
  new UI framing; reconcile `DICTATION_COPILOT.md` + the README/index. Doc-drift +
  link + image guards green.
- **HS-47-06 — Closeout.** Before/after (old bare tabs vs new), a green dogfood,
  full suite green, `final-summary.md`, phase CLOSED, PR to `main` merged on green.

---

## 5. Gotchas that will bite you

- **Astro scoped CSS dies on JS-injected DOM.** `dictation-app.js` renders parts
  of these surfaces at runtime (no `data-astro-cid`), so any CSS for an injected
  empty state / explainer **must** be `<style is:global>`. A class existing in the
  bundle does not mean it applied — **screenshot-verify** the surface actually
  rendered. Memory `reference_astro_scoped_css_js_dom`.
- **Never commit `holdspeak/static/_built/`** (gitignored). Commit `web/src`; run
  `npm run build` so page-content tests see your change; assert **0** `_built/`
  tracked before committing.
- **Routing/intent ripple** doesn't apply here (no plugin chain changes), but if
  you touch dictation page-content tests, update them in lockstep — don't silence.
- **The KB write path is approval-gated.** Reuse the project-doc-suggestion apply
  semantics for any UI-driven `.hs/` write; do not add a second write primitive.
- **LAN/sandbox:** the intel LLM is on `.43:8080` and sandboxed Bash can't reach
  the LAN — but this phase needs **no** LLM (KB substitution + `.hs/` editing +
  dry-run are all local). If you do hit `.43`, use `dangerouslyDisableSandbox`.

---

## 6. Where to start

`HS-47-01` (concept & naming) is the entry point — every other surface presents
the model it decides. Read `story-01-concept-and-naming.md`, make the naming
decision, apply the `/dictation` label/copy changes, run
`uv run pytest -q -k "dictation or doc_drift or link"` + `npm run build`, then
ship it through the PMO gate. Sequence: 01 → 02 → (03, 04) → 05 → 06.

Good luck. Keep it honest, keep it plain, keep the pipeline untouched.
