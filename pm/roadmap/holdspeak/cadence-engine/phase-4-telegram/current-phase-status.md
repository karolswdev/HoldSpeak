# Cadence Phase 4 — Telegram remote presence

**Status:** done (sim/hermetic — 272 cadence/web/config tests green; the live bot walk is the owner's
gate). **Start here:** `../README.md`. Builds on Phases 1–3 (merged).

**Last updated:** 2026-06-28 (Phase 4 shipped hermetically: the Telegram surface — pairing, commands,
inline-button decisions, and push-on-tick — all proven with a mocked transport, off by default).

## Objective

Make Qlippy reach you when you're away from the desk: a Telegram surface that **delivers nudges**
(due loops + their prepared move) and **receives decisions** (snooze/kill/done, and reply-to-agent),
with hard pairing and the egress badge flipping to `cloud`. This is the **first phase that genuinely
reaches out** — the Telegram Bot API is real off-machine egress — so the security model leads.

## Architecture decisions

- **The Telegram surface lives OUTSIDE the cadence core.** The Phase-1 no-side-effects guard scans
  `holdspeak/cadence/` and forbids network — and it stays that strong invariant. The Telegram surface
  is a sibling module `holdspeak/cadence_telegram.py` that *reads* the cadence service/repo and does
  the egress. (Surfaces do side effects; the core never does.)
- **The bot token is a credential, never logged or stored in a payload** — joined in memory at call
  time (the Slack-URL pattern, [[project_phase61_send_to_slack]]). Outbound HTTP uses stdlib
  `urllib.request` with a timeout, modelled on `webhook_post_actuator.py`.
- **Hard pairing.** Only `allowed_chat_ids` (config) may read anything; an unpaired chat is rejected
  with a single "not paired" line and **no data**. `/pair <code>` adopts a chat when the code matches
  a config pairing code. Tested: an unpaired chat can read nothing.
- **Never autonomous beyond notifying you.** A pushed nudge notifies the *paired* user (you) — that
  is the product. A *decision* (snooze/kill/done/reply) requires an explicit button/command. Any
  **irreversible** action (none in Phase 4 — lifecycle is local; actuator execution is Phase 6/7)
  would require a typed second-confirm (the `reversible` flag from the actuator).
- **Off by default.** `TelegramConfig.enabled = False` + empty token ⇒ inert (no poller, no send).
- **Live proof is the owner's button.** The hermetic surface (auth/commands/render/decisions) is
  fully tested with a mocked transport; the live bot (real token + a real chat pairing + a real
  push) is walked by the owner, like the mobile device walk ([[feedback_verify_on_device_not_seeded]]).

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-4-01 | `TelegramConfig` (off by default; token + allowed chats + pairing code) | done |
| CAD-4-02 | The transport: `call_telegram` (sendMessage/getUpdates) via urllib (token joined in memory) | done |
| CAD-4-03 | Authorization + command handling (`/start /pair /status /brief /loops`); unpaired rejection | done |
| CAD-4-04 | Decisions: inline-button callbacks → snooze/done + kill-with-confirm | done |
| CAD-4-05 | Push: the tick sends due-loop nudges to paired chats (records a nudge) | done |
| CAD-4-06 | Tests: auth/rejection, command parse + render, decisions, push (mocked transport), off-by-default | done |

## Where we are

**Phase 4 is hermetically complete** (the live bot walk is the owner's button). `TelegramConfig`
(top-level, off by default; `is_active` only when enabled + a token) gates everything.
`holdspeak/cadence_telegram.py` — a **sibling of the cadence core** so the no-side-effects guard
stays strong — holds the surface: `call_telegram` (urllib, the token joined into the URL only at
call time, never logged/stored), `TelegramSurface` with authorization (`allowed_chat_ids`; an
unpaired chat gets one "not paired" line and **no data**), `/start /pair /status /brief /loops`,
inline-button decisions (snooze/done one-tap, **kill behind a second confirm**), `push_due_nudges`
(records a `telegram` nudge per loop), and a `poll_once` getUpdates round for the live runner. The
`CadenceMixin` tick pushes due loops to paired chats when the surface is active. **Proof:** 272 tests
green (incl. 12 Telegram: unpaired-gets-nothing, pairing, token-never-in-text, the confirm gate,
push records); the cadence-core no-side-effects guard still passes; config round-trips.

**Owner's live walk:** set a bot token + a `pairing_code` in `cadence_telegram`, `/pair` from a real
chat, receive a pushed nudge, tap a decision. (Reply-to-agent over Telegram — the stateful typed
flow — is a deliberate small follow-up; the web reply composer ships it today.)

**Next: Phase 5 (daily push brief).**

## Exit criteria

- An unpaired chat gets nothing; a paired chat can `/brief`, `/loops`, `/status` and act on inline
  buttons; the tick pushes due nudges to paired chats (mocked send asserted).
- The bot token never appears in any rendered message, log, or persisted row.
- The Phase-1 cadence-core no-side-effects guard still passes (Telegram is a sibling surface).
- Off by default: no token ⇒ no poller, no send (test-proven). `uv run pytest -q` green.
- **Live walk (owner):** real bot pairs to a real chat, receives a nudge, drives a decision.
