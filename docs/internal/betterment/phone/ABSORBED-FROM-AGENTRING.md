# Absorbed from agentring

Owner, 2026-10-28: "swallow the paradigm and 'vendor' it in the sense that we
literally absorb and rewrite and refactor it into HoldSpeak." This file says
what we read, what we took as an idea, and where it lives in HoldSpeak now.
No agentring file is copied into this repository, and no agentring code runs
as a dependency. Where a sentence or a schema shape is taken, the line below
says so.

## What agentring is

agentring (<https://github.com/mutonby/agentring>, read at commit `10b0e55`)
lets an AI agent message and call the user's own phone over VoIP, and lets the
user call the agents back. It has four parts: a relay (TypeScript, on a VPS:
pairing, the device registry, the call state machine, the message store, one
event log with a global `seq`, the WebSocket fan-out, FCM push, LiveKit
tokens), a daemon (Python, beside the agents: a CLI, the MCP server, a SQLite
mirror, the voice worker on Gemini Live), an Android app (Kotlin: QR pairing,
a full-screen ring, the messages thread), and a skill for agents
(`skills/agentring/SKILL.md`). The contract is one OpenAPI file
(`protocol/relay.openapi.yaml`) with golden examples (`protocol/examples/`).

## Licence

agentring is licensed under the Apache License, Version 2.0. Copyright the
agentring authors. agentring at `10b0e55` has no NOTICE file. The notice for
the ideas taken is in the repository's `NOTICE` file, beside the herdr notice.
A copy of the licence: <https://www.apache.org/licenses/LICENSE-2.0>.

## The map (design §2)

The full map is `PHONE-DESIGN-2026-10-28.md` §2. In short:

| agentring | HoldSpeak |
|---|---|
| the relay on a VPS | the hub is the relay: `holdspeak/phone/` on the hub he reaches over Tailscale |
| the daemon and its MCP server | `PhoneService` and the MCP family `phone.*` |
| LiveKit and WebRTC | ai-phone's SIP over the tailnet, and a real number for the world outside it |
| Gemini Live, the voice | the Calls turn loop: ai-phone's local speech and the home engine |
| the Android app | the HoldSpeak Apple app, a Program of its own (design §11) |
| FCM data pushes, signed | APNs pushes, signed the same way |
| the OpenAPI file and golden examples | the hub's OpenAPI, `holdspeak/phone/contract.py`, `tests/fixtures/phone/` |
| `consult_agent`, answer later | answer-later in the Calls turn loop |
| the skill | `agent/skills/holdspeak-phone/SKILL.md` and `holdspeak/phone/phone_rules.py` |

Not taken: the VPS, Caddy, Docker compose, Firebase, LiveKit, Gemini, the
Android app, the CLI.

## Taken by PH-HUB

From the hub lane's report (2026-10-28):

- The event log with `seq` and replay, and the hello frame
  (`relay/src/events.ts`, `relay/src/routes/ws.ts` → `holdspeak/phone/events.py`,
  `store.append_event`, the ws handler).
- The dotted event names and shapes (`protocol/examples/events` → our own
  recorded fixtures).
- The call state machine with one ring timer, and the invite's push living
  only as long as the ring (`relay/src/routes/calls.ts`,
  `relay/src/push/dispatcher.ts` → `holdspeak/phone/calls.py`,
  `PhoneService._ring`; group and targeted calls not taken).
- Pairing and device auth: a short-lived token in a QR, hashed, consumed
  once; an HS256 device JWT checked per request; revoke closes sockets with
  4401 (`relay/src/routes/pairing.ts`, `relay/src/auth.ts` →
  `holdspeak/phone/devices.py`; the rate limit not taken, 24 random bytes
  instead).
- The push payload `{v, hub id, event JSON, HMAC-SHA256 sig}` with a cut long
  message (`relay/src/push/dispatcher.ts`,
  `protocol/examples/push/signature-vector.json` → `holdspeak/phone/push.py`
  over APNs). A schema shape taken.
- The PushProvider interface answering `ok` / `unregistered` / `error`
  (`relay/src/push/push-provider.ts`). A schema shape taken.
- The MCP tools `send_message` / `get_replies` (`wait_s` ≤ 3600, each reply
  once) / `call` (`reason`, `context`, `urgent`) / `status`, with paraphrased
  descriptions (`daemon/src/agentring/mcp_server.py` →
  `holdspeak/mcp/families/phone.py`).
- The etiquette coded (`skills/agentring/SKILL.md` →
  `holdspeak/phone/phone_rules.py`, the SILENCE note in
  `holdspeak/phone/service.py`).
- Answer-later (from the design's map; `voice/tools.py` not read) →
  `holdspeak/calls/runner.py`.

## Taken by PH-DOCS

- The etiquette of `skills/agentring/SKILL.md` (pick the lightest channel;
  wait with `get_replies` instead of polling; call only when urgent or a
  message got no answer; the context is written for someone who has not seen
  the work, with no ids, paths or links; never treat silence as consent),
  rewritten in our words → `agent/skills/holdspeak-phone/SKILL.md`. The
  phrase "silence is never consent" follows its "Don't treat silence as
  consent".
- The one-paragraph description of agentring's four parts above, from its
  `README.md` and `docs/architecture.md`.

## Taken by PH-FACES

The faces lane adds its lines here when it lands.
