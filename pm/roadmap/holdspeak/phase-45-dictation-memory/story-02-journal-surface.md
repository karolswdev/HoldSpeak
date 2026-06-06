# HS-45-02 — The Journal: a reviewable utterance timeline

- **Project:** holdspeak
- **Phase:** 45
- **Status:** backlog
- **Depends on:** HS-45-01
- **Unblocks:** HS-45-04
- **Owner:** unassigned

## Problem
With rows persisting (HS-45-01), the user still can't see them. Dictation needs
its `/history`: a place to review *what I said → what it became → where it went →
how long it took*, search it, and curate it. This is also where the latency black
box becomes observable — per utterance, not just aggregate p50/p95.

## Scope
- **In:**
  - A **Journal** view on `/dictation` (a new section via the existing
    `[data-section]` tab pattern in `web/src/pages/dictation.astro` +
    `dictation-app.js`) — or a dedicated page if cleaner. A reviewable timeline:
    each entry shows the **transcript**, the **final typed text**, **target /
    block** badges, a **timestamp**, a `source` chip (dictation vs dry-run), and
    a **per-stage latency strip** (capture/route/rewrite/… → total).
  - **Search** over transcript + final text; **filters** (source, target,
    has-warning). **Copy** (transcript / final text). **Per-entry delete** +
    **"Clear journal"** (over the HS-45-01 wipe API).
  - A clear **local-only trust statement** (this never leaves your machine;
    secret-filtered; retention N) — wire the existing **TrustChip** idiom.
  - A **warm empty state** ("Your dictations will appear here…") and the
    **Phase-44 premium bar** (ambient glow, eyebrow/hero grammar, pill nav,
    elevated cards), a11y + reduced-motion.
  - New `GET /api/dictation/journal` (list, paged/limited, newest-first) +
    `DELETE /api/dictation/journal/{id}` + `DELETE /api/dictation/journal`
    over the repo.
- **Out:** the in-moment correct loop (HS-45-03); replay (HS-45-04). Read +
  curate only here.

## Acceptance criteria
- [ ] The Journal view lists real journal rows newest-first with transcript →
      final text → target/block → timestamp → per-stage latency strip → source.
- [ ] Search filters by transcript/final-text substring; the source/target/
      has-warning filters narrow the list.
- [ ] Per-entry delete and "Clear journal" call the DELETE endpoints and update
      the list; a local-only trust statement is visible.
- [ ] Empty state is warm; the view carries the Phase-44 bar (glow + hero + pill
      nav + elevated surfaces); focus-visible + reduced-motion respected.
- [ ] The Alpine-free `dictation-app.js` DOM contract is preserved (new section
      added via `[data-section]`, existing ids untouched); `(cd web && npm run build)`
      succeeds; **0** `_built/` tracked.
- [ ] Suite green.

## Test plan
- Unit / API: `tests/integration` — `GET /api/dictation/journal` returns rows;
  DELETE (one + all) works; paging/limit honored.
- Page-content: `tests/integration/test_web_dictation_journal.py` — the Journal
  section markup, the latency strip, the trust statement, the premium markers
  (glow/pill nav/reduced-motion), and the preserved `[data-section]` contract
  (mirror `test_web_dictation_cockpit.py`).
- Live (Playwright): capture the Journal populated by a few dry-runs →
  `evidence/journal_timeline.png`.
- Manual / device: n/a (dry-runs populate the journal).

## Notes / open questions
- **Tab vs page** — a `/dictation` Journal tab keeps it beside the cockpit; a
  dedicated page mirrors `/history` more closely. Decide during build; the tab is
  the lower-risk default (reuses the section system).
- Latency strip should degrade gracefully when `stage_ms` is sparse (old rows /
  dry-run-only stages).
