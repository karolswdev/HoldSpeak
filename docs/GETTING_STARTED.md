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
See [Models](MODELS.md) for setup requirements and readiness failures.

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
| Capture cannot start | Check browser and operating-system microphone permissions. Run `holdspeak doctor`. |
| Transcription fails | Read the reported backend or model error. Install the platform extra if it is missing. |
| The hotkey works but text does not appear | Check desktop permissions and the preview setting. On Wayland, try clipboard paste. |
| A Thread cannot run | Open **Settings > Models**. Repair the named assignment or engine. |
| A documented control is absent | Compare your installed version with `main`. Check the guide for that feature. |
| You need to restore data | Read [Release and recovery](RELEASING.md) before you run `holdspeak restore`. |

## See also

- [User Guide](USER_GUIDE.md): daily tasks and detailed controls.
- [Interview](INTERVIEW.md): repeatable context discovery and suggestions.
- [Models](MODELS.md): engine availability and capability assignments.
- [Control modes](AUTHORITY.md): approval rules and action limits.
