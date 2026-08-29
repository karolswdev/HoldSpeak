# Evidence - HS-147-07

- **Story:** HS-147-07 - The walk and the close
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T07:00:57Z

- **Command:** `bash -c uv run --python 3.13.11 python scripts/door_walk_hs144.py --out pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/shots --report pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/walk-report.md --report-json pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/walk-report.json --pairs pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/walk-pairs.json --pairs-md pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/walk-pairs.md --tmp-root /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/walk-debug/tmp && echo '== CLOSE SWEEP (readable log: scratchpad/hs147-close-sweep.log) ==' && tail -1 /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/hs147-close-sweep.log && echo 'verdict: 11 inherited-baseline names + 1 census line-drift (remapped, 10/10 green) = baseline-subset, zero branch-new'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1f4f0b0721a2f4ab5f715a33d65ef521c7ed2db2

```text
  HUB  HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/walk-debug/tmp/hs144-door-walk-8v6jeyz7/home
  HUB  XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/walk-debug/tmp/hs144-door-walk-8v6jeyz7/xdg-config
  HUB  XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/walk-debug/tmp/hs144-door-walk-8v6jeyz7/xdg-data
  HUB  TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/walk-debug/tmp/hs144-door-walk-8v6jeyz7/tmp
  HUB  port=64236 pid=9654 token=hs144-06-…

== LEG COLD ==
  PASS  cold narrow starts at First Sentence [scope: [data-testid="chair-first-value"]]
  PASS  cold narrow has editable pad and Continue later [scope: First Sentence container]
  PASS  cold narrow has no Door [scope: whole document absence check]
  SHOT  pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/shots/cold-first-value-393.png — untouched First Sentence at narrow width
  PASS  cold 393: no page errors — [] [scope: current browser document]
  PASS  cold 393: document has no horizontal overflow [scope: document root; Door board viewport is not exempt]
  PASS  cold 393: body has no horizontal overflow [scope: body; Door board viewport is not exempt]
  PASS  cold starts at First Sentence [scope: [data-testid="chair-first-value"]]
  PASS  cold First Sentence heading is one job [scope: First Sentence container]
  PASS  cold First Sentence has editable pad [scope: First Sentence container]
  PASS  cold First Sentence has Click to speak [scope: First Sentence container]
  PASS  cold First Sentence has continue verb [scope: First Sentence container]
  PASS  cold has no Door before first value [scope: whole document absence check]
  PASS  cold has no Desk chrome before first value [scope: whole document absence check]
  PASS  cold has no fake transcript state [scope: First Sentence container]
  SHOT  pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/shots/cold-first-value-1440.png — untouched First Sentence at desktop
  PASS  cold 1440: no page errors — [] [scope: current browser document]
  PASS  cold 1440: document has no horizontal overflow [scope: document root; Door board viewport is not exempt]
  PASS  cold 1440: body has no horizontal overflow [scope: body; Door board viewport is not exempt]
  PASS  model-less speech returns named unavailability — {'type': 'error', 'error': 'Transcription unavailable.', 'reason': 'transcription_unavailable', 'failure_category': 'transcription_unavailable'} [scope: real /ws/dictation/stream browser protocol]
  PASS  typed first value visibly remains editable [scope: First Sentence editable pad]
  PASS  typed first value reaches visible Desk result and custody within 3 minutes — first_value_mode=typed_fallback elapsed_ms=1876.400 [scope: First Sentence real Continue later handoff]
  PASS  typed first value has authoritative note custody — notes=7 [scope: GET /api/notes after visible Desk handoff]
  PASS  typed handoff reveals normal Door state [scope: normal Chair after First Sentence handoff]
  PASS  typed first-value handoff: no page errors — [] [scope: current browser document]
  PASS  typed first-value handoff: document has no horizontal overflow [scope: document root; Door board viewport is not exempt]
  PASS  typed first-value handoff: body has no horizontal overflow [scope: body; Door board viewport is not exempt]
  PASS  post-handoff 393: no page errors — [] [scope: current browser document]
  PASS  post-handoff 393: document has no horizontal overflow [scope: document root; Door board viewport is not exempt]
  PASS  post-handoff 393: body has no horizontal overflow [scope: body; Door board viewport is not exempt]
  PASS  fixture sync ingestion accepted — status=200 payload={'success': True, 'received': {'meetings': 1, 'artifacts': 0, 'decision_records': 0, 'decision_record_sources': 0, 'decision_record_work': 0, 'decision_record_revisions': 0, 'projects': 0, 'knowledge_memberships': 0, 'pr [scope: production HTTP authority POST /api/sync/push]
  PASS  fixture sync reports one source meeting — {'meetings': 1, 'artifacts': 0, 'decision_records': 0, 'decision_record_sources': 0, 'decision_record_work': 0, 'decision_record_revisions': 0, 'projects': 0, 'knowledge_memberships': 0, 'project_relationships': 0, 'deployment_revisions': 0, 'refinement_thoughts': 0, 'notes': 0, 'kbs': 0, 'recipes': 0, 'chains': 0, 'workflows': 0, 'directories': 0, 'directory_memberships': 0, 'profiles': 0, 'models': 0, 'workbenches': 0} [scope: POST /api/sync/push response]
  PASS  Desk seed authority is preservation-safe — status=200 payload={'success': True, 'manifest': 'fresh-desk', 'applied': {}, 'profiles_seeded': 0, 'profiles_adopted': {}, 'workbenches_seeded': 0, 'filed': 0, 'total': 0} [scope: production HTTP authority POST /api/desk/seed]
  PASS  fixture Thought enters custody authority — status=201 payload={'thought': {'id': 'thought_fcf96ace951c', 'raw_id': 'thought_fcf96ace951c', 'raw_sha256': 'c3ef1083d1e712832249d018d4f85bd872a336c423f4497ae738659381bec4de', 'source': {'kind': 'typed'}, 'raw_captured_at': '2026-08-29T0 [scope: production HTTP authority POST /api/thoughts]
  PASS  fixture Thought returned a stable id — {'id': 'thought_fcf96ace951c', 'raw_id': 'thought_fcf96ace951c', 'raw_sha256': 'c3ef1083d1e712832249d018d4f85bd872a336c423f4497ae738659381bec4de', 'source': {'kind': 'typed'}, 'raw_captured_at': '2026-08-29T07:01:09Z', 'state': 'working', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'working_revision': 1, 'attachment_revision': 0, 'attachment_sha256': '32d501d122e130fea68b0fb2ebba835d666596c8e668985f2dd2ccf338f009de', 'attachments': [], 'working_note': {'id': 'note_thought_b21fb739caccdb5f', 'title': 'HS144 WALK active thought', 'body_markdown': 'HTTP custody route created this thought.', 'tags': [], 'deleted': False, 'last_modified': '2026-08-29T07:01:09Z'}, 'filing_status': 'filed', 'continuity': {'state': 'idle', 'code': ''}, 'directory_id': 'hs-seed-inbox'} [scope: POST /api/thoughts response]
  PASS  fixture schedule enters production authority — status=201 payload={'success': True, 'schedule': {'id': 'sr_d8ccb8b82b14', 'title': 'HS144 WALK baseline recording', 'cron_expr': '0 9 * * *', 'tz': 'UTC', 'one_shot': False, 'duration_minutes': 30, 'enabled': True, 'revision': 1, 'created [scope: production HTTP authority POST /api/scheduled-recordings]
  PASS  fixture schedule title is authoritative — {'success': True, 'schedule': {'id': 'sr_d8ccb8b82b14', 'title': 'HS144 WALK baseline recording', 'cron_expr': '0 9 * * *', 'tz': 'UTC', 'one_shot': False, 'duration_minutes': 30, 'enabled': True, 'revision': 1, 'created_at': '2026-08-29T07:01:09Z', 'last_fired_at': None, 'next_fire_at': '2026-08-29T09:00:00Z', 'armed_at': None, 'deadline_at': None, 'state': 'idle', 'last_outcome': '', 'last_receipt_id': '', 'delegation_receipt_id': 'sr_rcpt_f591ff7642b7', 'calendar_event_id': '', 'calendar_uid': '', 'calendar_source_id': '', 'receipt_id': 'sr_rcpt_860731b2c8c2'}} [scope: POST /api/scheduled-recordings response]

== LEG REVEAL ==
  PASS  Door owns its summary [scope: .door-board-section]
  PASS  Door owns upcoming rail [scope: .door-board-section]
  PASS  Overdue column exists inside Door [scope: .door-board-section > .door-board-column heading Overdue]
  PASS  Overdue owns its labelled source card [scope: Overdue Door column]
  PASS  Overdue count label agrees with aggregate [scope: Overdue column count label]
  PASS  Overdue API source id and title agree — api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}] [scope: GET /api/door board.overdue]
  PASS  Now column exists inside Door [scope: .door-board-section > .door-board-column heading Now]
  PASS  Now owns its labelled source card [scope: Now Door column]
  PASS  Now count label agrees with aggregate [scope: Now column count label]
  PASS  Now API source id and title agree — api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-29', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}] [scope: GET /api/door board.now]
  PASS  Waiting column exists inside Door [scope: .door-board-section > .door-board-column heading Waiting]
  PASS  Waiting owns its labelled source card [scope: Waiting Door column]
  PASS  Waiting count label agrees with aggregate [scope: Waiting column count label]
  PASS  Waiting API source id and title agree — api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-03', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}] [scope: GET /api/door board.waiting]
  PASS  Active column exists inside Door [scope: .door-board-section > .door-board-column heading Active]
  PASS  Active owns its labelled source card [scope: Active Door column]
  PASS  Active count label agrees with aggregate [scope: Active column count label]
  PASS  Active API source id and title agree — api cards=[{'id': 'thought_fcf96ace951c', 'source': 'thought', 'target_ref': 'thought:thought_fcf96ace951c', 'open_ref': 'note:note_thought_b21fb739caccdb5f', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-29T07:01:09Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_fcf96ace951c', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}] [scope: GET /api/door board.active]
  PASS  Unassigned owns source card without invented count [scope: Unassigned Door column]
  PASS  rail owns baseline schedule [scope: .door-upcoming-rail]
  PASS  schedule does not duplicate into retained Meetings lane [scope: retained Meetings lane absence check]
  PASS  Door aggregate counts are exact fixture truth — {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 1} [scope: GET /api/door counts]
  SHOT  pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/shots/after-chair-home-1440.png — populated Door board and rail at 1440px
  PASS  reveal 1440: no page errors — [] [scope: current browser document]
  PASS  reveal 1440: document has no horizontal overflow [scope: document root; Door board viewport is not exempt]
  PASS  reveal 1440: body has no horizontal overflow [scope: body; Door board viewport is not exempt]
  PASS  Door owns its summary [scope: .door-board-section]
  PASS  Door owns upcoming rail [scope: .door-board-section]
  PASS  Overdue column exists inside Door [scope: .door-board-section > .door-board-column heading Overdue]
  PASS  Overdue owns its labelled source card [scope: Overdue Door column]
  PASS  Overdue count label agrees with aggregate [scope: Overdue column count label]
  PASS  Overdue API source id and title agree — api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}] [scope: GET /api/door board.overdue]
  PASS  Now column exists inside Door [scope: .door-board-section > .door-board-column heading Now]
  PASS  Now owns its labelled source card [scope: Now Door column]
  PASS  Now count label agrees with aggregate [scope: Now column count label]
  PASS  Now API source id and title agree — api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-29', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}] [scope: GET /api/door board.now]
  PASS  Waiting column exists inside Door [scope: .door-board-section > .door-board-column heading Waiting]
  PASS  Waiting owns its labelled source card [scope: Waiting Door column]
  PASS  Waiting count label agrees with aggregate [scope: Waiting column count label]
  PASS  Waiting API source id and title agree — api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-03', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}] [scope: GET /api/door board.waiting]
  PASS  Active column exists inside Door [scope: .door-board-section > .door-board-column heading Active]
  PASS  Active owns its labelled source card [scope: Active Door column]
  PASS  Active count label agrees with aggregate [scope: Active column count label]
  PASS  Active API source id and title agree — api cards=[{'id': 'thought_fcf96ace951c', 'source': 'thought', 'target_ref': 'thought:thought_fcf96ace951c', 'open_ref': 'note:note_thought_b21fb739caccdb5f', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-29T07:01:09Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_fcf96ace951c', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}] [scope: GET /api/door board.active]
  PASS  Unassigned owns source card without invented count [scope: Unassigned Door column]
  PASS  rail owns baseline schedule [scope: .door-upcoming-rail]
  PASS  schedule does not duplicate into retained Meetings lane [scope: retained Meetings lane absence check]
  PASS  Door aggregate counts are exact fixture truth — {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 1} [scope: GET /api/door counts]
  PASS  narrow board scroll belongs to board viewport [scope: .door-board-viewport]
  SHOT  pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-07-walk/shots/after-chair-home-393.png — populated Door board and rail at 393px
  PASS  reveal 393: no page errors — [] [scope: current browser document]
  PASS  reveal 393: document has no horizontal overflow [scope: document root; Door board viewport is not exempt]
  PASS  reveal 393: body has no horizontal overflow [scope: body; Door board viewport is not exempt]
  PASS  reveal 393: narrow Door board owns its intentional scroll [scope: .door-board-viewport only]
  PASS  Door owns its summary [scope: .door-board-section]
  PASS  Door owns upcoming rail [scope: .door-board-section]
  PASS  Overdue column exists inside Door [scope: .door-board-section > .door-board-column heading Overdue]
  PASS  Overdue owns its labelled source card [scope: Overdue Door column]
  PASS  Overdue count label agrees with aggregate [scope: Overdue column count label]
  PASS  Overdue API source id and title agree — api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-sour
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

## Orchestrator triage note + close counsel (2026-08-29)

The capture above IS the third consecutive 8/8 walk run (the
readable runs 1 and 2 live in the session scratchpad logs; the
capture pairs with them per protocol). Close sweep (detached run,
readable log scratchpad/hs147-close-sweep.log): **12 failed / 6862
passed — 11 inherited-baseline names + 1 census line-drift from the
story-07 sync fix (sync_service pins 682→687, 697→702, remapped 1:1,
census 10/10 green in this tree) = baseline-subset, zero
branch-new.** The counsel independently verified the accounting
against the baseline file.

**Close counsel (fresh opus): RATIFY-WITH-CONCERNS, ZERO MUST-FIX.**
All five judgment calls ruled ACCEPTED: (a) the one-intent-one-row
suppression was within orchestrator authority ("exactly the process
the shot cross-read exists for"); (b) all four deviation rulings
substantively correct; (c) the walk's fire-proof chain (real
conductor test + glue test + sync-delivered origin line) is "an
honest chain... not a hole"; (d) the sync round-trip fix as rider
work — "ceremony without substance" to demand a story; (e) the
throttle directive — delivering the exhibit at close honors the
standing law's spirit under the owner's explicit terms. Cross-read
of all shot sets: internally consistent, times/durations/labels
agree. Human-compliance: "The one tap does what it says."

**Two counsel LEDGER items (carried in final-summary + status doc):**
the reappear-claim wording is over-broad (reconciliation prevents
the gap in practice); the fire-seam setattr-chain lambda is fragile
by construction (not a realistic bug; a refactor note).
