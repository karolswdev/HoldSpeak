# HoldSpeak User Guide

HoldSpeak is one local copilot with two modes, and this guide is the
day-to-day map of both:

- **Dictate:** hold a hotkey, speak, and insert useful text into the active app. With the dictation pipeline on, HoldSpeak uses project context and recent Claude/Codex state to rewrite rough speech into better prompts, and the dictation journal records every run so corrections teach it.
- **Meet:** record conversations (or import recordings and transcripts), transcribe them, and extract topics, actions, summaries, and reviewable artifacts, with meeting aftercare showing what is still open when it ends.

HoldSpeak is private by default. Audio capture, transcription, project context, and session metadata are stored locally unless you explicitly configure a cloud or OpenAI-compatible endpoint.

## Start Here

Use these guides depending on what you are setting up:

| Goal | Guide |
| --- | --- |
| Install HoldSpeak and get basic voice typing working | [Getting Started](GETTING_STARTED.md) |
| Configure the project-aware dictation pipeline | [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md) |
| Record and review meetings | [Meeting Mode Guide](MEETING_MODE_GUIDE.md) |
| Configure local/LAN dictation models | `/docs/dictation-runtime` in the local web UI |

## Product Map

| Area | What it does | Where to use it |
| --- | --- | --- |
| Voice typing | Hold a hotkey, speak, release, insert text | Any text field, editor, terminal, browser |
| Dictation pipeline | Routes and rewrites dictated text with local rules and optional LLM stages | `/dictation`, `holdspeak dictation ...` |
| Project facts | Keeps a `kb:` map in `.holdspeak/project.yaml`; exact values stamped into dictation verbatim, no LLM | `/dictation` -> Project Facts |
| Project context | Keeps repo-local `.hs/` files that guide intelligent rewrites (optional LLM stage) | `/dictation` -> Project Context |
| Automation hooks | Lets Claude Code and Codex report current cwd/session state to HoldSpeak | `/dictation` -> Hooks |
| Meeting mode | Captures microphone plus optional system audio | Dashboard, `holdspeak meeting` command |
| Meeting intelligence | Produces transcript, topics, summaries, actions, artifacts | Dashboard and `/history` |
| iPad app | Drives both modes from another device over the hub's HTTP API: dictate into the desk, read a meeting back with its artifacts and sources, approve a proposal, browse the archive | [Companions](#companions) |
| AIPI-Lite companion | Portable ESPHome device for meeting controls, status, and spoken replies to waiting Claude/Codex sessions | [AIPI-Lite Developer Workflow](AIPI_LITE_DEV_WORKFLOW.md), `/companion` |
| Runtime setup | Configures local MLX, llama.cpp, or OpenAI-compatible endpoints | `/dictation` -> Runtime, `/docs/dictation-runtime` |

## Workflow At A Glance

| Speak | Review | Refine |
| --- | --- | --- |
| ![Pixel art microphone with hold-to-talk waves](assets/pixellab/hold-to-talk-microphone.png) | ![Pixel art meeting notebook with action items](assets/pixellab/meeting-intelligence-notebook.png) | ![Pixel art code editor connected to local context](assets/pixellab/project-aware-typing.png) |
| Hold the configured hotkey and dictate into the focused app. | Capture meetings, search transcripts, and curate action items. | Let project context and Coder session state improve dictated prompts. |

<p align="center">
  <img src="assets/pixellab/operator-working-loop.gif" alt="Animated pixel art operator working at a terminal while companion and task cards update" width="280">
</p>

## Install And Start

Install from this checkout:

```bash
uv pip install -e .
```

Run diagnostics:

```bash
holdspeak doctor
```

Start the local web runtime:

```bash
holdspeak
```

By default, the web server binds to loopback only (`127.0.0.1`). The browser UI is the primary cockpit for meetings, history, dictation setup, runtime setup, and project context.

## Voice Typing

Use voice typing when you want direct text insertion into the active app.

1. Start HoldSpeak with `holdspeak`.
2. Focus the target text field.
3. Hold the configured hotkey.
4. Speak.
5. Release the hotkey.

Default hotkey:

- macOS: Right Option
- Linux: Right Alt

If global hotkeys or synthetic typing are blocked, especially on Wayland, keep HoldSpeak focused and use the focused hold-to-talk fallback.

### Speak your language

Whisper, the transcription engine, speaks about 99 languages, and the
**spoken language setting** (Settings, Voice typing, Spoken language)
decides how HoldSpeak uses that. The default, Auto-detect, lets Whisper
identify the language per utterance, which works well for longer speech.
Short utterances are where it can stumble: a few words in one language
can be detected as a neighboring one. If that happens to you, pin your
language and transcription stops guessing.

One setting covers everything that transcribes: dictation, live
meetings, and imported recordings all share the same engine, so they all
follow it.

### The wake word

Hold-to-talk needs a key; **the wake word** needs nothing but your voice.
Say the wake phrase (the pretrained model listens for "hey jarvis") and
HoldSpeak enters **the armed window**: a short, visible countdown during
which your next sentence is captured and run through the normal dictation
pipeline. Everything happens on your machine; the only network moment in
the whole feature is a one-time download of the detection models (about
7 MB) when you first enable it.

It is off by default, and what happens after it hears you is the safety
decision the feature is built around:

- **Preview first (the default).** Nothing is typed. The result appears as

(Separately from the wake word, `dictation.preview_before_type` in
Settings, Voice, applies the same card to every hold-key dictation;
that one is off by default.)
  a card with the transcript, the pipeline output, and a **Type it**
  button. Typing happens only when you press it, and the server types only
  the exact previewed text. Dismissing the card is always safe.
- **Type immediately (an explicit opt-in).** Your call to make, with the
  consequence stated where you make it: a false detection would type into
  whatever app is focused.

Turn it on under **Settings, Voice typing, Wake word**, and turn on
desktop presence with it: the presence surface (and Qlippy's dock, if he
is on) shows the armed state while you work in other apps. The wake word
pauses automatically whenever something else holds the microphone (a
hold-to-talk dictation, a meeting) and resumes after.

**The honest numbers.** Measured on synthesized speech across three
voices: ordinary sentences, including adversarial near-misses like "hey
travis" and "play jazz", produced **zero false detections in 57
utterances** at the default threshold. But a sentence that contains the
wake phrase or a near-homophone ("hey jarred…") can score
indistinguishably from the real thing; no threshold can separate them.
That is inherent to wake-word detection, and it is exactly why the
preview default exists: when it happens, the cost is a glance at a card,
never text in your document. Real rooms (noise, distance, accents) differ
from synthesized speech in both directions; the detection threshold is a
settings knob for that reason.

### Punctuation

Say punctuation words and HoldSpeak converts them:

| Say | Inserts |
| --- | --- |
| `period` or `full stop` | `.` |
| `comma` | `,` |
| `question mark` | `?` |
| `exclamation mark` | `!` |
| `colon` | `:` |
| `semicolon` | `;` |
| `new line` | line break |
| `new paragraph` | blank line |

These are the built-ins. **The spoken-symbol dictionary** adds your own:
open **Settings, Voice typing, Spoken-symbol dictionary** and map any
spoken phrase to any symbol or snippet ("tilde" to `~`, "arrow" to `→`,
"double colon" to `::`). Your entries win over the built-ins if the
phrases collide. Each entry has an attach mode that controls spacing:
`none` keeps the spacing you spoke, `left` glues the symbol to the
previous word (like `period` does), `right` to the next word, and `both`
to both sides (so "std double colon vector" with `both` types
`std::vector`).

Example:

```text
hello comma can you review this question mark
```

becomes:

```text
Hello, can you review this?
```

### Clipboard Token

Say `clipboard` anywhere in a dictated phrase to insert the current clipboard
text at that position. HoldSpeak treats `clipboard` as a replacement token, so
the word itself is removed and the actual clipboard contents are inserted into
the output that gets typed or pasted.

Example:

```text
Taking a look at this clipboard could you refactor it?
```

If the clipboard contains:

```python
def total(items):
    return sum(items)
```

HoldSpeak inserts:

```text
Taking a look at this
def total(items):
    return sum(items)
could you refactor it?
```

## The Dictation Pipeline For Coding Assistants

HoldSpeak can do more than transcription. With the dictation pipeline enabled, it can transform a rough spoken thought into a useful prompt for Claude, Codex, a terminal, a browser, or another target.

Use this for:

- Rewording spoken notes into clear prompts.
- Injecting repo-specific project context.
- Preserving project vocabulary and preferred spellings.
- Detecting that Claude/Codex is waiting for an answer and shaping your spoken reply accordingly.

### Enable The Dictation Pipeline

Open:

```text
/dictation -> Runtime
```

Enable:

- `Enable dictation pipeline`
- Optional: `Enable project-aware rewrite stage (.hs/)`
- Optional: set `Target profile override` when active-window detection is wrong.

Pick a runtime backend:

- `auto`: prefers MLX on Apple Silicon, otherwise llama.cpp.
- `mlx`: local Apple Silicon MLX model.
- `llama_cpp`: local GGUF model.
- `openai_compatible`: local or hosted `/v1/chat/completions` endpoint.

You can also validate from the CLI:

```bash
holdspeak dictation runtime status
holdspeak dictation dry-run "ask codex to inspect the failing test"
```

For a full step-by-step setup, see [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md).

### OpenAI-Compatible Endpoints

Use `openai_compatible` when the model is served somewhere else:

- LM Studio
- Ollama OpenAI bridge
- vLLM
- llama.cpp server
- LiteLLM
- OpenAI or another hosted compatible API

The picker path: author the endpoint once as a Runs on destination (the Web
compatibility route is `/profiles`), then pick it under Dictation → Runtime →
**Runs on**. The configuration shape below still works when no destination is
selected:

```json
{
  "dictation": {
    "pipeline": { "enabled": true },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "http://127.0.0.1:8000/v1",
      "openai_compatible_model": "qwen2.5-7b-instruct",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 8
    }
  }
}
```

Known-good endpoint families include llama.cpp server, LM Studio, Ollama's OpenAI bridge, vLLM, LiteLLM, and hosted OpenAI-compatible APIs. HoldSpeak reads the API key from the named environment variable. It does not store the key in the project context files. If the endpoint is unavailable, times out, or returns malformed output, HoldSpeak preserves the original transcript and surfaces the failure in dry-run/readiness output.

## Project Context

Project context is stored in a `.hs/` directory at the repo root. These files are meant to be simple, readable, and safe to commit if your team agrees.

```text
.hs/
  instructions.md
  context.md
  memory.md
  workflows.md
  issues.md
  terms.md
  targets.md
  ignore
```

Recommended use:

| File | Purpose |
| --- | --- |
| `instructions.md` | How HoldSpeak should rewrite or inject prompts for this repo |
| `context.md` | Architecture, important paths, setup notes, constraints |
| `memory.md` | Durable user-approved facts |
| `workflows.md` | Test, build, review, and deploy commands |
| `issues.md` | Current scratchpad for active problems |
| `terms.md` | Project vocabulary and preferred spellings |
| `targets.md` | Style notes for Codex, Claude, terminal, browser, editor, chat |
| `ignore` | Paths, topics, or data HoldSpeak should not inject |

Edit these from:

```text
/dictation -> Project Context
```

Write policy:

- `.hs/` files are the canonical format and are editable from the web UI after you choose to save.
- Flat files such as `.hs_context`, `.hs_issues`, `.hs_memory`, `.hs_instructions`, `.hs_workflows`, `.hs_terms`, `.hs_targets`, and `.hs_ignore` are read-only compatibility inputs.
- If both exist, `.hs/<name>.md` wins over the matching flat file.
- HoldSpeak never writes project context automatically during dictation.
- Binary files, very large files, and files with obvious secret-looking content are skipped with warnings instead of being injected.

Start small. A useful first version is:

```text
# .hs/instructions.md
When dictating into Codex or Claude, rewrite rough speech into a concise engineering request. Preserve explicit filenames, commands, and test names.

# .hs/context.md
This is a Python application with a local FastAPI web UI and one typed
Vite/React frontend.

# .hs/workflows.md
Run focused tests with `.venv/bin/python -m pytest <path>`.

# .hs/targets.md
Codex: concise implementation request.
Claude: product/design discussion is acceptable, but include concrete repo context.
Terminal: preserve command syntax exactly.
```

## Automation Hooks For Claude And Codex

Operating systems do not reliably expose the current working directory of a terminal app. Automation hooks let Claude Code or Codex report their own `cwd`, session id, transcript path, and tool state to HoldSpeak.

For the full install and verification flow, see
[Claude/Codex automation hook install](AGENT_HOOK_INSTALL.md).

Open:

```text
/dictation -> Hooks
```

The tab shows:

- Recent Claude/Codex hook status.
- Local registry path.
- Copy-ready hook templates.
- A toggle for assistant-message capture.

You can also generate templates from the CLI:

```bash
holdspeak agent-hook templates --agent claude
holdspeak agent-hook templates --agent codex
```

With assistant-message capture:

```bash
holdspeak agent-hook templates --agent claude --capture-messages
holdspeak agent-hook templates --agent codex --capture-messages
```

Assistant-message capture is opt-in. When enabled, HoldSpeak stores at most 4 KB of the latest assistant message from a Stop hook, marks likely questions as `awaiting_response`, and clears that captured text on the next submitted user prompt. The `/dictation` page shows a banner when Claude or Codex appears to be waiting for your reply.

Use **Clear** on the banner to remove the captured assistant text manually.

## Meeting Mode

Use meeting mode when you want a searchable, reviewable record of a conversation.

Before a first meeting:

```bash
holdspeak meeting --setup
holdspeak meeting --list-devices
```

Start HoldSpeak:

```bash
holdspeak
```

Use the web dashboard to start and stop meetings. During a meeting, HoldSpeak can show:

- Live transcript.
- Speaker labels.
- Bookmarks.
- Topics.
- Action items.
- Summaries.
- Intelligence queue status.

After a meeting, open:

```text
/history
```

Use History to search meetings, review action items, edit accepted actions, inspect generated artifacts, and export local handoff files.

## Meeting Intelligence

Meeting intelligence can run locally or through a configured OpenAI-compatible endpoint.

Local-first behavior:

- Transcripts are stored locally.
- Meeting artifacts are stored locally.
- Deferred queues are stored locally.
- External systems are not written unless a connector or export workflow explicitly does it.

Cloud or homelab behavior:

- If you set `meeting.intel_provider` to `cloud` or configure `intel_cloud_base_url`, meeting text may be sent to that endpoint for analysis.
- The picker path: author the endpoint once as a Runs on destination (the Web compatibility route is `/profiles`), then pick it under Settings → **Runs on**.
- Use `holdspeak doctor` from the same shell environment to verify endpoint, model, TLS, DNS, and authentication; its Runs on line names the destination each pipeline resolves to.

Example cloud/homelab config (the fallback shape when no Runs on destination is picked):

```json
{
  "meeting": {
    "intel_provider": "cloud",
    "intel_cloud_model": "qwen2.5-32b-instruct",
    "intel_cloud_api_key_env": "HOMELAB_INTEL_API_KEY",
    "intel_cloud_base_url": "http://homelab.local:8000/v1",
    "intel_deferred_enabled": true
  }
}
```

## Companions

HoldSpeak runs as a desktop hub. A companion on another device drives it over
the same local HTTP API your browser uses, on your own network (LAN or
Tailscale), with no hosted relay. Every request carries the hub's bearer token,
exactly as the browser does when the runtime is bound off loopback.

### The iPad app

The iPad is a client of both modes, not a remote control for one. It reaches the
hub through typed clients over the existing API, so the work happens on the desk
and the iPad shows it:

- **Dictate into your desk.** Speak an answer on the iPad and the hub runs that
  text through the full dictation pipeline (your corrections, your blocks, your
  routing) and types the result into the focused app or answers a waiting
  Claude/Codex session. A configured voice command fires on this remote path
  too, the same bounded action it would fire at the desk, so a keyword is not
  dictated as prose. The spoken language setting and the spoken-symbol
  dictionary apply on this path, the same as local dictation.
- **Read a meeting back in full.** Pull a meeting's artifacts with their
  confidence scores and the transcript sources each was grounded in, browse the
  archive narrowed server-side by speaker, tag, or text (the same facets as
  `/history`), and read its aftercare: what is open, decided, and changed.
- **Approve, separately.** Proposing an action and approving it stay two steps,
  the same human gate the desktop keeps. The iPad reads the proposals queued for
  review and decides them one at a time; nothing runs without that approval.
- **See what is grounded.** Activity pre-briefing nudges, source-cited, come
  through to the iPad so you can pick a record to ground the next dictation in.

The iPad's own storage is schema safe the way the desktop is: it backs an older
database up before migrating it, and refuses to open one written by a newer
build rather than risk your data. The on-device screens for these are still
coming together; the client layer they ride on is shipped and tested.

### AIPI-Lite

AIPI-Lite is an optional portable device for meeting controls, status feedback,
and spoken replies to a waiting Claude/Codex session. Firmware and bridge setup
are in the [AIPI-Lite Developer Workflow](AIPI_LITE_DEV_WORKFLOW.md).

## Mission Control On The Desk

If you plan work with [Delivery Workbench](https://github.com/karolswdev/delivery-workbench),
the desk renders your repositories as a conveyor: one belt per project, phases
as segments, the current phase's stories riding it, and live Coder sessions
pinned to the story they are working. Name your repositories in
`~/.holdspeak/delivery_workbench.json` and the belt appears at the foot of the
desk.

Everything on the belt is read from receipts. Roadmap state comes from each
repository's own `dw` command line, pull requests and their check results from
your own authenticated `gh`, and the event ticker from the repository's rail
log, with commit-gate refusals shown first and carrying the refused rule
verbatim. A story chip's evidence tick opens the evidence file right there on
the desk. When a repository cannot answer, its lane says so plainly instead of
pretending an empty belt.

The belt itself never writes. The one way to act from it is the story-flip
proposal, which rides the same propose, approve, execute flow as every other
action on the desk, and the repository's own commit gate keeps the final say.

## Steer A Session From The Desk

Watching is free; every steer resolves authority and is audited. Local steering
does not leave your machine.

Click any session pin on the belt, or the "Watch live" chip in a coder card,
and the session pull-out opens with a live view of that Coder session's terminal pane.
The view is read only: it updates on its own, marks itself stale when the
session has gone quiet, and never sends a keystroke.

The pull-out names the exact pane and the Control posture used for steering. In
Secure, click **Arm pane** for a five-minute exact-pane grant. In Normal, the
same deliberate action grants fifteen minutes. The chip becomes a countdown;
one click disarms it. In YOLO, an eligible registered session reads **YOLO ·
direct** and needs no HoldSpeak arm prompt for text or allowed keys. It does not
gain arbitrary terminal authority: the pane identity captured by the live view
rides every delivery, and the hub re-checks that identity immediately before a
keystroke. A missing or replaced pane refuses, so a reply meant for one session
cannot land in another. Changing posture or restarting the hub clears existing
pane grants.

Once the exact grant or YOLO posture is ready, the composer appears. Speak your
reply by holding the mic, or type it. The paper-plane toggle chooses whether a
return is pressed after the text lands, so a multi-part steer can stay in the
Coder session's input box. Send, and the reply lands in the pane exactly as you
composed it.

You can carry desk objects into a steer. Open the grounding picker in the
composer, choose a meeting or an artifact, and its content rides in ahead of
your message under a labeled header, capped so it fits what the Coder session can read
in one go. The composer shows the exact text before it sends, and refuses at
compose time if the context is too large, naming the size.

Triage what a session surfaces, three ways, all from the pull-out. Keep the
Coder session's current question as a Desk Note, its lineage naming the session and the
moment. Pin an off-rails session to a story yourself, a manual mark the belt
shows with a hollow ring so it never reads as the rails' own verdict. Or flip a
correlated story's status through the same proposal the belt uses, the commit
gate keeping the final say.

Every reply and every refusal is written to the steering audit: who, when, which
session and pane, the exact operation-policy snapshot, and a bounded text
fingerprint. The result also appears as a Receipt on the Coder session. Read the
source audit with `GET /api/coders/steering/audit`.

### Take Over A Session: Any Key, Any Pane, Any Machine

Steering is not only typing text. Under the same resolved authority you can send
real keys: interrupt a runaway with `C-c`, dismiss a prompt with `Escape`, or
drive a menu with the arrows and `Enter`. Keys go through the same one path and
the same audit as a text reply, so the trail reads like what you did: `C-c`,
`Down Down Enter`. A key that is not a real terminal key is refused by name and
never sent (`POST /api/coders/{key}/keys`).

The session does not have to be one HoldSpeak already knows. Every tmux pane on
the machine is listed at `GET /api/coders/steering/panes`, including a shell you
opened by hand. Watch any of them free. Secure and Normal ask you to arm its
exact pane id (`pane:%N`); YOLO can use that exact selection directly. Either
path re-verifies the canonical pane before delivery, so a pane you attach to by
hand has the same identity protection as a tracked session.

And the machine does not have to be this one. With a node configured
(`HOLDSPEAK_STEER_NODES`), the desk relays a watch, an arm, a steer, or a key
sequence to that node, which runs it against its own terminal. The machine that
types owns the authority decision and audit: the far node resolves its own
Control posture or grant, re-checks the expected pane, and records the attempt.
The relay only carries the command and expected identity. A node that does not
answer refuses by name, at once, rather than leaving you waiting.

The rule never changes as the reach grows: watching is free; Secure and Normal
use a bounded exact-pane grant; eligible YOLO steering uses the registered pane
and posture without another prompt; the pane is re-checked before every key; a
recycled pane refuses; and every attempt leaves a Receipt. YOLO removes the
HoldSpeak prompt, not the destination, identity, payload, or key checks.

You do all of this from the desk, not a terminal. Open the Panes list at the
bottom of the desk to see every tmux pane on the machine, and attach to any one.
When authority is ready, a row of keys appears next to the composer: one tap
sends `^C` to stop a runaway, or the arrows and `Enter` to drive a menu. A chip
in the header shows which machine you are steering, this Mac or a paired node.

The desk can also make and end sessions. The Panes list has a field to spawn a
new session by name (the name is checked, so it can never carry a stray command).
The Desk keeps Rename and Kill in a separate session-control window even when
YOLO can steer directly. Kill requires that arm and asks you to confirm, because
ending a session cannot be undone; Rename retains its strict name/argument
validation while its full policy classification remains open. Spawn, steer,
rename, and kill each leave their own line in the audit.

## Ground A Run On The Rails

If you plan work with Delivery Workbench, the rails themselves become
material you can hand to any run. In the grounding picker, beside your
meetings, is a rails group listing the belt's live projects: the
roadmap, the current phase, and its stories. Pick one and its content
rides into your ask or your steer, capped and labeled with where it
came from.

What rides in is a receipt, not a guess. The hub reads the exact file
the `dw` command line names for that story or phase, and hands the run
that file's text. It never reads a status out of the document, so a
grounded story is always the real thing on disk. A reference the hub
cannot resolve is refused by name rather than filled in.

## The Rails Journal

You can also let a local model keep a running note of what the rails
do. Turn the ambient observer on in your configuration (it is off by
default) and name the model you want it to use. From then on it watches
your pipeline's own event stream (story flips, commit-gate passes and
refusals, evidence captures, phase closes) and writes a short journal
entry for each batch of new activity. The entries are ordinary desk
notes: you can open them, file them, and ground a later run on them.

The observer only reads and writes its journal. It never touches the
rails; if you want to act on something it noticed, you use the same
story-flip proposal every other desk action uses, and your commit gate
keeps the final say. When the model is unreachable, the entry records
the events plainly and says the summary was unavailable, rather than
inventing one. Read the journal back with
`GET /api/missioncontrol/rails/journal`. Nothing here leaves your
machine: the observer reads your own `dw` and runs your own model.

## Privacy Model

HoldSpeak is designed to be local-first.

Local by default:

- Audio capture.
- Whisper transcription.
- Meeting history.
- Dictation block configuration.
- `.hs/` project context.
- Coder session registry.
- Captured assistant-message snippets, if enabled.

Leaves the machine only when configured:

- Cloud meeting intelligence.
- OpenAI-compatible dictation runtime hosted outside localhost.
- Connector integrations.
- Manual exports or uploads.

Sensitive files:

- Do not place secrets in `.hs/`.
- Use `.hs/ignore` to document paths and topics that should not be injected.
- Prefer environment variables for API keys.

## Troubleshooting

Run diagnostics first:

```bash
holdspeak doctor
```

Common issues:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Hotkey does not trigger | OS global hook restriction | Use focused hold-to-talk fallback or check permissions |
| Text does not paste/type | Synthetic typing blocked | Use clipboard/manual paste fallback |
| System audio missing | No BlackHole/Pulse monitor configured | Run `holdspeak meeting --setup` |
| Dictation LLM unavailable | Missing optional backend or model | Open `/dictation` -> Readiness or Runtime |
| Project context not detected | Wrong cwd or no project marker | Set Project root in `/dictation` |
| Claude/Codex context missing | Hooks not installed or not firing | Open `/dictation` -> Hooks |
| Captured Coder session question looks stale | Last prompt did not clear it | Use Clear on the Coder session banner |

## Recommended First Setup

1. Run `holdspeak doctor`.
2. Start `holdspeak`.
3. Open `/dictation`.
4. Set the Project root for your active repo.
5. Create `.hs/instructions.md`, `.hs/context.md`, `.hs/workflows.md`, and `.hs/targets.md`.
6. Open Hooks and copy the Claude/Codex templates you use.
7. Enable the dictation pipeline and run a dry-run.
8. Start using voice typing in your editor or LLM CLI.

## See also

- [README](../README.md): install, platform notes, configuration reference.
- [Getting Started](GETTING_STARTED.md): first-run setup and basic voice typing.
- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md): dictation pipeline, project context, output-target override, OpenAI-compatible endpoints, and automation hooks.
- [Dictation runtime setup](../web/src/pages/RuntimeDocsPage.tsx): source for the local Web runtime setup page.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): meeting-specific setup and troubleshooting.
- [Firefox Extension Guide](FIREFOX_EXTENSION_GUIDE.md): local companion extension install.
