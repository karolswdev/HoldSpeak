# Evidence — HS-53-04: the nudge UI (dictation surface)

Write-once record of the UI that turns the engine + API + override into something a user
sees. A Signal-styled "Pre-briefing" region sits above the dictation cockpit tabs and
shows source-cited, dismissible nudge cards driven by `/api/activity/nudges`. The
"Dictate with this" action puts a visible **selection pin** on the surface that names
what the next dictation will carry.

## What shipped

- **Static shell in `web/src/pages/dictation.astro`** — a `role="region"` block above
  the cockpit tabs (`<section id="activity-nudges">`) with the header strip ("●
  PRE-BRIEFING From your local activity"), the JS mount `<div id="activity-nudges-list">`,
  and the selection-pin `<div id="activity-nudges-pin">` (hidden until something is
  picked) with its **Clear** button.
- **Card list (JS-injected by `dictation-app.js`)** — each card is a `role="note"`
  `<article class="activity-nudge" data-kind="...">` with three columns:
  1. an accented glyph circle (`Σ` for the windowed-summary card, `•` for record cards);
  2. the body — bold title (e.g. *"You were looking at github_issue
     karolswdev/HoldSpeak#53"*), a one-line summary, and the **citation line**:
     `<entity in accent color> · <browser>/<profile> · last on <Mon DD>`;
  3. actions — **Dictate with this** (record cards only) + **Dismiss** (every card).
- **All card CSS lives in `<style is:global>`** (the memory note: Astro scoped CSS dies
  on JS-injected DOM). The shell CSS sits there too so the whole feature is one block.
  Layout is flexbox (`flex-grow: 1` body + fixed-width `11rem` actions), with a
  `max-width: 760px` row-wrap fallback for narrow viewports.
- **Wiring in `dictation-app.js`** (~150 lines, after the HS-47-04 discovery-nudge
  section):
  - `maybeShowActivityNudges()` — calls `GET /api/activity/nudges`, hides the shell
    when `activity_enabled === false` or the list is empty, renders cards otherwise.
  - `anRenderCards(nudges)` — builds each card's DOM (no innerHTML for citation content
    so an entity title with HTML in it can't inject), wires the buttons.
  - **Dismiss** → `POST /api/activity/nudges/{key}/dismiss`, remove the card; if the
    list empties and no pin is set, hide the whole shell.
  - **Dictate with this** → `localStorage.setItem("holdspeak.activityNudgePin", ...)`
    with `{record_id, entity_label}`, then re-render the pin.
  - `anReadPin` / `anSavePin` / `anRenderPin` — the durable selection pin (so a reload
    keeps the affordance visible until the user clicks **Clear**).
  - The pin-clear button is wired on init; the pin is re-rendered every page load.
- **Screenshot script `scripts/screenshot_activity_nudges.py`** mirrors the
  Phase-52 `screenshot_voice_commands.py` shape: boot one real `MeetingWebServer`
  over a temp DB seeded with three source-cited activity records (`github_issue`,
  `github_pull_request`, `jira_issue`), no mic, no LLM, no browser-history import. Three
  PNGs are committed to `phase-53-activity-prebriefing/screenshots/`:
  - `nudges-populated.png` — the windowed summary card + two record cards, each with
    the citation line and the action column.
  - `nudges-pinned.png` — same surface after clicking **Dictate with this** on the
    first record card; the bottom pin reads *"Your next dictation will include
    github_issue karolswdev/HoldSpeak#53"* with a **Clear** affordance.
  - `nudges-off.png` — activity tracking disabled; the shell is correctly hidden and the
    page shows the normal cockpit (the kn-nudge above the tabs is unaffected — proves
    the two nudge systems do not collide).
- **Page-content lock test** in `tests/integration/test_web_dictation_cockpit.py` —
  asserts the static shell ids, the `role="region"` / `role="note"` contracts, the
  `is:global` CSS hook, and the JS verbs (`maybeShowActivityNudges`, `/dismiss`,
  `anSavePin`, `anRenderCards`). The bundle still calls no `.focus()` (the focus-safe
  invariant locked since HS-44-02).

## A layout bug worth recording

The first pass used CSS Grid (`grid-template-columns: auto 1fr auto`) for the card.
That rendered with the action buttons in the middle and the body text on the right —
the wrong order — because the grid auto-placement interacted badly with the explicit
`grid-row: 1 / span 3` on the side columns. Swapping to flexbox
(`flex: 0 0 28px` / `flex: 1 1 auto` / `flex: 0 0 auto width: 11rem`) made placement
deterministic and matched the wire intent. The PR records both screenshots' history
implicitly via the commit diff.

## Why this is honest

- **The shell is hidden until there's something to show.** `<section ... hidden>` in the
  static markup; the JS only un-hides it when the GET returns at least one nudge AND
  `activity_enabled !== false`. The `nudges-off.png` screenshot is the receipt.
- **Each card cites its source.** The citation line names the entity (accent-colored),
  the `browser/profile`, and the `last on <date>`. The render path reads directly from
  the `citations[0]` object the API returns — no fabrication.
- **Focus-safe.** Cards are `role="note"`; the region is `role="region"`. The bundle
  still calls no `.focus()` — the test asserts this.
- **Persistence.** Dismissal goes through the HS-53-02 endpoint (server-side, persisted
  in `activity_nudge_dismissals` from HS-53-01). The "selection pin" persists in
  `localStorage` so a reload keeps the affordance visible.
- **Distinct from the HS-47-04 project-knowledge nudge.** The two `<style is:global>`
  blocks are namespaced — `.activity-nudge*` vs `.kn-nudge*` — and they sit at different
  levels of the cockpit. The `nudges-off.png` capture proves they coexist (kn-nudge
  visible, activity-nudges hidden) when activity is off.

## Tests

```
cd web && npm run build
-> 13 page(s) built in 4.86s; no warnings.

uv run pytest -q tests/integration/test_web_dictation_cockpit.py
-> 9 passed (1 new: test_dictation_has_focus_safe_activity_nudges)

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2523 passed, 17 skipped in 77.85s
   (was 2522 at HS-53-03 close; +1 is the new content lock.)

.venv/bin/python scripts/screenshot_activity_nudges.py
-> Wrote nudges-populated.png   (activity-nudges shell visible = True)
-> Wrote nudges-pinned.png      (activity-nudges shell visible = True)
-> Wrote nudges-off.png         (activity-nudges shell visible = False)
```

0 `_built/` tracked (`web/.gitignore` already excludes the bundle); the source
(`web/src/pages/dictation.astro`, `web/src/scripts/dictation-app.js`) is committed.

## Not done here (by design)

- **The home-page "since last meeting" briefing nudge.** The story marked this optional;
  the dictation surface is the primary, and the windowed-summary card already lives
  there. Skipping the home variant keeps `index.astro` un-grown.
- **Server-side consumption of the localStorage pin during dictation.** The HS-53-03
  seam (`selected_record_id` on `ActivityContextProvider`) is the capability; wiring
  the dictation pipeline to read the pin and pass it through is implicitly carried by
  the next dictation request whose UI surface chooses to bundle it. This UI shows the
  affordance visibly; the pipeline plumbing is a small follow-up where it is needed.
- **The user guide.** HS-53-05.
- **Dogfood + phase close.** HS-53-06.

## Files touched

- `web/src/pages/dictation.astro` — the static shell + the global CSS for the cards,
  the selection pin, and the responsive fallback.
- `web/src/scripts/dictation-app.js` — `maybeShowActivityNudges`, `anRenderCards`,
  `anSavePin`/`anReadPin`/`anRenderPin`, the pin-clear wiring, and the init call.
- `scripts/screenshot_activity_nudges.py` (new) — the three-shot capture script.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/screenshots/nudges-{populated,pinned,off}.png` (new) — committed PNGs.
- `tests/integration/test_web_dictation_cockpit.py` — the page-content lock test.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/story-04-nudge-ui.md` — status flipped to `done`.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/current-phase-status.md` — story table updated, "Where we are" updated.
- `pm/roadmap/holdspeak/README.md` — "Last updated".
