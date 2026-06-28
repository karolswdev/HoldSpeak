# The Cadence Engine

> HoldSpeak's local-first technical chief-of-staff. It turns your meetings, activity,
> dictation, and coding-agent state into **evidence-backed nudges** and
> **nearly-complete next actions**, then pushes you at a useful cadence until each loop
> is done, snoozed, killed, or delegated. Qlippy does not interrupt to say something
> vague. He interrupts only when he has done enough work that your next decision is a
> single tap.

**Off by default.** Nothing runs, nudges, or leaves your machine until you turn it on.

---

## The shape

```
Open Loop  ->  Next Best Action  ->  Nudge  ->  Decision
```

- **Open Loop:** an unresolved item. A meeting action item, a pending proposal, or a
  coding agent waiting on your answer. Loops are *projected* from those sources, so they
  stay in sync. But your decisions are remembered: a killed loop stays killed even if its
  source still exists.
- **Next Best Action:** the prepared move. A proposal becomes *Approve*. An owned action
  becomes a drafted *issue*. An unowned one becomes *Assign an owner*. A waiting agent
  becomes *Reply*. Deterministic by default. An LLM can *draft* the wording when you
  enable it (it never executes, you approve).
- **Nudge:** the move surfaced somewhere. The web page, the CLI, Telegram, or the
  desktop tick.
- **Decision:** one tap. Snooze, mark done, kill, delegate, approve, or send a reply.

## Surfaces

| Surface | How |
|---------|-----|
| **CLI** | `holdspeak cadence status`, `loops`, `run-now`, `brief`, `closeout`, `audit` |
| **Web** | the `/cadence` coach page (Now, Open loops, the end-of-day review, History) |
| **Telegram** | pair a chat, then `/brief`, `/loops`, `/status`, plus inline-button decisions |
| **Desktop** | the in-runtime tick pushes due nudges and the morning brief to paired chats |

## Turning it on

Everything lives under `cadence` (and `cadence_telegram`) in your HoldSpeak config, all
**off by default**:

```jsonc
{
  "cadence": {
    "enabled": false,            // the master switch — the in-runtime tick
    "pressure": "normal",        // gentle | normal | aggressive (timing only)
    "use_llm": false,            // LLM-DRAFT next actions (fail-closed to deterministic)
    "quiet_hours_start": 22,
    "quiet_hours_end": 8,
    "max_nudges_per_day": 12
  },
  "cadence_telegram": {
    "enabled": false,
    "bot_token": "",             // a credential — never logged or stored in a message
    "allowed_chat_ids": [],      // the hard pairing allow-list
    "pairing_code": ""           // /pair <code> self-pairs a chat
  }
}
```

`holdspeak cadence run-now` and the other read commands work even when the master switch
is off. The switch only governs the autonomous in-runtime tick.

## The trust boundary

This is a *pressure system*, not an autonomous agent. The guarantees, enforced by tests
rather than good intentions:

1. **No external side effect without your approval.** Any outbound action (a GitHub
   issue, a Slack post) goes through HoldSpeak's existing propose, approve, execute
   path. Cadence never calls a connector directly.
2. **The cadence core is pure.** It performs no network, terminal, subprocess, or
   connector execution. A test fails the build if that ever changes. Every surface that
   does reach out (the Telegram bot, the agent-reply delivery, the LLM provider) lives
   outside the core or takes an injected helper.
3. **The LLM only drafts.** When `use_llm` is on, a model may draft the wording of a next
   action. The output is structured JSON, validated, and fail-closed: any failure falls
   back to the deterministic action. Your transcripts are always treated as data, never
   as instructions.
4. **Honest egress.** Every nudge carries a badge. Most of cadence is local. A Telegram
   push is the one thing that leaves, and only to your paired chat.
5. **Telemetry-free audit.** `holdspeak cadence audit --out audit.json` writes a complete
   local snapshot (every loop, its evidence, the nudge history) so what Qlippy did, and
   why, is provable after the fact, with nothing leaving the machine.
6. **Your decisions stick.** Snooze and dismissal are respected. A killed loop is never
   resurrected unless its source materially changes.

## What it is not

Not a chatbot, not an autonomous shell executor, not a second runtime, not a cloud-first
memory, not a surveillance daemon, not a nag machine with vague reminders. It is one
thing: a local-first chief-of-staff that pushes with receipts, restraint, and a ready
next move.
