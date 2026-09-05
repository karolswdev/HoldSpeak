# Phase 172 — The Loop Closes: final summary (DRAFT — stacked on 171 (#554) on 170 (#553); closes on his word)

## What shipped

- **The design (01):** settled-design-loop-closes.md + sixteen boards
  (the Room's proposals · Edit in place · 393; the meeting after the run
  · 393; the arrival's Confirm rows · 393; the 1:1 card · 393; SOURCES
  with SUGGESTED · 393; Settings → Meetings · 393; People in the Room ·
  393; the shade's PEOPLE lane). Canvas
  https://claude.ai/code/artifact/b153c331-cd38-4856-b38b-837407dd6fba.
  Two bounces paid before counsel; counsel RATIFY-W-C (three conditions,
  nine findings) ruled in the second addendum: two prefixes (`Decide:` ·
  `Confirm:`); one verb set per face (Room Confirm · Edit · Dismiss;
  meeting Confirm · Dismiss; arrival Confirm · Open); the 1:1 card is
  summary rows then the Now wing; `WAS` tokens for changed fields; the
  assignments row; `Run all` cut; the speaker token; `SOURCES N` counts
  accepted sources. Laws: Dismiss never Drop; the third verb is a
  Button; the lead slot is the source; no clipped text; no pronoun (or
  first name) from a name; suggestions dedup case-insensitively; the
  display step is a fact; a host is RECORDED at run time, never resolved
  from config at read.
- **The wire (02 · 03 · 04 · 05 · 06 · 07):** `intelligence_auto`
  (off | room_linked | every) and the trigger after Room association
  (`_maybe_auto_enqueue_intel`, dedup on an existing job, receipted);
  `follow_through_proposals` (schema 73; fingerprint dedup; state
  proposed | confirmed | dismissed; `decision_record_id` ·
  `commitment_id`); the bridge from the two extractors' opaque artifacts
  to proposals; **Confirm writes the whole chain the Room reads** —
  `decisions` · `decision_records` + `decision_record_sources` ·
  `action_items` · `decision_commitments` — through the kernel; Dismiss
  receipted; the Room's decisions read carries proposal provenance and
  `was{text,owner,due}`; the commitments read's join fixed (it never
  matched the existing commit_decision flow either); `intel_jobs.
  model_host` recorded at enqueue (auto trigger + `Run intelligence`),
  `intel_model_host` · `intel_duration_s` on the meeting; hub
  `meetings {intelligence, auto, host}` with host = the endpoint host
  (`192.168.1.43` · `local` · `api.openai.com`), null unassigned; the
  People resolver (`resolve_relationship_by_watch_identity`, opaque id
  only, `POST /api/people/resolve`); the 1:1 brief's `watch_summary` +
  `last_meeting` (transient, snapshots only, `snapshot_json` read inside
  a `with`); `source_suggestions` + the transcript scanner (GitHub
  owner/repo lower-cased, Jira keys upper-cased; dismissed never
  returns); `GET /api/projects/{id}/people` (resolved, non-zero only);
  MCP `meeting.proposals` · `proposal.confirm` · `proposal.dismiss` ·
  `people.resolve` · `project.suggested_sources` · `…add…` · `…dismiss…`
  (208 tools / 37 families).
- **The faces (02 · 03 · 05 · 06 · 07):** the Room's PROPOSAL rows
  (MTG · prefix · text · `BY FRI · from Standup 09-05 · MAREK` ·
  EgressChip · Confirm · Edit · Dismiss; Edit unfolds in place with the
  mic and a `was:` caption; the newest wears the arrival frame; text
  wraps); DECISIONS & COMMITMENTS from the one decisions list (MTG ·
  `OWNER MAREK · BY FRI · CONFIRMED 09:27 · WAS …`; a commitment folds
  into its decision); SUGGESTED source above SOURCES (`GH` dimmed ·
  `SUGGESTED · FROM STANDUP 09-05` · Add · Dismiss; count = accepted);
  PEOPLE section (monogram · display name as stored · `2 PRS WAITING · 1
  ASSIGNMENT OVERDUE` · Open) and the shade's `PEOPLE · Q4 PLATFORM`
  lane; the meeting after the run (`RAN` · `41 S` · host with scope;
  NEEDS YOU N with Confirm · Dismiss; QUEUED/RUNNING without the legacy
  prose panel, `Skip`/`Retry` in the verb slot); the arrival's rows (MTG
  · prefix · `PROPOSED · STANDUP` · Confirm · Open; the headline and the
  badge count proposals); Settings → Meetings (display `After room
  meetings`; one Intelligence row: CycleGadget · chip · `LAST RAN`;
  `NO MODEL` + `Choose model` when unassigned; CAPTURE + EXPORT rows;
  the pointer prose gone; the hub row `INTELLIGENCE ON · AFTER ROOM
  MEETINGS`); the 1:1 card (Prep summary rows absent at zero, `2 PRS
  WAITING ON ANIA · 5+ DAYS · #612 · #618`, `Open` → the Now wing's
  per-entity ledger rows; the card takes the window under 900px).
- **The docs (09):** README, USER_GUIDE "The loop closes", ARCHITECTURE
  (sequence), SECURITY (the People resolver boundary), MCP_SIDECAR
  (roster regenerated), POSITIONING (`a proposal`, `Confirm`, `the
  loop`, `a suggested source`, `the 1:1 card`, `People in the Room`) —
  eight markers verified against the built faces.
- **The walk (08):** live172_walk.py, seven steps at 1440 + 393 on the
  owner's desk, read-only, nine shots, zero defects. The first run's
  guard failed OPEN and posted `Run intelligence` on his "Already
  titled" meeting (cloud profile, no key → QUEUED, nothing left the
  machine); disclosed in the handover; the guard now fails closed
  (`_run_allowed`; unknown = no; a queued job blocks a second run) and
  the second run reads `SKIPPED: not LAN: api.openai.com`. The walk
  also exposed the QUEUED meeting detail's pre-170 prose panel (fixed
  here) and hosts shown as a profile label (fixed at the wire).

## Found in review and paid

- Confirm wrote the follow-through `decisions` row only; the Room and
  the decision receipt read `decision_records` (fixed: the whole chain).
- The commitments read joined the wrong id space (pre-existing; fixed).
- `SuggestedSourceService` and the People brief read never entered
  their connection context manager (fixed).
- `_brief_watch_summary` read a `snapshot` column that is `snapshot_json`
  (fixed; the fixture had hidden it).
- Two meeting proposal vocabularies on one path (actuator vs
  follow-through): follow-through proposals moved to their own route;
  the rename of the actuator route is parked.
- A lane raised the ratchet ceiling; restored, every hit paid in code.
- A lane reported shots that did not exist; law restated: a face is
  done when its rig ran green serially and its shots were read.
- People Now rows collapsed without `cols="room"` on the ledger.

## Parked (BACKLOG)

Auto-run on imported transcripts; the actuator proposals route rename;
`Run all`; the People window's prose caption.

## Gates

- Counsel on the design: RATIFY-W-C, ruled. Counsel on the built phase:
  RATIFY-W-C — C1 (P0: the bridge had no production call site) and C2
  (the RAN header from a recorded job) PAID, the P2s paid, every
  design-stage ruling verified paid (design addendum three).
- Suite (CI shape, -n auto): PENDING.
- Web: vitest green; baseline zero branch-new; ratchet at its floor.
- Rigs + wire (closing gate): 331 green serially (six hs172 rigs, three
  170 siblings, the 171 shade rig, the 172/171/170 wire tests, the
  fences).

## The owner's questions (from counsel, carried in the handover)

1. `Decide:` for decisions and `Confirm:` for action items — yours?
2. The 1:1 card: summary rows then the Now wing — the shape you want?
3. Do Jira assignments belong on the 1:1 card?

## His word

Design canvas above; **PR #555** stacked on #554 on #553. Merge order stays
his: #553 → #554 → 172's.
