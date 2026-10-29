---
name: holdspeak-phone
description: Use when you need the owner's answer or attention and he may be away from the desk; reach his phone through HoldSpeak's phone.* MCP tools (send a message, wait for his reply, ask to call him). Not for changing the Phone code itself.
---

# holdspeak-phone

HoldSpeak can reach the owner on his phone: a short message he reads on the
lock screen and answers, or a call where a voice says why you call and takes
his answer. The desk is the relay; the tools come from HoldSpeak's MCP
server. Read first:

- `docs/phone.md` (the user doc: the two ways, Reach you, quiet hours)
- `docs/internal/betterment/phone/PHONE-DESIGN-2026-10-28.md` (§6 the rules, §7 the tools, "Built")
- `holdspeak/mcp/families/phone.py` (the tool schemas)

## Use the lightest channel

1. **`phone.send_message`** for all that can wait: a task is done or failed,
   a short summary, a question with a clear safe default. One line, 500
   characters or less. He reads it on a locked phone, so the first words
   say what it is about.
2. **`phone.get_replies(wait_s=…)`** after a question. Wait 300 to 900
   seconds in one call; do not poll in a loop. Each reply comes back one
   time only.
3. **`phone.call`** only when it is urgent, or when a message got no answer
   and the work cannot go on without him. Not for routine news, and never
   two calls in a row.

## The context contract (a call)

The voice on the call knows only what you give it.

- `reason`: one sentence. He sees and hears it first ("The nightly
  migration failed on step 3").
- `context`: what happened, the options, your advice, what you need from
  him, and what you must not decide. Write it for a person who has not seen
  your work. No ids, paths or links: the voice reads them aloud.
- `urgent`: only for a security or data-loss problem, or when he asked you
  to call.

The call returns when it ends: `transcript`, `end_reason`, `duration_s`
and `decision`. Act on what he said. If he did not answer, send one message
and wait; do not call again at once.

## The rules

- **Silence is never consent.** No reply is not a yes. Keep the safe
  default, and say in your report that you are waiting.
- **A call is egress and waits for his press.** `phone.call` is EGRESS: it
  shows in Needs you as "Call you about …?" until he presses **Call now**.
  It rings at once only when your Program has **May call** on and the level
  is not Secure. An agent that the desk launched does not get `phone.call`
  at all.
- **No secrets.** No tokens, keys or passwords in a message or a call
  context. The redactor refuses them.
- **The desk's own rules hold for you too.** Quiet hours (Settings ▸ Rhythm)
  keep a message for later and let only an urgent call ring; a Program
  step sends at most 3 messages an hour.
- **Whose word.** A reply comes from his phone; never present your own
  words as his.

## Proof

Report the message id that `phone.send_message` returned, the reply text
and its id from `phone.get_replies`, or the call id and `end_reason` from
`phone.call`. "He agreed" needs a reply or a `decision` you can quote.
