# The Loop Closes -- the settled design (Phase 172, story 01)

> **ON THE CANVAS (2026-09-05)** -- thirteen boards published at
> https://claude.ai/code/artifact/b153c331-cd38-4856-b38b-837407dd6fba ;
> counsel reading; faces build to the ratified boards under the standing
> goal; **his word gates the merge** (stacked on 171's #554 on 170's #553).

The owner's Tuesday moment (THE-TUESDAY-ARC.md section 2, "Phase 172"):
the standup ends; within a minute the Room reads "Standup -- 2 decisions
-- 3 action items"; NEEDS YOU gains "Confirm: Marek owns the PostgreSQL
migration -- by Fri"; before the 1:1 with Ania her card reads "2 PRs
waiting on Ania 3+ days -- 1 commitment overdue -- last meeting 5 items,
2 open." The face canon binds (docs/internal/UX-CANON.md); the Door's,
the Arrival's, and the Heartbeat's grammar (Phases 169-171) are the
ratified precedent.

## D0 -- the Tuesday moment

09:35. The standup ends; he presses nothing. Within 60 seconds the
Room's SINCE YOU LOOKED gains a new line: `Standup -- 2 decisions -- 3
action items`. NEEDS YOU grows by five rows: two decisions as PROPOSALS
(`Confirm: adopt PostgreSQL 17 for the data layer`) and three action
items (`Confirm: Marek owns the PostgreSQL migration -- by Fri`), each
with `Confirm` / `Edit` / `Dismiss`. He confirms one decision -- the
decision_record and the commitment appear in DECISIONS & COMMITMENTS.
He drops a duplicate. He edits the third to fix the due date, then
confirms.

13:50. Before the 1:1 with Ania at 14:00 he opens her People card.
It reads: `2 PRs waiting on her 3+ days -- 1 commitment overdue -- last
meeting: 5 items, 2 open`. He walks in prepared.

Meanwhile, the meeting transcript mentioned `karolswdev/holdspeak`
and `GOV-412`. The Room shows a SUGGESTED source row: `SUGGESTED --
karolswdev/holdspeak -- from Standup` with `Add` / `Dismiss`. He taps
`Add`; a Watch source is created. GOV-412 matches a connected Jira
project; a second suggestion appears. He dismisses it.

The auto-run setting lives in Settings -> Meetings: `INTELLIGENCE --
AFTER EVERY MEETING` with a CycleGadget and the model host chip.


## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| Intelligence arms proposals, never fires an effect | Constitution Article IV | Every extracted decision/action item arrives as a PROPOSAL in NEEDS YOU; `Confirm` is the chokepoint; no auto-commit, no auto-write |
| The kernel confirms | Constitution Article V, XI | `Confirm` writes the decision_record and commitment through the kernel; every write admitted and receipted |
| People stays encrypted -- the join never leaks a name | Constitution Article III | The People-to-Watch resolver matches display_name / owner_alias to Watch assignee/reviewer strings inside the encrypted People boundary; no alias string appears in plaintext outside the People store; the match runs in memory at read time |
| The model's host named where intelligence runs | Constitution Article III | The auto-run status token names the model's host: `RAN -- 41 S -- 192.168.1.43 -- LAN` (the egress chip at the point of decision); the Settings row shows the model host chip |
| No counters of zero | UX-CANON.md rule A.8 | PROPOSALS section absent when no proposals exist; People section absent when no aliases resolve; the brief's Watch sections absent when no match; SUGGESTED absent when no mentions detected |
| Every verb the library Button | UX-CANON.md rule A.1 | `Confirm` / `Edit` / `Dismiss` on PROPOSAL cards; `Add` / `Dismiss` on suggested sources; `Open` on People cards; `Run intelligence` on meeting rows |
| One egress vocabulary | UX-CANON.md, 170 settled counsel M1 | `THIS DEVICE` / `192.168.1.43 -- LAN` / the cloud key name -- the same vocabulary 170 settles; the egress chip on the intel status token and the Settings row |
| No prose | UX-CANON.md rule A.3 | Tokens, verbs, counts, names. The PROPOSAL card is a row, not a paragraph; the brief is rows not sentences |
| No modals | UX-CANON.md rule A.4 | `Edit` unfolds inline (EditInPlace on the proposal text); the People card opens in the split or a well, never a modal |
| Design before build | UX-CANON.md rule A.2 | This document is the design; artboards at 1440 + 393 drawn from it; his word before any code |
| Ledger not gate | Owner ruling | Every intel run, every Confirm/Dismiss, every proposal arrival -- receipted via the service event ledger; no ceremony beyond the receipt |


## D2 -- the faces (element by element, species named)

### (a) The Room's PROPOSALS in NEEDS YOU

**Position:** inside the Room's NEEDS YOU section (ProjectRoomCore.tsx:312),
interleaved with existing needs-you rows by recency. Absent when no
proposals exist (rule A.8).

**Each PROPOSAL row** (SurfaceLedgerRow, 52px lead slot, wrap):

- Lead: a source emblem token -- `MTG` for a meeting-sourced proposal
  (surface-token[data-chip], caption step, 11 mono uppercase).
- Primary (15/600): the proposal verb + the extracted text.
  Decision: `Confirm: adopt PostgreSQL 17 for the data layer`.
  Action item: `Confirm: Marek owns the PostgreSQL migration -- by Fri`.
  The verb `Confirm:` is the row's accent mark (a `data-proposal`
  attribute on the row for styling -- slightly bolder or a left-edge
  token).
- Cells (secondary step, 12 mono):
  - Provenance token: `Standup -- 09:35` (the meeting title + the
    segment timestamp from CardProvenance.source_timestamp).
  - Speaker token: `Marek` (the speaker label from the segment, when
    available; absent when unknown -- no `UNKNOWN`).
  - Model host: EgressChip `192.168.1.43 -- LAN` (the model that
    extracted this item, at the point of decision; Article III).
- Trailing verbs (dense):
  - `Confirm` (Button primary dense) -- writes the decision_record and
    the commitment through the kernel; the row transitions to the
    DECISIONS & COMMITMENTS section.
  - `Edit` (Button ghost dense) -- unfolds EditInPlace under the row:
    a StringGadget with the extracted text (editable), the owner field,
    the due field, and a `Save & confirm` (primary dense) + `Cancel`
    (ghost dense) pair. The edited text is what gets persisted.
  - `Dismiss` (Button ghost dense) -- dismisses the proposal; no record
    created; the row disappears; a `proposal.dismissed` receipt written.

**Empty state:** the section shows no PROPOSAL rows (the existing
needs-you items may still appear). When the entire NEEDS YOU section
is empty, it is absent.

**Species used:** SurfaceLedgerRow (wrap), surface-token[data-chip],
EgressChip, Button (primary dense, ghost dense), EditInPlace,
StringGadget.

**Widths:** 1440 -- the row is two lines (primary wrapping, cells on
the second line, trailing verbs at the right of the first line). 393 --
cells stack under the primary; trailing verbs at the bottom of the row.

### (b) The meeting detail's NEEDS YOU after an auto-run

**Position:** the meeting detail view (HistoryCore.tsx), the NEEDS YOU
section (the outcomes table at the top of the detail, after the header).

**State tokens on the meeting row in the stream** (SurfaceLedgerRow cells,
secondary step):

- Auto-run complete: `RAN -- 41 S -- 192.168.1.43 -- LAN` (StateChip
  success `RAN`, a duration token, EgressChip with the model's host).
  The `41 S` is the wall-clock seconds the intel job took.
- Auto-run in progress: `RUNNING -- 192.168.1.43 -- LAN` (StateChip
  idle/spinner `RUNNING`, EgressChip).
- Auto-run failed: `FAILED -- no model assigned` (StateChip failure
  `FAILED`, the plainReason as a muted token). When no model is
  assigned (170's Concierge not run): `FAILED -- NO MODEL` (StateChip
  warning `FAILED`, the failure is honest; Article VI).
- Auto-run skipped (unlinked meeting): no state token; the existing
  `OFF` + `Run intelligence` verb (170's design) applies.
- The NEEDS YOU caption row gains the count of extracted items:
  `NEEDS YOU -- 5` (or absent when zero).

**Rows in the detail's NEEDS YOU** (after intel completes): the same
PROPOSAL rows as in the Room's NEEDS YOU (decisions and action items
from the intel plugins), scoped to this meeting. The `Confirm` /
`Edit` / `Dismiss` verbs work identically.

**Species used:** StateChip (success, idle, failure, warning),
EgressChip, surface-token[data-chip], SurfaceLedgerRow (wrap), Button
(primary dense, ghost dense).

### (c) The arrival's NEEDS YOU gaining `Confirm:` rows

**Position:** the arrival's NEEDS YOU section (ChairHome.tsx:553),
where the 170 design already merges Room items and Door items.

**New row type:** PROPOSAL rows from all active Rooms, interleaved by
recency. Same grammar as (a): lead emblem `MTG`, primary `Confirm:
...`, provenance token, `Confirm` / `Edit` / `Dismiss`. The source emblem
carries the project name as a faint token when more than one Room
contributes (the 170 design's existing rule).

**Empty:** the section's empty state follows the 170 design (absent;
the headline says `Nothing needs you`).

**Species used:** same as (a).

### (d) The 1:1 card on People (the brief enrichment)

**Position:** the Prep lens on PeopleCore.tsx:288 (the existing brief
view). The enrichment adds Watch-derived sections BELOW the existing
sections (commitments, agenda, grounding notes, linked meetings).

**New sections** (each a SurfaceSection with its own caption):

1. `PRS WAITING` (caption + count, e.g., `PRS WAITING -- 2`):
   SurfaceLedgerRow per PR waiting on this person as a reviewer (from
   Watch entities where `reviewRequests` matches via the People
   resolver). Each row:
   - Primary (15/600): the PR title (truncated, ellipsis).
   - Cells: `3+ DAYS` (days since review requested, secondary step;
     a warning token when > 3 days) -- `karolswdev/holdspeak #612`
     (the repo/PR reference, secondary step).
   - Trailing: `Open` (Button ghost dense -- opens the PR URL).
   Absent when zero (rule A.8).

2. `OPEN ASSIGNMENTS` (caption + count):
   SurfaceLedgerRow per Jira issue assigned to this person (from Watch
   entities where `assignee` matches via the People resolver). Each row:
   - Primary (15/600): the issue summary.
   - Cells: `GOV-412` (the issue key) -- `IN PROGRESS` (the status).
   - Trailing: `Open` (Button ghost dense).
   Absent when zero (rule A.8).

3. `COMMITMENTS` (the existing section, now with an `OVERDUE` count
   token when any commitment is past due):
   - When overdue: `COMMITMENTS -- 3 -- 1 OVERDUE` (the `1 OVERDUE` as
     a warning token, secondary step).
   - The existing commitment rows stay.

4. `LAST MEETING` (the existing linked meetings section, now with an
   open-items summary on the section caption):
   - `LAST MEETING -- Sprint Review -- 5 items, 2 open` (the item
     count from the meeting's action_items; the `2 open` as a muted
     token).
   - The existing meeting rows stay.

**The People card summary line** (the one-line brief visible on the
People ledger row and the Room's PEOPLE section): `2 PRs waiting 3+
days -- 1 overdue` (the first two most actionable facts, tokens only).
When only one fact: `1 PR waiting 5 days`. When no Watch data and
no overdue commitments: the summary is absent (the name stands alone).

**Species used:** SurfaceSection (caption + count),
SurfaceLedgerRow, surface-token[data-chip], Button (ghost dense),
StateChip (warning for overdue).

**Widths:** 1440 -- sections stack vertically; rows are single-line.
393 -- same stacking; PR title truncates earlier; `Open` stays trailing.

### (e) The suggested source row in the Room's SOURCES

**Position:** inside the Room's SOURCES section (ProjectRoomCore.tsx),
ABOVE the existing Watch source rows (a suggestion needs you, so it leads). Absent when no suggestions exist
(rule A.8).

**Each suggested source row** (SurfaceLedgerRow):

- Lead: a `SUGGESTED` token (surface-token[data-chip], caption step,
  muted).
- Primary (15/600): the repo or issue reference --
  `karolswdev/holdspeak` or `GOV-412`.
- Cells: `from Standup` (secondary step, muted -- the meeting that
  mentioned it) -- the provider glyph (GitHub logo or Jira logo, via
  the existing provider glyph system).
- Trailing:
  - `Add` (Button primary dense) -- creates a Watch source on the
    Room via the existing add-source machinery (project_door_service
    or the project setup path). After Add, the suggested row
    disappears and a real Watch source row appears in SOURCES.
  - `Dismiss` (Button ghost dense) -- persists the dismissal so the
    same suggestion does not recur on future intel runs for the same
    meeting.

**Dedup rule:** a suggestion for a repo/issue that already has a Watch
source on this Room is suppressed (never shown). A suggestion for a
repo/issue already dismissed is suppressed.

**Species used:** SurfaceLedgerRow, surface-token[data-chip], Button
(primary dense, ghost dense).

### (f) The auto-run setting (Settings -> Meetings)

**Position:** inside the Meetings module detail face (opened from the
Settings hub's `MEETINGS` row; the 170 design's hub grammar).

**The row** (SurfaceLedgerRow):

- Primary (15/600): `Intelligence`.
- Cells:
  - CycleGadget: `AFTER EVERY MEETING` / `OFF` / `AFTER ROOM MEETINGS`.
    Default: `AFTER ROOM MEETINGS` (intelligence runs automatically only
    for meetings linked to a Room; the Room link is the consent act --
    Article V). `AFTER EVERY MEETING` enables auto-intel for all
    meetings. `OFF` disables auto-intel (the existing manual-only
    behavior).
  - EgressChip: the model host (from the intelligence model assignment
    -- 170's Concierge; e.g., `192.168.1.43 -- LAN` or `THIS DEVICE`).
    When no model assigned: StateChip `NO MODEL` (warning).
- Trailing: `Run all` (Button ghost dense -- enqueues intel jobs for
  all meetings that have never run intelligence; a batch version of
  `Run intelligence`). Absent when all meetings have run.

**The hub row update** (the Meetings row on the Settings hub,
settingsPrefs.tsx): the state token reflects the auto-run setting.
`MEETINGS -- INTELLIGENCE ROOM-LINKED` / `MEETINGS -- INTELLIGENCE
AFTER EVERY MEETING` / `MEETINGS -- INTELLIGENCE OFF` (warning when
off). The existing `INTELLIGENCE OFF` warning (170's design) stays as
is for the `OFF` case.

**Species used:** SurfaceLedgerRow, CycleGadget, EgressChip, StateChip
(warning), Button (ghost dense).


### All faces: dimensions

Every artboard at 1440 (the window at its design width) and 393 (the
glass / phone-width container query on `surface`). Three type steps
minimum per face: display (26/650) for the Room headline or arrival
headline, primary (15/600) for row titles and proposal text, secondary
(12 mono) / caption (11 mono uppercase) for tokens, section labels, and
provenance.


## D3 -- the wire

### The trigger after capture

**Seam:** `meeting_session/persistence.py:87-93`. Today, intel enqueues
only when `self.intel_enabled AND self.intel_deferred_enabled AND
state.intel_status == "queued" AND state.segments`. The per-meeting
`intel_status` defaults to `disabled` (db/schema.py:31). The census:
6/8 meetings have `intel_status = disabled`.

**What 172 adds:** after `session.save()` completes in
`meeting_glue.py:422-426`, a NEW conditional block:

- Check if the saved meeting is linked to a Room via
  `meeting_projects` (project_service.py:262, via
  `db.projects.get_meeting_projects(meeting_id)`).
- If linked AND the global auto-intel setting is `AFTER ROOM MEETINGS` or
  `AFTER EVERY MEETING`, AND no intel job already exists for this
  meeting's transcript hash (dedup via
  `db.intel.get_intel_job(meeting_id)` checking transcript_hash):
  enqueue an intel job via `db.intel.enqueue_intel_job(meeting_id,
  transcript_hash=..., reason="auto-intel: Room-linked")`.
- The model assignment comes from 170's Concierge
  (Config.load().meeting.intel_realtime_model); if no model is
  assigned, the job queues with status `no_model_assigned` and the
  Room shows `FAILED -- NO MODEL`.
- Every enqueue writes a `meeting.auto_intel_enqueued` receipt via
  the service event ledger (Article XI).

**Seam detail:** the project association already happens at
`meeting_glue.py:447` via `_associate_meeting_with_projects(meeting_id)`
which calls `project_detector` to match the meeting to projects. The
auto-intel trigger runs AFTER this association, so `meeting_projects`
is populated before the check.

**The deferred queue worker** (`intel_queue.py:592,
IntelQueueWorker`) already picks up queued jobs. No new worker needed;
the existing `_deferred_plugin_queue_loop`
(web_runtime.py:519) processes them.

### The extractor (which plugin)

**Two plugins extract the structured items 172 needs:**

1. `decision_capture` (plugins/builtin/decision_capture.py:179) --
   kind="synthesizer"; extracts decisions + open questions with
   provenance (source_timestamp from segment boundaries). Output shape:
   `{decisions: [{text, rationale, source_timestamp, ...}], open_questions: [...]}`.

2. `action_owner_enforcer` (plugins/builtin/action_owner_enforcer.py:139)
   -- kind="validator"; extracts action items with owner/due/gap. Output
   shape: `{action_items: [{task, owner, due, gap}]}`.

Both are registered in `plugins/builtin/__init__.py:127,139` and run as
part of the deferred intel pipeline (`drain_intel_queue` ->
`process_next_intel_job`). Their artifacts are persisted in the
`plugin_artifacts` table.

**No new plugin is needed.** The bridge (story 03) reads the persisted
artifacts from these two plugins after intel completes and maps them to
FollowThroughCards.

### The proposal bridge (extracted items -> PROPOSALS -> Confirm)

**The gap today:** plugin artifacts persist as opaque JSON in
`plugin_artifacts`. Nothing reads them to create FollowThroughCards or
NEEDS YOU proposals. The `actuator_service.py` proposal path is for
EXTERNAL effects (Slack, GitHub, webhook) -- not for internal
propose-approve of extracted decisions.

**What 172 builds:** a new method on FollowThroughService (or a thin
bridge service) that runs after an intel job completes:

1. Read plugin artifacts for the meeting from `decision_capture` and
   `action_owner_enforcer`.
2. For each extracted decision: create a FollowThroughCard with
   `source="intel_proposal"`, `lane="unassigned"`, provenance from the
   plugin artifact (meeting_id, source_timestamp, speaker label).
   The card carries a `proposal_status` field: `pending` / `confirmed` /
   `dismissed`.
3. For each extracted action item: create a FollowThroughCard with
   `source="intel_proposal"`, `lane` derived from owner/due
   (unassigned when no owner, now when owner+due, waiting when
   owner+no-due), provenance from the plugin artifact.
4. These cards appear in the Room's NEEDS YOU via the existing
   `follow_through_service.board()` (filtered by `project_id` via
   `meeting_projects`).
5. `Confirm` on a decision card: calls
   `follow_through_service.commit_decision(decision_id, owner, due_at)`
   which creates an `action_item` + `decision_commitment` through the
   kernel (follow_through_service.py:263-320). The card transitions
   from NEEDS YOU to DECISIONS & COMMITMENTS.
6. `Confirm` on an action item card: similar -- creates an `action_item`
   row directly (the action_owner_enforcer already has owner/due).
7. `Dismiss`: marks the card as `dismissed` (a new status on the proposal
   row or the FollowThroughCard); the card disappears from NEEDS YOU.
8. `Edit`: allows amending text/owner/due inline before Confirm.

**Schema addition:** a `follow_through_proposals` table (or a
`proposal_status` column on `action_items` / a new lightweight table):

```
follow_through_proposals (
  id TEXT PRIMARY KEY,
  meeting_id TEXT NOT NULL,
  project_id TEXT,
  source_plugin TEXT NOT NULL,       -- "decision_capture" | "action_owner_enforcer"
  source_artifact_id TEXT,
  extracted_text TEXT NOT NULL,
  extracted_owner TEXT,
  extracted_due TEXT,
  proposal_status TEXT NOT NULL DEFAULT 'pending',  -- pending | confirmed | dismissed
  segment_timestamp TEXT,
  speaker_label TEXT,
  model_host TEXT,                   -- the egress host at extraction time
  created_at TEXT NOT NULL,
  resolved_at TEXT
)
```

The FollowThroughService.board() gains a fourth source: these proposal
rows (status=pending) mapped to FollowThroughCards with
`source="intel_proposal"`. Confirmed proposals create real action_items
/ decision_records and the proposal row flips to `confirmed`. Dropped
rows flip to `dismissed`.

**Dedup:** a proposal is unique by (meeting_id, source_plugin,
extracted_text hash). Re-running intel on the same meeting with the
same transcript hash (already deduped at the enqueue level via
intel_queue.py) does not create duplicate proposals. If intel is re-run
with a different transcript (e.g., after editing), new proposals may
appear; old pending ones for the same meeting are marked `superseded`.

### The People-to-Watch resolver

**Seam:** `people_service.py:707` --
`resolve_relationship_by_owner(owner_string)`. Already exists. Does
case-insensitive match of `owner_string` against `owner_aliases` on
all non-archived relationships.

**What 172 adds:** a new method
`resolve_relationship_by_watch_identity(identity_string)` that:
1. Calls the existing `resolve_relationship_by_owner(identity_string)`.
2. If no match by alias, also checks `display_name` (case-insensitive).
3. Returns `{state, relationship}` (same shape as existing).

**The match inputs from Watch entities:**
- GitHub PRs: `reviewRequests` (watch_sources.py:108) -- a list of
  reviewer login strings (e.g., `["karolswdev"]`), extracted via
  `_reviewer_names` (watch_sources.py:41-49) which pulls `login`,
  `name`, or `slug` from the reviewer dict.
- Jira issues: `assignee` (watch_sources.py:368) -- the assignee's
  display name (e.g., `"Karol Sane"`).

**The boundary:** the match runs INSIDE the encrypted People store
(in-memory). The resolver is called at read time from the 1:1 brief
(story 05) and the People card in the Room (story 07). It never
writes. No alias string appears in plaintext outside the People store
(Article III).

**Owner aliases as the linking mechanism:** the owner links a GitHub
login or Jira display name as an alias via the existing
`link_owner_alias` (people_service.py:637). Example:
- Relationship: Ania (display_name="Ania Kowalska")
- Aliases: ["ania-k"] (GitHub login), ["Ania Kowalska"] (Jira name)
- Watch PR reviewer: "ania-k" -> resolves to Ania
- Watch Jira assignee: "Ania Kowalska" -> resolves to Ania

### The 1:1 brief enrichment

**Seam:** `people_service.py:364` -- `one_on_one_brief()`. Today
returns: open_commitments, agenda_items, grounding_note_count,
linked_meetings, unlinked_meeting_count.

**What 172 adds:** a new `watch_summary` section in the brief return:

```python
{
  "prs_waiting": [
    {"title": "Fix migration", "repo": "karolswdev/holdspeak",
     "pr_number": 612, "days_waiting": 5, "url": "..."}
  ],
  "oldest_waiting_days": 5,
  "open_assignments": [
    {"summary": "PostgreSQL migration", "key": "GOV-412",
     "status": "In Progress", "url": "..."}
  ],
  "commitments_overdue_count": 1,
}
```

**Wire:** the brief method gains an optional `watch_db` parameter (the
project DB for reading Watch snapshots). It:
1. Calls `resolve_relationship_by_watch_identity` with the
   relationship's display_name and each owner_alias.
2. For each matched identity string, reads Watch entity snapshots
   (via `project_service._entities()` on persisted snapshots --
   project_service.py:505 or similar) filtered by that identity.
3. For GitHub entities: filters where `reviewRequests` contains the
   matched identity AND `state` is open -> `prs_waiting`.
4. For Jira entities: filters where `assignee` matches -> `open_assignments`.
5. No new Watch evaluations triggered (reads are free; Article V.5).

**The brief is transient:** no writes to any store (the 138 law).

### The suggested source

**Seam:** `project_detector.py:52` -- `ProjectDetectorPlugin`. Today
scores transcript windows against project keyword/member lists. It
does NOT produce source suggestions.

**What 172 builds:** a post-intel step (not a new plugin; a service
method) that scans the intel artifacts for recognizable repo and issue
mentions:

1. **Repo detection:** regex for `owner/repo` patterns (GitHub) in the
   transcript text. The regex: `[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+` with
   context (preceded by whitespace or URL prefix).
2. **Issue detection:** Jira-style keys `[A-Z]+-[0-9]+` matched
   against connected Jira projects (from `watch_sources.py`'s
   JiraWatchSource -- the connected site's project keys provide the
   prefix set).
3. Each match becomes a row in a `source_suggestions` table:
   ```
   source_suggestions (
     id TEXT PRIMARY KEY,
     project_id TEXT NOT NULL,
     meeting_id TEXT NOT NULL,
     provider TEXT NOT NULL,       -- "github" | "jira"
     reference TEXT NOT NULL,      -- "karolswdev/holdspeak" | "GOV-412"
     status TEXT DEFAULT 'pending', -- pending | accepted | dismissed
     created_at TEXT NOT NULL
   )
   ```
4. `Add` creates a Watch source using the existing add-source flow.
5. `Dismiss` sets `status = dismissed`.
6. Dedup: a suggestion matching an existing Watch source on the same
   Room is suppressed. A dismissed suggestion is suppressed for the
   same (project_id, reference) pair.

### The wire summary (file:line)

| Seam | File:line | Role |
|---|---|---|
| stop_capture | meeting_service.py:360 | The user's stop verb; delegates to meeting_glue |
| _stop_active_meeting | runtime/meeting_glue.py:367 | Stops capture, saves, associates projects |
| session.save | meeting_session/persistence.py:77 | Persists meeting + conditionally enqueues intel |
| intel_status default | db/schema.py:31 | Per-meeting toggle; defaults to `disabled` |
| _associate_meeting_with_projects | runtime/meeting_glue.py:447 | Links meeting to detected projects (runs before auto-intel trigger) |
| enqueue_intel_job | meeting_session/persistence.py:92, db/meetings.py:813 | Enqueues the intel job |
| drain_intel_queue | intel_queue.py:592 | Picks up queued jobs and runs them through plugins |
| decision_capture plugin | plugins/builtin/decision_capture.py:179 | Extracts decisions + open questions |
| action_owner_enforcer plugin | plugins/builtin/action_owner_enforcer.py:139 | Extracts action items with owner/due |
| plugin registration | plugins/builtin/__init__.py:127,139 | Both plugins registered in the builtin set |
| FollowThroughCard | services/follow_through_service.py:66 | The card dataclass with provenance |
| FollowThroughService.board | services/follow_through_service.py:128 | Aggregates cards from action_items, loops, decisions, People |
| commit_decision | services/follow_through_service.py:263 | Creates action_item + decision_commitment from accepted decision |
| create_from_meeting | services/decision_record_service.py:73 | Mints a decision_record from a meeting decision |
| resolve_relationship_by_owner | services/people_service.py:707 | Case-insensitive alias match inside encrypted store |
| link_owner_alias | services/people_service.py:637 | Links a string as an alias on a relationship |
| one_on_one_brief | services/people_service.py:364 | Computes transient 1:1 brief (never writes) |
| _reviewer_names | services/watch_sources.py:41 | Extracts reviewer login names from GitHub PR entities |
| Jira assignee | services/watch_sources.py:368 | The `assignee` field on Jira issue entities |
| ProjectDetectorPlugin | plugins/project_detector.py:52 | Scores transcript against projects (read-only) |
| Room DECISIONS & COMMITMENTS | web/src/features/project-room/ProjectRoomCore.tsx:576 | Renders decisions and commitments in the Room |
| Room NEEDS YOU | web/src/features/project-room/ProjectRoomCore.tsx:312 | Renders needs-you items in the Room |
| Arrival NEEDS YOU | web/src/desk/chair/ChairHome.tsx:553 | Renders needs-you items on the arrival |
| Meeting detail intel | web/src/pages/cores/HistoryCore.tsx:139 | The Run intelligence verb |
| People Prep lens | web/src/pages/cores/PeopleCore.tsx:288 | The 1:1 brief view |
| SystemShade PROJECTS | web/src/desk/components/SystemShade.tsx:390 | The shade's PROJECTS section (171) |
| MeetingConfig | holdspeak/config/meeting.py:16 | intel_enabled, intel_realtime_model, intel_provider |
| actuator_proposals table | db/schema.py:429 | The external actuator proposal path (not used for internal proposals) |
| decisions table | db/schema.py:384 | Meeting-derived decisions |
| action_items table | db/schema.py:98 | Meeting-derived action items |
| decision_commitments table | db/schema.py:224 | Links decisions to action items as commitments |


## D4 -- counsel's hunts

### H1: A proposal that fires

The most dangerous defect: a plugin-extracted decision is auto-committed
as a real decision_record + commitment without the owner pressing
`Confirm`. Article IV: voice arms, it does not fire. Hunts:
- The auto-intel trigger must ONLY enqueue, never commit.
- The proposal bridge must ONLY create pending proposal rows, never
  call `commit_decision` without a user gesture.
- The `Confirm` verb must be the ONLY path to `commit_decision`.
- Test: a rig that boots a hub, runs auto-intel, and asserts that
  `decision_records` count = 0 and `decision_commitments` count = 0
  after intel completes (only proposals exist, no records).

### H2: A name leaking

The People-to-Watch resolver matches inside the encrypted boundary.
Hunts:
- The match result (the relationship with its aliases) must never
  appear in API responses that leave the People boundary.
- The brief's `watch_summary` must contain only Watch entity data
  (PR titles, issue keys) -- never the alias string that matched.
- The suggested source row must show the repo/issue reference, never
  the person who mentioned it.
- Test: assert that the brief API response contains no `owner_alias`
  fields and no raw alias strings.

### H3: A duplicate proposal per re-run

If the owner clicks `Run intelligence` a second time on the same
meeting (or if auto-intel re-triggers), the same proposals must not
appear twice. Hunts:
- The dedup at enqueue level (transcript_hash) prevents re-running on
  the same transcript.
- If the transcript changes and intel re-runs, the proposal bridge
  must check for existing pending proposals with the same
  (meeting_id, source_plugin, extracted_text) before creating new ones.
- Test: call `Run intelligence` twice on the same meeting; assert
  proposal count = N (not 2N).

### H4: The auto-run's cost on a cloud model

If the owner assigns a cloud model (e.g., Claude via API) for
intelligence, every meeting auto-triggers a cloud call. Hunts:
- The Settings row must show the model's EgressChip prominently:
  `INTELLIGENCE -- AFTER EVERY MEETING -- CLAUDE -- CLOUD` (the egress
  chip is the warning).
- The status token on the meeting row must name the cloud host:
  `RAN -- 12 S -- api.anthropic.com -- CLOUD`.
- Consider: a confirmation prompt before the first cloud auto-run?
  No -- the assignment is the consent (Article V); the egress chip is
  the disclosure (Article III). But the cost is honest: the Settings
  row should show `~$0.02 per meeting` (estimated from the last run's
  token count, if available) as a muted secondary token.

### H5: The Room's zero states

When proposals exist but all are dismissed/confirmed, the NEEDS YOU
section may show zero items. Hunts:
- Dropped and confirmed proposals are excluded from the board query.
- The NEEDS YOU section is absent when zero (rule A.8).
- When the Room has zero PROPOSALS but has other needs-you items (from
  Watches), the section shows only those.
- Test: confirm all proposals; assert NEEDS YOU shows only Watch items.


## D5 -- the walk on his desk

The walk proves the Tuesday moment on his real desk with his real
meetings and his one Room.

### Beat 1: The auto-run fires

His real meetings: the "Already titled" standups and the Sprint Reviews.
He links one to his Room. He stops capture. Within 60 seconds the
meeting row's state token changes from `OFF` to `RUNNING` to `RAN -- N
S -- 192.168.1.43 -- LAN`. Stopwatch on the latency from stop to `RAN`.

### Beat 2: PROPOSALS appear in NEEDS YOU

After intel completes, the Room's NEEDS YOU gains PROPOSAL rows. The
proposals show the extracted text, the meeting title, the speaker (when
available), and the model host. He counts them; they match the meeting's
content.

### Beat 3: Confirm and Dismiss

He confirms one decision. The decision_record and commitment appear in
DECISIONS & COMMITMENTS. He drops one duplicate. No record created.

### Beat 4: Edit then Confirm

He edits one proposal (fixes the due date). He confirms. The edited
text is what appears in DECISIONS & COMMITMENTS.

### Beat 5: The People card

Before his 1:1: the People card (Prep lens) shows PRs waiting on the
person, days since oldest, open Jira assignments, overdue commitments.
The data matches the real Watch entities. He verifies the alias link
resolves correctly.

### Beat 6: A suggested source

The meeting transcript mentioned a repo. The Room's SOURCES shows a
SUGGESTED row. He accepts one; a Watch source appears. He dismisses
another; it disappears and does not recur.

### Beat 7: People reachable at 393

At 393: the Room shows People rows (resolved from Watch entities). He
taps one; the People card opens with the enriched brief.

Seven beats at both widths (1440 + 393). Stopwatch per face. His words
verbatim. His verdict.


## Honest sizes

| Story | Size | Rationale |
|---|---|---|
| 01 The design | S | Artboards from this doc; no code |
| 02 The auto-intel trigger | M | A conditional block after session.save + the Settings CycleGadget + the per-meeting intel_status migration for Room-linked meetings; the deferred queue already exists |
| 03 The proposal bridge | L | The new `follow_through_proposals` table + the bridge from plugin artifacts to FollowThroughCards + the Confirm/Edit/Dismiss verbs on the Room face + the dedup logic; the first time extracted intelligence becomes actionable |
| 04 The People resolver | S | One new method on PeopleService wrapping the existing `resolve_relationship_by_owner` + display_name check |
| 05 The brief enrichment | M | The `watch_summary` section on `one_on_one_brief` + the Watch entity reads through the resolver + the Prep lens face update |
| 06 The suggested source | M | The transcript scan (regex, not LLM) + the `source_suggestions` table + the Room face rows + the Add/Dismiss verbs |
| 07 People in the Room and shade | M | The PEOPLE section in the Room + the People card from the Room + the shade entry point at 393 + the resolver integration |
| 08 The walk | S | His desk, seven beats; no code |
| 09 The docs | S | Re-shot for the new faces + the loop-closes Mermaid diagram |
| 10 The close | S | Gates, sweep, the PR |


## Addendum — the orchestrator's rulings on the boards (2026-09-05)

Read beside the thirteen story-01 shots; each ruling binds the build.

- **One verb word.** `Dismiss` everywhere a proposal or a suggestion is
  declined; `Drop` is retired from this design. `Dismiss` writes no
  record beyond the receipt.
- **The third verb is a Button.** A collapsed PROPOSAL row carries
  `Confirm` (primary dense) · `Edit` (ghost dense) · `Dismiss` (ghost
  dense). Row text is never a trigger (UX-CANON A.1).
- **The lead slot is the source.** Every ledger row's 52px lead slot
  carries the source emblem (`MTG`, `GH`, `J`); state lives in the
  caption (`CONFIRMED 09:41` in success color; `SUGGESTED` as a token).
  No checkmarks, no words in the emblem slot.
- **No clipped text.** Proposal text wraps to two lines at 640 with
  the verbs top-aligned; the phone stacks verbs under the caption.
- **`was:` lists only what changed.** After `Edit` → `Save & confirm`,
  the confirmed row's `was:` caption names only the fields the owner
  changed (text, owner, due), never the whole original when one field
  moved.
- **The arrival's `Open`** opens the Room scrolled to that proposal;
  `Confirm` on the arrival commits through the kernel exactly as in
  the Room (one path, one receipt).
- **Speaker token** appears only on the Room's two-line rows and only
  when known; compact meeting-detail rows carry none.
- **No pronoun from a name.** The 1:1 card reads `N PRS WAITING ON
  {display name}`; if the name will not fit, `N PRS WAITING`. The
  product never infers she/he from a name.
- **Suggestions dedup case-insensitively** against existing sources of
  the same provider (GitHub owner/repo is case-insensitive; Jira keys
  are upper-cased before compare). A suggestion that matches an
  existing source is never raised; the sample on the board must obey
  the same law.
- **The Meetings settings module's display step** is the auto-run
  state as a sentence-case fact (`After room meetings` · `Off` · `After
  every meeting`), never the word `Meetings` (UX-CANON A.7); the
  Intelligence row keeps the CycleGadget with `OFF` · `AFTER ROOM
  MEETINGS` · `AFTER EVERY MEETING`.
- **The People card display** is the person's name in the display
  step's normal color (no problem state on the card); wings Prep ·
  Now · History at 640, Prep · Now at 393.


## Addendum — counsel RATIFY-W-C (2026-09-05) and the orchestrator's rulings

Counsel read the thirteen boards, the doc, and the wire: **RATIFY-W-C**,
three conditions, nine findings. Each is ruled here; the boards win
where text and board disagreed, except where a board broke a law.

**C1 — two prefixes.** Decision-kind proposals lead with `Decide:`;
action-kind proposals lead with `Confirm:` (both accent, the rest of
the text primary). D2.a's single `Confirm:` is superseded. The prefix
is the kind; nothing else announces it.

**C2 — the verb set per face.** Room proposal rows: `Confirm` · `Edit`
· `Dismiss`. Meeting-detail NEEDS YOU rows: `Confirm` · `Dismiss`
(Edit lives in the Room; the meeting is where you read, the Room is
where you shape). Arrival rows: `Confirm` · `Open` (triage; Open lands
in the Room scrolled to the proposal). D2.b and D2.c read accordingly.

**C3 — the People card.** The Prep wing is the summary: one row per
concern (`N PRS WAITING ON {name}` · `N ASSIGNMENTS OPEN` · `N
COMMITMENTS OVERDUE` · `LAST MEETING`), each with its tokens and one
`Open`. `Open` on a summary row switches to the **Now** wing, which
lists the per-entity SurfaceLedgerRows (one per PR, one per issue,
one per commitment) each with its own `Open` to the source URL. Inline
reference tokens on a summary row cap at three, then `+N`. D2.d's
per-entity rows live in Now, not Prep. Rows absent at zero.

**F5 — after an edit.** The confirmed row's caption carries the changed
fields as `WAS …` tokens after the state: `BY WED · CONFIRMED 09:41 ·
WAS BY FRI`; text edits read `WAS "…"` truncated to 40 chars. Nothing
when nothing changed.

**F6 — OPEN ASSIGNMENTS** is a fourth Prep summary row of the same
species (`1 ASSIGNMENT OPEN · KAN-7 · OVERDUE`), absent at zero. The
board omitted it; the builder ships it and shoots it.

**F7 — `Run all`** is cut from this phase (a batch effect that may
egress to a paid host; the per-meeting `Run intelligence` stands).
D2.f loses the verb; parked in BACKLOG.

**F8 — speaker token.** On the Room's two-line proposal rows the
caption reads `from Standup 09-05 · MAREK` when the speaker is known;
nothing when unknown (no UNKNOWN). Same species as the provenance
token.

**F9 — SOURCES counts sources.** The `SOURCES N` caption counts
accepted sources only; a SUGGESTED row sits above the count's rows
and is not counted (UX-CANON A.8). Board corrected.

Counsel's three questions for the owner are carried to the handover
(prefix vocabulary; the People card's summary-then-Now shape; whether
assignments belong on the card). The faces build to these rulings; his
word gates the merge.

**Story 07 boards (RoomPeople, RoomPeoplePhone, ShadePeople) — rulings.**
The display name is shown as stored, in the Room and in the shade;
no first name is derived from it (a derivation is an inference, like a
pronoun). The shade's PEOPLE lane is scoped by caption (`PEOPLE · Q4
PLATFORM`) and its tokens are terse (`1 OVERDUE`); the Room's are full
(`1 ASSIGNMENT OVERDUE`). A person lists only with at least one
non-zero token; the section is absent at zero.


## Addendum — counsel on the BUILT phase (2026-09-05): RATIFY-W-C, paid

Two conditions, eight findings; every design-stage ruling (C1–C3,
F5–F9) verified PAID in the build. The build-stage conditions:

- **C1 (P0) — the bridge was never called.** `bridge_meeting_artifacts`
  and the suggestion scanner had no production call site; six green
  rigs had seeded proposals by SQL. Paid: the intel completion seam
  (`intel_queue.py` `_on_intel_complete`) runs the bridge, then the
  scanner per linked Room, then marks the needs-you aggregate dirty —
  each in its own failure boundary, idempotent on the fingerprint; an
  end-to-end test drives job → rows → route → arrival count, twice.
  **Law:** a new service entry point needs a production CALL SITE and
  one test through the real seam before a phase closes.
- **C2 — the RAN header proved from a recorded job** (`RAN · 41 S ·
  192.168.1.43 · LAN`); the rig seeds the `intel_jobs` row.
- **F-P2s paid:** the `LAST RAN hh:mm · N S` receipt on the Intelligence
  row (the board rules); `<ul>` children are `<li>`; one `egressFor`
  helper; the 393 People shot scrolls to its section; the arrival
  Confirm rig; the auto-trigger exercised with seeded Rooms.
- **The arrival's freshness:** a durable dirty marker
  (`desk_projection_state` · `needs_you_aggregate`) written on
  completion / Confirm / Dismiss; the cache compares it on every read.
  No cross-thread singleton, no 15-minute fallback.

Counsel's three questions for the owner are in the handover.
