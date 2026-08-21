# HoldSpeak

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/holdspeak-mark.png" alt="HoldSpeak logo, a held key with rising soundwaves" width="120">
</p>

<p align="center"><strong>A local-first voice desk: dictate a thought, edit it, then copy it or keep it. HoldSpeak keeps work on this device unless you configure a destination; its boundary badge names any configured egress.</strong></p>

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/karolswdev/HoldSpeak/blob/main/LICENSE)
[![Tests](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml/badge.svg)](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#platform-support)

HoldSpeak starts with one short loop: launch `holdspeak`, choose **Dictate one
sentence**, edit the text, then **Copy** it or **Keep as Note**. Your first
completion furnishes the Desk automatically with Inbox, Personal, Work,
Meetings, Decisions, and Reference; a Start here note; and editable prompts in
**Everyday context**. Its shipped default is unused: explicitly attach it for
one Thought, or explicitly make an attached set the default for future local
Thoughts. No extra setup is required before this first value.

After that, HoldSpeak can type into another app or keep work on the Desk as
notes, meetings, decisions, and artifacts. Transcription runs on this machine.
Optional model-backed features use a destination you configure under Settings,
Models; the badge in the corner names what can leave this machine and where it
goes.

A meeting should change what happens next, not disappear into an archive.
HoldSpeak keeps decisions as durable records with transcript moments, lets you
accept or supersede them, and promotes the ones that stand into ADRs, notes, or
decision announcements. Project Memory finds the text years later across the
local material you kept, while Ask this project answers from cited sources and
states how many matches fit its prompt. The read-only Process window shows what
the kernel journal says is running, waiting, unknown, or finished without
controlling the work.

**Every model attempt has one door and one receipt.** Ask, Agents, Sequences,
Workflows, Workbenches, scheduled work, meetings, dictation, wake capture, local
Whisper, endpoints, and mesh workers all enter the admitted `InferenceRunner`
path at the executing boundary. A multi-step run or live session may be the
parent, but each real provider attempt is its own child. It binds the exact frozen
deployment revision and receives one immutable terminal receipt. Cancellation
rejects late output; fallback and retry attempts get separate receipts; uncertain execution stays `indeterminate` instead of being
reported as success. Prompts, transcripts, audio, completions, and token streams
are not copied into the kernel journal. The complete integrator contract is
[Inference admission: one path, one receipt per attempt](docs/ARCHITECTURE.md#inference-admission-one-path-one-receipt-per-attempt).

> **Status: 0.x, early but real.** HoldSpeak is on PyPI (`pip install holdspeak`).
> The features are mature; APIs, config, and defaults can still change while it is
> pre-1.0. Upgrades are safe by default (your data is backed up first). Feedback
> and contributions welcome.

## The two modes

| Dictate | Meet |
| --- | --- |
| ![Pixel art microphone with hold-to-talk waves](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/hold-to-talk-microphone.png) | ![Pixel art meeting notebook with action items](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/meeting-intelligence-notebook.png) |
| Hold the hotkey, speak, release: the text goes into the active app. The dictation pipeline is on: configure a model-backed rewrite to route rough speech by intent, enrich it with your project's context, and shape it for its target (Codex, Claude, the terminal, the browser, your editor). Every run lands in the dictation journal; one tap on a wrong result teaches the correction memory. Voice commands map a spoken keyword to a real action (open a URL, launch an app, run a command). Say the wake phrase and it listens hands-free, with the result previewed, never typed, until you confirm; an optional preview mode does the same for every dictation (the card shows the text first, Type it commits, Discard drops it). The spoken language setting pins any of Whisper's 99 languages, and the spoken-symbol dictionary types your own vocabulary ("double colon" becomes `::`). Activity pre-briefing offers what you touched recently as dictation context, source-cited. | Capture mic and system audio live with speaker labels, or import a recording or a transcript file you already have (vtt and srt keep their real timestamps and speaker names). 14 built-in plugins submit admitted model attempts to pull typed artifacts out of the transcript: decisions, action items, ADRs, risk registers, incident timelines. Meeting aftercare then shows what is open, decided, and changed since last time; an accepted action can become a filed issue, and the digest or follow-up draft can go to your team through Send to Slack. Fresh installs use YOLO: eligible configured actions execute with a receipt. Secure and Normal retain per-action approval. The archive is searchable and filterable by date, speaker, tag, and open actions. |

This is what they look like in the product, not in pixel art. A saved meeting
comes back as typed, reviewable artifacts:

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/history.png" alt="A saved meeting open at /history: the transcript on the left, and on the right a stack of artifact cards (a Risk register table with impact, likelihood, mitigation, and owner; Decisions and open questions; typed Requirements), each with a confidence score and a copy button." width="760">
</p>
<p align="center"><em>A meeting after intelligence ran: a risk register, decisions, and requirements, each extracted by an LLM-backed plugin and rendered read-only at /history.</em></p>

## The Desk

Launch `holdspeak` and the browser opens on the Desk: everything the two
modes produce, living as objects in one spatial world. Meetings, notes,
Knowledge, Agents, and their Artifacts appear on the Desk as working
icons that carry their state (member counts, freshness, needs-you);
Zones are drawers that open into remembering windows; drop an object
onto an Agent or a Knowledge crystal and the named verb under the
cursor says exactly what release does; right-click anything for Info.
Click selects, double-click opens.

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/desk.png" alt="The HoldSpeak Desk: pixel-art objects (meetings as cassettes, notes, a Knowledge plant, an Artifact page) floating on a warm dark stage; a Q3 release Zone tray holding one filed Meeting; Coder session avatars on a right-edge rail; a record orb bottom-center; a compact HoldSpeak menu and an egress badge top-left." width="760">
</p>
<p align="center"><em>The front door: the world your voice work lives in. The orb records, the rail asks, the tray files.</em></p>

**The Chair is home after first value.** The browser opens on the Chair: four fixed lanes
(Brief, Follow-Through, Meetings, Agents) showing what needs you at a
glance, and a capture hero at the center. Tap the hero to record a meeting
(one tap, same verb as the dock orb). Say "start meeting" into its mic and
recording starts by voice. Ask AI is one tap away from the hero. Each lane
header opens its full surface in a window; every action opens a window, never
a page transition. The **Floor** button in the dock swaps to the spatial
floor (the object world below) and back. A toggle in Settings, Sounds & Presence
controls **Desk Sounds**, the six mechanical click sounds the Chair plays on
key presses, window opens, and landings.

The Desk is where the loops close. Press the orb and the hub records a
meeting; when it ends, the meeting lands on the stage as an object. Rope a
few objects together with the lasso and **Ask AI** about exactly that pile:
the answer prints as a card you keep or bin, and a kept card records every
object it read plus your instruction. The boundary badge names This device,
a paired device, a private endpoint, or an external service. See
[The Desk](https://github.com/karolswdev/HoldSpeak/blob/main/docs/WEB_DESK.md).

**Ground this ask.** The composer carries an attach control: pick meetings,
expand each one to its digest, its transcript, or any artifact it produced,
and the gauge measures the selection against the model's window before you
run. The question is answered from those records (the hub reads them from
its own store), the kept card names them, and an unknown reference refuses
with its id instead of guessing.

**Develop the thought without hiding the context.** Any kept or ordinary Note
can become one resumable Thought while its original bytes remain preserved.
It opens as a real Thought Workbench: a full document plane with a compact
Markdown formatting rail beside a focused AI interview on desktop, and
Note/Interview panes on a phone. **Ask AI**
starts one explicit refinement turn. **Add & ask next** atomically adds the
answer to the Note and authorizes exactly one next turn; **Add to Note** stops
there. **Finish Thought** is always direct. The Workbench names where each turn
will run and shows the actual placement receipt when it returns.
Without a runnable model, **Set up AI** opens the exact Models settings surface;
the Workbench rechecks readiness after configuration instead of leaving a dead
AI button.

Context begins empty. The Attach control puts pinned Everyday context first,
with recent/search and the full Note catalog progressively disclosed. The hub
resolves qualified refs and freezes exact Note versions; the browser never
posts copied context. A stale source is named and must be updated or removed
before another turn. Opening, editing, attaching, or reading Original never
starts AI by itself.

If you want that same context on future work, open **Attach context** and choose
**Use these by default** for the complete set attached to this Thought. The
default is empty until you do. It applies only to Thoughts created or adopted
later on this hub; it never changes an existing Thought, syncs to another hub,
or starts a model turn. **Remove from this Thought** changes only the open
Thought. **Stop using by default** clears the future set without detaching
anything already attached. If one configured source is unavailable at birth,
the Thought still opens with no AI context and a receipt names why the whole set
was skipped.

**Talk to your Agents.** Tap an avatar on the rail and it opens a
conversation, not a one-shot prompt: turns accumulate, the thread survives a
reload, each reply wears the badge for where that turn actually ran, and any
reply can be kept on the Desk as an Artifact. The attach control rides the
chat composer too, so a conversation can be grounded on the meetings it is
about.

**Open a model.** The rail also lists every model the hub can run: its own
engine and each Runs on destination's model. One tap opens a chat pinned to that model,
through the same conversation surface, grounding included.

**The gate: your agent asks first.** Off by default, and armed only by two
deliberate steps of yours, a Claude Code session's risky Bash call can stop
and ask the Desk before it runs: the held call rises in the shade with a
redacted preview, Approve lets it run, and Deny sends your one-line reason
back to the agent verbatim. Armed, the gate fails closed: an unreachable hub
means a denied call, never a silent pass. The work your sessions ship shows
up beside them as receipts too: registered repositories' pull requests as
honest rows (state, CI conclusion, when observed, and how the match was made),
and a one-line session receipt whose every number states its provenance.

**Follow a pull request without leaving the Desk.** Send a Coder session into
the matched worktree, keep a model-written review as an Artifact, or prepare a
GitHub comment whose complete text waits for your approval. The pull request
row shows the result as a Receipt, while merge, close, and force push stay out
of reach by design.

## Data boundaries

- **Every run names its destination.** Transcription and model-backed work can
  run on this device, a paired device, a private endpoint, or an external
  OpenAI-compatible service.
  Author them once under **Settings, Models** as reusable destinations, then
  assign one per feature with the Runs on pickers, and one per Agent where you
  author it. The destination definition syncs across your surfaces while its
  key stays local: set, replace, or remove it inline in **Settings, Models**.
  A destination can name another of your machines: run
  `holdspeak mesh serve` there and every run against that destination executes on
  that node, with its own model and keys.
  See [Security & privacy](https://github.com/karolswdev/HoldSpeak/blob/main/docs/SECURITY.md) and [Models](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MODELS.md).
- **It learns how you work, and shows you the receipts.** The dictation
  journal records what you said, what it typed, where it routed, and how long
  it took. Fix a wrong result in one tap and the correction memory learns; the
  learning digest reports a real "learned from N similar" count, honest at
  zero; replay an old utterance through the updated pipeline and watch the
  routing change. See [the learning loop](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_PIPELINE_GUIDE.md#12-dictation-journal-corrections--replay).
- **Meetings end with their loops closed.** A meeting produces artifacts,
  an aftercare digest, and receipted actions where most tools stop at a
  transcript. Fresh installs use YOLO with actuators enabled and a wildcard
  allowlist: eligible actions to configured destinations execute immediately.
  Secure and Normal retain per-action approval. Every execution remains bound
  to its configured destination and recorded as a receipt. See
  [meeting intelligence](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md).
- **Honest by construction.** `holdspeak doctor` reports what is actually
  broken. The import panel says which timestamps are approximate. The learning
  digest never inflates a count. Upgrades back your database up before
  touching it and refuse to open data written by a newer build. The docs hold
  themselves to the same bar.

## See it learn

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/operator-working-loop.gif" alt="Animated pixel art operator working at a terminal while companion and task cards update" width="280">
</p>

Because every dictation is recorded, you can look back at what it heard, fix
a mistake in one tap (which teaches it), and replay the utterance through the
updated pipeline. Instead of trusting that it improved, you watch it happen.
[See the full walkthrough](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_COPILOT.md).

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/journal.png" alt="The HoldSpeak dictation journal: a said-to-typed timeline of recent dictations, each card showing the spoken transcript, the typed result, its routing target, and a per-utterance latency strip; one row marked corrected." width="760">
</p>
<p align="center"><em>The dictation journal. Every utterance, with what you said, what it typed, where it routed, and how long it took.</em></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/learning-digest-week.png" alt="The 'What HoldSpeak learned' digest: a this-week / all-time toggle, headline counts for corrections made, dictations corrected, and utterances nudged, a breakdown by block and target, and per-correction 'learned from N similar' rows." width="760">
</p>
<p align="center"><em>The learning digest. Honest, windowed counts from the same matcher that nudges your routing.</em></p>

## Meet Qlippy

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/presence/qlippy-avatar.png" alt="Qlippy, HoldSpeak's pixel-art paperclip mascot: an orange paperclip with big expressive eyes and skeptical eyebrows." width="160">
</p>

Yes, he is a paperclip. The famous one had two problems: he interrupted you,
and he could not actually do anything. Qlippy is the apology for both. He
lives on the desktop presence surface (opt-in, two switches deep), spends
most of his time as a tiny animated dock sprite mirroring what the runtime is
doing, and slides out a card only for the few moments that genuinely need
you: an action awaiting your approval, a correction that actually reached
past dictations, a meeting that ended with open items.

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/presence/qlippy-native-overlay.png" alt="The native Linux overlay on a real desktop: Qlippy in an alert pose beside the headline 'A decision needs you', the exact preview of a proposed GitHub issue, the egress badge naming the destination, and Approve and Decline buttons, floating over a browser window." width="420">
</p>
<p align="center"><em>The marquee moment, on a real desktop: a proposed GitHub issue waiting for a decision. The native panel takes pointer clicks only while a card shows and can never steal keyboard focus.</em></p>

**He never acts on his own.** Approving on his card sends the identical
audited request the dashboard sends. Every card carries the egress badge,
one small pill that says at a glance whether its data stays local or goes
out, and to where. Dismissing him is always safe, and he is honest to a
fault: the "Learned from you" card only ever appears when a correction
really reached past dictations, with the real count.

| A decision needs you | Learned from you |
| --- | --- |
| ![Qlippy's decision card: the alert-pose mascot, the exact preview of a proposed GitHub issue, the egress badge naming the destination, and Approve and Decline buttons.](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/presence/qlippy-decision-card.png) | ![Qlippy's learned card: the mascot with a lightbulb, reporting that a correction was applied and matches 2 past dictations, with its local badge and a View digest button.](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/presence/qlippy-learned-card.png) |
| The exact preview, the destination on the badge, your call. | Only when a correction really reached past dictations, with the honest count. Local only. |

Off by default, like everything ambient here. Turn him on under
**Settings, Desktop presence, "Qlippy, the mascot"**.

## How it compares (as of mid-2026)

Honest comparisons, architecture-level on purpose: where your audio goes,
what the tool spans, and whether it learns. These tools are good at what
they do; pick the one that fits.

| Tool | What it does better | What HoldSpeak does better |
|---|---|---|
| **OS dictation** (Apple Dictation, Windows Voice Typing) | Zero setup, free, always available | Your own models, LLM rewriting with project context, the learning loop, meetings |
| **Local Whisper apps** (superwhisper, MacWhisper, VoiceInk) | Simpler setup, polished single-purpose UX | The LLM stays local too (their AI modes often call cloud APIs), a visible learning loop, meeting intelligence, Linux support |
| **AI dictation services** (Wispr Flow, Aqua Voice) | Out-of-box accuracy and editing polish, no model management | Your voice never leaves your machine, open source, no subscription, meetings |
| **Talon** | The deepest hands-free coding and computer control there is | Prose-first dictation with LLM rewriting, lower learning curve, meeting intelligence |
| **Raw Whisper tooling** (whisper.cpp scripts) | Total control, minimal surface | A product: typing integration, routing, the journal, meetings, a web UI |

And the trade-offs in the other direction: HoldSpeak is 0.x, the smart parts
need a model you provide, setup is heavier than a menu-bar app, there is no
Windows build today, and Wayland limits global hotkeys to best effort.

## Quickstart

Install from PyPI and launch the web runtime:

```bash
pip install holdspeak
holdspeak          # launch the web runtime (the browser opens on the Desk)
```

Prefer [`uv`](https://docs.astral.sh/uv/)? `uv pip install holdspeak`.

Or use the install script (creates an isolated venv and a `holdspeak` launcher),
or work from a clone:

```bash
# one-line install
curl -fsSL https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/scripts/install.sh | bash

# or from a clone (for development)
git clone https://github.com/karolswdev/HoldSpeak.git && cd HoldSpeak
uv pip install -e .
holdspeak
```

### Your first sentence

In the browser, choose **Dictate one sentence**, edit the text, then choose
**Copy** or **Keep as Note**. That first completion furnishes your Desk
automatically. It includes six drawers: Inbox, Personal, Work, Meetings,
Decisions, and Reference; a Start here note; and five editable prompts in
**Everyday context**: About me, Current priorities, How I like help, People &
vocabulary, and Meeting preferences. The prompts contain questions and
examples, not facts about you. Everyday context is never sent to AI
automatically; attach it only when you want it used.

If microphone permission or transcription needs attention, the first-sentence
surface tells you the one recovery to take. `holdspeak doctor` is also available
when you want diagnostics for microphone permissions and backends; it is not a
first-value prerequisite.

### Later: voice typing, repairs, and deployment

For voice typing in another app, hold the global hotkey (Right Option on macOS,
Right Alt on Linux), speak, and release. The Desk's **Speak** surface also has
that action with an explicit Aim and a dry-run **Rehearse** control.

Automatic furnishing is the ordinary first-run path. For repair, `holdspeak
seed` creates only starter objects HoldSpeak has never seen, preserving your
edits and deletions. To deliberately restore the default Desk, use the
destructive, confirmed **Settings, Desk → Reset to seed** action. To add a
model-backed feature or deploy headlessly, configure its destination and
**Runs on** choice in **Settings, Models**; a
`HOLDSPEAK_PROFILE_<ID>_KEY` environment variable remains the headless key
fallback. See [Models (bring your own)](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MODELS.md)
and [Inference destinations](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INFERENCE_TARGETS.md).

Install only the extras you need for those later features:

```bash
pip install 'holdspeak[meeting]'          # meeting mode and AI intelligence
pip install 'holdspeak[dictation-mlx]'    # the dictation pipeline on Apple Silicon (MLX)
pip install 'holdspeak[dictation-llama]'  # the dictation pipeline, cross-platform (GGUF)
pip install 'holdspeak[dictation-openai]' # the dictation pipeline via an OpenAI-compatible endpoint
```

(From a clone, use the editable form instead, e.g. `uv pip install -e '.[meeting]'`.)

### Upgrading and your data

Your whole HoldSpeak database is a single SQLite file. Before a version jump you
can snapshot it with `holdspeak backup`, and put one back with `holdspeak
restore`. Upgrades are safe by default: HoldSpeak backs up an older database
before it touches it, and refuses to open a database written by a newer build
rather than risk your data. `holdspeak doctor` reports the schema and config
state it found. The full policy is in
[`docs/RELEASING.md`](https://github.com/karolswdev/HoldSpeak/blob/main/docs/RELEASING.md).

## Platform support

| Capability | macOS 14+ (Apple Silicon) | Linux X11 | Linux Wayland |
|---|---|---|---|
| Voice typing | ✅ | ✅ | ✅ |
| Global hotkey | ✅ | ✅ | ⚠️ Best effort |
| Cross-app typing | ✅ | ✅ | ⚠️ Best effort |
| Meeting mode | ✅ | ✅ | ✅ |
| System audio capture | ✅ BlackHole | ✅ Pulse/PipeWire | ✅ Pulse/PipeWire |

Wayland often blocks global hooks and synthetic typing, so HoldSpeak falls back to clipboard paste for injection.

## Meeting intelligence, a little deeper

Record a meeting live, or bring one you already have: import a recording
(WAV out of the box; compressed formats with ffmpeg) or a transcript file
(`.vtt`, `.srt`, `.txt`) from the archive page or with `holdspeak import
call.wav`, and it becomes a real meeting, run through the same intelligence.
The transcript is scored for intent (architecture, delivery, product,
incident, comms), a sequence of plugins runs, and each model attempt enters the
admitted path before it can produce a typed artifact. The results render
read-only in the Meetings window on the Desk (deep link `/history`).
HoldSpeak ships 14 built-in plugins, all real and backed by an LLM.

Plugins can also propose actions. An actuator can produce an external side
effect, like filing a ticket or posting an update. Fresh installs use YOLO with
actuators enabled: eligible configured destinations execute immediately and
write a receipt; Secure and Normal retain per-action approval. Write your own
with the [Plugin Authoring guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/PLUGIN_AUTHORING.md); for endpoints and routing, see
the [Meeting Mode Guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md).

Then close the loop. Meeting aftercare shows what is still open (by owner),
what was decided, and what changed since the last meeting. Jump to the
transcript moment that justifies any result, file an accepted action as an
issue, or draft a copyable follow-up. Under the default YOLO posture, eligible
configured sends execute with a receipt; Secure and Normal keep the approval
step. See the
[Meeting Mode Guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md#meeting-aftercare-close-the-loop).

## Companions

HoldSpeak runs as a desktop hub, and a companion on another device drives it
over the same local HTTP API your browser uses, on your own network (LAN or
Tailscale), with no hosted relay. Two companions exist today.

### The iPad app

The iPad is a first-class client of both modes, not a remote control for one.
It talks to the hub through typed clients over the existing API: it dictates an
answer into your desk (the hub runs that text through the full dictation
pipeline, applying your corrections and routing, and types the result, and a
matching voice command fires there too), previews the rewrite before anything
types (an opt-in receipt: what you approve is exactly what lands, verbatim),
authors the voice command board itself (every action still runs on the Mac,
and the board says so), pins your spoken language and your spoken-symbol
dictionary on that dictation path, reads a meeting back with its artifacts,
confidence, and sources, closes the meeting's loop from the aftercare digest
(an accepted action item becomes a GitHub issue proposal, typed against a
repo you name inline), reviews every pending proposal for a meeting wherever
it was created (the human gate stays its own step, and approving a Slack
send carries the cloud mark because that approval executes), searches and
filters the archive with the same facets the web has (narrowed on the hub,
never a stale page filtered locally), imports a recording or transcript file
into the hub's full intelligence pipeline (the new meeting appears
immediately, honestly marked importing), reads the learning digest and the
dictation journal with their real "learned from N similar" reach, and pulls
activity pre-briefing nudges whose "Dictate with this" grounds the next
utterance in the cited record. Live Coder sessions appear on its Desk too:
with the hooks installed (one command, reversible), every running Claude Code
or Codex session appears as an object with its current status and question. You
can answer by typing, speaking, or using a Meeting or Note as grounding so the
reply is grounded in that record, or by letting the AI draft the reply for
you (on this device or a configured endpoint, with the destination named).
Nothing sends itself: a draft lands editable, and only your explicit send
delivers it into the live session on your Mac. Its trust surface is the same one badge the
desktop wears: every desk object carries its real posture (a connector reads
an external service with its target named, dictation to your desktop names the
paired device, and a Note stored here reads This device), the app's header states the desktop's
posture in the web chip's own four words, and a guard holds Apple product
copy to the same canonical names and no-privacy-prose rule as the docs and
the web. Its on-device storage is schema safe the same
way the desktop is: it backs an older database up before migrating, and
refuses to open one written by a newer build. A readiness section in its
Settings states that store's health (schema version, integrity, a refused
newer database named as exactly that) beside your desktop's own doctor
readout, section by section, so the iPad can tell you it is healthy without
a trip to the Mac. The app itself is not released
yet; the screens and the typed client layer they ride on are built and tested.

### AIPI-Lite

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/aipi-lite-companion.png" alt="Pixel art AIPI-Lite companion device" width="220">
</p>

AIPI-Lite is an optional ESPHome-based device you can carry between rooms. Put it
on Wi-Fi (a phone hotspot works), and it gives you meeting-capture controls and
status feedback. With Claude/Codex hooks on, it shows when a Coder session is waiting
so you can speak the reply back into the coding session. Buy the hardware from the
[official page](https://aipi.com/products/aipi-lite) or the
[Amazon listing](https://www.amazon.com/dp/B0FQNNVV36); firmware and bridge setup
are in the [AIPI-Lite Developer Workflow](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AIPI_LITE_DEV_WORKFLOW.md).

## MCP sidecar

The MCP sidecar (`holdspeak-mcp`) is the desk's programmable surface over
stdio. It exposes 127 tools across 27 families and 32 resources,
so any MCP client can read and drive the desk without the web UI.

Claude Code discovers the sidecar automatically: the repo ships a
`.mcp.json` that wires it. For other MCP clients, the entry point is one
command:

```bash
uv run holdspeak-mcp
```

Four tools invoke inference through the admitted path; their results carry
the receipt (model, provider, egress, placement). The sidecar names the
verbs it deliberately excludes (live-runtime delivery paths it does not
own) so an MCP client discovers the boundary at tool-listing time.

See [MCP sidecar](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MCP_SIDECAR.md) for the full
reference: families, model-invoking tools, trust model, resources, and
deliberate absences.

## Where to go next

| I want to… | Read this |
|---|---|
| Browse all the docs | [Documentation index](https://github.com/karolswdev/HoldSpeak/blob/main/docs/README.md) |
| Understand how it works, with diagrams | [Architecture](https://github.com/karolswdev/HoldSpeak/blob/main/docs/ARCHITECTURE.md) |
| Get it running and verify my setup | [Getting Started](https://github.com/karolswdev/HoldSpeak/blob/main/docs/GETTING_STARTED.md) |
| Take the first-sentence loop or repair/deploy later | [Getting Started](https://github.com/karolswdev/HoldSpeak/blob/main/docs/GETTING_STARTED.md) |
| Choose / configure a model | [Models (bring your own)](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MODELS.md) |
| Point every feature at one endpoint | [Inference destinations](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INFERENCE_TARGETS.md) |
| Live on the Desk (the web front door) | [The Desk](https://github.com/karolswdev/HoldSpeak/blob/main/docs/WEB_DESK.md) |
| See speech become a project-grounded task | [The Dictation Copilot](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_COPILOT.md) |
| Set up the dictation pipeline for Codex / Claude | [Dictation Pipeline Setup](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_PIPELINE_GUIDE.md) |
| Review, correct, and replay past dictations | [The dictation journal & replay](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_PIPELINE_GUIDE.md#12-dictation-journal-corrections--replay) |
| Map spoken keywords to real actions | [Voice Commands](https://github.com/karolswdev/HoldSpeak/blob/main/docs/VOICE_COMMANDS.md) |
| Turn on Qlippy, the mascot | [Qlippy](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_PIPELINE_GUIDE.md#qlippy-the-mascot-optional) |
| Use meeting mode and configure AI intelligence | [Meeting Mode Guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md) |
| Drive HoldSpeak from another device | [Companions](#companions) |
| Wire up the AIPI-Lite companion | [AIPI-Lite Developer Workflow](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AIPI_LITE_DEV_WORKFLOW.md) |
| Put Coder sessions on the Desk | [Claude/Codex automation hooks](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AGENT_HOOK_INSTALL.md) |
| Install Claude / Codex automation hooks | [Claude/Codex automation hooks](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AGENT_HOOK_INSTALL.md) |
| Hold an agent's risky calls for my approval | [The Gate](https://github.com/karolswdev/HoldSpeak/blob/main/docs/USER_GUIDE.md#the-gate-a-steered-agent-asks-first) |
| Drive the desk from Claude Code or another MCP client | [MCP sidecar](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MCP_SIDECAR.md) |
| Understand what's stored and what can leave my machine | [Security & Privacy](https://github.com/karolswdev/HoldSpeak/blob/main/docs/SECURITY.md) |

## Configuration

Config lives at `~/.config/holdspeak/config.json`, but you rarely edit it by hand.
The Settings window on the Desk exposes the hotkey, meeting intel, dictation
pipeline, and presence options. Endpoint and model identity has exactly one
editor, **Settings, Models**: the destination list plus the Runs on pickers.
The old `intel_cloud_*` and `openai_compatible_*` fields no longer configure
anything. An upgrade reads them once, turns them into destinations named
`legacy-intel` and `legacy-dictation`, and points the matching feature at
them; after that the destination is the truth and the fields are ignored.
The full reference is in
[Getting Started](https://github.com/karolswdev/HoldSpeak/blob/main/docs/GETTING_STARTED.md) and the guides above.

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](https://github.com/karolswdev/HoldSpeak/blob/main/CONTRIBUTING.md) for setup
(`uv`, the git hooks, the test command) and the commit-contract workflow. Recent
changes are in [`CHANGELOG.md`](https://github.com/karolswdev/HoldSpeak/blob/main/CHANGELOG.md). If you want to build on
HoldSpeak rather than just use it, the
[Plugin Authoring guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/PLUGIN_AUTHORING.md) and
[Connector Development](https://github.com/karolswdev/HoldSpeak/blob/main/docs/CONNECTOR_DEVELOPMENT.md) are the doors in.

## License

Licensed under the Apache License 2.0. See [`LICENSE`](https://github.com/karolswdev/HoldSpeak/blob/main/LICENSE).
