# Phase 53 — Agent Brief (read this first)

You are picking up **Phase 53 — Activity Pre-Briefing** for HoldSpeak. This brief is
self-contained: the mission, the exact code seams (mapped against the live tree at
scaffold time), the rules of the road, and a per-story definition of success. Read it,
then read [`current-phase-status.md`](./current-phase-status.md) and the story you're
working. If this brief disagrees with the live status docs or the codebase, the
**codebase wins** — re-verify before trusting any line or number below.

---

## 0. Mission

HoldSpeak already watches local activity (browser history, GitHub/Jira/calendar
enrichment) and stores it as source-cited records. Today that lives on the `/activity`
page as a ledger you go and inspect. The value is not the ledger; it is bringing the
relevant bit of it to you at the moment it helps.

Turn the activity layer into concrete, source-cited, dismissible **pre-briefing
nudges** on the daily surfaces:

- "Here is what you touched since your last meeting" before you start dictating or meet.
- "You were looking at issue `owner/repo#123`. Dictate a reply with it as context?"

Every nudge cites the activity record that produced it (which browser, which page,
when), is dismissible, and never acts on its own. It is ambient, not creepy: it
surfaces and offers, you decide. One nudge action is "dictate with this as context",
which feeds the selected activity record into the dictation pipeline.

This is a **feature** (backlog candidate F) on the daily-dictation north star. It does
not change meeting capture, intel, plugins, or synthesis behavior.

---

## 1. The one thing you must not get wrong

**A nudge surfaces and offers. It never acts, and it never appears uninvited when the
user has not opted into activity.**

- **Read-only and consenting.** A nudge shows recent activity and offers an action
  (dictate with this, dismiss). It never runs a command, opens a page, or sends
  anything on its own. The only thing that fires is what the user clicks.
- **Gated by the existing activity privacy toggle.** Activity tracking is already
  opt-in (`/api/activity/settings`, `enabled`). If activity is off, there are no
  records and there must be no nudges. Do not add a second always-on watcher.
- **Source-cited, always.** Every nudge names where it came from: the browser/profile,
  the page title or entity (`github_issue owner/repo#123`), and when (`last_seen_at`).
  No nudge without a citation a user can verify on `/activity`.
- **Dismissible and quiet.** A nudge is a `role="note"` card that never steals focus
  (clone the `#kn-nudge` pattern). Dismissing one keeps it dismissed.
- **Local-only.** Activity is local; nudges are computed locally; nothing egresses.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md`, **7** checkboxes; `mkdir -p .tmp` first). A story
  flipping to `done` ships its `evidence-story-{n}.md` in the same commit; **one**
  done-flip per commit. The phase-exit story needs `evidence-story-{last}.md` **and**
  `final-summary.md` in the same commit. Status line is `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates the story header, this phase
  `current-phase-status.md`, the project `README.md`, and any canon doc touched.
- **One PR per phase, merged on green CI** (Unit, Integration macOS, E2E macOS, Linux
  Smoke, Route screenshots). Branch `phase-53-activity-prebriefing`; at close push + PR
  to `main` + merge.
- **Tests actually run.** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **The web bundle is gitignored.** Edit `web/src`, `cd web && npm run build`, commit
  source only, never `holdspeak/static/_built/`. JS-injected DOM needs `<style
  is:global>`; screenshot-verify.
- **High UI/UX bar** (`ui-ux-pro-max`). A nudge is a real, inviting, dismissible card,
  not a banner. Ship screenshot evidence (`scripts/screenshot_*.py` pattern).
- **User-facing docs obey the Phase-51 guard.** The new guide (HS-53-05) must be
  product-tense with no roadmap vocabulary; run the `humanizer` skill over it.
- **Density invariant (D rides along).** `dictation.astro` is ~2.7k lines. If the nudge
  UI lands there, factor as you go; do not grow the page further without paying it down.

---

## 3. The ground truth (code seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift.

**The activity record (the citation source):**
- `holdspeak/db/models.py:207` — `ActivityRecord`: `source_browser` (`:211`),
  `source_profile`, `url`/`normalized_url`, `title`, `domain`, `entity_type` /
  `entity_id` (`:222-223`, e.g. `github_issue` + `owner/repo#123`), `last_seen_at`
  (`:220`, the window key), `project_id`.
- `holdspeak/db/activity.py:29` — `ActivityRepository`: `upsert_activity_record`
  (`:69`), `list_activity_records` (`:233`). A windowed query (records with
  `last_seen_at >= <ts>`) is the new read the engine needs.

**The activity context bundle (the dictation-context path):**
- `holdspeak/activity_context.py:86` — `build_activity_context(db, project_id, limit,
  refresh) -> ActivityContextBundle`; `.to_dict()` at `:20-44` already aggregates
  records + `entity_counts` / `domain_counts` / `source_counts`.
- `holdspeak/activity_context.py:45` — `ActivityContextProvider`: the callable that
  injects `{"activity": bundle.to_dict()}` into plugin/dictation context. "Dictate with
  this as context" extends this with a selected record (an override).

**Meeting window (for "since last meeting"):**
- `holdspeak/db/models.py:25` — `MeetingSummary` with `started_at` (`:28`) / `ended_at`
  (`:29`); `holdspeak/db/meetings.py` lists meetings. The previous meeting's `ended_at`
  is the lower bound for "since last time".

**The web surfaces:**
- The activity routes live under `holdspeak/web/routes/activity/` (`ledger.py` serves
  `/api/activity/records` + `/api/activity/status`, `candidates.py`, `enrichment.py`).
  Add a small nudges router (or extend ledger) for `GET /api/activity/nudges` +
  `POST /api/activity/nudges/{id}/dismiss`.
- `web/src/pages/dictation.astro:42` — `#kn-nudge`, the proven dismissible nudge card
  (`role="note"`, hidden by default, a dismiss button, JS-toggled in `dictation-app.js`).
  **Clone this pattern** for the activity nudge.
- `web/src/pages/index.astro` — the runtime/home has a pre-meeting `section.briefing`
  (around `:188`); a "since last meeting" nudge can surface there too.

**No existing nudge engine** — `activity_nudges` is greenfield.

---

## 4. Per-story definition of success

- **HS-53-01 — The nudge engine + dismissal store.** A new module (e.g.
  `holdspeak/activity_nudges.py`) computes a small set (1 to 3) of source-cited nudges
  from recent activity: a windowed "since last meeting / recent" summary and a per-record
  "dictate with this as context" suggestion, each carrying its source citation and the
  originating `ActivityRecord` id, scored by a simple deterministic relevance heuristic
  (recency, entity type, project match). A dismissal store (a small table or settings
  field) keeps a dismissed nudge dismissed. Off when activity tracking is off. Pure data
  + engine, no UI. Unit-tested (window, citation, dismissal, off-path).
- **HS-53-02 — The nudges API.** `GET /api/activity/nudges` (compute, drop dismissed,
  return top N with citations) and `POST /api/activity/nudges/{id}/dismiss`. Returns an
  empty list when activity is off. Tested.
- **HS-53-03 — Dictate with this as context.** Extend the activity-context path so a
  nudge-selected record is injected into the dictation pipeline as context (an override
  on `ActivityContextProvider` / `build_activity_context`, or a small endpoint the
  dictation flow consumes). Selecting a record makes its entity available to the rewrite,
  without changing the default (no selection) behaviour. Tested.
- **HS-53-04 — The nudge UI.** A dismissible, source-cited nudge card on the dictation
  surface (clone `#kn-nudge`): it names the source, shows what you touched, and offers
  "Dictate with this" + "Dismiss". Quiet, focus-safe, off when activity is off. Optional:
  the "since last meeting" nudge on the home briefing. `npm run build` clean;
  `<style is:global>` for any JS-injected DOM; screenshot evidence committed.
- **HS-53-05 — Docs (dedicated docs story).** A short user guide: what pre-briefing
  nudges are, that they are local + source-cited + dismissible + never act on their own,
  how the "dictate with this" action works, and how the activity toggle gates them.
  Product-tense, passes the Phase-51 guard, `humanizer` run, linked in the docs index.
- **HS-53-06 — Closeout.** A dogfood proving the engine end to end (seed activity + a
  prior meeting -> a windowed, source-cited nudge is computed; dismiss it -> it stays
  gone; activity off -> no nudges; "dictate with this" injects the record). Full suite
  green, `final-summary.md`, phase CLOSED, PR merged on green, BACKLOG candidate F
  flipped to shipped.

---

## 5. Gotchas that will bite you

- **Do not add a second activity watcher.** Read the records that already exist; the
  import path (`activity_history.py`) and the privacy toggle are already there. The
  engine is a reader.
- **Relevance is heuristic and must be honest.** There is no relevance score today
  (see the activity map's limitations). Use a simple, explainable heuristic (recency +
  entity type + project match) and do not oversell it. A nudge with a weak signal should
  not appear; quiet beats noisy.
- **Citation is coarse.** Records carry browser/profile + `last_seen_at` (last visit to a
  URL), not a per-session timestamp. Cite what is true ("you visited this 5 times, last
  on <date>"), not a fabricated precision.
- **Browser-only.** Activity is browser history + enrichment. Do not imply it sees your
  desktop apps or Slack.
- **Dismissal must persist** in a way that survives a reload (a table or a settings
  field, not only in-memory), or the same nudge nags forever.
- **Focus-safe.** The nudge never steals focus while the user dictates elsewhere; it is a
  `role="note"`, like `#kn-nudge`.
- **The new doc must pass last phase's guard** (no `Phase 53` / `HS-53-xx`).

---

## 6. Where to start

`HS-53-01` (the engine + dismissal store) is first: it is the brain everything else
surfaces. Build it as a reader over the existing activity records + the meeting window,
with a simple honest relevance heuristic, fully unit-tested, before any API or UI.
Suggested sequence: 01 -> 02 -> 03 -> 04 -> 05 -> 06. Keep it read-only, source-cited,
dismissible, gated by the activity toggle, and quiet. This is the phase that turns the
activity HoldSpeak already has into something that helps you before you ask.
