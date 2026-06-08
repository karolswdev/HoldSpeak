# Evidence — HS-53-05: the pre-briefing user guide

Write-once record of the user-facing guide for the activity pre-briefing feature. A
short, product-tense doc that names what the cards are, the local + source-cited +
dismissible + never-acts contract, the dictate-with-this action, and the activity
tracking toggle that gates the whole thing.

## What shipped

- **New `docs/ACTIVITY_PREBRIEFING.md`** (~95 lines). Sections:
  - A one-paragraph thesis ("the opposite of a feed").
  - A boxed off-until-activity-is-on note (the consent gate up front).
  - **What you see** — a description of the hero block above the dictation cockpit
    tabs, the windowed-summary card, and the per-record cards with their citation
    chips.
  - **What the citation means** — the entity chip (what HoldSpeak recognised the page
    as, falling back to title/URL), the source chip (browser + profile, honest about
    multiple profiles), the date chip (last-visit, not per-session, with a concrete
    Tuesday example). Written as flowing prose, not an inline-header bullet list.
  - **What the actions do** — Dismiss is durable and local; "Dictate with this" pins
    the selected record so the next dictation can use it as context, with a visible
    selection strip and a Clear button.
  - **How the relevance is chosen** — a simple deterministic rule (recency + entity
    type + project match), not a learned model; weak signals do not appear; two
    refreshes a minute apart give the same answer.
  - **What it does not do** — four plain bullets (no `**Bold colon**` inline-headers,
    per the humanizer pattern): it does not watch desktop apps, it does not call out,
    it does not learn from dictation, it does not act on its own.
  - **Turning it off** — flip the activity tracking toggle on `/activity`.
  - **Where the records come from** — a one-paragraph pointer to the existing
    browser-history readers and enrichment connectors.
- **Linked from `docs/README.md`** under "Dictate: voice typing and the intelligent
  copilot", just after the Voice Commands entry. The index stays a map: a single
  bullet with a one-paragraph summary, mirroring the existing Voice Commands and
  Dictation Copilot entries.

## Why this is honest

- **No roadmap vocabulary.** The doc speaks in product-tense throughout: no `Phase
  NN`, no `HS-NN-NN`, no `PMO`, no `closeout`, no "the current roadmap". The
  Phase-51-installed guard (`tests/unit/test_doc_drift_guard.py`'s
  `test_no_user_facing_doc_leaks_roadmap_vocabulary`) scans the new doc and passes.
- **No em or en dashes.** Verified twice (after the draft and after the humanizer
  edits): `grep -n "[—–]" docs/ACTIVITY_PREBRIEFING.md docs/README.md` is empty. The
  draft used only commas, semicolons, parentheses, and colons.
- **Humanizer pass.** The `humanizer` skill's pattern guide was applied. The main
  tell in the first draft was pattern #16 (inline-header vertical lists with
  `**The entity.**` / `**It does not X.**` colons in two bullet lists). Both were
  rewritten: the citation section became flowing prose, and the "what it does not do"
  list became plain bullets that lead with the negation in the prose itself. No AI
  vocabulary clusters (`vibrant`, `tapestry`, `underscore`, `pivotal`, `crucial`,
  `comprehensive`, `enhance`, `leverage`) appear in the doc.
- **Every claim grounded in shipped code.** The hero text matches the static markup
  in `dictation.astro`; the citation chips described match what `dictation-app.js`
  emits; the "dictate with this" action matches the localStorage pin + the HS-53-03
  `selected_record_id` seam (this evidence file uses the internal story id; the
  user-facing doc never does); the relevance rule matches the heuristic in
  `holdspeak/activity_nudges.py`; the gate matches the
  `ActivityRepository.get_activity_privacy_settings` consent check.

## Tests

```
uv run pytest -q -k "doc_drift or doc_guard or doc"
-> 75 passed, 2 skipped
   (the roadmap-vocab guard scans the new doc and is happy; the link/image guards
    confirm the new ./ACTIVITY_PREBRIEFING.md ref in docs/README.md resolves.)

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2523 passed, 17 skipped
   (no count change — docs-only.)

grep -n "[—–]" docs/ACTIVITY_PREBRIEFING.md docs/README.md
-> (empty; no em or en dashes.)
```

`npm run build` is N/A for a docs-only change; 0 `_built/` tracked.

## Not done here (by design)

- **The dogfood + final-summary + PR merge.** HS-53-06.
- **A second user-facing doc.** The pre-briefing is a small feature, and the
  Activity page already has its own guidance on `/activity`. A single short doc plus
  the index entry is the right surface.

## Files touched

- `docs/ACTIVITY_PREBRIEFING.md` (new) — the guide.
- `docs/README.md` — one new bullet under "Dictate".
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/story-05-docs.md` — status
  flipped to `done`.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/current-phase-status.md` — story
  table updated, "Where we are" updated.
- `pm/roadmap/holdspeak/README.md` — "Last updated".
