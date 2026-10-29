# Getting Started

Install HoldSpeak, open its web Desk, and keep one useful sentence as a Note.
Then choose engines for Ask, Threads, voice typing, and meeting work.

## Requirements

- Python 3.10 or later.
- A microphone for voice typing or recording.
- For a source install: Git, `uv`, npm, and Node.js 22.12 or later.
- For local text work: CMake and a C++ compiler.

The base install includes the Apple Silicon speech backend, a local GGUF text
runtime, and an OpenAI-compatible client. Linux needs the `linux` extra for
`faster-whisper`. The web Desk needs a browser that can reach the local hub.

On macOS, install PortAudio when it is missing:

```sh
brew install portaudio
```

On Debian or Ubuntu, install the system audio packages:

```sh
sudo apt-get install portaudio19-dev ffmpeg xclip pulseaudio-utils
```

Linux permissions and global hotkeys depend on the desktop session. Wayland
can block a global key or direct text insertion. Use the clipboard fallback
when the focused application does not accept direct insertion.

## Install from source

The Python build hook installs the web dependencies and builds the web app.

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

3. Install one platform variant.

   ```sh
   # Apple Silicon
   uv pip install -e .

   # Linux
   uv pip install -e '.[linux]'
   ```

Keep the environment active when you run `holdspeak`.

## Install a published package

A published package can differ from the repository branch.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install holdspeak
```

On Linux, install `holdspeak[linux]`. A wheel includes the web app. A source
package needs npm to build it.

## Start HoldSpeak

1. Start the local hub.

   ```sh
   holdspeak
   ```

2. Open the URL printed in the terminal.

The hub listens on loopback by default. Use the printed URL because its port
and access parameters can differ. Read [Security & Privacy](SECURITY.md)
before you enable remote access.

The hub is the service host for the Desk. The browser is the user interface.
MCP clients and paired clients use the same service boundary when configured.

## Keep your first sentence

1. Open **Go > Setup** (or **Settings > This Mac > Setup**) and read the
   **Readiness** list.
2. If the **Speech** row is not ready, select **Set up speech** and wait for
   its state to become **Ready**.
3. Select **Say one sentence**, allow microphone access, and speak.
4. Select **Keep as note**.

Without a microphone or a ready speech model, write the sentence in **New
Note** instead. Setup can remain pending or blocked while text Notes still
work. The active setup flow uses **Readiness**, **Set up speech**, and
**Say one sentence**; an older first-run screen is parked.

The result is an editable Note. **Thought** is an older domain name for the
same refinement path. The current window label is **Note**. A setup state of
`needs_attention` or `blocked` affects later AI work. It does not prevent you
from writing a Note.

The first Desk setup can create the standard drawers and a Start here Note.
The **Everyday context** prompts are examples. They contain no guessed facts.
Attach a prompt only when you want an engine to use it.

## Find your work

Open **Today** for current work and **Needs you** for items that need an
action. Open **Memory** to search retained records and standing pages. Open a
Project for its Project Room. Use **Go** or Search to open another app.

Open **Go > Ask AI** (the window is labelled **Ask**), or press **⌘I**. Ask
and Thread use one window. To start a new conversation, select the first row
in **Recent** or press **⌘N**. The first question becomes a saved Thread, and
follow-up questions continue it.
Select **Ask about this** on a record to start with that record in **About**.
About is a retrieval starting point. It is not a promise that other permitted
Desk records are excluded.

## Set up models

1. Open **Settings > Engines**.
2. Read the engine and host for each capability.
3. Add an endpoint or download a model when no engine is ready.
4. Select **Use these** when the required assignments are ready.
5. Select **Test** only when you want to send a real request.

A CLI engine is an inference route. It is not a coding-agent session. A
coding-agent handoff starts a separate agent session with its own repository
and worktree. A persona supplies instructions. It is not an engine or a live
agent.

See [Models](MODELS.md) for readiness and [Control modes](AUTHORITY.md) for
approval rules. A cloud **Check** can make a paid request. Read the route and
host before a run.

## Ask your first question

For a guided discussion in the current Desk, start an Ask with a specific request.
For example: “Help me prepare a weekly architecture decision review. Ask one useful question at a time.”
Use follow-up questions and **Save as note** to keep a separate working brief.

The retained Interview mode has sectioned facts and suggestions through the Thread services.
Its older browser mode tabs and section controls are parked.
The current Ask does not expose an **Interview** mode picker.
Read [Interview](INTERVIEW.md) for the available service path and the separate Note-refinement pane.

## Dictate into another app

1. Put the cursor in a text field.
2. Hold Right Option on macOS or Right Alt on Linux.
3. Speak.
4. Release the key.

These are the default keys. Settings can change them. The control mode and
preview setting decide whether HoldSpeak types directly or shows a preview.
See [Voice typing](USER_GUIDE.md#voice-typing) for punctuation, clipboard
insertion, and the wake word.

## Grant macOS permissions

Voice typing needs three permissions. Each permission covers a different step.

| Permission | Allows | Without it |
| --- | --- | --- |
| Microphone | Audio capture | HoldSpeak hears no audio. |
| Input Monitoring | Global hotkey | The key is not detected. |
| Accessibility | Insertion into the focused app | Text is transcribed but not inserted. |

Grant permissions in **System Settings > Privacy & Security**. Grant them to
the application that launches HoldSpeak. If a terminal starts the hub, grant
the terminal. Restart that launcher after a grant.

Speak shows the permission state. Select **Re-check** after a change. macOS
can also ask to control **System Events** so HoldSpeak can identify the
frontmost application.

Linux has no matching permission panes. A global hotkey needs an active GUI
session. Use clipboard paste when the desktop blocks direct typing.

## Add optional capabilities

Install only the extra that you need:

| Capability | Command |
| --- | --- |
| Meeting analysis and speaker labels | `uv pip install -e '.[meeting]'` |
| MLX text runtime on Apple Silicon | `uv pip install -e '.[dictation-mlx]'` |
| Local wake word | `uv pip install -e '.[wakeword]'` |
| Server-side speech output | `uv pip install -e '.[tts]'` |

For a package install, use `holdspeak[extra]` and omit `-e`. Provider setup
and source scope are separate from package installation. See [Project
Rooms](PROJECT_ROOMS.md) for provider prerequisites.

## Troubleshooting

| Problem | Action |
| --- | --- |
| The web app does not build | Check `node --version`. Install Node.js 22.12 or later. Repeat the install. |
| Capture does not start | Check browser microphone permission and the macOS Microphone pane. Run `holdspeak doctor`. |
| The key does nothing | Grant Input Monitoring to the launching application. Restart it. Select **Re-check** in Speak. |
| Text is transcribed but not inserted | Grant Accessibility to the launching application. Check the preview setting. Use clipboard paste on Wayland. |
| A Thread does not run | Open **Settings > Engines**. Repair the named assignment or engine. |
| Ask has no tool result | Check the selected engine, its tool support, source permission, and any held **Allow once** request. |
| You need to restore data | Read [Release and recovery](RELEASING.md), then run `holdspeak restore`. |

## See also

- [User Guide](USER_GUIDE.md): daily Desk tasks and controls.
- [The Desk](WEB_DESK.md): navigation, windows, Ask, and records.
- [Calls](calls.md): phone-number calls, the Line, and call controls.
- [Phone](phone.md): the future paired-phone client path and current fallback.
- [Interview](INTERVIEW.md): repeatable context discovery.
- [Models](MODELS.md): engines, availability, and assignments.
- [Control modes](AUTHORITY.md): approval rules and action limits.
