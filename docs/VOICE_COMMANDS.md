# Voice Commands

A voice command maps a spoken keyword to one action. When you say the keyword
as a whole utterance, HoldSpeak runs the action and types nothing. A command
can run a desk verb, open a URL, launch an app, run a shell command, or type a snippet.

A new desk has these commands on:

| Say | Action |
|---|---|
| `start recording` | Starts a meeting recording |
| `stop recording` | Stops the current recording |
| `new note` | Creates and opens a note |
| `ask HoldSpeak` | Opens Ask |
| `open today` | Opens Today |

Use **Talk** in **Speak** for these desk commands. During a recording, only
`stop recording` is accepted. Field microphones type words into their field;
they do not run commands. A saved Off setting stays off.

Read [Getting Started](./GETTING_STARTED.md) first if dictation does not work yet.

> **You own what you configure.** A command runs without a confirmation
> prompt. If you map "ship it" to a shell command, that command runs on your
> machine when you say "ship it". The configuration is your approval.

## Set up a command

1. Open **Speak > Voice commands**. The old `/commands` address opens this wing.
2. Click **Add command**.
3. Type the **Spoken keyword**, for example `terminal`.
4. Set **Command behavior** and fill in the **Payload**.
5. Use **Preview** for a desk verb, or **Test without saving** for a custom action.
6. Click **Save command**.
7. If commands are off, use **Enable in Settings** and turn on **Voice commands**.

Press **Talk** in Speak, say the phrase alone, then press Stop. Custom local
actions also work with the dictation hotkey. Desk verbs use Speak.

## Command behaviors

| Behavior | Action | Example payload |
|---|---|---|
| **Desk verb** | Runs one of the five desk actions above | Select the desk verb |
| **Open URL** | Opens the URL in your default browser (`open` on macOS, `xdg-open` on Linux) | `https://example.com/docs` |
| **Launch app** | Opens the app (`open -a` on macOS, the app name on Linux) | `Terminal` |
| **Shell command** | Runs the command on your machine | `git push origin HEAD` |
| **Type text** | Types the snippet into the focused app | A standup template |

**Type text** is the only behavior that types. Desk verbs cannot send,
change settings, grant access, or run a command you did not select.

Each command runs exactly the payload you saved. Your speech selects a
command. It never builds one. A misheard word can fire a different command
that you already saved. It cannot create a new command.

The board shows each command as the quoted keyword and one line that says
what it does, for example `runs git status · runs code`.

## How matching works

HoldSpeak compares your whole phrase with each keyword. The match ignores
case, surrounding spaces, and trailing `. ! ? ,`. "Terminal." matches
`terminal`.

- The whole utterance must match. A keyword inside a longer sentence is
  dictated as normal text.
- The first matching command in the list runs.
- The editor shows the normalized keyword next to the field.
- Voice commands are checked after punctuation cleanup and before the
  [dictation pipeline](./DICTATION_PIPELINE_GUIDE.md). A command that matches
  skips the pipeline.

## Test a command

**Preview** for a desk verb shows its action. It does not run the verb.
Use Talk in Speak to run it.

**Test** on a custom-action row runs the saved command. **Test without saving**
in the editor runs that draft. For **Open URL**, **Launch app**, and **Shell
command**, the test runs the real action. For **Type text**, the test shows
a preview only, because the text goes to the focused app when you speak.

## Turn commands on and off

The Voice commands wing shows **Commands on** or **Commands off**.
Use **Manage in Settings** or **Enable in Settings** to reach the switch.
While the switch is off, no command fires. You
can edit commands while it is off.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Nothing happens when I say the keyword | Turn on **Voice commands**. Say the keyword alone. |
| A command runs the wrong action | Read the line on the card. Edit the command. |
| A shell command fails | Click **Test**. The error shows on the page. Fix the payload. |
| Two commands share a keyword | The first one in the list runs. Rename one keyword. |
| A command fails when I speak it | The last error shows as "Voice command failed". Test the command from the board. |

## See also

- [Getting Started](./GETTING_STARTED.md): install, permissions, first dictation.
- [Dictation Pipeline Guide](./DICTATION_PIPELINE_GUIDE.md): what happens to text that is not a command.
- [Security & Privacy](./SECURITY.md): what stays on your machine.
