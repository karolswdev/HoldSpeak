# Voice Commands

Voice commands turn a spoken keyword into a real action. Say a keyword while
dictating and HoldSpeak runs the action instead of typing it: open a URL, launch an
app, run a shell command, or type a snippet. You configure every command on the
Voice Commands board, so you decide exactly what runs.

They are off until you turn them on. If you are starting from zero, read
[Getting Started](./GETTING_STARTED.md) first.

> **You own what you configure.** A voice command runs the action you set up, with no
> confirmation prompt at the moment you speak it. If you map "ship it" to a shell
> command, that command runs on your machine when you say "ship it". The safety comes
> from you configuring it, and from each command being limited to exactly the action
> you gave it.

## Quickstart

1. Open the **Commands** page (`/commands`, under "Configure" in the top nav).
2. Click **Add a command**, or pick one of the starter examples.
3. Type the keyword you want to say (for example `terminal`).
4. Choose what it does and fill in the one field that appears (a URL, an app, a
   command, or a snippet).
5. Click **Test** to fire it once and confirm it works, then **Save**.
6. Turn the **Voice commands** switch on (top right of the board).

Now hold your dictation hotkey, say the keyword on its own, and release. HoldSpeak
runs the action and types nothing.

## How matching works

HoldSpeak compares your whole spoken phrase against each command's keyword. The match
is case-insensitive and ignores trailing punctuation, so "Terminal." matches the
keyword `terminal`. The match is exact and whole-phrase: speaking a keyword on its own
fires the command; speaking a longer sentence is dictated normally.

This is deterministic. Your speech only selects **which** command fires. It never
builds a new command, so a misheard word can at most fire a different command you
already set up. It cannot invent one.

The board shows the normalized keyword each command listens for ("matches: terminal")
so there is no guessing.

## What a command can do

Each command does exactly one of four things. The editor shows one field for the kind
you pick, and the board reads back the exact action on every card.

| Kind | What it does | Example |
|---|---|---|
| **Open URL** | Opens a URL in your default browser | `docs` opens your project page |
| **Launch app** | Opens an app (`open -a` on macOS, the app name on Linux) | `terminal` opens Terminal |
| **Shell** | Runs a shell command on your machine | `ship it` runs `git push origin HEAD` |
| **Type text** | Types a snippet into the focused app | `standup` types your standup template |

`Type text` is the one kind that still types: it inserts your snippet wherever your
cursor is, which is useful for templates and boilerplate. The other three do something
on your machine instead of typing.

## Running shell commands

A shell command runs real code on your machine when you say the keyword. The board is
honest about this: a shell command shows in a monospace box with a "runs code" mark,
and the editor reminds you that it runs with no confirmation. There is no extra prompt
because you already approved it by configuring it.

Each command is limited to the exact action you saved. A command that runs
`git status` can only ever run `git status`. It cannot be turned into a different
command by anything you say.

## Test before you rely on it

Every command has a **Test** button, on its card and in the editor. Test fires the
action once from the board so you can confirm it works before you depend on it while
dictating. For `Open URL`, `Launch app`, and `Shell`, Test runs the real action. For
`Type text`, Test shows you the preview, since it types into whatever app has focus.

## Turning it on and off

The whole feature is off by default. The master switch on the board turns it on and
off. While it is off, the dictation hotkey types exactly as it always has, and no
command fires. You can build and edit commands while the feature is off, then turn it
on when you are ready.

## Limitations

- **Whole-phrase only.** A command fires when its keyword is the whole thing you say.
  HoldSpeak does not pick commands out of the middle of a sentence.
- **Type text follows focus.** A `Type text` command inserts into whatever app has
  focus when you say the keyword, the same as normal dictation.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Nothing happens when I say the keyword | Check the master switch is on, and that you said the keyword on its own. The card shows the exact phrase it matches. |
| The command runs the wrong thing | Open the card's preview line: it shows exactly what fires. Edit it if it is not what you meant. |
| A shell command fails | Click **Test** to see the error inline, then fix the command. |
| Two commands share a keyword | The editor warns you when a keyword is already used. Rename one. |

## See also

- [Getting Started](./GETTING_STARTED.md): install, permissions, and your first dictation.
- [User Guide](./USER_GUIDE.md): the day-to-day, including the web runtime.
- [Security & Privacy](./SECURITY.md): what stays on your machine and what controls you have.
