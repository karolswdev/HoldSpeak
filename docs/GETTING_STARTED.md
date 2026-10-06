# Getting Started

Install HoldSpeak and keep your first sentence as text.
Then set up models for Threads, Interview, and other AI work.

## Requirements

- Python 3.10 or later.
- A microphone and permission to use it.
- For a source installation: Git, `uv`, npm, and Node.js 22.12 or later.

The base install includes the transcription backend for Apple Silicon (MLX Whisper), the local GGUF text runtime, and the OpenAI-compatible client.
Linux needs the `linux` extra for faster-whisper.
The transcription backend can download model files on first use.
The local text runtime builds from source, so it needs CMake and a C++ compiler.

On macOS, install PortAudio if it is missing: `brew install portaudio`.
On Debian or Ubuntu, install the system audio packages:

```sh
sudo apt-get install portaudio19-dev ffmpeg xclip pulseaudio-utils
```

Linux packages and desktop permissions differ by distribution.
Wayland can block global hotkeys and direct text insertion.

## Install from source

The Python build hook installs the Web dependencies and builds the Web app.

1. Clone the repository.

   ```sh
   git clone https://github.com/karolswdev/HoldSpeak.git
   cd HoldSpeak
   ```

2. Create and activate a virtual environment.

   ```sh
   uv venv
   source .venv/bin/activate
   ```

3. Install HoldSpeak. Run only the command for your platform.

   ```sh
   # Apple Silicon
   uv pip install -e .

   # Linux
   uv pip install -e '.[linux]'
   ```

Keep this environment active for the commands in this guide.

## Install a published package

A published package can differ from `main`.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install holdspeak
```

On Linux, install `'holdspeak[linux]'` instead.
A prebuilt wheel includes the Web app. A source package needs npm to build it.

## Start HoldSpeak

1. Start the hub.

   ```sh
   holdspeak
   ```

2. Open the URL printed in the terminal.

The hub listens on loopback (`127.0.0.1`).
Use the printed URL, because the port and access parameters can differ.
Read [Security & Privacy](SECURITY.md) before you enable remote access.

## Keep your first sentence

1. Select **Dictate one sentence** on the Desk.
2. Allow browser microphone access if the browser asks.
3. Say a short sentence.
4. Edit the text if necessary.
5. Select **Copy** or **Keep as Note**.

This step needs no model.
If you have no microphone, type the sentence.
A setup state of `needs_attention` or `blocked` affects later AI work only.

The first **Keep as Note** creates six drawers: Inbox, Personal, Work, Meetings, Decisions, and Reference.
It also creates a Note named Start here and the **Everyday context** prompts.
The prompts hold questions and examples. They hold no guessed personal facts.

Everyday context starts unused.
Attach it when you want a model to use it.
See [Develop a thought](USER_GUIDE.md#develop-a-thought) for the controls.

## Find your work

The **arrival** shows items that need you, unfinished Thoughts, a brief, and recent Meetings.
Select **Floor** to open the spatial Desk.
Use the **Desk** menu to create records and the **Go** menu to open tools.

| Address | Opens |
| --- | --- |
| `/` | The Desk, with first capture on a new installation |
| `/dictation` | Speak |
| `/history` | Meetings |
| `/studio` | Studio |
| `/settings` | Settings |
| `/setup` | Setup checks and recovery |

Each address opens its window on the Desk.
See [The Desk](WEB_DESK.md) for windows and navigation.

## Set up models

1. Open **Settings > Models**.
2. Read the engines that the Concierge lists.
3. Add an endpoint or download a model if no engine fits.
4. Check the host and engine proposed for each capability group.
5. Select **Use these** when the required groups are ready.

Select **Adjust** to change one capability.
A cloud **Check** can make a paid request. Its control shows a cost indicator.
Select **Test** to send one real request through the assigned route.
See [Models](MODELS.md) for requirements and readiness failures.

## Start an Interview

1. Select **Desk > New Thread**.
2. Select the **Interview** mode.
3. Describe one outcome that you want from HoldSpeak.
4. Select **Send**.

Example: "Help me prepare a weekly architecture decision review."
The model asks questions, reads permitted records, and saves context or suggestions.
Use **Section** to revisit a topic.
See [Interview](INTERVIEW.md) for details.

## Dictate into another app

1. Put the cursor in a text field.
2. Hold Right Option on macOS or Right Alt on Linux.
3. Speak.
4. Release the key.

These are the default keys. Settings can change the key.
The Control mode and the preview setting decide if HoldSpeak types at once or shows a preview.
See [Voice typing](USER_GUIDE.md#voice-typing) for punctuation, clipboard insertion, and the wake word.

## Grant macOS permissions

Voice typing needs three permissions. Each one covers a different part of the path.

| Permission | What it allows | Without it |
| --- | --- | --- |
| Microphone | Audio capture | Nothing is heard |
| Input Monitoring | The global hotkey | The key is never noticed |
| Accessibility | Typing into the focused app | Words are transcribed but do not arrive |

Grant each one in **System Settings > Privacy & Security**.

Grant them to the application that launches HoldSpeak.
If you start the hub from a terminal, enable that terminal, not HoldSpeak.
A different launcher needs its own grants.

Quit and reopen the launching application after you grant.
macOS can show a permission as granted and still ignore it until the process restarts.

macOS can also ask to control **System Events**.
HoldSpeak uses it to find the frontmost application, so it knows where the words go.

Speak shows which permission is missing.
The hotkey state reads:

- `ACTIVE`: the key is up and all grants are held.
- `BLOCKED`: the key is up and a grant is missing.
- `UNAVAILABLE`: the key listener did not start.

Each missing permission shows its own row: `DENIED`, `NOT ASKED`, or `UNKNOWN`.
`NOT ASKED` means the launching application is not in that pane yet.
`UNKNOWN` means HoldSpeak could not read the state.
After you change a permission, select **Re-check**. You do not need to restart the hub.

Linux has no such panes.
A global hotkey needs an active GUI session.
Where Wayland blocks typing, use the clipboard paste fallback.

## Add optional capabilities

Install only the extras that you need:

| Capability | Command |
| --- | --- |
| Meeting analysis and speaker labels | `uv pip install -e '.[meeting]'` |
| MLX text runtime on Apple Silicon | `uv pip install -e '.[dictation-mlx]'` |
| Local wake word | `uv pip install -e '.[wakeword]'` |
| Server-side speech output | `uv pip install -e '.[tts]'` |

For a package install, use `holdspeak[extra]` and omit `-e`.
See [Meeting mode](MEETING_MODE_GUIDE.md) for system audio setup.
See [Project Rooms](PROJECT_ROOMS.md) for source-provider requirements.

## Troubleshooting

| Problem | Action |
| --- | --- |
| The Web app does not build | Check `node --version`. Install Node.js 22.12 or later. Repeat the install. |
| Capture does not start | Check the browser microphone permission and the macOS Microphone pane. Run `holdspeak doctor`. |
| Transcription fails | Read the backend error. Install the platform extra if it is missing. |
| The key works but no text appears | Grant Accessibility to the launching application. Restart it. Check the preview setting. On Wayland, try clipboard paste. |
| The key does nothing | Grant Input Monitoring to the launching application. Restart it. Select **Re-check** in Speak. |
| A Thread does not run | Open **Settings > Models**. Repair the named assignment or engine. |
| You need to restore data | Read [Release and recovery](RELEASING.md). Then run `holdspeak restore`. |

## See also

- [User Guide](USER_GUIDE.md): daily tasks and controls.
- [Interview](INTERVIEW.md): repeatable context discovery.
- [Models](MODELS.md): engines and capability assignments.
- [Control modes](AUTHORITY.md): approval rules and action limits.
