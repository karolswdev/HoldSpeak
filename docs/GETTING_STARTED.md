# Getting Started

Install HoldSpeak and keep your first sentence as text.
Then configure models for Threads, Interview, and other AI work.

## Requirements

- Python 3.10 or later.
- A microphone and permission to use it.
- A supported transcription backend: MLX Whisper on Apple Silicon, or faster-whisper on Linux.
- For a source installation: Git, `uv`, npm, and Node.js 22.12 or later.

The transcription backend can download model files on first use.
A text model is a separate requirement for AI work.

On macOS, grant microphone access to the process that starts HoldSpeak.
Global hotkeys and text insertion can also require Accessibility and Input Monitoring permissions.
If PortAudio is missing, install it with `brew install portaudio`.

On Debian or Ubuntu, install the system audio dependencies:

```sh
sudo apt-get install portaudio19-dev ffmpeg xclip pulseaudio-utils
```

Linux packages and desktop permissions differ by distribution.
Wayland can restrict global hotkeys and direct text insertion.

## Install from source

This path provides the features documented on `main`.
The Python build hook installs the Web dependencies and builds the Web app.

1. Clone the repository.

   ```sh
   git clone https://github.com/karolswdev/HoldSpeak.git
   cd HoldSpeak
   ```

2. Create a virtual environment.

   ```sh
   uv venv
   ```

3. Activate the environment.

   ```sh
   source .venv/bin/activate
   ```

4. Install HoldSpeak with the applicable command.

   ```sh
   # Apple Silicon
   uv pip install -e .

   # Linux
   uv pip install -e '.[linux]'
   ```

Run only the command for your platform.
Keep this environment active for the commands in this guide.

## Install a published package

A published package can differ from these documents.
Use this path when you want a release instead of a source checkout.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install holdspeak
```

On Linux, replace the last command with `python -m pip install 'holdspeak[linux]'`.
A prebuilt wheel includes the Web app. A source package requires npm to build it.

## Start HoldSpeak

1. Start the runtime.

   ```sh
   holdspeak
   ```

2. Open the URL printed in the terminal.

The default listener uses loopback (`127.0.0.1`).
Use the printed URL because the port and access parameters can differ.
See [Security & Privacy](SECURITY.md) before you enable remote access.

## Keep your first sentence

1. Select **Dictate one sentence** on the Desk.
2. Grant browser microphone access if requested.
3. Dictate a short sentence.
4. Edit the transcript if necessary.
5. Select **Copy** or **Keep as Note**.

This step requires no model and no configured AI service.
Type the sentence instead when a microphone is unavailable.
**Copy** and **Keep as Note** become available as soon as the text field contains text.
A setup verdict of `needs_attention` or `blocked` describes later AI work.
It does not withhold this first sentence.

The first completion creates six drawers: Inbox, Personal, Work, Meetings, Decisions, and Reference.
It also creates a Start here Note and the **Everyday context** prompts.
These prompts contain questions and examples. They contain no inferred personal facts.

Everyday context starts unused.
Attach it when you want a model to use it.
You can also choose an explicit default for future Thoughts.
See [Develop a thought](USER_GUIDE.md#develop-a-thought) for those controls.

## Find your work

The **arrival** shows items that need you, unfinished Thoughts, a brief, and recent Meetings.
Use **Floor** to open the spatial Desk.
Use the **Desk** menu to create records and the **Go** menu to open tools.
On phones, use the compact **Go** menu.

| Address | Destination |
| --- | --- |
| `/` | The Desk, including first capture on a new installation |
| `/dictation` | Speak |
| `/history` | Meetings |
| `/studio` | Studio |
| `/settings` | Settings |
| `/setup` | Setup diagnostics and recovery |

These addresses open the corresponding surface within the Desk.
See [The Desk](WEB_DESK.md) for windows, objects, and navigation.

## Configure AI work

1. Open **Settings > Models**.
2. Review the engines listed by the Concierge.
3. Add an endpoint or download a supported model if no suitable engine exists.
4. Check the host and engine proposed for each capability group.
5. Select **Use these** when the required groups are ready.

Use **Adjust** when an individual capability needs a different assignment.
A cloud **Check** can make a paid request. Its control shows the cost indicator.
Select **Test** under the proposed set to run one real request through the assigned route.
See [Models](MODELS.md) for setup requirements and readiness failures.

Opening **Models** from an unfinished task opens it as a window over that task.
The task keeps its text. Readiness is re-read when you apply a set with **Use these**.

## Start an Interview

1. Select **Desk > New Thread**.
2. Select the **Interview** mode.
3. Describe one outcome you want from HoldSpeak.
4. Select **Send**.

For example: “Help me prepare a weekly architecture decision review.”
The model can ask questions, inspect permitted records, and save context or suggestions.
Use **Section** to revisit a topic.
See [Interview](INTERVIEW.md) for saved context, manual drafts, and current limits.

## Dictate into another app

1. Place the cursor in a text field.
2. Hold Right Option on macOS or Right Alt on Linux.
3. Speak.
4. Release the key.

These are the default hotkeys. Settings can specify a different key.
The active Control mode and preview setting determine whether HoldSpeak types immediately or shows a preview.
See [Voice typing](USER_GUIDE.md#voice-typing) for punctuation, clipboard insertion, and wake-word input.

## Grant macOS permissions

Voice typing needs three separate permissions on macOS. Each one buys a
different part of the path, and any of them can be missing on its own.

| Permission | What it buys | Without it |
| --- | --- | --- |
| Microphone | The audio itself | Nothing is heard |
| Input Monitoring | The global hotkey | Right Option is never noticed |
| Accessibility | Typing into the focused app | Words are transcribed, then never arrive |

All three live in **System Settings > Privacy & Security**, one pane each.

**Grant them to the application you launch HoldSpeak from.** This is the part
that surprises people. If you start the hub from a terminal, macOS attributes
the request to that terminal, so the entry you must enable is Terminal or
iTerm, not something named HoldSpeak. If you later launch it a different way,
the grants do not follow, and you grant the new launcher instead.

**Quit and reopen the launching application after you grant.** macOS applies
several of these only to a newly started process. A permission can read as
granted in System Settings and still not work until the application restarts.

You may also see a prompt asking to control **System Events**. HoldSpeak uses
that to identify which application is frontmost, so it knows where the words
are going.

Speak, in the Desk, reads all three and says which one is missing. The hotkey
itself reads `ACTIVE` when the key is up and every grant is held, `BLOCKED`
when the key is up but a grant is missing, and `UNAVAILABLE` when the listener
did not install at all. `BLOCKED` is the state that used to be invisible: the
key appears to work and hears nothing.

Each permission that is not granted draws its own row, reading `DENIED`,
`NOT ASKED`, or `UNKNOWN`. `NOT ASKED` means the launching application is not
listed in that pane yet, which is the ordinary state before the first grant.
`UNKNOWN` means HoldSpeak could not read the state and will not guess. After
you change a permission, press `Re-check` rather than restarting the hub.

When every grant is held and the key is up, none of this is drawn. A working
hotkey says nothing, because there is nothing to repair.

Linux has no equivalent panes. There, a global hotkey needs an active GUI
session, and Wayland may block synthetic typing entirely. Use the clipboard
paste fallback where it does.

## Add optional capabilities

From an active source environment, install only the extras you need:

| Capability | Command |
| --- | --- |
| Meeting analysis and optional meeting dependencies | `uv pip install -e '.[meeting]'` |
| Local GGUF text runtime | `uv pip install -e '.[dictation-llama]'` |
| MLX text runtime on Apple Silicon | `uv pip install -e '.[dictation-mlx]'` |
| OpenAI-compatible dictation runtime | `uv pip install -e '.[dictation-openai]'` |

The package form uses `holdspeak[extra]` in place of `.[extra]` and omits `-e`.
See [Meeting mode](MEETING_MODE_GUIDE.md) for system audio setup.
See [Project Rooms](PROJECT_ROOMS.md) for source-provider requirements.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Installation cannot build the Web app | Check `node --version` and `npm --version`. Install the required Node version, then repeat the installation. |
| Capture cannot start | Check the browser microphone permission, then **System Settings > Privacy & Security > Microphone**. Run `holdspeak doctor`. |
| Transcription fails | Read the reported backend or model error. Install the platform extra if it is missing. |
| The hotkey works but text does not appear | Grant **System Settings > Privacy & Security > Accessibility** to the application you launched from, then restart it. Check the preview setting. On Wayland, try clipboard paste. |
| The hotkey does nothing at all | Grant **System Settings > Privacy & Security > Input Monitoring** to the application you launched from, then restart it. Speak names this state and offers `Re-check`. |
| A Thread cannot run | Open **Settings > Models**. Repair the named assignment or engine. |
| A documented control is absent | Compare your installed version with `main`. Check the guide for that feature. |
| You need to restore data | Read [Release and recovery](RELEASING.md) before you run `holdspeak restore`. |

## See also

- [User Guide](USER_GUIDE.md): daily tasks and detailed controls.
- [Interview](INTERVIEW.md): repeatable context discovery and suggestions.
- [Models](MODELS.md): engine availability and capability assignments.
- [Control modes](AUTHORITY.md): approval rules and action limits.
