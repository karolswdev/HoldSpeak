# Phase 178 - The Portfolio

**Last updated:** 2026-09-05.

> **PARKED behind Phase 200 The Working Practice (2026-09-06, the owner's line in the sand, PR #563). Not deleted; re-chartered on his word when Phase 200's gates say the desk is used daily.**

## Goal

Many Rooms as one desk. A Projects surface aggregates every active Room
into a portfolio view: cross-project needs-you in depth (not the flat
count of 171's aggregate but the rows themselves, grouped, ranked),
release readiness across Rooms (173's scorecard replicated at the
portfolio level), dependency alerts between projects (a PR in one repo
blocking a milestone in another), and every Room reachable from the
command deck (Article I: the Desk is the operating surface). The Monday
brief gains a portfolio section. The portfolio never leaves the machine
(Article III); every read is free (Article V:5, Article XI:5).

## Status

**PLANNED 0/10.**

**Depends on:** Phase 173 merged (the health signals and the release-
readiness scorecard this phase aggregates); Phase 177 merged (the
Thread at Work grounds the portfolio's ask on Watches and Room data).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday, 09:15. He opens the desk and sees one surface: PROJECTS. Three
Rooms, two red (overdue commitments), one green. He scans: "gov has
2 PRs waiting > 48h on Ania; infrastructure-api has a flaky CI streak;
the iOS companion has no blockers." He clicks the amber row; it opens
the Room. He never opened three Rooms to know.

Census facts from THE-TUESDAY-ARC.md section 0 that this phase pays:
`GET /api/desk/needs-you` (projects.py:380) iterates every active Room
per request (the N+1 that 171 caches and this phase deepens); the
Monday brief ran ONCE and aggregates nothing by project; no cross-Room
comparison, dependency view, or release-readiness aggregate exists;
`list_projects` (project_service.py:223) returns flat project payloads
with no Room health summary; the Door lists projects but shows no
portfolio aggregate; the command deck registers `desk.new-project` but
no portfolio surface.

## Scope

- In:
  - A PROJECTS surface on the Desk: a window showing every active Room
    in rows with their needs-you count, the first WHY, the release-
    readiness scorecard indicator (green/amber/red from 173), and the
    age of the oldest unresolved item; sorted by urgency.
  - Cross-project needs-you in depth: the portfolio's detail pane shows
    needs-you rows across all Rooms, grouped by project, ranked by
    severity and age; the same rows 171's shade shows, but with full
    depth and filtering.
  - Release-readiness aggregate: a portfolio-level scorecard (173's
    per-project scorecard replicated across Rooms; a red in any Room
    turns the aggregate red for that signal).
  - Dependency alerts: when a Watch entity in one Room references a
    resource (repo, issue, PR) that another Room also watches, and that
    entity is in a blocking state (review requested, CI failing, overdue
    commitment), the portfolio surfaces a dependency alert row.
  - The command deck gains a PORTFOLIO verb (opens the Projects surface)
    and per-Room verbs (opens that Room directly).
  - The Monday brief gains a PORTFOLIO section (per-project summary with
    the scorecard, the top needs-you, and the delta since last brief).
  - `GET /api/desk/portfolio` — the server-side aggregate that backs
    the surface (a deeper read than `GET /api/desk/needs-you`; reuses
    the cadence cache from 171).
  - The design on the library before build (canvas at 1440 + 393).
  - His walk on his desk: the portfolio with his real projects, the
    dependency alert if one exists, the Monday brief's portfolio section.
- Out:
  - Cross-desk portfolios (a portfolio is one desk, one owner).
  - External writes from the portfolio surface (reads only; the nudge
    lives in the Room, not the portfolio).
  - New Watch source types or new health signals beyond 173's set.
  - Project creation from the portfolio (the Door owns creation).
  - The companion's portfolio view (Phase 179).

## Exit criteria (evidence required)

- [ ] The PROJECTS surface shows every active Room with needs-you
      count, first WHY, release-readiness indicator, and oldest
      unresolved age; sorted by urgency.
- [ ] Cross-project needs-you rows display grouped by project, ranked
      by severity and age, with filtering.
- [ ] The release-readiness aggregate correctly summarizes 173's
      per-project scorecards.
- [ ] A dependency alert surfaces when a Watch entity referenced by two
      Rooms is in a blocking state.
- [ ] The command deck opens the portfolio surface and each Room
      directly.
- [ ] The Monday brief includes a PORTFOLIO section with per-project
      summary and delta.
- [ ] `GET /api/desk/portfolio` returns the aggregate payload using
      the cadence cache (response time < 100 ms from cache).
- [ ] The design on the canvas at 1440 + 393 is ratified by the owner
      before the build (Article IX.2; UX-CANON.md rule A.2).
- [ ] His walk on his desk: the portfolio with his real projects; his
      word (Article IX.4).
- [ ] Zero egress (Article III); every read free (Article V:5).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-178-01 | The design (the Portfolio's faces on the canvas before build) | backlog | [story-01-the-design](./story-01-the-design.md) | -- |
| HS-178-02 | The portfolio aggregate (the server-side cross-Room read, cadence-cached) | backlog | [story-02-the-portfolio-aggregate](./story-02-the-portfolio-aggregate.md) | -- |
| HS-178-03 | The Projects surface (the Desk window with Room rows, urgency sort, depth pane) | backlog | [story-03-the-projects-surface](./story-03-the-projects-surface.md) | -- |
| HS-178-04 | Release readiness across Rooms (the aggregate scorecard) | backlog | [story-04-release-readiness-across-rooms](./story-04-release-readiness-across-rooms.md) | -- |
| HS-178-05 | Dependency alerts (cross-Room entity references in blocking states) | backlog | [story-05-dependency-alerts](./story-05-dependency-alerts.md) | -- |
| HS-178-06 | The Monday brief portfolio section (per-project summary, delta, scorecard) | backlog | [story-06-the-monday-brief-portfolio](./story-06-the-monday-brief-portfolio.md) | -- |
| HS-178-07 | The command deck (PORTFOLIO verb + per-Room verbs) | backlog | [story-07-the-command-deck](./story-07-the-command-deck.md) | -- |
| HS-178-08 | The walk (his desk: the portfolio with his real projects; his word) | backlog | [story-08-the-walk](./story-08-the-walk.md) | -- |
| HS-178-09 | The docs (the portfolio in the architecture; the guide's projects section) | backlog | [story-09-the-docs](./story-09-the-docs.md) | -- |
| HS-178-10 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-10-the-close](./story-10-the-close.md) | -- |

## Where we are

PLANNED. Waiting for Phase 173 (the health signals and release-readiness
scorecard this phase aggregates) and Phase 177 (the Thread's grounding
on Room data). The recon is complete:

**The cross-Room read today:** `GET /api/desk/needs-you` (projects.py:380)
iterates every active project, calls `service.room()` per project, and
flattens needs-you items into one list. This is the nearest thing to a
portfolio view but it is flat (no grouping, no release-readiness, no
dependency detection, no depth pane). The response grows linearly with
project count and is not cadence-cached (171 owns that cache).

**The Room sections today:** `project_service.py:360-390` builds the
Room with 12 sections (resources, changes, review, needsYou, sources,
health, sinceRead, decisions, commitments, target, updates, steward).
Each section is fault-isolated (`_room_section`). The health section
(`_read_room_health`) exists but does not carry 173's signals yet (173
adds reviewer latency, issue aging, flaky CI, merge-queue depth).

**The Monday brief today:** `monday_brief_service.py:112` generates a
brief from all kernel operations, but with no per-project structure.
The brief ran ONCE on 2026-08-24 (1839 items). It has no portfolio
section, no per-project scorecard, no delta computation.

**The projects list today:** `GET /api/projects` (projects.py:65) returns
flat project payloads (`list_projects`, project_service.py:223). No
health summary, no needs-you count, no release-readiness indicator per
project in the list response.

**The command deck today:** `verbRegistry.ts` registers `desk.new-project`
but no portfolio verb and no per-Room open verb.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| Portfolio surface complexity for 3 projects | Medium | The surface must earn its place against "will you use this on a Tuesday?" -- at 3 projects the flat shade may be enough; the design story decides whether the portfolio is a full window or a deeper shade section | The owner says the shade is enough at his scale |
| Dependency detection false positives | Low | Dependency alerts only surface for Watch entities explicitly in blocking states (review requested, CI failing, overdue); never for shared-reference alone | The owner mutes dependency alerts within 48 h of his walk |
| Cross-Room read performance | Low | The cadence cache from 171 is the floor; `GET /api/desk/portfolio` reuses it; the portfolio aggregate is computed on the cadence tick, not per request | Response time > 200 ms from cache |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- Whether the portfolio is a full Desk window or a deeper section of
  the shade -- decided at design time from the owner's project count
  and the Tuesday question.
- Whether dependency alerts cross Watch source types (a GitHub PR
  blocking a Jira issue) or stay within one source -- decided at design
  time from the entity reference model.
- The Monday brief's portfolio section shape (per-project paragraph
  vs per-project scorecard row) -- decided at design time.
