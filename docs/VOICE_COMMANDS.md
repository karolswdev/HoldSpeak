# Voice Commands

A voice command maps a spoken keyword to one action. When you say the keyword
as a whole utterance, HoldSpeak runs the action and types nothing. A command
can open a URL, launch an app, run a shell command, or type a snippet.

Voice commands are off until you turn them on. Read
[Getting Started](./GETTING_STARTED.md) first if dictation does not work yet.

> **You own what you configure.** A command runs without a confirmation
> prompt. If you map "ship it" to a shell command, that command runs on your
> machine when you say "ship it". The configuration is your approval.

## Set up a command

1. Open the **Commands** page (`/commands`).
2. Click **Add command**.
3. Type the **Spoken keyword**, for example `terminal`.
4. Set **Command behavior** and fill in the **Payload**.
5. Click **Test without saving** to check the action.
6. Click **Save command**.
7. Click **Enable in Settings**. In **Settings > Voice > Typing**, turn on
   **Voice commands**.

Hold the dictation hotkey, say the keyword alone, and release. HoldSpeak runs
the action.

## Command behaviors

| Behavior | Action | Example payload |
|---|---|---|
| **Open URL** | Opens the URL in your default browser (`open` on macOS, `xdg-open` on Linux) | `https://example.com/docs` |
| **Launch app** | Opens the app (`open -a` on macOS, the app name on Linux) | `Terminal` |
| **Shell command** | Runs the command on your machine | `git push origin HEAD` |
| **Type text** | Types the snippet into the focused app | A standup template |

**Type text** is the only behavior that types. The other three act on your
machine.

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

**Test** on a card runs the saved command. **Test without saving** in the
editor runs the draft. For **Open URL**, **Launch app**, and **Shell
command**, the test runs the real action. For **Type text**, the test shows
a preview only, because the text goes to the focused app when you speak.

## Turn commands on and off

The switch lives in **Settings > Voice > Typing > Voice commands**. The
Commands page shows **Commands on** or **Commands off** and links to it.
While the switch is off, no command fires and the hotkey types as normal. You
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
