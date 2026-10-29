# Phone: HoldSpeak reaches you on your phone, and you reach it

Owner, 2026-10-28: "How could we integrate this? … Do it. And definitely swallow
the paradigm and 'vendor' it in the sense that we literally absorb and rewrite
and refactor it into HoldSpeak." The "it" is agentring (github.com/mutonby/
agentring, Apache-2.0, commit 10b0e55, "Let your AI agents call your phone over
VoIP, and call them back"). This design absorbs its model into HoldSpeak's own
nouns and code; nothing of agentring runs as a dependency. Attribution:
`ABSORBED-FROM-AGENTRING.md` beside this file and the repository's third-party
notices carry the Apache-2.0 notice and name what was taken as an idea and what
was rewritten.

## 1. The job

When the desk needs him and he is not at it, it must reach him where he is:
a message on his phone he can answer from the lock screen, or a call that rings
even when the phone is locked, with a voice that says why, takes his answer and
hands it back as the decision. And the other way: from his phone he asks the
desk what CI said, what merged overnight, what Alice's 1:1 needs, and the desk
answers by voice from its own tools.

HoldSpeak already has the brain and the mouth: the Calls capability
(`../calls/CALLS-DESIGN-2026-10-28.md`): ai-phone on the Mac as the SIP phone
with local speech, the home box's qwen as the mind, the Calls turn loop with the
desk's tools as hands, the gate (allowed numbers, passphrase, his spoken yes for
egress), Settings ▸ Calls. What it lacks is agentring's half: **a message channel
with replies and an event log, a call state machine with ringing, missed and
urgent, a paired device, and the etiquette an agent follows when it decides to
reach a person.** Phone is that half, rewritten on HoldSpeak's hub.

## 2. What agentring is, and what we take (the absorption map)

| agentring piece | What it does there | In HoldSpeak |
|---|---|---|
| relay (TypeScript, a VPS behind Caddy) | pairing, device registry, call state machine, message store, event log with a global `seq`, WebSocket fan-out, FCM push, LiveKit tokens | **the hub is the relay**: `holdspeak/phone/` (store, events, calls, devices, push) on the hub he already reaches over Tailscale; no second server |
| daemon (Python beside the agents) | CLI, MCP tools `send_message` `get_replies` `call` `status`, SQLite mirror, voice worker | **the hub's service layer**: `PhoneService`, the MCP family `phone.*`, the Calls turn loop as the voice |
| LiveKit (SFU) + WebRTC | call audio across NAT | **ai-phone's SIP over the tailnet**: the device is a SIP endpoint of ai-phone; no SFU, no NAT problem on a tailnet; a real number (Telnyx) for the world outside it |
| Gemini Live | the voice: speech-to-speech in the cloud | **ai-phone's local speech + qwen on the home box** (the Calls design, as built); `RealtimeBackend` is replaced by the Calls turn loop; nothing of a call leaves the tailnet unless he set a hosted engine |
| Android app (Kotlin) | QR pairing, CallStyle full-screen ring, LiveKit audio, messages thread with inline reply | **the HoldSpeak Apple app** (`apple/`, SwiftUI, iOS 17): CallKit + PushKit VoIP push, a SIP client to ai-phone, the messages thread; a Program of its own (§11) |
| FCM data pushes, HMAC-signed | wake a locked phone | **APNs**: a VoIP push (PushKit) for a call, an alert push with a reply action for a message; signed the same way; his Apple developer keys in the keystore (his press) |
| `protocol/relay.openapi.yaml` + golden fixtures | one contract, three languages | the hub's OpenAPI (regenerated), `holdspeak/phone/contract.py` pydantic models, Swift `Codable` twins under `apple/Sources/Contracts/Phone.swift`, round-trip fixtures in `tests/fixtures/phone/` |
| `agents.yaml` + `consult_agent` ("answer later") | the voice asks an agent, waits 20 s, carries on, answers later or as a message | the Calls turn loop's hands already run the desk's tools; **answer-later** is added: a tool slower than 20 s says "working on it", the answer comes as a later turn or a message after hang-up (`agent_helpers` wait, as AG11) |
| the skill (`skills/agentring/SKILL.md`): pick the lightest channel, the context contract, don't treat silence as consent | how an agent decides to reach a person | `agent/skills/holdspeak-phone/SKILL.md`, and the same rules coded in `phone_rules.py` for the engine's own reaching (§6) |
| `priority: urgent` (bypass Do Not Disturb) | real emergencies | `urgent` on a call: APNs `interruption-level: critical` requires an entitlement he must request; until then urgent = ring again once after 60 s |
| missed call → message with inline reply | nothing is lost | the same, plus a Needs you row |

Not taken: the VPS, Caddy, Docker compose, Firebase, LiveKit, Gemini, the Android
app, "one user per relay" (ours is one owner per hub, the same thing).

## 3. The nouns

| He sees | In data | It is |
|---|---|---|
| **Phone** | the channel `phone` in Settings ▸ Calls | the way the desk reaches him away from it, and he reaches the desk |
| **Your phone** | `phone_devices` | a paired device: name, platform, push token, SIP identity, last seen |
| **Message** | `phone_messages` | one line from the desk to the phone or back; `reply_to` threads it; read receipts |
| **Call** | `phone_calls` | ringing → answered / missed / declined → ended; direction, reason, urgent, the transcript and the decision it produced |
| **Reach** | the verb | the desk's own decision to message or call him, by rule (§6) |
| **Event** | `phone_events` | the sequence-numbered log the phone and the desk replay from |

## 4. The states

Call: `ringing` (invite sent; `expires_at` 30 s) → `answered` → `ended` (by him, by the desk, by a timeout); or `missed` (no answer in 30 s → one message with the reason and the question, inline-replyable); or `declined`. A missed urgent call rings once more after 60 s, then becomes a message.

Message: `sent` → `delivered` (push accepted) → `read` (the app marked it) ; a reply is a message with `reply_to`.

Device: `pairing` (a QR with a 10-minute token) → `paired` (a device JWT, revocable) → `revoked`.

The event log: every change above is an event with `seq`; `GET /api/phone/events?after_seq=` and the device WebSocket replay from `seq`; a daemonless desk never loses a reply (agentring's one event log, kept).

## 5. The transports, in the order they work

1. **Today: a real number.** `phone.call` places the call through Calls (ai-phone `call --relay`) to his number via the Telnyx line (or any SIP line in ai-phone); the voice is the Calls turn loop; the transcript and the decision come back the way a Calls turn does. Works on any phone, locked, on cellular, no app. Needs his Telnyx sign-up (the Calls note on his desk). Messages on this transport are SMS through the same line when the line has it, else the message waits for transport 2 and shows as a Needs you row.
2. **Next: the HoldSpeak app.** The Apple app pairs by QR, keeps a WebSocket to the hub over Tailscale when open, receives an APNs VoIP push for a call and an alert push for a message when closed; a call is answered through CallKit and carried as a SIP call to ai-phone over the tailnet; messages have inline reply. §11 is its Program.
3. **Both at once.** With a device paired, a call rings the app first and falls back to the number after 30 s; messages go to the app and, when it has no push for 5 minutes, to the number's SMS if any.

## 6. Reach: when the desk may message or call him (the rules, by Control level)

Phone has its own rules module, `holdspeak/phone/phone_rules.py`, `reach(level, kind, facts) -> Reach | Hold`, with the same shape as Programs' `program_rules.decide`. The kinds that may reach him:

| Kind | Secure | Normal | YOLO |
|---|---|---|---|
| a Program's core question (§ Programs design) | message | message; call after 10 min without a reply when the Program says `may_call` | call at once when `may_call`, else message |
| a Program step red after its rounds | message | message | message; call when `may_call` and the Program is the night's |
| a Program done | nothing | message | message |
| a heartbeat finding tagged security or data-loss | message | call | call, urgent |
| a meeting's aftercare asks | nothing | message | message |
| an agent's question the desk could not draft | message | message, call after 10 min when he is away (no desk presence 30 min) | call |
| anything an agent asks for through `phone.*` itself | the tool's own rules (§7) | | |

Always: quiet hours (Settings ▸ Calls ▸ Phone, default 23:00–07:00: messages queue, only `urgent` rings); never twice in 5 minutes for the same thing; a message first and a call only when the message got no reply, unless the kind says call; never a call while a call is on. Every Reach is a kernel operation (`phone.reach`) with its rule, and a line under the Program's Decided for you when it came from a Program.

## 7. The desk's tools for agents (MCP family `phone`)

Through `PhoneService`, in the CONDUCTOR palette, with agentring's etiquette coded, not only written:

| Tool | Does | Rules |
|---|---|---|
| `phone.send_message(text, reply_to?)` | one line to his phone | ≤ 500 chars; a Program step's agent may send at most 3 per hour; secrets are refused by the redactor |
| `phone.get_replies(wait_s?)` | his new replies, each once; waits up to `wait_s` (≤ 3600) | an agent waits instead of polling; silence is never consent (the tool says so in its answer) |
| `phone.call(reason, context, urgent?)` | the phone rings; the voice says the reason, talks from the context, returns `{transcript, end_reason, duration_s, decision?}` | EGRESS: his press (Secure/Normal) through Needs you ("Call you about …?") unless the Program's `may_call` and the level allow (§6); `context` is the contract: what to tell, what to ask, what not to decide; no ids, paths, links (read aloud); `urgent` only on security/data-loss or when he asked for a call |
| `phone.status()` | the paired phones, the line, quiet hours, the last reach | read |

The voice on a `phone.call` is the Calls turn loop with the CONDUCTOR read tools plus `program.decide` behind his spoken yes (the Calls gate, as built); **answer-later** for any hand slower than 20 s.

## 8. You reach the desk

"Call the desk" from the app, or dialing the number: the Calls gate (allowed numbers, passphrase) as built; the voice's hands are the Conductor palette's reads (`program.get`, `desk_needs_you`, `today_get`, `people_one_on_one_brief`, `heartbeat_status`, `meeting_get`), `program.decide` and `phone.send_message` (to himself: "send me that link") behind the spoken yes. A question the hands cannot answer in 20 s is answered later as a message.

## 9. The faces (kit only)

- **Settings ▸ Calls ▸ Phone**: *Your phone* (Pair a phone: a QR the app scans, the device row with Last seen and Revoke), *Reach you* (per kind the three words Message · Call · Nothing, prefilled by the level), *Quiet hours*, *Urgent may ring through Do Not Disturb* (off until the entitlement), *The number* (from Calls). A QR needs an encoder: the repository has none; take `qrcode-generator` (MIT, 12 KB) as a dependency or vendor the encoder under `web/src/lib/qr/` with its notice.
- **The Calls window** gains **Phone**: the messages thread (desk and phone, replies threaded, a mic composer so he can message his phone from the desk), the calls list (reason, when, answered or missed, Open transcript), the devices. The same list grammar as Calls' turns.
- **Needs you**: "Asked on your phone · 12 min · no reply" with Call now / Let it wait; "Missed call: <reason>" with Call again / Answer here.
- **Today**: Since morning counts reaches ("Reached you 2 times: 1 answered").
- **The Program window**: a Reach line under Decided for you when the engine messaged or called.

## 10. Contract for the lanes

Tables (`holdspeak/db/schema.py`, minimal): `phone_devices(id, name, platform, push_token, push_kind, sip_identity, jwt_kid, state, paired_at, last_seen_at, revoked_at)`, `phone_messages(id, seq, direction 'to_phone'|'from_phone', text, reply_to, created_at, delivered_at, read_at, origin_ref, program_step_id)`, `phone_calls(id, seq, direction, reason, context_digest, urgent, state, created_at, answered_at, ended_at, end_reason, transcript_ref, decision_json, transport 'number'|'app', calls_turn_id)`, `phone_events(seq PK, type, ts, payload_json)`, one index on `phone_events(ts)`.

REST (all through `run_in_threadpool`; the device principal is a JWT, every request re-checks the device row; the owner principal is the hub token):
```
POST /api/phone/pair                       → {token, qr_png_base64?, expires_at}      owner
POST /api/phone/devices                     {pair_token, name, platform, push_token}   device (pairing)
GET  /api/phone/devices · DELETE /api/phone/devices/{id}                              owner
POST /api/phone/messages  {text, reply_to?} → {msg_id}                                owner, agent, device
GET  /api/phone/messages?after_seq=         · POST /api/phone/messages/{id}/read       both
POST /api/phone/calls {reason, context, urgent} → {call_id, state}                    owner, agent (gated)
POST /api/phone/calls/{id}/accept|decline|end                                          device / owner
GET  /api/phone/calls/{id}                                                             both
GET  /api/phone/events?after_seq=   ·  GET /api/phone/ws?after_seq=   (device stream)
GET  /api/phone/status                                                                 owner
```
Push: `holdspeak/phone/push.py` with `PushProvider` (`send(target, payload, ttl, high_priority) -> ok|unregistered|error`), `ApnsPush` (token-based auth with his .p8 key in the keystore; VoIP topic for calls, alert topic with a reply category for messages) and `NullPush` (logs; the rig). Signed payloads (HMAC with a per-device secret) as agentring does. No FCM in this PR (an Android device is a later provider).

Frame: `phone_changed {kind: message|call|device, id, state}` (registry + consumer). Switch: `HOLDSPEAK_PHONE=off` (off in every rig). MCP: `holdspeak/mcp/families/phone.py` (§7), palette CONDUCTOR; `phone.call` EGRESS in `tool_authority.py`. Routing: `needs_you_membership` gains `phone_items`; Programs' `program_runner` asks `phone_rules.reach` where it today only writes a Needs you row; a `may_call` boolean on Program and step (default off; on in the Overnight template).

Fixtures: recorded through the real routes with a fake device (a tiny client in `tests/fixtures/fake_phone_device.py` that pairs, opens the event stream, accepts a call, replies to a message) and the fake ai-phone from the Calls rig.

## 11. The app, as a Program on his desk

"Phone: the iPhone rings" is created on his desk in Drafting (not started; a multi-week build he should press Start on himself), repository HoldSpeak, base main, Build and review, Runs on Claude Code, reviewer Codex, with these steps:

1. `apple/Sources/Contracts/Phone.swift`: Codable twins of `holdspeak/phone/contract.py`, round-tripped against `tests/fixtures/phone/*.json`.
2. Pairing: scan the QR, `POST /api/phone/devices`, keep the device JWT in the Keychain, the hub's Tailscale URL from the QR.
3. The event stream: a WebSocket client with `after_seq` resume, messages thread screen with inline reply, read receipts.
4. Push: PushKit VoIP registration and the alert category with a reply action; the signed payload check; the token posted to the hub.
5. CallKit: report an incoming call from the VoIP push, answer/decline to the hub, the call screen.
6. Audio: a SIP user agent registered to ai-phone over the tailnet (evaluate a Swift SIP stack vs. a thin WebRTC path to ai-phone; the step's report decides), hold/mute, speaker.
7. "Call the desk" from the app (outbound through the same SIP path), and the status screen (paired, line, quiet hours).
8. Device build and TestFlight through `apple/scripts/`; the entitlements he must request (VoIP push, critical alerts).

## 12. What he presses

1. Nothing new for messages and calls to reach him by number: the Calls note already says Telnyx; once the line is in, `Reach you` works on the number.
2. Pair a phone: Settings ▸ Calls ▸ Phone ▸ Pair, scan with the app when the app exists.
3. His Apple developer key for push, in Settings ▸ Calls ▸ Phone, when the app's Program reaches step 4.
4. Start the "Phone: the iPhone rings" Program.

## 13. Slices (one PR, lanes on one branch)

| Lane | Owns | Done when |
|---|---|---|
| **PH-HUB** | `holdspeak/phone/` (store, events, calls, devices, push, service, contract, phone_rules, the Calls transport), schema, routes, MCP, needs-you items, the Programs runner's reach, frames, switch, tests, recorded fixtures | the fake device pairs, gets a message, replies, and the reply is read by `phone.get_replies`; a `phone.call` on the number transport runs through the fake ai-phone and returns a transcript and a decision; a call the fake device does not answer becomes a missed message with a Needs you row; quiet hours hold; the rules table per level; the event log replays from `after_seq` |
| **PH-CANVAS** then **PH-FACES** | the canvas of §9 at 1440 and 393, then the faces | every state drawn from the recorded fixtures; pairing shows a QR; presses go through |
| **PH-DOCS** | this design + ABSORBED-FROM-AGENTRING.md + third-party notices, `docs/phone.md`, the skill, RECIPE PH1–PHn, UX-CANON line, STATUS | docs current, gen_docs clean |
| **the Program** | created on his desk by the orchestrator through `/api/programs` in Drafting (§11) | he sees it in Programs |

## Built, 2026-10-28

The hub lane (PH-HUB, `a65f523e4` on `lane/phone-20261028`) built §3 to §8
and §10. The design's intent stands; this section names where the build
differs from the text above, and why. The faces (§9) are the PH-FACES lane's.

### Where the build differs

- **`phone.call` is not offered to a launched agent.** A launch gets only the
  WORK half of the family: `phone.send_message`, `phone.get_replies` and
  `phone.status` (`holdspeak/mcp/tool_authority.py`, the Phone lines;
  `holdspeak/services/conductor_launch.py`, "a call is EGRESS and never
  offered"). Every other caller of `phone.call` meets the EGRESS gate of §7:
  his press in Needs you, unless the Program may call and the level is not
  Secure.
- **APNs needs `httpx[http2]`.** `ApnsPush` answers `error`
  (`http2_unavailable`) until the HTTP/2 extra is installed; the extra is not
  added to `pyproject.toml` in this PR. Until his Apple key is in the
  keystore the hub runs `NullPush`, which logs and keeps what it would have
  sent (`holdspeak/phone/push.py`).
- **Quiet hours come from the desk's one quiet-hours store,** the one
  Settings ▸ Rhythm writes (`read_quiet_hours`,
  `holdspeak/services/heartbeat_service.py`; default 22:00–08:00), not a
  second setting under Settings ▸ Calls ▸ Phone with 23:00–07:00. A message
  in quiet hours is written and its push waits ("Reached you: a message, held
  for the morning"). **No push releases the queued messages in the morning**:
  the phone reads them from the event log the next time it connects.
- **No SMS.** ai-phone's commands (`call`, `listen`, `say`, `hangup`) have no
  SMS (`holdspeak/phone/transport_number.py`, `sms_available` is false). A
  message with no paired phone is a Needs you row, "No phone is paired", with
  Let it wait (`phone_items`, `holdspeak/services/needs_you_membership.py`).
- **The app transport is the state machine and the pushes only.** The hub
  rings, times out, re-rings an urgent call once and falls back to the number;
  the audio of an app call and its transcript are the Apple Program's (§11
  step 6). Today a call with words is a call on the number.
- **Only the Programs rows of §6 reach him today.** The Programs engine asks
  `phone_rules.reach` for `core_question`, `step_red` and `program_done`
  (`ProgramService.reach_phone`, `holdspeak/services/program_service.py`;
  the callers in `holdspeak/services/program_runner.py`). The rules for
  `heartbeat_security`, `aftercare` and `agent_question` are in the table
  and tested, but no heartbeat, aftercare or agent-question path calls them
  yet (RECIPE PH12).
- **Two `may_call` columns:** `programs.may_call` and `program_steps.may_call`
  (default 0; a step may call when it or its Program may). The Overnight
  template sets it on (`holdspeak/program_templates.py`).
- **The QR names the address he pressed Pair on** (his Tailscale name when
  he pressed it over Tailscale), with the token and its expiry
  (`qr_payload`, `holdspeak/phone/devices.py`). `qr_png_base64` is `null`:
  the faces draw the QR from `qr_payload`.

### What is the same as written

The four tables of §10, the REST routes of §10 (plus `POST
/api/phone/messages/{id}/wait`, `GET /api/phone/calls`, `POST
/api/phone/calls/{id}/ring` and `POST /api/phone/calls/{id}/again` for the
Needs you verbs), the call states of §4 with a 30 s ring and one urgent
re-ring after 60 s, answer-later at 20 s (`holdspeak/calls/runner.py`), the
rules table of §6 (`holdspeak/phone/phone_rules.py`), the kernel operation
`phone.reach`, the frame `phone_changed`, the switch `HOLDSPEAK_PHONE=off`,
and the four `phone.*` MCP tools (305 tools in 52 families). Proof:
`tests/integration/test_phone_flow.py` (14 tests on a real hub with a fake
device and the fake ai-phone) and the `tests/unit/test_phone_*.py` files.
