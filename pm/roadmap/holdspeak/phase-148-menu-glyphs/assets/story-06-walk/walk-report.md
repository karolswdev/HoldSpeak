# HS-144-06 — cold Door walk report

**Mode:** full cold walk
**Result:** PASS

## Leg results

| Leg | Result | Timing / fact | Assertion scope |
|---|---|---|---|
| cold | PASS | 1860.900 ms | First Sentence container; First Sentence editable pad |
| reveal | PASS | — | .door-board-section; .door-board-section > .door-board-column heading Active |
| completion | PASS | 50.700 ms | .door-board-section .door-board-receipt; GET /api/door after Door action |
| schedule | PASS | — | #schedule\:__create__ opened from .door-upcoming-rail; #schedule\:__create__ opened from narrow .door-upcoming-rail |
| calendar | PASS | — | .door-upcoming-rail calendar_event row; .door-upcoming-rail scheduled_recording row |
| one-tap | PASS | — | 60s-lead ruling (D4); DELETE via door-cancel-confirm + GET /api/scheduled-recordings |
| click-depth | PASS | — | .door-upcoming-rail calendar row; ClickLedger Schedule + #schedule\:__create__ |
| doorframe | PASS | — | #surface-meetings; .desk-menubar |
| menus | PASS | — | .desk-menu-ghost-hint majority-collapse; .desk-menu-glyph lane law |

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
- PASS — **typed first value reaches visible Desk result and custody within 3 minutes**. Scope: First Sentence real Continue later handoff. first_value_mode=typed_fallback elapsed_ms=1860.900
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
- PASS — **Overdue API source id and title agree**. Scope: GET /api/door board.overdue. api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Now column exists inside Door**. Scope: .door-board-section > .door-board-column heading Now.
- PASS — **Now owns its labelled source card**. Scope: Now Door column.
- PASS — **Now count label agrees with aggregate**. Scope: Now column count label.
- PASS — **Now API source id and title agree**. Scope: GET /api/door board.now. api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-29', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Waiting column exists inside Door**. Scope: .door-board-section > .door-board-column heading Waiting.
- PASS — **Waiting owns its labelled source card**. Scope: Waiting Door column.
- PASS — **Waiting count label agrees with aggregate**. Scope: Waiting column count label.
- PASS — **Waiting API source id and title agree**. Scope: GET /api/door board.waiting. api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-03', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Active column exists inside Door**. Scope: .door-board-section > .door-board-column heading Active.
- PASS — **Active owns its labelled source card**. Scope: Active Door column.
- PASS — **Active count label agrees with aggregate**. Scope: Active column count label.
- PASS — **Active API source id and title agree**. Scope: GET /api/door board.active. api cards=[{'id': 'thought_699ad5132ad3', 'source': 'thought', 'target_ref': 'thought:thought_699ad5132ad3', 'open_ref': 'note:note_thought_b50641538e337fc7', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-29T17:07:10Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_699ad5132ad3', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}]
- PASS — **Unassigned owns source card without invented count**. Scope: Unassigned Door column.
- PASS — **rail owns baseline schedule**. Scope: .door-upcoming-rail.
- PASS — **schedule does not duplicate into retained Meetings lane**. Scope: retained Meetings lane absence check.
- PASS — **Door aggregate counts are exact fixture truth**. Scope: GET /api/door counts. {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 0}
- PASS — **reveal 1440: no page errors**. Scope: current browser document. []
- PASS — **reveal 1440: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **reveal 1440: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **Door owns its summary**. Scope: .door-board-section.
- PASS — **Door owns upcoming rail**. Scope: .door-board-section.
- PASS — **Overdue column exists inside Door**. Scope: .door-board-section > .door-board-column heading Overdue.
- PASS — **Overdue owns its labelled source card**. Scope: Overdue Door column.
- PASS — **Overdue count label agrees with aggregate**. Scope: Overdue column count label.
- PASS — **Overdue API source id and title agree**. Scope: GET /api/door board.overdue. api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Now column exists inside Door**. Scope: .door-board-section > .door-board-column heading Now.
- PASS — **Now owns its labelled source card**. Scope: Now Door column.
- PASS — **Now count label agrees with aggregate**. Scope: Now column count label.
- PASS — **Now API source id and title agree**. Scope: GET /api/door board.now. api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-29', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Waiting column exists inside Door**. Scope: .door-board-section > .door-board-column heading Waiting.
- PASS — **Waiting owns its labelled source card**. Scope: Waiting Door column.
- PASS — **Waiting count label agrees with aggregate**. Scope: Waiting column count label.
- PASS — **Waiting API source id and title agree**. Scope: GET /api/door board.waiting. api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-03', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Active column exists inside Door**. Scope: .door-board-section > .door-board-column heading Active.
- PASS — **Active owns its labelled source card**. Scope: Active Door column.
- PASS — **Active count label agrees with aggregate**. Scope: Active column count label.
- PASS — **Active API source id and title agree**. Scope: GET /api/door board.active. api cards=[{'id': 'thought_699ad5132ad3', 'source': 'thought', 'target_ref': 'thought:thought_699ad5132ad3', 'open_ref': 'note:note_thought_b50641538e337fc7', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-29T17:07:10Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_699ad5132ad3', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}]
- PASS — **Unassigned owns source card without invented count**. Scope: Unassigned Door column.
- PASS — **rail owns baseline schedule**. Scope: .door-upcoming-rail.
- PASS — **schedule does not duplicate into retained Meetings lane**. Scope: retained Meetings lane absence check.
- PASS — **Door aggregate counts are exact fixture truth**. Scope: GET /api/door counts. {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 0}
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
- PASS — **Overdue API source id and title agree**. Scope: GET /api/door board.overdue. api cards=[{'id': 'hs144-walk-overdue', 'text': 'HS144 WALK unblock overdue Door', 'owner': 'Ada', 'due': '2026-08-28', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'overdue', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-overdue', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-overdue', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Now column exists inside Door**. Scope: .door-board-section > .door-board-column heading Now.
- PASS — **Now owns its labelled source card**. Scope: Now Door column.
- PASS — **Now count label agrees with aggregate**. Scope: Now column count label.
- PASS — **Now API source id and title agree**. Scope: GET /api/door board.now. api cards=[{'id': 'hs144-walk-now', 'text': 'HS144 WALK review Door today', 'owner': 'Bea', 'due': '2026-08-29', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'now', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-now', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-now', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Waiting column exists inside Door**. Scope: .door-board-section > .door-board-column heading Waiting.
- PASS — **Waiting owns its labelled source card**. Scope: Waiting Door column.
- PASS — **Waiting count label agrees with aggregate**. Scope: Waiting column count label.
- PASS — **Waiting API source id and title agree**. Scope: GET /api/door board.waiting. api cards=[{'id': 'hs144-walk-waiting', 'text': 'HS144 WALK prepare next review', 'owner': 'Cy', 'due': '2026-09-03', 'status': 'pending', 'meeting_id': 'hs144-walk-source-meeting', 'decision_id': None, 'stale_score': None, 'source': 'action_item', 'lane': 'waiting', 'provenance': {'meeting_id': 'hs144-walk-source-meeting', 'segment_text': None, 'segment_speaker': None, 'segment_start': None, 'moment': None, 'available': False}, 'target_ref': 'action_item:hs144-walk-waiting', 'lawful_verbs': [{'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'done'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'dismiss'}}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'snooze'}, 'required_arguments': ['payload.until']}, {'name': 'follow_through.complete', 'arguments': {'card_id': 'hs144-walk-waiting', 'verb': 'delegate'}, 'required_arguments': ['payload.to']}]}]
- PASS — **Active column exists inside Door**. Scope: .door-board-section > .door-board-column heading Active.
- PASS — **Active owns its labelled source card**. Scope: Active Door column.
- PASS — **Active count label agrees with aggregate**. Scope: Active column count label.
- PASS — **Active API source id and title agree**. Scope: GET /api/door board.active. api cards=[{'id': 'thought_699ad5132ad3', 'source': 'thought', 'target_ref': 'thought:thought_699ad5132ad3', 'open_ref': 'note:note_thought_b50641538e337fc7', 'title': 'HS144 WALK active thought', 'body_preview': 'HTTP custody route created this thought.', 'state': 'working', 'continuity_state': 'idle', 'updated_at': '2026-08-29T17:07:10Z', 'aggregate_revision': 1, 'lifecycle_revision': 1, 'filing_status': 'filed', 'lawful_verbs': [{'name': 'thought.complete', 'arguments': {'thought_id': 'thought_699ad5132ad3', 'expected_aggregate_revision': 1, 'expected_lifecycle_revision': 1}, 'required_arguments': ['request_id']}]}]
- PASS — **Unassigned owns source card without invented count**. Scope: Unassigned Door column.
- PASS — **rail owns baseline schedule**. Scope: .door-upcoming-rail.
- PASS — **schedule does not duplicate into retained Meetings lane**. Scope: retained Meetings lane absence check.
- PASS — **Door aggregate counts are exact fixture truth**. Scope: GET /api/door counts. {'overdue': 1, 'now': 1, 'waiting': 1, 'active': 1, 'upcoming_today': 0}
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
- PASS — **Done changes its owning Overdue column within 500ms**. Scope: Overdue Door card detachment measured by page performance.now(). completion_ms=50.700
- PASS — **read active Thought for stale-refusal setup**. Scope: production HTTP authority GET /api/thoughts/thought_699ad5132ad3. status=200 payload={'thought': {'id': 'thought_699ad5132ad3', 'raw_id': 'thought_699ad5132ad3', 'raw_sha256': 'c3ef1083d1e712832249d018d4f85bd872a336c423f4497ae738659381bec4de', 'source': {'kind': 'typed'}, 'raw_captured_at': '2026-08-29T1
- PASS — **drift active Thought through custody authority**. Scope: production HTTP authority PATCH /api/thoughts/thought_699ad5132ad3/working. status=200 payload={'thought': {'id': 'thought_699ad5132ad3', 'raw_id': 'thought_699ad5132ad3', 'raw_sha256': 'c3ef1083d1e712832249d018d4f85bd872a336c423f4497ae738659381bec4de', 'source': {'kind': 'typed'}, 'raw_captured_at': '2026-08-29T1
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
- PASS — **Settings saves local fixture through sources-wire API**. Scope: PUT /api/settings calendar.sources AND _calendar_sources fact. [{'kind': 'file', 'host': '', 'refresh_seconds': 900, 'egress': False, 'id': 'walk-file', 'label': 'Walk File', 'enabled': True}]
- PASS — **real CalendarIngestConductor refresh succeeds**. Scope: isolated child CalendarIngestConductor.refresh(). exit=0 stdout={"calendar_refresh": true} stderr=
- PASS — **fixture event is source-labelled inside Door rail**. Scope: .door-upcoming-rail calendar_event row.
- PASS — **calendar evidence also shows scheduled-recording rail row**. Scope: .door-upcoming-rail scheduled_recording row.
- PASS — **fixture rail row owns location and meeting link**. Scope: calendar_event row in .door-upcoming-rail.
- PASS — **Door aggregate contains actual fixture calendar source**. Scope: GET /api/door upcoming. [{'id': 'ce_37ebf40e2879d599b13d8cc485e14a8eb50130f0d65d4267834e124a6a30a71d', 'source': 'calendar_event', 'target_ref': 'calendar_event:ce_37ebf40e2879d599b13d8cc485e14a8eb50130f0d65d4267834e124a6a30a71d', 'title': 'HS144 WALK calendar fixture', 'starts_at': '2026-08-29T19:07:00Z', 'ends_at': '2026-08-29T19:52:00Z', 'location': 'Walk Room 4', 'meeting_url': 'https://meet.example.test/hs144-walk', 'state': 'scheduled', 'source_id': 'walk-file', 'source_label': 'Walk File'}, {'id': 'sr_10550d4495f5', 'source': 'scheduled_recording', 'target_ref': 'scheduled_recording:sr_10550d4495f5', 'title': 'HS144 WALK baseline recording', 'starts_at': '2026-08-30T09:00:00Z', 'ends_at': '2026-08-30T09:30:00Z', 'location': None, 'meeting_url': None, 'state': 'idle'}, {'id': 'sr_dfe63179c28d', 'source': 'scheduled_recording', 'target_ref': 'scheduled_recording:sr_dfe63179c28d', 'title': 'HS144 WALK in-world recording', 'starts_at': '2027-08-29T11:37:00Z', 'ends_at': '2027-08-29T12:37:00Z', 'location': None, 'meeting_url': None, 'state': 'idle'}]
- PASS — **calendar evidence capture has no Settings window**. Scope: fresh Door capture document.
- PASS — **calendar fixture rail: no page errors**. Scope: current browser document. []
- PASS — **calendar fixture rail: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **calendar fixture rail: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **HTTPS sources-wire egress fact is true**. Scope: PUT /api/settings calendar.sources derived _calendar_sources fact. [{'kind': 'https', 'host': 'calendar.example.test', 'refresh_seconds': 900, 'egress': True, 'id': 'walk-https', 'label': '', 'enabled': True}]
- PASS — **Settings restores local fixture before cleanup**. Scope: PUT /api/settings calendar.sources restore.
- PASS — **calendar egress fact: no page errors**. Scope: current browser document. []
- PASS — **calendar egress fact: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **calendar egress fact: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.

### one-tap — PASS
- PASS — **one-tap fixture refresh succeeds**. Scope: isolated child CalendarIngestConductor.refresh(). exit=0
- PASS — **both one-tap events reach the aggregate**. Scope: GET /api/door upcoming. ['HS144 WALK calendar fixture', 'HS144 WALK one-tap review', 'HS144 WALK one-tap standup']
- PASS — **every event row offers RECORD THIS**. Scope: [data-upcoming-source="calendar_event"] door-record-this.
- PASS — **one tap arms a linked enabled one-shot**. Scope: POST via door-record-this + GET /api/scheduled-recordings. [{'id': 'sr_7e35e054700e', 'title': 'HS144 WALK one-tap standup', 'cron_expr': '0 0 1 1 *', 'tz': 'MDT', 'one_shot': True, 'duration_minutes': 45, 'enabled': True, 'revision': 1, 'created_at': '2026-08-29T17:07:39Z', 'last_fired_at': None, 'next_fire_at': '2026-08-29T19:06:00Z', 'armed_at': None, 'deadline_at': None, 'state': 'idle', 'last_outcome': '', 'last_receipt_id': '', 'delegation_receipt_id': 'sr_rcpt_214e609245f5', 'calendar_event_id': 'ce_8a05176c46ccd652e636dc02d7da5356edda5449455a1029a333414a77b183f2', 'calendar_uid': 'hs147-walk-a', 'calendar_source_id': 'walk-one-tap'}]
- PASS — **armed fire time carries the 60s lead**. Scope: 60s-lead ruling (D4). next_fire_at=2026-08-29T19:06:00Z expected_epoch=1788030360.0
- PASS — **one intent renders one row (linked schedule suppressed)**. Scope: GET /api/door upcoming suppression ruling.
- PASS — **two-beat cancel disarms server-side**. Scope: DELETE via door-cancel-confirm + GET /api/scheduled-recordings.
- PASS — **stale tap refuses in-flow by name**. Scope: door-arm-refusal on the stale row (live L1 guard). ALREADY ARMED
- PASS — **one-tap 1440: no page errors**. Scope: current browser document. []
- PASS — **one-tap 1440: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **one-tap 1440: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **synced linked meeting keeps calendar_event_id (round-trip law)**. Scope: POST /api/sync/push + GET /api/meetings. [{'id': 'hs147-walk-linked-meeting', 'started_at': '2026-08-29T16:07:39.351121', 'ended_at': '2026-08-29T16:52:39.351121', 'title': 'HS144 WALK one-tap review', 'duration_seconds': 2700, 'segment_count': 0, 'action_item_count': 0, 'tags': [], 'intel_status': 'disabled', 'intel_status_detail': None, 'capture_status': 'finalized', 'capture_failure': None, 'capture_checkpoint_seconds': 0, 'provenance': 'native', 'calendar_event_id': 'ce_6424ee2a39846a246e7194c2eee7804222042c06ef1ff649b05a5904c420046b', 'calendar_event_title': 'HS144 WALK one-tap review', 'calendar_source_label': 'Walk Tap'}]
- PASS — **Meetings surface wears the origin line**. Scope: [data-meeting-origin="calendar-event"] on the Meetings surface. FROM WALK TAP · HS144 WALK ONE-TAP REVIEW
- PASS — **one-tap origin line: no page errors**. Scope: current browser document. []
- PASS — **one-tap origin line: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **one-tap origin line: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **one-tap 393: no page errors**. Scope: current browser document. []
- PASS — **one-tap 393: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **one-tap 393: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.

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

### menus — PASS
- PASS — **Go menu declares launcher context**. Scope: nav[role=menu] data-menu-context.
- PASS — **Go menu wears the glyph lane**. Scope: .desk-menu-glyph lane law. glyph spans=13
- PASS — **keycaps render as drawn wells**. Scope: .desk-menu-well keycap wells.
- PASS — **D3 repair: click-open focuses the first item**. Scope: autoFocus on intentional bar open (3s poll). activeElement role=menuitem
- PASS — **ghosted rows carry the stipple class**. Scope: .is-ghost stipple law. is-ghost=9
- PASS — **majority ghost reason collapses to one footer**. Scope: .desk-menu-ghost-hint majority-collapse.
- PASS — **minority reason stays inline once**. Scope: inline minority ghost reason.
- PASS — **keycaps stay visible when ghosted**. Scope: ghosted keycap wells.
- PASS — **head menu carries registry labels + keycaps**. Scope: registry-derived head menu (AA graduation).
- PASS — **list-view context menu is reachable (ledger item closed)**. Scope: list-view row contextmenu.
- PASS — **menus list-view leg: no page errors**. Scope: current browser document. []
- PASS — **menus list-view leg: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **menus list-view leg: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
- PASS — **393 Go wears lane + wells**. Scope: 393 Go grammar.
- PASS — **menus 393 leg: no page errors**. Scope: current browser document. []
- PASS — **menus 393 leg: document has no horizontal overflow**. Scope: document root; Door board viewport is not exempt.
- PASS — **menus 393 leg: body has no horizontal overflow**. Scope: body; Door board viewport is not exempt.
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

- Shots: `pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/story-06-walk/shots/`
- Machine JSON: `pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/story-06-walk/walk-report.json`
- Pair manifest: `pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/story-06-walk/walk-pairs.json` and `pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/story-06-walk/walk-pairs.md`
- Owner review / beauty verdict / Tuesday answer: pending owner shot review; this worker does not fabricate an owner nod.

## Cleanup

- closed Playwright browser
- stopped hub pid=33883 exit=0
- deleted ICS fixture tree: /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/walk148-tmp/hs144-door-walk-w_gm97rb/fixtures
- deleted walk HOME/XDG/TMP tree: /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/walk148-tmp/hs144-door-walk-w_gm97rb
- cleanup=pass
