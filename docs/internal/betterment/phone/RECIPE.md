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

## PH12. The other reach kinds (Left)

The rules for `heartbeat_security`, `aftercare` and `agent_question` are in
`phone_rules.py`, but no path calls them. Wire the heartbeat's security and
data-loss findings, a meeting's aftercare asks, and an agent question the
desk could not draft (with "away": no desk presence for 30 minutes) to
`PhoneService.reach`.

## PH13. The APNs HTTP/2 dependency (Left)

`ApnsPush` needs `httpx[http2]` (`h2`). Add the extra to `pyproject.toml`
when the app reaches its push step (PH-APP4), and prove one push to a
TestFlight build.

## PH14. The morning release of queued messages (Left)

In quiet hours a message is kept and its push waits; no push goes out when
quiet hours end. The phone gets the message when it next connects. Send one
push at the end of quiet hours that names the waiting messages.

## PH15. Urgent through Do Not Disturb (Left)

APNs `interruption-level: critical` needs the critical-alerts entitlement
from Apple. Until he has it, urgent means "ring once more after 60 s".

## PH16. Today counts the reaches (Left, unless PH-FACES ships it)

Today's Since morning says "Reached you 2 times: 1 answered" (design §9).

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
