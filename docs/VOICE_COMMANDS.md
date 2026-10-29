# Voice Commands

Voice Commands match a complete spoken utterance against configured closed
commands. A match dispatches its configured action. Text that does not match
remains dictation text.

## Set up a command

Create commands in **Settings ▸ Speak ▸ Voice commands**. Each command has a phrase, an action,
and an enabled state. Keep phrases distinct. A `type_text` action needs a
focused desktop relay or the action records a named refusal.

The test route is `POST /api/commands/test`. It evaluates the configured
command without making a live desktop effect.

## Command behaviors

Commands can route to a Desk operation, type configured text, or start and stop
supported capture behavior. The streaming route and the remote dictation route
use the same bounded dispatcher.

A voice command does not bypass authentication, the audio floor, the target
identity, or operation policy. A voice command failure does not block ordinary
dictation. The journal records whether a command matched and whether its
connector completed.

## How matching works

The dispatcher normalizes the complete utterance and checks enabled commands.
It does not run a model to guess an action. Partial or ambiguous text stays
prose. A configured voice command is not a generic command language.

## Test a command

Use the test control or `POST /api/commands/test` with a disposable phrase.
Inspect the returned match and refusal. The test path does not type into the
focused application.

## Turn commands on and off

Disable the voice-command setting to keep every utterance as dictation. The
stream still transcribes one final utterance and returns its text.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Phrase stays as prose | Speak the full configured phrase and check that it is enabled. |
| Type action refuses | Check the focused relay and desktop typing readiness. |
| Meeting voice command refuses | Release the browser mic interval before starting Meeting. |
| Remote command fails | Read the delivery receipt and retry the same delivery id if the outcome is unknown. |

## See also

- [Dictation Pipeline Guide](DICTATION_PIPELINE_GUIDE.md)
- [Dictation architecture](DICTATION_ARCHITECTURE.md)
- [Security](SECURITY.md)
