# Phase 147 settled design — the event-linked recording

The design-beat spec (ORCHESTRATION.md §2b): the link model, the
lifecycle, the invariants, and the sanctioned exceptions. Ruled by
the orchestrator 2026-08-28 from the audit census + walk; one Opus
counsel ruling taken BEFORE implementation; the owner may overrule
any row at the sitting. Builders implement against this — they do
not redesign.

**Counsel verdict (2026-08-28): RATIFY-WITH-CONCERNS, zero
MUST-FIX.** Three should-fixes absorbed into this spec (R1
refresh-in-place; D3b transaction/idempotence; D7 explicit
`pending_calendar_event_id`); two items ledgered in the phase
status doc (adjacent recurring arms colliding on an R2 rebind — L1
refuses the second honestly; identical snapshot events collapsing
to one uid — already how the projection index treats them).

## The one sentence

Tapping RECORD THIS on an UPCOMING calendar event creates an
event-linked one-shot scheduled recording (Phase 136 machinery,
unchanged lifecycle) whose times and title are computed from the
event server-side, which follows the event honestly through feed
refreshes, and whose captured meeting carries the event's identity.

## D1 — the link model

`scheduled_recordings` gains three additive columns (declarative
schema, reconcile.py, additive-only law):

- `calendar_event_id TEXT NOT NULL DEFAULT ''` — the projection id
  (`ce_…`) at arm time; the DISPLAY + join key.
- `calendar_uid TEXT NOT NULL DEFAULT ''` and
  `calendar_source_id TEXT NOT NULL DEFAULT ''` — the RECOVERY keys
  (uid survives time shifts; source scopes it).

`meetings` gains `calendar_event_id TEXT` (nullable). No JSON bags —
columns are queryable and this table has no bag precedent.

**Invariant L1 (one live arm per event):** partial unique index on
`calendar_event_id WHERE calendar_event_id != '' AND enabled = 1`,
PLUS a service-level check returning the named refusal
`event_already_armed`. One-shot schedules disable on every terminal
outcome (existing `_advance_after_terminal`), so the index naturally
frees the event for a future re-arm.

## D2 — the arm verb (server-computed, one tap, no form)

`POST /api/scheduled-recordings` accepts optional
`calendar_event_id`. When present the service loads the event and
computes EVERYTHING (the client sends nothing else):

- `title` = event title; `one_shot` = true; `enabled` = true;
  `tz` = the hub's local zone.
- `duration_minutes` = ceil((ends_at − starts_at)/60), capped at
  480; if the event has already started, ceil((ends_at − now)/60)
  so the recording covers the REMAINDER, and fires immediately.
- `next_fire_at` = starts_at − 60 s (the lead ruling, D4); never in
  the past by more than "already started" allows.

Named refusals, in-flow, never prose: `calendar_event_not_found`,
`event_already_ended`, `event_already_armed`. An event in progress
IS armable (the tired-Tuesday case: you sit down five minutes late
and want the rest recorded) — it arms and fires on the next tick.
Datetime arithmetic uses fromisoformat/astimezone ONLY (the
ISO-offset law; never string-mangle).

## D3 — the honest follow (reconciliation invariants)

After every `replace_projection(source_id, …)` the ingest conductor
reconciles that source's linked, enabled, non-fired schedules
(states idle/arming only — see X1):

- **R1 (still there, refresh in place):** an event row with the
  same `id` exists → refresh the schedule's `duration_minutes` and
  `title` if the event's `ends_at`/`title` changed (counsel finding
  5: the projection id hashes `starts_at` only — an extended meeting
  is invisible to id identity, and D3's promise is "the recording
  follows the meeting", not just its start time).
- **R2 (time shift):** id gone, but rows with the same
  `(source_id, uid)` exist → rebind to the occurrence whose
  `starts_at` is nearest the old one; update `calendar_event_id`,
  `next_fire_at`, `duration_minutes`, `title`. The recording follows
  the meeting.
- **R3 (event removed):** no row with that uid remains → the
  schedule is disabled with state `cancelled`,
  `last_outcome = "event_removed"` (existing state vocabulary; no
  new states). A recording never fires for a meeting the calendar
  says is cancelled.

**Exception X1 (never yank a live capture):** a schedule in
`arming` or `recording` is NEVER touched by reconciliation — the
meeting is happening in front of the owner; the calendar feed does
not get to kill it. The existing tap-to-cancel countdown and manual
stop remain the only authorities there.

**Invariant D3a:** reconciliation runs inside the same ingest tick
as the projection replace (not a new daemon), and only for the
refreshed source — a broken calendar still never touches a healthy
source's arms.

**Invariant D3b (counsel finding 1):** the projection replace and
its reconciliation share one transaction, or reconciliation is
idempotent and catches its own errors (log, never propagate) —
a reconciliation crash must never leave the ingest tick dead, and a
dangling `calendar_event_id` self-heals on the next refresh.

## D4 — timing rulings

60 s arm lead (`next_fire_at = starts_at − 60`), unchanged 60 s
conductor tick and 10 s countdown. Envelope: recording starts
between start−50 s and start+10 s. No conductor changes; pre-meeting
seconds are harmless, a late first minute is not. Recorded as a
ruling, not an accident.

## D5 — snapshot identity repair

`calendar_snapshot_service.py:289` stops minting `uuid4()` per
confirm: `uid = sha256(title \0 starts_at \0 ends_at \0 location)
[:16] + "@holdspeak-snapshot"`. Re-confirming the same week yields
the same uids, so R1/R2 hold for snapshot sources too, and
re-imports stop orphaning arms. (Two identical events at the same
time collapse to one uid — accepted; the projection's unique index
already treats them as one.)

## D6 — the tap surface (house grammar)

- Each EVENT row gains an inline **RECORD THIS** button (the
  DoorCard `lawful_verbs` button precedent; in-world, no modal, no
  form). Placement per the walk: the row's right column under
  STARTS, or a `grid-column: 2 / -1` line at 393.
- An armed event row swaps the button for an **ARMED** chip +
  **CANCEL?** in-world verb (existing cancel/delete authority).
  `DoorService._calendar_event_item` projects `armed_schedule_id`
  by joining enabled schedules on `calendar_event_id`.
- Refusals render in-flow on the row (the receipt-bar/turn grammar);
  errors never overlap UI.
- The rail's SCHEDULED RECORDING rows and the header button are
  untouched; the generic form remains for non-event recordings.

## D7 — meeting provenance

`calendar_event_id` threads `_fire` → `_start_meeting_fn` →
`_start_meeting()` → the meetings row via an explicit
`pending_calendar_event_id` callback attribute mirroring the
existing `pending_title` pattern: the `web_server.py:986-991`
lambda sets it, `meeting_glue.py:293-298` reads and applies it
(counsel finding 3 — spelled out so no builder re-derives the
seam). The Meetings surface shows a quiet origin
line (source label + event title) on linked records. Follow-through
cards already carry `meeting_id`; the chain
event → meeting → commitment is thereby closed without touching the
follow-through schema. Egress: none — everything here is local; no
new badge surface.

## Out of scope (named)

Auto-arm rules ("record all events from source X"), stop-at-live-
event-end tracking (duration is fixed at arm/rebind time), joining
meeting URLs, multi-event batch arming, iPad/Swift surfaces (web is
the spec).
