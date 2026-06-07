# Phase 48 — Agent Brief (read this first)

You are picking up **Phase 48 — The Visible Learning Loop ("What HoldSpeak
learned")** for HoldSpeak. This brief is self-contained: the mission, the exact
code seams (mapped against the live tree), the rules of the road, and a per-story
definition of success. Read it, then read
[`current-phase-status.md`](./current-phase-status.md) and the story you're
working. If this brief disagrees with the live status docs or the codebase, the
**codebase wins** — re-verify before trusting any line or number below.

---

## 0. Mission

HoldSpeak already hears rough speech, routes and rewrites it in context, records
every attempt, learns from your corrections, and can replay to prove it improved.
That local speech-to-work loop is the product's most ownable idea — and it is
**invisible**. The user sees two raw lists (a Memory tab, a Journal tab) and a
buried correction form. Make the loop **visible** (a "What HoldSpeak learned"
digest), **trustworthy** (honest "learned from N similar" signals where the work
happens), and a **normal ritual** (one-tap right/wrong on a result).

This is a **visibility + trust + delight** phase, and it is the open-source pitch:
"it gets better at your voice, on your machine, and shows you the proof." It does
**not** change what the pipeline does — routing, rewrite, and substitution are
untouched. You are adding a read-only aggregation, surfacing honest counts, and
making correction effortless.

---

## 1. The one thing you must not get wrong

**Every number must be real, and from the same matcher that actually nudges
routing.** The whole point of this phase is trust. If "learned from N similar" is
inflated, decorative, or computed by a second, different similarity than the one
the pipeline uses, you have built the opposite of trust.

- The matcher is `CorrectionStore.best_match_in` / `similarity` in
  `holdspeak/plugins/dictation/corrections.py` (Jaccard token overlap,
  `min_similarity=0.5` default). Use **that** to count "N similar" over journal
  transcripts. Do not invent embeddings or a second heuristic.
- Surfaces stay **quiet at N=0**. No claim of learning that did not happen.
- Respect `corrections_enabled` (off by default) and the secret-filter: a
  secret-filtered correction teaches nothing (`taught=false`), and the UI must say
  so honestly (the existing toast already does this).

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md` §"Contract template"); `mkdir -p .tmp` first, the
  pre-commit hook validates and deletes it. A story flipping to `done` **must**
  ship its `evidence-story-{n}.md` in the same commit; **one** done-flip per commit.
  The phase-exit story needs `evidence-story-05.md` **and** `final-summary.md` in
  the same commit. The story Status line must be the list-item form
  `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates: the story header status,
  the phase `current-phase-status.md` (row + Last-updated + "Where we are"), the
  project `README.md` (phase row + Current-phase + Last-updated), and any canon doc
  the story touched.
- **One PR per phase, merged when CI green.** Work on a phase branch; at close,
  push + open a PR to `main` + merge with a merge commit when all four CI suites
  pass (Unit · Integration macOS · E2E macOS · Linux Smoke). Memory
  `feedback_merge_phases_via_pr`.
- **Tests actually run.** Flip a story to `done` only after running the relevant
  tests and reading the output. Full suite:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` (the metal file hangs without
  a mic). Type-check is not validation.
- **Behavior-preserving.** The digest is read-only; correcting reuses the existing
  write path; pipeline tests stay green and routing stays byte-identical when
  corrections are off.
- **Write like a human.** The user is allergic to AI-flavored prose. In any doc or
  UI copy you add: **no em or en dashes**, no emoji-decorated bullets, no
  rule-of-three padding, no "not X but Y". Plain, varied, direct. (`humanizer`
  skill available; `docs/internal/DOCS_STYLE.md` is the voice authority.)

---

## 3. The ground truth (code seams, already mapped)

Backend (data + matcher):

- `holdspeak/db/journal.py` — `DictationJournalRepository` (`record`, `recent`
  filtered by `source`, `get`, `mark_corrected`, `delete`, `clear`, `count`).
  Rows: transcript, final_text, intent, block_id, target_profile, stage_ms,
  total_ms, confidence, warnings, `corrected`, `correction_id`, `created_at`
  (ISO text). Schema in `holdspeak/db/core.py` (table `dictation_journal`); model
  `DictationJournalRecord` in `holdspeak/db/models.py`.
- `holdspeak/db/corrections.py` — `DictationCorrectionRepository`
  (`record_correction`, `recent_corrections`, `delete_correction`, `clear`). Rows:
  `kind` (intent/target), `gist`, `value`, `created_at`. Model
  `DictationCorrectionRecord`.
- `holdspeak/plugins/dictation/corrections.py` — `CorrectionStore` (the in-memory
  ring + write-through). **The matcher you must reuse:** `best_match_in()` and
  `similarity()` (Jaccard). `snapshot()`, `recent()`, `list_for_display()`.
- `holdspeak/dictation_telemetry.py` — `build_depth_readiness()` is the only
  existing aggregation, and it is **in-session only** (resets on restart). There is
  **no** historical/weekly rollup and corrections track **no** coverage count —
  that is your new work in HS-48-01.
- `holdspeak/db/milestones.py` — `MilestoneRepository` (framework only; one
  `FIRST_DICTATION_SUCCESS` constant). Optional for a "first correction" touch.

Web routes (`holdspeak/web/routes/dictation/pipeline.py`):

- `GET /api/dictation/journal` → `{enabled, retention, count, items[...]}`;
  `DELETE .../journal/{id}`, `DELETE .../journal`.
- `POST /api/dictation/journal/{id}/correct` → `{corrected, taught, correction_id,
  size}` — **the moment-of-truth teach path; reuse it.**
- `POST /api/dictation/journal/{id}/replay` → `{before, after, changed, ...}`.
- `GET /api/dictation/corrections` → `{enabled, kinds, size, items[...]}`;
  `POST`/`DELETE` for CRUD.
- `POST /api/dictation/dry-run` returns `journal_id` so the result can offer the
  in-flow fix.
- `_run_dictation_dry_run_text` (`.../dictation/_helpers.py`) gates the matcher on
  `corrections_enabled` + repository presence (snapshot=None otherwise → identical
  routing).

UI (Astro; source in `web/src`, built bundle is **gitignored** under
`holdspeak/static/_built/` — run `(cd web && npm run build)`, Node ≥ 22.12, after
any `web/src` edit; page-content tests read the built JS):

- `web/src/pages/dictation.astro` — **Memory** tab (`section-memory` /
  `#view-memory`: `#mem-list`, `#mem-add-form`, `#mem-depth`) and **Journal** tab
  (`section-journal` / `#view-journal`: `#journal-list`, search/filters). The
  dry-run **moment of truth** host is `#dry-moment`.
- `web/src/scripts/dictation-app.js` — `loadMemory` / `renderMemoryCorrections` /
  `renderMemoryDepth`; `loadJournal` / `renderJournal` / `renderJournalEntry`;
  `renderMomentOfTruth` / `submitMomentFix` (the correct flow). The runtime DOM is
  JS-rendered (heed the scoped-CSS trap in §5).

Tooling you'll reuse:

- **Dogfood:** `scripts/dogfood_project_knowledge.py` is the model — HTTP-driven
  over a `TestClient`, a deterministic stub runtime standing in for the local
  model, asserting real output. Mirror it for the digest proof.
- **Screenshots:** `scripts/screenshot_project_knowledge.py` (boots a real server
  over seeded state, no mic/LLM) is the model for before/after captures.
- **UX:** the `ui-ux-pro-max` skill + the Phase-43/44 "Signal" language (eyebrow +
  display headline, elevated rounded surfaces, contained pills, reduced-motion-safe,
  worked examples). Memories `project_phase30_ui_overhaul`, `feedback_high_ui_standards`.

---

## 4. Per-story definition of success

- **HS-48-01 — The learning digest.** A read-only aggregation endpoint
  (`GET /api/dictation/learning-digest?window=week|all`) over journal + corrections:
  corrections made, dictations corrected, by-kind/target/block breakdown, and a real
  "N similar" per correction via the Jaccard matcher. A Signal-styled "What
  HoldSpeak learned" view with a window toggle and a teaching empty state. Honest,
  read-only, no new writes. The foundation everything else presents.
- **HS-48-02 — Inline trust signals.** A truthful "learned from N similar" chip on
  the dry-run result + journal entries (hidden at N=0), and a post-correction
  confirmation that states real coverage (upgrade the generic "taught" toast). One
  matcher, no second source of truth.
- **HS-48-03 — Correction ritual.** A one-tap right/wrong on results + journal
  entries; "wrong" opens the existing correct flow inline, pre-scoped to the likely
  fix. Reuse `renderMomentOfTruth`/`submitMomentFix` and the correct endpoint; no
  new write primitive; focus-safe.
- **HS-48-04 — Docs.** The Intelligent Typing guide (and/or Dictation Copilot)
  tells the loop end to end (dictate → one-tap fix → learns → digest shows it →
  replay proves it); README/index frames it as the local-first differentiator;
  guards green; grounded in code; bounded-honesty about the Jaccard matcher.
- **HS-48-05 — Closeout.** Before/after (old buried tabs vs the new digest + signals
  + one-tap correction), a green dogfood, full suite green, `final-summary.md`,
  phase CLOSED, PR to `main` merged on green.

---

## 5. Gotchas that will bite you

- **Honest counts only.** (See §1.) The most important rule of this phase. Reuse
  `CorrectionStore` similarity; stay quiet at N=0; respect `corrections_enabled` +
  secret-filter. A pretty but wrong number fails the phase.
- **Astro scoped CSS dies on JS-injected DOM.** `dictation-app.js` renders the
  Memory/Journal/result DOM at runtime (no `data-astro-cid`). Any CSS for an
  injected digest/chip/affordance **must** be `<style is:global>`, or build it as
  static markup toggled by JS (the Phase-47 pattern), and **screenshot-verify** it
  actually rendered. Memory `reference_astro_scoped_css_js_dom`.
- **Focus-safe.** The dictation bundle must keep **zero `.focus()`** — there is a
  guard (`test_moment_affordance_present_and_focus_safe`). Use `scrollIntoView`
  (reduced-motion-aware) if you must, never `.focus()`.
- **Never commit `holdspeak/static/_built/`** (gitignored). Commit `web/src`; run
  `npm run build` so page-content tests see your change; assert **0** `_built/`
  tracked before committing.
- **Page density.** `dictation.astro` (~2.3k lines) and `dictation-app.js` (~2.4k
  lines) are already large and grew in Phase 47. Factor new UI into section
  partials / behavior modules rather than appending. This phase is a good moment to
  start that discipline (the strategic review flagged it).
- **`created_at` is ISO text.** Window by it carefully (string compare on ISO works
  for ranges, or parse). Seed deterministic timestamps in tests.

---

## 6. Where to start

`HS-48-01` (the digest) is the entry point — every other surface presents or feeds
the aggregation it adds. Read `story-01-learning-digest.md`, build the read-only
aggregation endpoint over the journal + corrections (reusing the Jaccard matcher
for "N similar"), then the "What HoldSpeak learned" view, run
`uv run pytest -q -k "dictation or journal or corrections or learning"` +
`npm run build` + a screenshot, and ship it through the PMO gate. Sequence:
01 → 02 → 03 → 04 → 05.

Keep it honest, keep it plain, keep the pipeline untouched. This is the feature
that makes the open-source story land: a tool that gets better at your voice, on
your machine, and shows you the proof.
