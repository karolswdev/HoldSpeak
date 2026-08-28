# Phase 146 — Multiple Calendars

**Status:** in progress (2/7).

**Last updated:** 2026-08-28.

## Owner mandate

At the Phase 145 close (2026-08-28, merged the same day as PR #499)
the owner was shown the next-features menu and picked **Multiple
calendars**: widen the ingest from one ICS subscription to several
(work + personal), merged into the Door's one UPCOMING rail with
per-source provenance. Branch `feat/hs146-multi-calendar` from main
`4c08a613`.

Standing laws with extra weight here: **setup flows must be joyful**
(the Settings calendar surface is under the magnifying glass —
ugly-but-lawful is rejected); migrations stay minimal (single-user
reality); mic on every text input; no modals; errors in-flow. The
standing charter questions apply: *will you use this on a tired
Tuesday?* and *does this operate with joy?*

## Evidence base

- [`assets/plan-multi-calendar.md`](./assets/plan-multi-calendar.md)
  — the read-only opus plan (2026-08-28): the anchored
  single-calendar architecture table, the seven settled decisions,
  the edit map, the story cut, the risk notes.

## Settled design (orchestrator-ruled; the owner may overrule any row)

The plan's seven [ORCH-CALL]s, ruled the same day (no counsel round
spent on the charter; one counsel close pass at the end per the
ceremony budget):

1. **Config shape:** `CalendarSource {id, label, url, enabled}` in
   `CalendarConfig.sources: list`. One-shot minimal migration in
   `Config.load()` (old `subscription` → first source, key consumed
   once, no compat alias).
2. **Per-source last-good law:** the conductor refreshes each enabled
   source independently; `replace_projection` deletes only that
   source's rows; a failed source never touches a healthy source's
   projection. End-of-tick orphan cleanup removes rows for
   no-longer-enabled sources (disabled = not shown; re-enable
   refetches). Additive `source_id`/`source_label` columns; unique
   index `(source_id, uid, starts_at)`.
3. **Rail provenance:** mono label chip per EVENT row ONLY when >1
   distinct source; label → hostname → "LOCAL" fallback order
   (rendered uppercase per the house grammar).
4. **`calendar_configured`** = ≥1 enabled source passes validation.
5. **Settings = the joy surface:** GadgetTable list editor (label +
   url + enabled per row, mics on both text fields, in-world REMOVE?
   verb), per-source egress chips. Wire becomes
   `{calendar: {sources: [...]}}` + `_calendar_sources` derived fact.
6. **No dedupe.** Cross-feed UIDs aren't global; duplicates show with
   provenance.
7. **Guard truth:** no api-surface regen (route set unchanged), door
   aggregate key set unchanged, MCP settings description + six "one
   subscription" prose sites updated in the docs story.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-146-01 | Multi-source plumbing (config + DB + conductor) | done | [story-01](./story-01-multi-source-plumbing.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-146-02 | Settings service + wire | done | [story-02](./story-02-settings-service-wire.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-146-03 | The settings list editor (joy surface) | ready | [story-03](./story-03-settings-list-editor.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-146-04 | Rail provenance + seed repairs | ready | [story-04](./story-04-rail-provenance.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-146-05 | The walk and the close | ready | [story-05](./story-05-docs-walk-close.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-146-06 | The calendar book (thorough docs) | ready | [story-06](./story-06-the-calendar-book.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-146-07 | The Calendar Snapshot adapter | ready | [story-07](./story-07-calendar-snapshot-adapter.md) | [evidence-story-07](./evidence-story-07.md) |

## Risk register

- **Seed coordination:** three e2e/walk seeds hardcode
  `{"calendar": {"subscription": str}}`
  (`test_hs144_door_glass.py:222`, `test_hs145_door_polish_glass.py:370`,
  `door_walk_hs144.py:751`). The settings WIRE keeps accepting the
  old key until story 02 flips validation — so story 01 (config
  internals) must either keep the wire shape stable or land the seed
  flips in the same commit. The charter assigns seed flips to the
  first commit that breaks the old wire shape, whichever story that
  is.
- **Walk leg 5** interacts with the single textbox by name; it is
  rewritten in story 04/05 against the list editor.
- **Reconcile column adds** are the standard `_add_missing_columns`
  path; existing rows lawfully get `''` source ids (pre-multi era).
- **Sweep baseline** unchanged: Phase 143 inherited baseline,
  verdict vocabulary "baseline-exact, zero branch-new".

## Decision log

- 2026-08-28 — Phase chartered on the owner's menu pick (
  "Multiple calendars" over event→one-tap-record). Plan archived;
  all seven [ORCH-CALL]s ruled as recorded in the settled design.
- 2026-08-28 — **OWNER ORDER: a dedicated thorough-documentation
  story.** HS-146-06 (the calendar book) added: a real USER_GUIDE
  Calendars section, the SECURITY multi-source egress truth, an
  ARCHITECTURE calendar-pipeline section, the entry-point mentions,
  the six "one subscription" sites (moved out of story 05), and a
  doc-drift retirement guard if the mechanism accommodates it.
  Story 05 amended to walk+close only and now depends on 06 (docs
  after features, before closeout — the house law). Phase is 0/6.
- 2026-08-28 — **OWNER RULING: the Calendar Snapshot adapter folds
  INTO this phase as HS-146-07** (over the recommended Phase-147
  deferral; backlog candidate AE is the settled direction). The
  no-server O365 case: screenshot → vision extraction via a router
  assignment (egress honest) → week anchor never silently guessed →
  review-before-commit → a generated local `.ics` registered as a
  file CalendarSource, with the 146 parser staying the one trust
  boundary. The story carries a REQUIRED design-beat plan round
  before implementation. Stories 05 (walk) and 06 (docs) now also
  cover the adapter; phase is 1/7.
- 2026-08-28 — HS-146-02 closed (evidence-story-02.md): the real
  sources wire with per-entry named refusals + the `_calendar_sources`
  fact; RULED dual-fact reality — `_calendar_subscription` ships
  alongside until story 03 retires the UI consumer and story 04 flips
  the seeds/walk (12 consumers tabled in the worker report); the
  routing census drifted again on the hot file and was remapped 1:1
  (pointers, classifications, resolver references).
- 2026-08-28 — HS-146-01 closed (details + full-sweep triage in
  evidence-story-01.md): the multi-source plumbing with the
  wire-stability bridge; 66-test focused close; sweep 13 failed /
  6745 passed = 11 baseline + 2 lawful branch-caused fixture updates
  (schema snapshot regen; routing-census line-drift remap). Two
  orchestrator surgical deltas recorded: restored five out-of-scope
  comment deletions; hardened the bridge so a `sources` wire write
  validates every URL until story 02 lands the real treatment.
