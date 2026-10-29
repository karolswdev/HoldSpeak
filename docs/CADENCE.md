# Cadence

Cadence reviews unresolved work and prepares next actions. It can collect
meeting action items, proposed actions, and Coder sessions that need a reply.
Cadence does not send an external nudge during its collection tick.

The background Cadence loop is off by default. The morning Brief job is on by
default and prepares one deterministic Brief at 06:00 local time. Manual
commands can still inspect work or request an evaluation.
Cadence is separate from the [Heartbeat](USER_GUIDE.md#notices-and-the-heartbeat) and from preferences saved in [Interview](INTERVIEW.md).

## Inspect work manually

Run these commands from the HoldSpeak environment:

```sh
holdspeak cadence status
holdspeak cadence loops
holdspeak cadence run-now
holdspeak cadence brief
holdspeak cadence closeout
holdspeak cadence audit --out audit.json
```

`run-now` performs one evaluation even when the background loop is disabled.
The Web surface is available through **Rhythm** or `/cadence`.

## Understand the records

| Record | Meaning |
| --- | --- |
| Open loop | Unresolved work projected from a source |
| Next action | A prepared response, such as an owner assignment or issue draft |
| Nudge | A presentation of a next action through an enabled surface |
| Decision | Your snooze, completion, dismissal, or delegation |

Cadence retains your decision about a loop. A dismissed loop stays dismissed
until its source changes materially. An optional model can draft wording. It
does not change the action or its authority.

## Configure background Cadence

The `cadence` object is in `~/.config/holdspeak/config.json`:

```json
{
  "cadence": {
    "enabled": false,
    "brief_enabled": true,
    "brief_hour": 6,
    "pressure": "normal",
    "use_llm": false,
    "max_nudges_per_day": 12,
    "tick_interval_seconds": 300
  }
}
```

Set `enabled` to `true` to run the background loop. Set `brief_enabled` to
`false` to prepare the Brief only when you select **Generate**. The minimum
`tick_interval_seconds` is 30. `pressure` is `gentle`, `normal`, or
`aggressive` and changes timing only. `use_llm` allows bounded draft wording;
Cadence falls back to its deterministic action when the draft is unusable.

Quiet hours are configured by the Heartbeat policy in **Settings > Rhythm**.
The old `cadence.quiet_hours_start` and `cadence.quiet_hours_end` keys are
retired. A stale client write of those keys is dropped.

**Secure** allows an explicit **run-now** but prevents the background loop.
See [Control mode](SECURITY.md#control-mode).

## Deliver through Telegram

Telegram is a separate `cadence_telegram` surface. It is disabled by default
and needs a bot token plus `allowed_chat_ids`, or a `pairing_code`. A chat can
pair with `/pair <code>`. Only paired, allowed chats receive delivery.

The available commands include `/brief`, `/loops`, `/closeout`, and `/status`.
Inline controls can record a decision about presented work. Telegram does not
replace the operation authority for an external effect.

## Inspect outcomes

Read the action's execution state and Receipt. Accepting text does not prove
that an executor completed an effect. An external destination has its own
credential and boundary.

The audit export includes loops, supporting records, and nudge history. A
model draft can send the selected context to its configured model endpoint.
Telegram delivery sends the presented content to the configured chat.

## Troubleshooting

| Problem | Action |
| --- | --- |
| No background evaluation | Check `enabled`, runtime state, and Control mode. |
| Manual evaluation works but Telegram is quiet | Check Telegram enablement, token, pairing, chat allow-list, and timing policy. |
| A discarded loop returns | Inspect whether its source changed materially. |
| A next action has no external result | Read its authorization and execution states. |
| An Interview cadence preference does nothing | Configure a supported recurring path. Interview context alone does not enable Cadence. |

## See also

- [Automation](AUTOMATION.md): triggers and execution paths.
- [Notices and the Heartbeat](USER_GUIDE.md#notices-and-the-heartbeat): Heartbeat configuration.
- [Control modes](AUTHORITY.md): approval and grant rules.
- [Security & Privacy](SECURITY.md): data and credential boundaries.
