# Phase 147 — One-Tap Record

**Status:** in progress (6/7).

**Last updated:** 2026-08-29.

## Owner mandate

At the Phase 146 close (2026-08-28, merged as PR #500) the owner
asked for the next BIG functional unlock and picked **Event →
one-tap record** from the menu — the rail's natural next verb,
deferred twice before. The thesis is the flywheel closing: a
calendar event on the UPCOMING rail becomes, with ONE tap, an armed
recording (Phase 136's proven countdown machinery) that captures the
meeting and carries the event's identity into it — calendars (146) →
the Door (144/145) → capture (136) → intelligence (143) →
follow-through, one loop. The owner's pick also folded in the two
Phase 146 counsel ledger riders (snapshot 422 surfacing; vision
pre-filter). Branch `feat/hs147-one-tap-record` from main
`fabba984`.

Standing laws with extra weight: no modals / errors in-flow (the
tap and its refusals live ON the rail row); the ISO-offset law
(never string-mangle; this phase is MADE of datetime arithmetic);
the stub law (the arm path must be proven against the real conductor
lifecycle, fakes only at the engine-factory level); shots
cross-read; migrations stay minimal (additive columns only). The
standing charter questions apply: *will you use this on a tired
Tuesday?* and *does this operate with joy?*

## Evidence base

- [`assets/audit-census.md`](./assets/audit-census.md) — the
  structural census (2026-08-28, opus, read-only): every seam
  file:line, the identity facts, the five-plane gap list. Headline:
  **no code path connects a calendar event to a recording or meeting
  today — the systems are fully disjoint.**
- [`assets/audit-walk.md`](./assets/audit-walk.md) +
  [`assets/audit-walk-shots/`](./assets/audit-walk-shots/) — the
  live before-state (real hub, isolated HOME, both widths). Headline:
  **the job is impossible today** — an EVENT row is a passive `<li>`;
  the closest path is 2 clicks + manually retyping title and time
  into a form with no event concept. Zero rendering defects: pure
  new-verb work.
- [`assets/settled-design.md`](./assets/settled-design.md) — the
  design-beat spec (D1–D7): the link model, the arm verb, the
  reconciliation invariants (R1–R3, X1), the timing rulings, the
  snapshot identity repair, the tap surface, meeting provenance.
  Taken to the Opus counsel BEFORE implementation per
  ORCHESTRATION.md §2b; the ruling and its disposition are recorded
  below.

## Settled design

The full spec is [`assets/settled-design.md`](./assets/settled-design.md);
builders implement against it and do not redesign. The rulings in
one breath: three additive link columns + one live arm per event
(D1); the arm verb is server-computed from the event — one tap, no
form, named refusals, in-progress events armable for the remainder
(D2); feed refreshes reconcile linked arms — follow time shifts by
`(source_id, uid)`, cancel on event removal, NEVER touch a live
arming/recording (D3, X1); 60 s lead, no conductor changes (D4);
snapshot UIDs become content-deterministic (D5); RECORD THIS /
ARMED + CANCEL? inline on the rail row per the DoorCard verb
precedent (D6); `calendar_event_id` rides the fire seam onto the
meeting row with a quiet origin line (D7).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-147-01 | The link (schema + arm verb, server side) | done | [story-01](./story-01-the-link.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-147-02 | The tap (rail verb + armed state, web) | done | [story-02](./story-02-the-tap.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-147-03 | The honest follow (reconciliation + snapshot identity) | done | [story-03](./story-03-the-honest-follow.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-147-04 | Meeting provenance (the event on the record) | done | [story-04](./story-04-meeting-provenance.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-147-05 | Snapshot polish riders (the 146 ledger pair) | done | [story-05](./story-05-snapshot-polish.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-147-06 | The record book (docs) | done | [story-06](./story-06-the-record-book.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-147-07 | The walk and the close | ready | [story-07](./story-07-walk-and-close.md) | [evidence-story-07](./evidence-story-07.md) |

## Where we are

**6/7.** HS-147-06 (the record book) is DONE — a cold reader can now
run the whole loop from the docs alone: the USER_GUIDE "Arm an event
for recording" section (labels verbatim: Record this, ARMED, Cancel?,
ALREADY ARMED / EVENT ENDED / EVENT NOT FOUND), the README one-tap
sentence, and a full event-linked-recording pipeline section in
ARCHITECTURE_BACKEND_RUNTIME with verified anchors. Doc guards green;
the stash-compare law proved zero branch-new violations hiding in
the two inherited-baseline language guards. Meanwhile the walk grew
its one-tap leg and passed 8/8 TWICE (including the live origin line
through the sync authority — made possible by a sync round-trip fix
the leg's construction exposed: meeting_state_from_sync_value dropped
calendar_event_id, violating its exact-inverse contract; fixed +
pinned). Only the close (07) remains. Earlier — **5/7.** HS-147-04 (meeting provenance) is DONE — the loop closes:
a fired event-linked recording writes `calendar_event_id` onto the
meeting row through the explicit `pending_calendar_event_id` seam
(the counsel's D7 amendment, mirroring pending_title exactly), the
read side exposes it on HTTP and MCP, and the Meetings surface wears
a quiet origin line (`FROM <SOURCE> · <EVENT>`, server-enriched,
honestly absent when the event row is gone). 137+34 focused green
orchestrator-read; the LIVE origin shot rides the walk (07) where a
real fire produces a linked meeting — named, not skipped. All five
feature stories are DONE; the record book (06) and the walk + close
(07) remain. Earlier — **4/7.** HS-147-03 (the honest follow) is DONE — an arm no longer
lies when the feed moves: R1 refresh-in-place (an extended meeting
refreshes duration under the same projection id — the counsel's
catch, implemented and pinned), R2 nearest-occurrence rebind by
(source_id, uid) with next_fire_at/duration/title following, R3
cancel with event_removed for vanished events, X1 immunity for
arming/recording rows, all inside the ingest tick, per-source, with
D3b idempotence (a reconcile crash never kills the tick). Snapshot
UIDs are content-deterministic — re-imports stop orphaning arms.
91 focused green orchestrator-read; two deviations ruled (the rare
pre-read-failure degrade is LEDGERED). Earlier — **3/7.** HS-147-02 (the tap) is DONE — the job exists on glass: one
real tap on RECORD THIS arms the event (proven end-to-end by the new
tests/e2e/test_hs147_one_tap_glass.py on a live hub), ARMED +
two-beat CANCEL?, the honest stale-row refusal rendering ALREADY
ARMED in-flow, both widths, 11/11 existing door glass green under
the new geometry. The shot cross-read earned its keep AGAIN: it
caught the armed intent rendering twice (event row + near-duplicate
schedule row) → ruled one-intent-one-row, suppression landed with a
unit pin + glass assertion, exhibit re-shot. Wave-2 remainder (03
the honest follow, 04 meeting provenance) is built, orchestrator-
verified (89 + 137/34 focused green), shipping next. Earlier —
**2/7.** HS-147-01 (the link) was DONE — the keystone: three additive
link columns + the L1 partial unique index (one live arm per event),
the server-computed arm verb (`POST /api/scheduled-recordings
{calendar_event_id}` computes title/one_shot/enabled/local-tz/
duration-with-remainder-rule/60s-lead entirely server-side;
fromisoformat/astimezone only), the three named refusals through
route AND MCP, `armed_schedule_id` projected on door calendar items,
and a full arm→countdown→fire→auto-stop→terminal-advance lifecycle
proof on the REAL conductor (stub law satisfied). 24 new tests; 156
focused green re-run by the orchestrator. The commit also healed
branch-new census fallout from 05 (the retired resolve_placement
entries — deliberate deregistration with attribution; the builder
had mis-attributed it as pre-existing, caught by orchestrator
triage). Wave 2 rides next: 02 (the tap) ∥ 03 (the honest follow) ∥
04 (meeting provenance) in disjoint lanes. Earlier — **1/7.**
HS-147-05 (the snapshot polish riders) was DONE first — the
independent lane shipped while story 01 built: the IMPORT SCREENSHOT
bare catch is dead (422 refusals surface in the PrefStatusBar via the
same `readableError` path the drop layer uses), and the
direct-dispatch fallback pre-filters to vision-capable profiles (v2
capability manifest first, kind heuristic for unbound legacy;
`no_vision_model_assigned` now fires with ZERO inference dispatches
— call-count asserted; the non-vision `resolve_placement` fallback
removed). 37 Python + 21 web focused tests green, re-run and read by
the orchestrator. Full-sweep verdict rides the next quiet-tree
window. Story 01 (the link) is in-progress in its parallel lane;
02/03/04 wait on it.

## Decision log

- **2026-08-28 — owner pick:** Event → one-tap record chosen from
  the four-option menu (over JIRA Desk Sync, a standalone real-metal
  vision probe, and Candidate Z) as the next big functional unlock;
  the two 146 snapshot ledger items ride as story 05 per the picked
  option's rider clause.
- **2026-08-28 — orchestrator rulings (the spec):** link by
  projection id with `(source_id, uid)` recovery keys; one live arm
  per event; in-progress events armable for the remainder; 60 s
  lead accepted (start envelope −50 s…+10 s vs event start); event
  removal cancels the arm but a live arming/recording is NEVER
  yanked by a feed (X1); snapshot UIDs go content-deterministic.
  The owner may overrule any row at the sitting.
- **2026-08-28 — counsel design ruling: RATIFY-WITH-CONCERNS,
  zero MUST-FIX.** Three should-fixes ABSORBED into the spec and
  stories before any builder rides: (1) R1 becomes refresh-in-place
  — an end-time-only extension updates duration/title under the
  same projection id (the id hashes `starts_at` only, so "the
  recording follows the meeting" would otherwise mean its start
  time only); (2) invariant D3b — replace+reconciliation share a
  transaction or reconcile is idempotent with caught errors, so a
  crash never kills the ingest tick and a dangling link self-heals;
  (3) D7 names the `pending_calendar_event_id` callback attribute
  explicitly. Two items LEDGERED (see the ledger). The counsel's
  human-compliance verdict: the one-tap promise holds — "the
  refusal surface is complete, the visibility surface is complete."

- **2026-08-29 — orchestrator ruling (one intent, one row):** the
  story-02 shot cross-read caught the armed intent rendering twice
  (the EVENT row wearing ARMED plus its linked schedule as a
  near-duplicate SCHEDULED RECORDING row 60 s earlier). Ruled: a
  linked schedule row is suppressed while its event is in the
  projection; it reappears if the event leaves (pending work never
  hidden). Unit pin + glass assertion; exhibit re-shot.
- **2026-08-29 — deviation rulings at ship time:** house
  NotFound = the named refusal (01); dummy cron on event-linked
  one-shots accepted, conductor drives by next_fire_at (01); DELETE
  disarms an idle linked one-shot, the countdown cancel route stays
  for arming-state (02); the rare pre-read-failure R2→R3 degrade is
  LEDGERED, loud and re-armable (03).

## Ledger (counsel, carried openly)

- **Adjacent recurring arms on an R2 rebind:** if two occurrences
  of one recurring uid are both armed and the series shifts, both
  rebinds can target the same nearest occurrence — L1 refuses the
  second honestly (one armed recording instead of two, re-armable).
  Named, not fixed: needs two arms on one series plus a series
  shift.
- **Identical snapshot events collapse to one uid** under D5's
  deterministic hash — accepted; the projection's unique index
  already treats them as one row.

## Risk register

- **Reconciliation vs conductor race:** the ingest tick (15 min) and
  the arming tick (60 s) both write `scheduled_recordings`. X1
  narrows the window (reconcile touches idle/arming-linked rows
  only for the refreshed source) but the seam needs a deliberate
  test in story 03.
- **Recurring events share a uid:** R2 rebinding picks the
  occurrence nearest the old `starts_at`; a pathological feed that
  drops one occurrence and shifts another could rebind to the wrong
  one. Realistic exposure is low (single owner, 15-min refresh);
  story 03's test plan pins the nearest-occurrence rule.
- **Glass seeds:** the Door glass e2e files and
  `scripts/door_walk_hs144.py` photograph the rail; new inline
  buttons change row geometry. Story 02 owns keeping them green;
  the walk script grows its leg in story 07.
- **Asset clobber law stands:** glass runs clobber phase asset
  dirs (141/143/144/145/146 — and now 147's own once committed);
  `git checkout --` them after every run.
