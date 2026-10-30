# Phone: the recipe

The slices that make `PHONE-DESIGN-2026-10-28.md` real. The owner asked for
it on 2026-10-28 ("Do it. And definitely swallow the paradigm and 'vendor'
it"), so PH1 to PH10 ship in one PR from the program branch
`lane/phone-20261028`, built by three lanes (PH-HUB, PH-FACES, PH-DOCS;
design §13). The slices after PH10 are left for later PRs in the fast cycle
(`CLAUDE.md`). Short paths: `desk/` is `web/src/desk/`, `hs/` is
`holdspeak/`. Tests follow the test diet: T1 a hub test, T2 vitest (one file
per app), T3 the desk sweep, T4 a real browser only for keys, drag or touch.

**The rig for every slice.** `tests/fixtures/fake_phone_device.py` is a tiny
phone: it pairs, opens the event stream, accepts or declines a call and
replies to a message. The fake ai-phone of the Calls rig
(`tests/fixtures/fake_ai_phone.py`) carries a call on the number.
`scripts/record_phone_fixtures.py` records the hub's real answers into
`tests/fixtures/phone/` and `desk/calls/__fixtures__/`. Every rig hub sets
`HOLDSPEAK_PHONE=off` unless the test drives Phone.

State: **Shipped** means in this PR. **Left** means a later slice.

---

## PH1. The record and the event log (Shipped)

- **Goal**: devices, messages, calls and one sequence-numbered event log are
  stored, and a phone replays what it missed.
- **Files**: `hs/db/schema.py` (+ `tests/fixtures/db_schema_canonical.txt`),
  `hs/phone/store.py`, `hs/phone/events.py`, `hs/phone/contract.py`.
- **Changes**: `phone_devices`, `phone_messages`, `phone_calls`,
  `phone_events` (one index on `ts`); `append_event` gives each change its
  `seq`; replay from `after_seq`; the hello frame; pydantic models that
  round-trip the recorded fixtures.
- **Done when**: a phone that reconnects with `after_seq` gets every event
  after it, in order, once.
- **Tests**: T1 `tests/unit/test_phone_contract.py`;
  `tests/integration/test_phone_flow.py::test_the_event_log_replays_from_after_seq_after_a_reconnect`.

## PH2. Pairing and the device token (Shipped)

- **Goal**: he pairs a phone with a QR; the phone has its own revocable
  token.
- **Files**: `hs/phone/devices.py`, `hs/principals.py` (the device routes),
  `hs/web/routes/phone.py`.
- **Changes**: a 10-minute token (24 random bytes, kept as a hash, used
  once); the QR payload names the address he pressed Pair on; an HS256
  device JWT checked against the device row on every request; revoke closes
  the socket with 4401.
- **Done when**: a revoked phone gets 401 and its socket closes.
- **Tests**: T1 `tests/unit/test_phone_devices.py`;
  `test_phone_flow.py::test_a_revoked_phone_gets_401_and_its_socket_closes`.

## PH3. Messages, replies and read receipts (Shipped)

- **Goal**: the desk sends one line; he replies from the phone; the reply is
  read once.
- **Files**: `hs/phone/service.py`.
- **Changes**: `send_message` (500 characters, the redactor, a step's 3 an
  hour), `reply_to` threads, `delivered` and `read`, `get_replies(wait_s)`
  that waits and returns each reply once, the SILENCE note.
- **Done when**: the fake phone gets the message, replies, and
  `phone.get_replies` reads the reply once.
- **Tests**: `test_phone_flow.py::test_a_paired_phone_gets_the_message_replies_and_get_replies_reads_it_once`,
  `::test_get_replies_waits_for_the_reply_instead_of_polling`.

## PH4. The call state machine (Shipped)

- **Goal**: a call rings, is answered, missed, declined or ended, and a
  missed call is never lost.
- **Files**: `hs/phone/calls.py`, `hs/phone/service.py`.
- **Changes**: one ring timer per call (30 s); an urgent call rings once
  more after 60 s; a missed app call falls back to the number when there is
  a line; else it is one message with its reason and a Needs you row.
- **Done when**: every state has its moves, and a call the phone does not
  answer becomes a missed message.
- **Tests**: T1 `tests/unit/test_phone_calls.py`;
  `test_phone_flow.py::test_a_call_the_phone_does_not_answer_becomes_a_missed_message_and_a_needs_you_row`,
  `::test_an_urgent_call_rings_once_more_then_is_missed`,
  `::test_an_answered_call_is_accepted_and_ended_by_the_phone`.

## PH5. Push (Shipped)

- **Goal**: a locked phone wakes for a call and shows a message.
- **Files**: `hs/phone/push.py`.
- **Changes**: `PushProvider` (`ok`, `unregistered`, `error`); `ApnsPush`
  (token auth with his .p8 key from the keystore; the VoIP topic for a call,
  an alert with a reply category for a message); `NullPush` for rigs and
  until his key; the signed payload `{v, hub, event, sig}`, a long message
  cut.
- **Done when**: the signature checks and a long message is cut.
- **Tests**: T1 `tests/unit/test_phone_push.py`.
- **Not in this slice**: the `httpx[http2]` extra (PH13).

## PH6. The number transport and answer-later (Shipped)

- **Goal**: a `phone.call` rings his real number through Calls and comes back
  with the words and his decision; a slow hand does not leave the line
  quiet.
- **Files**: `hs/phone/transport_number.py`, `hs/calls/runner.py`,
  `hs/calls/service.py`.
- **Changes**: the call through ai-phone `call --relay`; answer-later: a hand
  slower than 20 s says "I am working on it" and the answer comes as a later
  turn or a message after the hang-up.
- **Done when**: a call through the fake ai-phone returns a transcript and a
  decision.
- **Tests**: T1 `tests/unit/test_phone_answer_later.py`;
  `test_phone_flow.py::test_phone_call_on_the_number_runs_through_calls_and_returns_the_transcript_and_decision`,
  `::test_a_slow_hand_says_working_on_it_and_answers_as_a_message_after_the_hang_up`.

## PH7. Reach: the rules by control level (Shipped)

- **Goal**: the desk decides by rule when to message or call him.
- **Files**: `hs/phone/phone_rules.py`, `hs/kernel/phone_ops.py`,
  `hs/services/program_service.py` (`reach_phone`),
  `hs/services/program_runner.py`, `hs/program_templates.py`,
  `hs/db/programs.py`.
- **Changes**: `reach(level, kind, facts)` with the §6 table; his own word
  per kind wins; a reply ends it; never twice in 5 minutes; never a call
  during a call; quiet hours from Settings ▸ Rhythm; the kernel operation
  `phone.reach`; a Decided for you line; `may_call` on Program and step (on
  in Overnight).
- **Done when**: each row of §6 has a test at each level, and a Program's
  core question reaches the phone with its line.
- **Tests**: T1 `tests/unit/test_phone_rules.py`;
  `test_phone_flow.py::test_the_rules_per_level_through_the_service`,
  `::test_quiet_hours_hold_a_message_and_let_an_urgent_call_through`,
  `::test_a_programs_core_question_reaches_the_phone_with_a_decided_for_you_line`.

## PH8. The desk's tools: REST, MCP, the frame, Needs you (Shipped)

- **Goal**: agents and the faces reach Phone through one service.
- **Files**: `hs/web/routes/phone.py`, `hs/mcp/families/phone.py`,
  `hs/mcp/tool_authority.py`, `hs/services/conductor_launch.py`,
  `hs/services/needs_you_membership.py` (`phone_items`),
  `hs/realtime_frames.py`, `hs/web/announce.py`.
- **Changes**: 15 routes off the loop (one carries accept, decline, end, ring and again; one is the socket); four MCP tools (`phone.call` EGRESS;
  a launch gets only the WORK three); Needs you rows "Asked on your phone",
  "Missed call", "Call you about …?", "No phone is paired"; the frame
  `phone_changed`; `HOLDSPEAK_PHONE=off`.
- **Done when**: an agent's call waits for his press in Needs you, and a hub
  with Phone off registers nothing.
- **Tests**: `test_phone_flow.py::test_an_agents_call_waits_for_his_press_in_needs_you`,
  `::test_phone_off_registers_nothing`; the API surface regen.

## PH9. The faces (In this PR, the PH-FACES lane)

- **Goal**: §9 of the design: Settings ▸ Calls ▸ Phone (Pair a phone with
  the QR, Reach you, the number), Phone in the Calls window (the thread with
  a mic composer, the calls, the devices), the Needs you rows, the Reach line
  under Decided for you.
- **Files**: `desk/calls/`.
- **Done when**: every state is drawn from the recorded fixtures at 1440 and
  393; the presses go through.
- **Tests**: T2 vitest on the Calls app with `desk/calls/__fixtures__/phone.*`;
  T3 the desk sweep.

## PH10. The documents (Shipped)

- **Files**: this recipe, the design's "Built" section,
  `ABSORBED-FROM-AGENTRING.md`, `NOTICE`, `docs/phone.md`,
  `agent/skills/holdspeak-phone/SKILL.md`, `README.md`, `docs/README.md`,
  `docs/internal/UX-CANON.md`, `INVENTORY.md`, `TRACKER.md`,
  `pm/STATUS.md`.
- **Tests**: the docs guards (`tests/unit/test_docs_navigation.py`,
  `test_product_copy.py`, `test_api_surface.py`,
  `test_mcp_sidecar_doc_drift.py`, `test_engines_name_guard.py`).

---

## PH11. SMS on the number (Left)

ai-phone has no SMS command, so a message with no paired phone waits as a
Needs you row ("No phone is paired"). When ai-phone (or the line) can send
SMS, `transport_number.sms_available` turns true and the message goes out as
a text.

## PH12. The other reach kinds (Shipped 2026-10-29, lane PHONE-NEXT)

- **Goal**: the rules for `heartbeat_security`, `aftercare` and
  `agent_question` have callers, at the places that write their Needs you rows.
- **Files**: `hs/phone/reach_sites.py` (new), `hs/services/heartbeat_service.py`,
  `hs/intel_queue_conductor.py`, `hs/meeting_session/persistence.py`,
  `hs/services/meeting_intel_service.py`, `hs/services/agent_responder.py`,
  `hs/phone/service.py`.
- **Changes**: after a heartbeat sweep builds Needs you, each row tagged
  security or data loss, or a Program finding whose words the Programs rules
  call security or data loss (`is_core`), reaches him once per row
  (`heartbeat:<row id>`; the sweep receipt lists the reaches). Where a
  recorded meeting's aftercare is ready (the three `aftercare_ready` emitters),
  its open items and proposals to review reach him once
  (`meeting:<id>:aftercare`). The agent responder reaches him for a question
  the desk could not draft (a REAL verdict, and every question at Secure),
  once per wait (`agent:<key>:<wait id>`); "away" is a fact of every reach
  (no desk presence for 30 minutes). The phone's sweep asks the responder
  whether the wait still waits before it calls (`PhoneService.open_check`).
  Each reach is `PhoneService.reach`, so the rules decide and each one is a
  `phone.reach` kernel operation. A site reaches nothing when no phone is
  paired and no number is set (a message there would only be a second Needs
  you row about the first).
- **Tests**: `tests/integration/test_phone_flow.py` (the PH12 block): the
  real hub and the fake device; a security finding rings urgent at YOLO, rings
  at Normal, is a message at Secure; a meeting's asks are a message at Normal
  once and nothing at Secure; an undraftable agent question is a message, then
  a call after 10 minutes away at Normal, no call when the wait ended, a call
  at YOLO, a message at Secure.

## PH13. The APNs HTTP/2 dependency (Shipped 2026-10-29, lane PHONE-PH13)

- **Goal**: `ApnsPush` sends for real, and the Phone section says why a push
  would not go.
- **Files**: `pyproject.toml` + `uv.lock` (`httpx[http2]` in the core
  dependencies: h2, hpack, hyperframe, all MIT), `NOTICE`,
  `hs/phone/push.py`, `hs/phone/service.py`, `hs/phone/contract.py`,
  `tests/fixtures/fake_apns.py` (new), `scripts/record_phone_fixtures.py`,
  `desk/calls/PhoneSettings.tsx`, `desk/calls/PhoneWing.tsx`,
  `desk/calls/phoneTypes.ts`, `desk/calls/__fixtures__/phone.*.json`.
- **Changes**: the client speaks HTTP/2 only (`http1=False`: h2 over TLS to
  Apple; h2 with prior knowledge to a test server on `http://`). Each device
  row carries `push_state`: `ready`, `no_key` (no APNs key saved: the hub's
  fallback `NullPush(state="no_key")`), `http2_unavailable` (h2 does not
  import) or `unregistered` (the phone sent no push token). The Phone
  section and the Phone wing draw "Push not ready: <the reason>" (warn) in
  place of the paired fact; a ready phone reads as before. The phone
  recorder pins quiet hours off, so a night run records the day-time desk.
- **Tests**: T1 `tests/unit/test_phone_push.py` (the ES256 provider token
  verified with the public key; a call and a message sent over HTTP/2 to the
  fake APNs: VoIP topic and priority 10, alert topic with the reply
  category, the bearer token, the signed payload; 410 and BadDeviceToken are
  `unregistered`; the saved key in the key store; the four push words on the
  wire through the `Device` contract); T2 `desk/__tests__/calls.app.test.tsx`
  (the three reasons and a ready phone).
- **Left**: no face saves his APNs key yet (Settings ▸ Calls ▸ Phone has no
  key row; `no_key` says so). One push to a TestFlight build (PH-APP4).

## PH14. The morning release of queued messages (Shipped 2026-10-29, lane PHONE-NEXT)

- **Goal**: a message kept in quiet hours reaches his phone when they end.
- **Files**: `hs/phone/service.py` (`release_held`, `tick`).
- **Changes**: the phone's runner tick (once a minute) first releases, then
  follows up. Outside quiet hours, each message to his phone written inside
  them in the last day and not yet on his phone goes out in order, one push
  each, its line "Held overnight: …", and one `message.delivered` event each.
  The stored message keeps its own words; only the push line says it was held.
  The 10 minutes before a follow-up call count from the release.
- **Tests**: `tests/integration/test_phone_flow.py::test_a_message_queued_at_23_30_goes_out_when_quiet_hours_end_and_not_before`
  (clock pinned: nothing at 06:59, both at 07:00 in order, once).

## PH15. Urgent through Do Not Disturb (Left)

APNs `interruption-level: critical` needs the critical-alerts entitlement
from Apple. Until he has it, urgent means "ring once more after 60 s".

## PH16. Today counts the reaches (Shipped 2026-10-29, lane PHONE-APNS-KEY)

Today says "Reached you 2 times: 1 answered" (design §9) from the
`today` block of `GET /api/phone/status`, at any hour (the Programs pattern,
PG18): before 17:00 the line heads the day, after 17:00 it is a row in Since
this morning. No line when the desk did not reach him.

## PH17. His Apple push key (Shipped 2026-10-29, lane PHONE-APNS-KEY)

- **Goal**: the `no_key` state gets its Save.
- **Files**: `hs/phone/push.py` (`save_key_fields`, `saved_key_presence`,
  `ApnsPush.answer`, the `silent` push kind), `hs/phone/service.py`
  (`push_key`, `save_push_key`, `test_push`), `hs/web/routes/phone.py`
  (`GET|PUT /api/phone/push`, `POST /api/phone/push/test`, owner only),
  `web/src/desk/calls/PhoneSettings.tsx` (the Push group), `docs/phone.md`.
- **Changes**: Settings ▸ Calls ▸ Phone ▸ Push keeps the `.p8` (a pad with its
  mic, a paste or a file drop), the Key ID and the Team ID write only in the
  phone key store's `apns-key` slot, each row "Stored in your keystore" or
  "Missing"; the bundle ID is prefilled `dev.holdspeak.mobile` (the app's
  identifier, `apple/App/Info.plist`). `push_state` is `ready` when all four
  are saved. Test push sends one silent (background) push to the newest
  paired phone and says Apple's answer: 200 "Apple accepted it"; 400
  BadDeviceToken or 410 "This phone's token is stale: open the app once"; 403
  "Apple refused the key: check the Key ID and Team ID".
- **Proof**: `tests/unit/test_phone_push.py` (the round trip says `present`
  only; the answers against the fake APNs server), `tests/integration/test_phone_flow.py`
  (the routes through the real hub), `web/src/desk/__tests__/calls.app.test.tsx`
  (the recorded answers, `scripts/record_phone_fixtures.py --push`).

---

## The app: the Program "Phone: the iPhone rings" (Left)

The Apple app is a Program on his desk, `program-29a6d2ef5d55`, in Drafting
(design §11). He presses Start. Its steps:

- **PH-APP1. Contracts.** `apple/Sources/Contracts/Phone.swift`: Codable twins
  of `hs/phone/contract.py`, round-tripped against `tests/fixtures/phone/*.json`.
- **PH-APP2. Pairing.** Scan the QR, `POST /api/phone/devices`, keep the
  device token in the Keychain, the hub's address from the QR.
- **PH-APP3. The event stream.** A WebSocket client with `after_seq` resume;
  the messages thread with inline reply and read receipts.
- **PH-APP4. Push.** PushKit VoIP registration, the alert category with a
  reply action, the signed payload check, the token posted to the hub.
- **PH-APP5. CallKit.** Report an incoming call from the VoIP push; answer
  and decline to the hub; the call screen.
- **PH-APP6. Audio.** A SIP user agent registered to ai-phone over the
  tailnet (a Swift SIP stack or a thin WebRTC path; the step's report
  decides); hold, mute, speaker. This is where an app call gets words and a
  transcript.
- **PH-APP7. Call the desk.** An outbound call from the app on the same SIP
  path; the status screen (paired, the line, quiet hours).
- **PH-APP8. Ship it.** A device build and TestFlight through `apple/scripts/`;
  the entitlements he must request (VoIP push, critical alerts).
