# Cadence

Cadence reviews unresolved work and prepares next actions.
It can use meeting action items, proposed actions, and Coder sessions that need a reply.

The background Cadence loop is off by default.
Manual commands can still inspect work or request an evaluation.
Cadence is separate from the [Heartbeat](USER_GUIDE.md#rhythm) and from preferences saved in [Interview](INTERVIEW.md).

## Inspect work manually

Run these commands from your HoldSpeak environment:

```sh
holdspeak cadence status
holdspeak cadence loops
holdspeak cadence run-now
holdspeak cadence brief
```

`status` reports the engine state.
`loops` lists unresolved work.
`run-now` requests one evaluation, including when background Cadence is disabled.
`brief` shows the current brief.

The Web Cadence surface also provides current work, open loops, review, and history.
Open it through Studio or the `/cadence` address.

## Understand the records

| Record | Meaning |
| --- | --- |
| Open loop | Unresolved work derived from a source record |
| Next action | A prepared response to that work, such as an owner assignment or issue draft |
| Nudge | A presentation of the next action through an enabled delivery surface |
| Decision | Your response, such as snooze, completion, dismissal, or delegation |

Cadence retains your decisions about a loop.
A dismissed loop stays dismissed unless its source materially changes.
The optional model can draft wording. Execution still requires the applicable operation authority.

## Configure background Cadence

The configuration uses the `cadence` object in `~/.config/holdspeak/config.json`.
These example values keep background work and model drafts disabled:

```json
{
  "cadence": {
    "enabled": false,
    "pressure": "normal",
    "use_llm": false,
    "quiet_hours_start": 22,
    "quiet_hours_end": 8,
    "max_nudges_per_day": 12
  }
}
```

Set `enabled` to `true` when you want the runtime loop.
The runtime must be available for background evaluation.
**Secure** Control mode permits explicit `run-now` but prevents the background loop.
See [Control modes](AUTHORITY.md) for precedence and effects.

`pressure` accepts `gentle`, `normal`, or `aggressive` and changes timing.
It does not add authority.
`use_llm` permits model-generated draft wording.
If that draft fails validation, Cadence uses its deterministic next action.

## Deliver through Telegram

Telegram delivery has a separate `cadence_telegram` configuration.
It is disabled by default and requires a bot token plus permitted chat IDs or the pairing flow.
Only configured, permitted chats receive delivery.
Keep the token in the credential configuration, not in a Note or Thread.

The Telegram controls include `/brief`, `/loops`, and `/status`.
Inline controls can record decisions about the presented work.
Telegram configuration does not replace authority checks for a proposed external action.

## Inspect outcomes

Use the action's execution state and Receipt to determine whether an effect occurred.
Accepting content does not prove that an executor completed it.
Eligible configured destinations can execute directly under YOLO.
Normal and Secure require the applicable decision or scoped grant.

To export a local audit file, run:

```sh
holdspeak cadence audit --out audit.json
```

The audit includes loops, supporting records, and nudge history.
Model drafts can send context to the configured model endpoint.
Telegram delivery sends content to the configured chat.
Authorized outbound actions can contact their configured destinations.
See [Security & Privacy](SECURITY.md) for the complete data boundary.

## Troubleshooting

| Problem | Action |
| --- | --- |
| No background evaluation occurs | Check `enabled`, the runtime state, and Control mode. |
| Manual evaluation works but no Telegram message arrives | Check Telegram enablement, credentials, pairing, and timing limits. |
| A discarded loop returns | Check whether its source materially changed. Inspect the audit history. |
| A next action exists but has no external result | Inspect its authorization and execution states. |
| An Interview cadence preference never runs | Configure a supported recurring path. Interview context alone does not enable Cadence. |

## See also

- [Automation](AUTOMATION.md): triggers and execution paths.
- [Rhythm](USER_GUIDE.md#rhythm): Heartbeat configuration.
- [Control modes](AUTHORITY.md): approval and grant rules.
- [Security & Privacy](SECURITY.md): data and credential boundaries.
