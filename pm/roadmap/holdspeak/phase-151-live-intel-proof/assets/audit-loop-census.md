# Phase 151 audit B — the loop census (condensed)

Read-only opus audit, 2026-08-30. The production chain hop-by-hop +
the honest list of what 147-150 faked. Companions:
[audit-metal-census.md](./audit-metal-census.md),
[metal-probes.md](./metal-probes.md).

## The chain (every hop anchored)

1. **Capture**: ScheduledRecordingConductor._tick
   (scheduled_recording_conductor.py:163) → _fire (:473) →
   start_meeting_fn (web_server.py:997-1004) →
   MeetingSession.start (session.py:422, capture_status
   provisional) → MeetingRecorder mic/system streams
   (meeting_recorder.py:480/:524, sd.InputStream) →
   TranscribeLoopMixin every 10 s → segments. stop() (:622) →
   final transcribe (:666) → _handoff_intel_at_stop (:686, sets
   intel_status=queued) → finalized (:722-724) → save (:750).
   **The capture path STRICTLY requires a live PortAudio input
   device.** AudioSource protocol (audio.py:27) has NO file
   adapter; only AudioRecorder (mic) and RemoteAudioRecorder (WS
   PCM) implement it. Headless real-capture = a virtual audio
   device at the OS level (BlackHole/pulse null-sink), outside the
   product.
2. **Intel**: persistence.py:88-103 enqueue → intel_queue worker →
   _process_bound_intel_job (intel_queue.py:297; :312-314 "no
   transcript" terminates) → bound.execute
   capability=meeting.deferred_analysis (:338-355) →
   bound_analysis_dispatch (deferred_bound.py:100+) →
   MeetingIntel._analyze_once.
3. **Prompt** (intel/parsing.py:16-46): system "Return ONLY a
   single valid JSON object…"; schema shape
   `{"topics": [...], "action_items": [{"task", "owner":
   "Me|Remote|null", "due"}], "summary"}`.
   **The prompt itself is person-blind — it STEERS the model to
   Me/Remote/null, designed pre-150.** (Probe 2 showed the model
   emits real names anyway when asked with a named-owner schema.)
4. **Owner parsing** (_coerce_action_items, parsing.py:111-131):
   passes any string through (strip only; None/""/"null" → None).
   No normalization, no reserved handling at this layer.
5. **Fresh items**: review_state="pending"
   (intel/models.py:62-65); _save_intel upsert preserves existing
   review_state when incoming is pending (db/meetings.py:432-435).
   **Pending items land in the UNASSIGNED lane**
   (follow_through_service.py:578-579) regardless of owner; they
   reach now/waiting/overdue only after triage.
6. **Action-item identity**: id = sha256(task:owner)[:12]
   (intel/models.py:43-44) — a changed owner string on
   re-extraction makes a NEW row, so the delegated_at CASE guard
   (db/meetings.py:440-445) mostly fires on the NULL↔value edges.
7. **The person leg**: link_owner_alias
   (people_service.py:640-684; reserved {"me","remote","you"} :43,
   casefold exact match); web isReservedOwner
   (DoorBoardLane.tsx:222-226) hides map… for reserved strings
   (:746). **Messy-string reality**: "Ewa S." ≠ "Ewa" (exact
   casefold match only — multiple aliases per person is the
   designed answer); "myself"/"I" are NOT reserved and would show
   map… (risk noted).

## Control-vs-treatment (the honest experiment)

Same real audio through the import door twice, isolated HOMEs:
- **Control**: intel disabled (session/meeting config) → zero
  action_items rows, zero intel_snapshots, no meeting cards on the
  board, empty brief People.
- **Treatment**: profile + assignment → real .43 dispatch → N
  action_items rows (review_state=pending → UNASSIGNED lane) →
  triage/map → chips → brief person sections.
- Artifacts: action_items rows; intel_snapshots row; board JSON;
  brief person_sections; frames of each.

## The walk shape

Headless legs: import real WAV → real mlx-whisper transcription →
real .43 intel via the modern binding → pending items on the Door →
map gesture → chips/staleness → brief sections + verbs. The ONE
attended leg: one-tap record capturing real room audio (the owner
plays a real 1:1 recording — their ruling) through the live mic
path: armed → countdown → fire → segments → stop → queued intel →
the same tail.

## What 147-150 faked (the honest list)

Every walk used `POST /api/sync/push` with pre-authored intel
(147 evidence-story-07; 150 story-0203-rig.py:122-144 and
story-07-rig.py:96-115 — hardcoded action_items, pre-accepted,
pre-owned). NEVER real: capture from a live mic in any walk; real
Whisper on real audio in any walk; MeetingIntel.analyze against
ANY real model; _coerce_action_items on real model output; real
owner strings; process_next_intel_job against a real endpoint; the
full loop end-to-end. 147-150 proved rendering, routes, gestures,
lanes, and the overlay — all on seeded data.
