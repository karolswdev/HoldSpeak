# HS-144-06 — cold Door walk report

**Mode:** full cold walk
**Result:** PASS

## Leg results

| Leg | Result | Timing / fact | Assertion scope |
|---|---|---|---|
| cold | PASS | 1341.100 ms | First Sentence container; First Sentence editable pad |
| reveal | PASS | — | .door-board-section; .door-board-section > .door-board-column heading Active |
| completion | PASS | 38.600 ms | .door-board-section .door-board-receipt; GET /api/door after Door action |
| schedule | PASS | — | #schedule\:__create__ opened from .door-upcoming-rail; #schedule\:__create__ opened from narrow .door-upcoming-rail |
| calendar | PASS | — | #surface-settings Meetings Calendar GadgetRow (not global chrome); .door-upcoming-rail calendar_event row |
| click-depth | PASS | — | .door-upcoming-rail calendar row; ClickLedger Schedule + #schedule\:__create__ |
| doorframe | PASS | — | #surface-meetings; .desk-menubar |

## First-value truth

- `first_value_mode=typed_fallback`: this cold fresh HOME had no transcription callback/model. The walk verifies the real WebSocket named refusal `transcription_unavailable`; it never supplies or calls a fake transcript.
- The timer begins immediately before typing into the actual First Sentence pad and stops only once the actual Save draft & continue handoff visibly reaches the normal Desk. The report separately proves the resulting note custody through `GET /api/notes`.

## Completion semantics

- Quiet success is the authoritative Door card disappearing. `completion_ms` is same-page `performance.now()` click-to-card-detachment, followed by `GET /api/door` confirmation. No success toast was added or claimed.
- The named in-place receipt is separately proven on a real stale Thought `HTTP 409` refusal.

## Click-depth ledger

| Measure | Audit-B before | After | Recorded browser clicks | Final evidence selector | Result |
|---|---:|---:|---|---|---|
| Tasks | 1 | 0 | none | `.door-board-section .door-board-column:has(h4:text-is('Now'))` | PASS |
| Upcoming | 1+ | 0 | none | `.door-upcoming-rail [data-upcoming-source="calendar_event"]` | PASS |
| Open schedule creation | 2 | 1 | Door rail → Schedule recording | `#schedule\:__create__` | PASS |

## Assertion details

### cold — PASS
- PASS — **cold narrow starts at First Sentence**. Scope: [data-testid="chair-first-value"].
- PASS — **cold narrow has editable pad and Continue later**. Scope: First Sentence container.
- PASS — **cold narrow has no Door**. Scope: whole document absence check.
- PASS — **cold 393: no page errors**. Scope: current browser document. []
- PASS — **cold 393: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **cold 393: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **cold starts at First Sentence**. Scope: [data-testid="chair-first-value"].
- PASS — **cold First Sentence heading is one job**. Scope: First Sentence container.
- PASS — **cold First Sentence has editable pad**. Scope: First Sentence container.
- PASS — **cold First Sentence has Click to speak**. Scope: First Sentence container.
- PASS — **cold First Sentence has continue verb**. Scope: First Sentence container.
- PASS — **cold has no Door before first value**. Scope: whole document absence check.
- PASS — **cold has no Desk chrome before first value**. Scope: whole document absence check.
- PASS — **cold has no fake transcript state**. Scope: First Sentence container.
- PASS — **cold 1440: no page errors**. Scope: current browser document. []
- PASS — **cold 1440: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **cold 1440: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **model-less speech returns named unavailability**. Scope: real /ws/dictation/stream browser protocol. {'type': 'error', 'error': 'Transcription unavailable.', 'reason': 'transcription_unavailable', 'failure_category': 'transcription_unavailable'}
- PASS — **typed first value visibly remains editable**. Scope: First Sentence editable pad.
- PASS — **typed first value reaches visible Desk result and custody within 3 minutes**. Scope: First Sentence real Continue later handoff. first_value_mode=typed_fallback elapsed_ms=1341.100
- PASS — **typed first value has authoritative note custody**. Scope: GET /api/notes after visible Desk handoff. notes=7
- PASS — **typed handoff reveals normal Door state**. Scope: normal Chair after First Sentence handoff.
- PASS — **typed first-value handoff: no page errors**. Scope: current browser document. []
- PASS — **typed first-value handoff: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **typed first-value handoff: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **post-handoff 393: no page errors**. Scope: current browser document. []
- PASS — **post-handoff 393: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **post-handoff 393: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.

### reveal — PASS
- PASS — **Door owns its summary**. Scope: .door-board-section.
- PASS — **Door owns upcoming rail**. Scope: .door-board-section.
- PASS — **Overdue column exists inside Door**. Scope: .door-board-section > .door-board-column heading Overdue.
- PASS — **Overdue owns its labelled source card**. Scope: Overdue Door column.
- PASS — **Overdue count label agrees with aggregate**. Scope: Overdue column count label.
- PASS — **Overdue API source id and title agree**. Scope: GET /api/door board.overdue. api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-27', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Now column exists inside Door**. Scope: .door-board-section > .door-board-column heading Now.
- PASS — **Now owns its labelled source card**. Scope: Now Door column.
- PASS — **Now count label agrees with aggregate**. Scope: Now column count label.
- PASS — **Now API source id and title agree**. Scope: GET /api/door board.now. api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Waiting column exists inside Door**. Scope: .door-board-section > .door-board-column heading Waiting.
- PASS — **Waiting owns its labelled source card**. Scope: Waiting Door column.
- PASS — **Waiting count label agrees with aggregate**. Scope: Waiting column count label.
- PASS — **Waiting API source id and title agree**. Scope: GET /api/door board.waiting. api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-02', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Active column exists inside Door**. Scope: .door-board-section > .door-board-column heading Active.
- PASS — **Active owns its labelled source card**. Scope: Active Door column.
- PASS — **Active count label agrees with aggregate**. Scope: Active column count label.
- PASS — **Active API source id and title agree**. Scope: GET /api/door board.active. api cards=[{'id': 'thought_f5674e79ab18', 'source': 'thought', 'target_ref': 'thought:thought_f5674e79ab18', 'open_ref': 'note:note_thought_43c983c6e0231566', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-28T08:08:06Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_f5674e79ab18', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}]
- PASS — **Unassigned owns source card without invented count**. Scope: Unassigned Door column.
- PASS — **rail owns baseline schedule**. Scope: .door-upcoming-rail.
- PASS — **schedule does not duplicate into retained Meetings lane**. Scope: retained Meetings lane absence check.
- PASS — **Door aggregate counts are exact fixture truth**. Scope: GET /api/door counts. {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 1}
- PASS — **reveal 1440: no page errors**. Scope: current browser document. []
- PASS — **reveal 1440: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **reveal 1440: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **Door owns its summary**. Scope: .door-board-section.
- PASS — **Door owns upcoming rail**. Scope: .door-board-section.
- PASS — **Overdue column exists inside Door**. Scope: .door-board-section > .door-board-column heading Overdue.
- PASS — **Overdue owns its labelled source card**. Scope: Overdue Door column.
- PASS — **Overdue count label agrees with aggregate**. Scope: Overdue column count label.
- PASS — **Overdue API source id and title agree**. Scope: GET /api/door board.overdue. api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-27', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Now column exists inside Door**. Scope: .door-board-section > .door-board-column heading Now.
- PASS — **Now owns its labelled source card**. Scope: Now Door column.
- PASS — **Now count label agrees with aggregate**. Scope: Now column count label.
- PASS — **Now API source id and title agree**. Scope: GET /api/door board.now. api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Waiting column exists inside Door**. Scope: .door-board-section > .door-board-column heading Waiting.
- PASS — **Waiting owns its labelled source card**. Scope: Waiting Door column.
- PASS — **Waiting count label agrees with aggregate**. Scope: Waiting column count label.
- PASS — **Waiting API source id and title agree**. Scope: GET /api/door board.waiting. api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-02', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Active column exists inside Door**. Scope: .door-board-section > .door-board-column heading Active.
- PASS — **Active owns its labelled source card**. Scope: Active Door column.
- PASS — **Active count label agrees with aggregate**. Scope: Active column count label.
- PASS — **Active API source id and title agree**. Scope: GET /api/door board.active. api cards=[{'id': 'thought_f5674e79ab18', 'source': 'thought', 'target_ref': 'thought:thought_f5674e79ab18', 'open_ref': 'note:note_thought_43c983c6e0231566', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-28T08:08:06Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_f5674e79ab18', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}]
- PASS — **Unassigned owns source card without invented count**. Scope: Unassigned Door column.
- PASS — **rail owns baseline schedule**. Scope: .door-upcoming-rail.
- PASS — **schedule does not duplicate into retained Meetings lane**. Scope: retained Meetings lane absence check.
- PASS — **Door aggregate counts are exact fixture truth**. Scope: GET /api/door counts. {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 1}
- PASS — **narrow board scroll belongs to board viewport**. Scope: .door-board-viewport.
- PASS — **reveal 393: no page errors**. Scope: current browser document. []
- PASS — **reveal 393: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **reveal 393: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **reveal 393: narrow Door board owns its intentional scroll**. Scope: .door-board-viewport only.
- PASS — **Door owns its summary**. Scope: .door-board-section.
- PASS — **Door owns upcoming rail**. Scope: .door-board-section.
- PASS — **Overdue column exists inside Door**. Scope: .door-board-section > .door-board-column heading Overdue.
- PASS — **Overdue owns its labelled source card**. Scope: Overdue Door column.
- PASS — **Overdue count label agrees with aggregate**. Scope: Overdue column count label.
- PASS — **Overdue API source id and title agree**. Scope: GET /api/door board.overdue. api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-27', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Now column exists inside Door**. Scope: .door-board-section > .door-board-column heading Now.
- PASS — **Now owns its labelled source card**. Scope: Now Door column.
- PASS — **Now count label agrees with aggregate**. Scope: Now column count label.
- PASS — **Now API source id and title agree**. Scope: GET /api/door board.now. api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Waiting column exists inside Door**. Scope: .door-board-section > .door-board-column heading Waiting.
- PASS — **Waiting owns its labelled source card**. Scope: Waiting Door column.
- PASS — **Waiting count label agrees with aggregate**. Scope: Waiting column count label.
- PASS — **Waiting API source id and title agree**. Scope: GET /api/door board.waiting. api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-02', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Active column exists inside Door**. Scope: .door-board-section > .door-board-column heading Active.
- PASS — **Active owns its labelled source card**. Scope: Active Door column.
- PASS — **Active count label agrees with aggregate**. Scope: Active column count label.
- PASS — **Active API source id and title agree**. Scope: GET /api/door board.active. api cards=[{'id': 'thought_f5674e79ab18', 'source': 'thought', 'target_ref': 'thought:thought_f5674e79ab18', 'open_ref': 'note:note_thought_43c983c6e0231566', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-28T08:08:06Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_f5674e79ab18', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}]
- PASS — **Unassigned owns source card without invented count**. Scope: Unassigned Door column.
- PASS — **rail owns baseline schedule**. Scope: .door-upcoming-rail.
- PASS — **schedule does not duplicate into retained Meetings lane**. Scope: retained Meetings lane absence check.
- PASS — **Door aggregate counts are exact fixture truth**. Scope: GET /api/door counts. {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 1}
- PASS — **narrow board scroll belongs to board viewport**. Scope: .door-board-viewport.
- PASS — **200% Door card action has visible keyboard focus**. Scope: Now Door card at DSF 2.
- PASS — **reveal 200%: no page errors**. Scope: current browser document. []
- PASS — **reveal 200%: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **reveal 200%: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **reveal 200%: narrow Door board owns its intentional scroll**. Scope: .door-board-viewport only.

### completion — PASS
- PASS — **completion target exposes production Done descriptor**. Scope: GET /api/door board.overdue descriptor. [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]
- PASS — **completion button belongs to named Overdue card**. Scope: Overdue Door column -> fixture card.
- PASS — **Done changes the authoritative Door aggregate**. Scope: GET /api/door after Door action.
- PASS — **Done changes its owning Overdue column within 500ms**. Scope: Overdue Door card detachment measured by page performance.now(). completion_ms=38.600
- PASS — **read active Thought for stale-refusal setup**. Scope: production HTTP authority GET /api/thoughts/thought_f5674e79ab18. status=200 payload={'thought': {'id': 'thought_f5674e79ab18', 'raw_id': 'thought_f5674e79ab18', 'raw_sha256': 'c3ef1083d1e712832249d018d4f85bd872a336c423f4497ae738659381bec4de', 'source': {'kind': 'typed'}, 'raw_captured_at': '2026-08-28T0
- PASS — **drift active Thought through custody authority**. Scope: production HTTP authority PATCH /api/thoughts/thought_f5674e79ab18/working. status=200 payload={'thought': {'id': 'thought_f5674e79ab18', 'raw_id': 'thought_f5674e79ab18', 'raw_sha256': 'c3ef1083d1e712832249d018d4f85bd872a336c423f4497ae738659381bec4de', 'source': {'kind': 'typed'}, 'raw_captured_at': '2026-08-28T0
- PASS — **stale 409 receipt stays in Door**. Scope: .door-board-section .door-board-receipt.
- PASS — **stale refusal opens no dialog**. Scope: whole document dialog absence.
- PASS — **completion and stale receipt: no page errors**. Scope: current browser document. []
- PASS — **completion and stale receipt: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **completion and stale receipt: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.

### schedule — PASS
- PASS — **Door schedule form is in-world**. Scope: #schedule\:__create__ opened from .door-upcoming-rail.
- PASS — **Door schedule form has voice-enabled title**. Scope: Door schedule form.
- PASS — **in-world schedule is authoritative and visible on Door rail**. Scope: production schedule list AND owning Door rail.
- PASS — **schedule 1440: no page errors**. Scope: current browser document. []
- PASS — **schedule 1440: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **schedule 1440: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **narrow Door schedule form is in-world**. Scope: #schedule\:__create__ opened from narrow .door-upcoming-rail.
- PASS — **schedule 393: no page errors**. Scope: current browser document. []
- PASS — **schedule 393: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **schedule 393: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **schedule 393: narrow Door board owns its intentional scroll**. Scope: .door-board-viewport only.

### calendar — PASS
- PASS — **Settings saves local fixture through its real control**. Scope: Settings Meetings Calendar subscription AND GET /api/settings. {'kind': 'file', 'host': '', 'refresh_seconds': 900, 'egress': False}
- PASS — **real CalendarIngestConductor refresh succeeds**. Scope: isolated child CalendarIngestConductor.refresh(). exit=0 stdout={"calendar_refresh": true} stderr=
- PASS — **fixture event is source-labelled inside Door rail**. Scope: .door-upcoming-rail calendar_event row.
- PASS — **fixture rail row owns location and meeting link**. Scope: calendar_event row in .door-upcoming-rail.
- PASS — **Door aggregate contains actual fixture calendar source**. Scope: GET /api/door upcoming. [{'id': 'sr_f33532dc8c41', 'source': 'scheduled_recording', 'target_ref': 'scheduled_recording:sr_f33532dc8c41', 'title': 'HS144 WALK baseline recording', 'starts_at': '2026-08-28T09:00:00Z', 'ends_at': '2026-08-28T09:30:00Z', 'location': None, 'meeting_url': None, 'state': 'idle'}, {'id': 'ce_d4e0f41e9df6c76099e3786addbaa65076a044f2d0f8736dd22c5ca440019614', 'source': 'calendar_event', 'target_ref': 'calendar_event:ce_d4e0f41e9df6c76099e3786addbaa65076a044f2d0f8736dd22c5ca440019614', 'title': 'HS144 WALK calendar fixture', 'starts_at': '2026-08-28T10:08:00Z', 'ends_at': '2026-08-28T10:53:00Z', 'location': 'Walk Room 4', 'meeting_url': 'https://meet.example.test/hs144-walk', 'state': 'scheduled'}, {'id': 'sr_a1c10f638fb9', 'source': 'scheduled_recording', 'target_ref': 'scheduled_recording:sr_a1c10f638fb9', 'title': 'HS144 WALK in-world recording', 'starts_at': '2027-08-28T02:38:00Z', 'ends_at': '2027-08-28T03:38:00Z', 'location': None, 'meeting_url': None, 'state': 'idle'}]
- PASS — **calendar fixture rail: no page errors**. Scope: current browser document. []
- PASS — **calendar fixture rail: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **calendar fixture rail: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **HTTPS subscription egress fact is true**. Scope: GET /api/settings derived calendar fact. {'kind': 'https', 'host': 'calendar.example.test', 'refresh_seconds': 900, 'egress': True}
- PASS — **egress chip belongs to Settings subscription control**. Scope: #surface-settings Meetings Calendar GadgetRow (not global chrome).
- PASS — **Settings restores local fixture before cleanup**. Scope: Settings Meetings Calendar subscription.
- PASS — **calendar egress fact: no page errors**. Scope: current browser document. []
- PASS — **calendar egress fact: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **calendar egress fact: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.

### click-depth — PASS
- PASS — **click-depth Tasks is direct board evidence**. Scope: Overdue and Now Door columns. completed fixture is absent; Now remains direct task evidence
- PASS — **click-depth Tasks has settled Now card and count**. Scope: Now Door column.
- PASS — **click-depth Tasks uses zero clicks**. Scope: ClickLedger Tasks.
- PASS — **click-depth Upcoming is direct rail evidence**. Scope: .door-upcoming-rail calendar row.
- PASS — **click-depth Upcoming uses zero clicks**. Scope: ClickLedger Upcoming.
- PASS — **click-depth schedule form opens after one Door click**. Scope: ClickLedger Schedule + #schedule\:__create__.
- PASS — **click-depth: no page errors**. Scope: current browser document. []
- PASS — **click-depth: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **click-depth: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.

### doorframe — PASS
- PASS — **393 Go is visible Desk chrome control**. Scope: .desk-menubar.
- PASS — **393 Go owns Meetings registered app**. Scope: role=menu[name="Go menu"].
- PASS — **393 Go Meetings opens registered Meetings surface**. Scope: #surface-meetings.
- PASS — **doorframe Go 393: no page errors**. Scope: current browser document. []
- PASS — **doorframe Go 393: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **doorframe Go 393: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **doorframe Go 393: narrow Door board owns its intentional scroll**. Scope: .door-board-viewport only.
- PASS — **deep-link 01/15 registered Meetings visible**. Scope: fresh desktop document 1 /meetings.
- PASS — **deep-link desktop 01: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 01: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 01: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 02/15 registered Meetings visible**. Scope: fresh desktop document 2 /meetings.
- PASS — **deep-link desktop 02: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 02: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 02: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 03/15 registered Meetings visible**. Scope: fresh desktop document 3 /meetings.
- PASS — **deep-link desktop 03: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 03: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 03: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 04/15 registered Meetings visible**. Scope: fresh desktop document 4 /meetings.
- PASS — **deep-link desktop 04: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 04: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 04: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 05/15 registered Meetings visible**. Scope: fresh desktop document 5 /meetings.
- PASS — **deep-link desktop 05: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 05: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 05: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 06/15 registered Meetings visible**. Scope: fresh desktop document 6 /meetings.
- PASS — **deep-link desktop 06: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 06: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 06: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 07/15 registered Meetings visible**. Scope: fresh desktop document 7 /meetings.
- PASS — **deep-link desktop 07: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 07: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 07: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 08/15 registered Meetings visible**. Scope: fresh desktop document 8 /meetings.
- PASS — **deep-link desktop 08: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 08: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 08: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 09/15 registered Meetings visible**. Scope: fresh desktop document 9 /meetings.
- PASS — **deep-link desktop 09: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 09: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 09: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 10/15 registered Meetings visible**. Scope: fresh desktop document 10 /meetings.
- PASS — **deep-link desktop 10: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 10: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 10: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 11/15 registered Meetings visible**. Scope: fresh desktop document 11 /meetings.
- PASS — **deep-link desktop 11: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 11: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 11: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 12/15 registered Meetings visible**. Scope: fresh desktop document 12 /meetings.
- PASS — **deep-link desktop 12: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 12: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 12: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 13/15 registered Meetings visible**. Scope: fresh desktop document 13 /meetings.
- PASS — **deep-link desktop 13: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 13: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 13: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 14/15 registered Meetings visible**. Scope: fresh desktop document 14 /meetings.
- PASS — **deep-link desktop 14: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 14: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 14: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **deep-link 15/15 registered Meetings visible**. Scope: fresh desktop document 15 /meetings.
- PASS — **deep-link desktop 15: no page errors**. Scope: current browser document. []
- PASS — **deep-link desktop 15: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link desktop 15: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **narrow fresh /meetings reaches registered surface**. Scope: fresh 393px /meetings document.
- PASS — **deep-link narrow: no page errors**. Scope: current browser document. []
- PASS — **deep-link narrow: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **deep-link narrow: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **pair assets exist: after-chair-home-1440.png**. Scope: before/after pair manifest. before=True after=True
- PASS — **claimed changed pair is not byte-identical: after-chair-home-1440.png**. Scope: SHA-256 false-positive tell. hashes differ
- PASS — **pair assets exist: after-chair-home-393.png**. Scope: before/after pair manifest. before=True after=True
- PASS — **claimed changed pair is not byte-identical: after-chair-home-393.png**. Scope: SHA-256 false-positive tell. hashes differ
- PASS — **pair assets exist: after-cadence-surface-1440.png**. Scope: before/after pair manifest. before=True after=True
- PASS — **claimed changed pair is not byte-identical: after-cadence-surface-1440.png**. Scope: SHA-256 false-positive tell. hashes differ
- PASS — **pair assets exist: after-cadence-surface-393.png**. Scope: before/after pair manifest. before=True after=True
- PASS — **claimed changed pair is not byte-identical: after-cadence-surface-393.png**. Scope: SHA-256 false-positive tell. hashes differ
- PASS — **pair assets exist: cold-first-value-1440.png**. Scope: before/after pair manifest. before=True after=True
- PASS — **pair assets exist: cold-first-value-393.png**. Scope: before/after pair manifest. before=True after=True

## Evidence

- Shots: `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-06-shots/`
- Machine JSON: `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-06-walk-report.json`
- Pair manifest: `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-06-pairs.json` and `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-06-pairs.md`
- Owner review / beauty verdict / Tuesday answer: pending owner shot review; this worker does not fabricate an owner nod.

## Cleanup

- closed Playwright browser
- stopped hub pid=65478 exit=0
- deleted ICS fixture tree: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs144-door-walk-m25l6yg9/fixtures
- deleted walk HOME/XDG/TMP tree: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs144-door-walk-m25l6yg9
- cleanup=pass
