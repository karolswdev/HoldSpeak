# HoldSpeak Dictation Pipeline Setup

The gap between what you say and what you meant to type is where dictation
tools usually stop; the dictation pipeline is HoldSpeak crossing it. It
routes an utterance through local rules, project context, agent context, and
an optional LLM rewrite stage before inserting text, so rough speech lands
as useful text for the active app.

Use this after basic voice typing works. If you are starting from zero, read
[Getting Started](GETTING_STARTED.md) first.

> Want to **see it in action** before configuring? [The Dictation
> Copilot](./DICTATION_COPILOT.md) shows a real spoken→enriched run (and a
> reproducible demo) where rough speech becomes a project-grounded coding task.

## What You Are Setting Up

The intelligent-typing loop is:

```text
speech -> Whisper transcript -> punctuation cleanup -> dictation pipeline -> typed text
```

The pipeline can:

- classify an utterance against dictation blocks;
- inject your **project facts** and **project context** (see below);
- rewrite rough speech into a cleaner prompt;
- adapt output for Codex, Claude, terminal, browser, editor, or chat;
- suggest narrow `.hs/.../*.md` project documentation updates for review.

> **Project knowledge has two parts, and they are different.** *Facts* (the
> **Project Facts** tab) are a small key-value map (`kb:`) in
> `<repo>/.holdspeak/project.yaml`. Each key becomes a `{project.kb.<key>}`
> placeholder that the default **`kb-enricher`** stage stamps into a block's
> template, verbatim, with no LLM. *Context* (the **Project Context** tab) is the
> *separate* `.hs/` folder of Markdown files (`instructions`, `context`,
> `workflows`, `targets`, plus an `ignore` for secrets); the **optional
> `project-rewriter`** (LLM) stage reads it to rewrite your speech. In short:
> facts are exact values stamped in; context is guidance a rewrite reads. Set up
> both in [§5. Set Up Project Knowledge](#5-set-up-project-knowledge). HoldSpeak
> reads both but never writes them without your approval.

## 1. Open The Dictation Cockpit

Start HoldSpeak:

```bash
holdspeak
```

Open:

```text
/dictation
```

Start with the **Readiness** tab. It tells you what is configured, what is
missing, and what to fix next.

## 2. Choose A Runtime Backend

Open:

```text
/dictation -> Runtime
```

Enable:

- `Enable dictation pipeline`
- Optional: `Enable project-aware rewrite stage (.hs/)`

Choose one backend:

| Backend | Use when |
| --- | --- |
| `auto` | You want HoldSpeak to prefer MLX on Apple Silicon and otherwise use llama.cpp |
| `mlx` | You are on Apple Silicon and have an MLX model installed |
| `llama_cpp` | You have a local GGUF model |
| `openai_compatible` | You have a local, LAN, or hosted `/v1/chat/completions` endpoint |

Install extras as needed:

```bash
uv pip install -e '.[dictation-mlx]'
uv pip install -e '.[dictation-llama]'
uv pip install -e '.[dictation-openai]'
```

## 3. Configure An OpenAI-Compatible Endpoint

Use this path for llama.cpp server, LM Studio, Ollama OpenAI bridge, vLLM,
LiteLLM, or a hosted OpenAI-compatible API.

In `/dictation -> Runtime`, set:

| Field | Example |
| --- | --- |
| Backend | `openai_compatible` |
| Base URL | `http://127.0.0.1:8000/v1` |
| Model | `qwen2.5-7b-instruct` |
| API key env | `OPENAI_API_KEY` |
| Timeout seconds | `8` |

Config file shape:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["intent-router", "project-rewriter", "kb-enricher"],
      "target_profile_override": "auto"
    },
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

HoldSpeak reads the API key from the named environment variable. Do not put API
keys in `.hs/` files.

> **Extended thinking disabled by default.** HoldSpeak sets `thinking: false` on
> every call to an OpenAI-compatible endpoint. This prevents extended-thinking
> inference mode from activating on models that support it (e.g., Claude 3.7+
> Sonnet), which would add significant latency and token cost to short
> dictation rewrites. If your endpoint does not support the `extra_body` field
> this parameter is silently ignored.

A known-good local profile:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["project-rewriter"],
      "target_profile_override": "codex_cli"
    },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "http://127.0.0.1:8080/v1",
      "openai_compatible_model": "Qwen3.5-9B-UD-Q6_K_XL.gguf",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 20
    }
  }
}
```

Validation used a local `/v1/chat/completions` server at `127.0.0.1:8080`
and `holdspeak dictation dry-run`. If HoldSpeak reports that the OpenAI
client package is missing, install:

```bash
uv pip install -e '.[dictation-openai]'
```

## 4. Set The Target Profile

HoldSpeak tries to detect the active app automatically. If detection is wrong,
set a manual target override in:

```text
/dictation -> Runtime -> Target profile override
```

Options:

| Option | Meaning |
| --- | --- |
| `Auto-detect target` | Use active-window hints |
| `Codex CLI` | Shape dictation as an implementation prompt for Codex |
| `Claude Code` | Shape dictation as a prompt/reply for Claude Code |
| `Terminal shell` | Preserve command syntax more aggressively |
| `Browser` | Write prose suitable for browser text boxes |
| `Editor` | Write code/editor-friendly prose |
| `Chat` | Write conversational chat text |

Use **Reset target to auto** when active-window detection is working again.

## 5. Set Up Project Knowledge

Project knowledge is what HoldSpeak knows about this repo. It has two parts that
do different jobs: **facts** are exact values stamped in verbatim; **context** is
background the rewrite model reads. Set up both from the UI. HoldSpeak reads both
but never writes them without your approval.

### Facts (the Project Facts tab)

A fact is an exact value you reuse a lot: your stack, a deploy command, a ticket
prefix. Facts live in the `kb:` map of `<repo>/.holdspeak/project.yaml`. Each key
becomes a `{project.kb.<key>}` placeholder that the default **`kb-enricher`** stage
stamps into a matched block's template, verbatim, with no model involved (facts
are on the default pipeline).

Open:

```text
/dictation -> Project Facts
```

Click **Use starter facts**, fill in the values you care about, and Save. A fact:

```yaml
# <repo>/.holdspeak/project.yaml
kb:
  stack: Rails 7 + Postgres 16
```

referenced by a block template:

```text
Follow our stack: {project.kb.stack}
```

comes out as exact text:

```text
Follow our stack: Rails 7 + Postgres 16
```

The **Project facts context** starter block (Blocks -> Starter templates) already
references `{project.kb.stack}`, so once you set the `stack` fact a dry-run shows
it stamped. Keys must match `[A-Za-z_][A-Za-z0-9_]*`; values are strings (or empty
for null).

### Context (the Project Context tab)

Context is prose, not values: background the **optional `project-rewriter`** (LLM)
stage reads so it phrases dictation the way this project expects. It only takes
effect when you enable the rewrite stage (Runtime). Open:

```text
/dictation -> Project Context
```

The fastest start is the **Set up project knowledge** panel on that tab: "Use a
starter set" scaffolds the files below (you review before they write), or "Draft
with your coding agent" gives you a copiable prompt so Claude or Codex writes the
`.hs/` files for this repo, which you then review in the tab. To do it by hand,
create a small `.hs/` directory in your repo:

```text
.hs/
  instructions.md
  context.md
  workflows.md
  targets.md
  ignore
```

Start with this minimal set:

```md
# .hs/instructions.md
When dictating into Codex or Claude, rewrite rough speech into a concise
engineering request. Preserve explicit filenames, commands, and test names.

# .hs/context.md
This project is a local-first Python app with a FastAPI web runtime and Astro
frontend.

# .hs/workflows.md
Run focused Python tests with `.venv/bin/pytest <path>`.
Rebuild the web bundle with `cd web && npm run build`.

# .hs/targets.md
Codex: concise implementation request.
Claude: product/design discussion is acceptable, but include concrete repo context.
Terminal: preserve command syntax exactly.
Browser: keep output plain and paste-friendly.

# .hs/ignore
.env
secrets
private keys
```

Write policy:

- HoldSpeak reads `.hs/` during dictation.
- HoldSpeak does not silently write `.hs/` files.
- Suggested `.hs/.../*.md` updates require explicit review and apply.
- Secret-looking content is skipped or rejected.

## 6. Install Claude/Codex Agent Hooks

Agent hooks let Claude Code and Codex tell HoldSpeak their current `cwd`,
session id, transcript path, and recent assistant state. This is how HoldSpeak
can know which project an LLM CLI is working in.

Use [Claude/Codex Agent Hook Install](AGENT_HOOK_INSTALL.md) for the full
machine-level install, verification, capture-mode, and AIPI companion checks.

Open:

```text
/dictation -> Agent Hooks
```

Copy the template for the tool you use. Or generate templates from the CLI:

```bash
holdspeak agent-hook templates --agent claude
holdspeak agent-hook templates --agent codex
```

To let HoldSpeak capture the latest assistant message and detect when the agent
is waiting for your reply:

```bash
holdspeak agent-hook templates --agent claude --capture-messages
holdspeak agent-hook templates --agent codex --capture-messages
```

Assistant-message capture stores only a small local snippet and can be cleared
from the `/dictation` banner.

## 7. Run A Dry-Run

Use the web UI:

```text
/dictation -> Dry-run
```

Try:

```text
ask codex to inspect the failing project context test and propose a minimal fix
```

Or use the CLI:

```bash
holdspeak dictation dry-run "ask codex to inspect the failing project context test and propose a minimal fix"
```

Check:

- runtime status is loaded or available;
- target profile is correct;
- stage telemetry has no unexpected fallback;
- final text is useful;
- project documentation suggestion appears only when it is genuinely useful.

## 8. Review Suggested Project Documentation

When the project-aware rewrite stage sees durable context worth preserving, it
may suggest a narrow project documentation update such as:

```text
.hs/memory/retry-worker-next-run.md
.hs/decisions/agent-hooks-context-channel.md
.hs/workflows/web-build-command.md
```

Open:

```text
/dictation -> Project Context
```

Review the suggested path, rationale, and content. You can edit the content
before applying or dismiss the suggestion. A suggestion that mostly duplicates
what the target file already says is **suppressed** before you ever see it, and
a suggestion you **dismiss won't recur** for a near-duplicate utterance in the
same session (see the quality gate in §10). Apply only writes validated paths
under:

```text
.hs/memory/
.hs/decisions/
.hs/handoffs/
.hs/workflows/
.hs/issues/
```

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Runtime unavailable | Missing extra/model/server | Open Readiness and Runtime; run `holdspeak doctor` |
| Dry-run preserves original text | Stage fallback or no project context | Check dry-run telemetry and `.hs/instructions.md` |
| Target says `unknown` | Active-window hints unavailable | Set Target profile override |
| Codex/Claude cwd is missing | Hooks not installed/firing | Open Agent Hooks and copy templates again |
| Suggestions are noisy | Context too broad or prompt too generic | Narrow `.hs/instructions.md` and `.hs/targets.md` |
| Endpoint times out | Model/server too slow | Increase timeout or use a smaller/faster model |

## 10. Copilot Depth (multi-pass, memory, model-assist, telemetry)

These knobs make the copilot deeper and self-improving. **Every one is opt-in
and off by default**: with them off, behavior is identical to the basic
pipeline. See [The Dictation Copilot](./DICTATION_COPILOT.md) for a live demo of
all of them firing at once.

### Set it in the UI, no file editing

```
/dictation -> Runtime -> Copilot depth
```

Everything below is a slider or a toggle in the **Copilot depth** card. There is
no need to touch `config.json`; set it here and it round-trips through the
settings API.

![The Copilot depth card: a segmented rewrite-passes control, toggles for
correction memory and model-assisted target detection, and a reveal-on-toggle
confidence threshold.](assets/cockpit/copilot-depth.png)

| Control (Runtime → Copilot depth) | Knob (`dictation.pipeline`) | Default | What it does |
| --- | --- | --- | --- |
| **Rewrite passes** (segmented 1-5) | `rewrite_passes` | `1` | Project-rewriter passes (draft → critique → refine). `1` is single-pass. Extra passes are skipped if they would breach `max_total_latency_ms`. |
| **Learn from my corrections** (toggle) | `corrections_enabled` | `false` | Consult the **correction memory** when routing: a correction you made earlier nudges a similar later utterance. |
| **Infer the target when unsure** (toggle) | `target_detect_llm_enabled` | `false` | When window/app detection is unsure, ask the LLM to infer the **target profile** from your words. A manual override always wins. |
| **Ask the model below confidence** (slider) | `target_detect_llm_below` | `0.8` | The heuristic-confidence threshold below which the LLM fallback fires. |

The **"Save & test in dry-run"** button saves the config and jumps straight to
the dry-run so you can try the exact settings you just chose.

**Multi-pass rewriting.** With `rewrite_passes > 1`, the project-rewriter drafts,
then critiques and tightens its own draft. A failed or over-budget refine pass
falls open to the best draft so far, so enabling it never makes output worse
than single-pass.

**Correction memory.** When a correction is recorded (from the live runtime, or
added by hand in the Memory tab), a later similar utterance is nudged toward it.
The memory is **DB-backed and persists across restarts**: corrections you make
survive a relaunch (a bounded in-memory ring stays the fast nudge path; the
SQLite store is durability). Corrections are gist-only: gists are truncated and
secret-looking text is rejected before anything is stored. Curate it in the UI:

```
/dictation -> Memory
```

![The Memory tab: "What the copilot has learned" lists the persistent
corrections with remove buttons and an add form; "Pipeline depth · this session"
renders per-stage p50/p95 bars, budget guidance, and the multi-pass
timings.](assets/cockpit/memory-panel.png)

The **What the copilot has learned** panel lists every persistent correction
(kind · gist · → corrected value · when) with a remove (`×`) on each, an **add**
form, a **Forget all** button, and the `corrections_enabled` toggle in context.

**Model-assisted target detection.** On Wayland/terminal setups where the active
window can't be read, the heuristic returns low confidence; with the fallback on,
the LLM infers the target (`claude_code`, `codex_cli`, `browser`, …) from the
utterance. A manual **Target profile override** still wins over both.

**Suggestion quality gate.** The project-doc suggestion path no longer
re-proposes what your target `.hs/*.md` already says (suppressed as
`already_covered`), and a suggestion you dismissed won't recur for a near-duplicate
utterance in the same session. The dry-run response carries a `suggestion_status`
(`stored` / `already_covered` / `dismissed` / `no_suggestion`).

**Depth telemetry.** The **Pipeline depth · this session** panel in the Memory
tab renders, over the session's recent runs:

- per-stage **p50/p95** latency (ms) + run count, each with a bar against your
  latency budget (it turns red at ≥ 66%);
- **budget guidance**: a hint when a stage's p95 reaches ≥ 66% of
  `max_total_latency_ms` (consider a smaller/faster model);
- the most recent **multi-pass** rewrite timings as chips;
- the correction-store size.

Telemetry is in-memory and resets on restart (run a few dry-runs to populate
it). The same data is on `GET /api/dictation/readiness` as the `depth` block
(`depth.stages` / `depth.guidance` / `depth.rewrite_pass_ms` /
`depth.corrections`) for headless use.

### Advanced: the same knobs in `config.json`

Prefer to edit the file (headless / scripted setups)? The same four knobs live
under `dictation.pipeline`:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["intent-router", "kb-enricher", "project-rewriter"],
      "rewrite_passes": 2,
      "corrections_enabled": true,
      "target_detect_llm_enabled": true,
      "target_detect_llm_below": 0.8
    }
  }
}
```

## 11. Desktop Presence (ambient, on-desktop status)

When you dictate into another app, the HoldSpeak web dashboard isn't on
screen, so you can't see whether the copilot is **listening**,
**transcribing**, or **typing**. Desktop presence is an **opt-in, native**
surface that tells you, at a glance, what the runtime is doing right now,
without ever stealing keyboard focus from the app you're typing into.

It is **off by default** and adds **no GUI dependency** unless you turn it on.

### Turn it on

Presence is a **config toggle**. Flip it from the **Settings** page (or the
welcome wizard); the runtime starts and stops the presence host live. Or set it
directly in your config:

```json
{ "presence": { "enabled": true } }
```

For a headless or power-user launch you can also force it on with an environment
variable (a retained override; the config toggle is the normal path):

```bash
HOLDSPEAK_DESKTOP_PRESENCE=1 holdspeak
```

Install the optional native extra for your platform:

```bash
uv pip install -e '.[presence]'
```

On **Linux** you also need the freedesktop system typelibs (PyGObject binds to
them; they are not pip packages):

```bash
# Notification + tray (Tier 1)
sudo apt-get install gir1.2-notify-0.7 gir1.2-ayatanaappindicator3-0.1
# Floating HUD overlay (Tier 2: X11 / wlroots only)
sudo apt-get install gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

> With the flag **unset**, the runtime is byte-identical and pulls in none of
> these; presence is purely additive.

### What you'll see: the states

Presence reflects the live runtime activity and disappears when idle:

| State | Label | Meaning |
| --- | --- | --- |
| `listening` | Listening | Hotkey held; capturing audio |
| `recording` | Recording | Recording your utterance |
| `transcribing` | Transcribing | Turning speech into text (Whisper) |
| `processing` | Processing | Running the dictation pipeline |
| `typing` | Typing | Injecting text into the active app |
| `complete` | Complete | Done; lingers briefly, then hides |
| `error` | Needs attention | Something failed; lingers so you notice |

`idle` never renders a surface; presence is **transient** by design, present
only while something is happening.

### macOS

On macOS you get the rich **floating HUD**, a frameless, non-activating panel
that hosts the Signal presence card (native rounded corners + shadow, live over
the websocket), plus a **menu-bar glyph**.

![The macOS presence HUD: a dark Signal card with an animated state glyph,
"Transcribing: Turning your speech into text…", and the dictation source
("Hotkey").](assets/presence/macos-hud.png)

![The HoldSpeak glyph in the macOS menu bar, alongside the system status
items.](assets/presence/macos-menubar-glyph.png)

The HUD uses an `NSWindowStyleMaskNonactivatingPanel`, so it **cannot take
keyboard focus**: while it's visible, your keystrokes keep flowing into the
frontmost app. Needs the `pyobjc` extra (`.[presence]`); without it (or without
WebKit), presence falls back to the web dashboard card and nothing breaks.

### Linux

On Linux, Tier 1 works everywhere: an **in-place-updating notification** (one
banner that mutates as the state changes, rather than spamming new ones) plus a
**tray glyph** (StatusNotifierItem):

![A GNOME notification banner reading "HoldSpeak: Transcribing / Turning your
speech into text…", updating in place as the state
changes.](assets/presence/linux-notification.png)

Where the compositor allows free-floating always-on-top windows (**X11** and
**wlroots** Wayland), you also get the same rich **floating HUD** as macOS:
a GTK3 + WebKit2 overlay of the very same Signal card:

![The Linux floating HUD overlay: the same dark Signal "Transcribing" card,
rendered as a GTK-WebKit popup over the desktop.](assets/presence/linux-overlay.png)

> **The Wayland caveat.** On mainstream Wayland (**GNOME/KDE**), the compositor
> blocks arbitrary always-on-top overlays, so the floating HUD is **not**
> available there; the native path is the Tier-1 **notification + tray glyph**
> (which is focus-safe and works on every desktop). The floating HUD is for
> macOS, X11, and wlroots compositors. HoldSpeak probes your session at startup
> and picks the best available surface automatically.
>
> On **GNOME** specifically, the tray glyph needs the *AppIndicator* shell
> extension installed/enabled; without it, presence degrades to
> notification-only.

### The focus invariant

The one non-negotiable rule: **the presence surface never takes keyboard
focus.** While it's on screen, you're actively typing into another app, so any
focus theft would land your keystrokes in the wrong window. Every surface
guarantees this at the platform level: macOS via the non-activating panel,
Linux via notifications and the tray (which can't be focused) and an
override-redirect, non-focus overlay window.

### Qlippy, the mascot (optional)

Presence has an optional second layer: **Qlippy**, a small pixel-art
companion who gives the runtime a face. He is a homage to a certain office
paperclip, rebuilt for a tool that types what you say. Where the plain
presence card tells you what the runtime is doing, Qlippy also surfaces the
few moments that genuinely need you, and he does it without ever acting in
your place.

Qlippy is **off by default**, even when presence is on. He has his own
toggle, so the minimal ring stays the default for existing presence users:

```json
{ "presence": { "enabled": true, "mascot": true } }
```

Or flip **"Qlippy, the mascot"** inside the Desktop presence section of
**Settings**. Turning presence off removes the whole surface, Qlippy
included, in one click.

**Two levels.** The **dock** is ambient: a small animated sprite in the
corner of the presence surface that mirrors the runtime state (listening,
thinking, celebrating a finished dictation with a short flourish, dozing off
after five quiet minutes). It has no buttons and makes no sound. The
**card** slides out next to him only when something deserves your attention.
One card at a time, every card dismissible, and ignoring a card is always
safe.

**Exactly these moments produce a card:**

- **A decision needs you.** An action is proposed and waiting for approval,
  for example filing an accepted meeting action as a GitHub issue. This card
  stays until you resolve or dismiss it. It never decides for you and never
  expires into a decision.
- **The result of an action you approved.** It ran exactly as previewed, or
  it failed and the card says so plainly (and that nothing was sent).
- **Learned from you.** A correction you taught actually reaches past
  dictations, with the honest match count. If a correction was not stored or
  matches nothing, no card appears: Qlippy never claims learning that did
  not happen.
- **A finished meeting left open items.** The aftercare digest found work
  still open, with the top items named.

![The decision card: Qlippy in an alert pose beside "A decision needs you",
the exact preview of the proposed action, the egress badge naming the
destination, and Approve / Decline buttons.](assets/presence/qlippy-decision-card.png)

**Qlippy never acts on his own.** The Approve button on a card sends the
identical request the dashboard's Approve sends: it records your decision in
the same audit trail, and execution stays behind the same guarded,
permission-checked path. Dismissing a decision card is always safe; the
proposal stays on the dashboard, untouched.

**Every card carries the egress badge** instead of explanatory text: one
small pill that says where the card's data goes, at a glance.

- **⌂ Local** (green): everything involved lives on this machine. Learned,
  aftercare, and wake preview cards are always local.
- **☁ + a destination** (orange): approving sends the previewed content to
  that named destination, and nowhere else. Decision and result cards name
  their target on the badge, for example "☁ slack".
- **⌂+☁** (orange): a mixed operation, partly local, partly out.

The preview on a decision card is the exact content in question; the badge
is the destination. That pair is the whole answer.

**On the native HUD too.** On macOS and on overlay-capable Linux (X11 and
wlroots), the same cards appear in the floating HUD. The panel accepts
pointer clicks only while a card is showing, returns to click-through the
moment it resolves, and at no point can it take keyboard focus, so your
keystrokes keep landing in the app you are typing into even as you click
Approve.

![The native Linux overlay hosting the decision card over a real desktop:
the same dark card with Qlippy, the preview, the egress badge, and the
Approve and Decline buttons.](assets/presence/qlippy-native-overlay.png)

**Motion and accessibility.** New cards are announced to screen readers.
Hovering a card pauses its auto-dismiss timer. With reduced motion enabled,
slide animations become simple fades and the sprites hold still.

## 12. Dictation journal, corrections & replay

This is the learning loop, and it is the part of HoldSpeak worth showing off: it
hears rough speech, routes and rewrites it, records the attempt, learns from your
corrections, shows you what it learned, and lets you replay to prove it improved.
All of it runs on your machine. The loop has five steps, and the rest of this
section walks them in order:

1. **Dictate.** Every run is journaled (real dictation and dry-run alike).
2. **Correct.** One tap on a result says "that was wrong" and teaches the fix.
3. **Learn.** The correction nudges similar future utterances toward your fix.
4. **See it.** The "What HoldSpeak learned" digest shows the honest count.
5. **Replay.** Re-run a past utterance and watch the routing change.

Open it from the **Journal** tab on `/dictation`.

![The dictation Journal: a said → typed timeline. Each entry shows a source chip
(Spoken / Dry-run), the routed block + target, a timestamp, the transcript and
the typed text side by side, and a per-stage latency strip.](assets/journal/journal-timeline.png)

### Your dictation stays local

The journal is **local-only**: it never leaves your machine. Nothing about it
is uploaded, synced, or shared. Privacy comes from *local + filter + cap +
wipe*, not from being off:

- **Secret-filtered.** Before an entry is stored, the transcript and typed text
  are checked with the same secret-shape filter the correction memory uses; a
  field that looks like it carries a key/token is redacted, so a secret never
  lands in the journal.
- **Retention-capped.** The journal keeps the most recent *N* entries
  (`dictation.journal_retention`, default 500) and prunes older ones on every
  write.
- **Curatable.** Delete any single entry, or **Clear journal** to wipe it all,
  from the tab.
- **Toggle.** The journal is **on by default** (local). Turn it off with
  `dictation.journal_enabled = false`; when off, **no** rows are written and
  your typed output is byte-identical to journaling-off. (Journaling is a pure
  side-channel: it never changes what gets typed or how fast.)

### What is recorded

One row per pipeline run, real dictation **and** dry-run, tagged by source:

| Field | What it captures |
|---|---|
| transcript | what you said (secret-filtered) |
| final text | what was typed (secret-filtered) |
| route | the matched block + confidence |
| target | the target profile it was headed to |
| latency | per-stage timing + total (the latency strip) |
| source | `dictation` (spoken) or `dry_run` |
| corrected | set when you fix it in the moment (below) |

Search the timeline by transcript/typed text; filter by source, "only with
warnings", or "only corrected".

### Step 2: correct it in one tap

When a dictation lands wrong, the cheapest time to fix it is right then. Every
result carries a quiet **"Was that right?"** with two buttons, **Right** and
**Fix it**. It sits on the dry-run result (the no-mic path, and the same surface
for real dictation) and on every journal entry.

- **Right** is a single tap. It just acknowledges the result and writes nothing,
  so your routing is untouched.
- **Fix it** opens the correction inline, already scoped to the likely fix. If
  the run had a target, you pick **Wrong block** or **Wrong target** in one tap;
  otherwise it goes straight to the block. The value it routed to is pre-filled
  as the placeholder, so correcting is one decision, not a blank form. Type the
  right value and press **Teach**.

![The one-tap fix on a journal entry: "Was that right?" with Right and Fix it,
and the inline "Teach the copilot the right block" form pre-scoped after one
tap.](assets/screenshots/correction-ritual.png)

That gesture does two things. It **teaches** the copilot (it writes a correction,
the same kind the [Memory tab](#10-copilot-depth-multi-pass-memory-model-assist-telemetry)
manages, so similar future utterances are nudged toward your fix), and it
**marks the journal entry corrected**. The teach is gist-only and
secret-filtered, exactly like the Memory tab, and it never takes keyboard focus.
The confirmation is honest about reach: it tells you how many similar utterances
the fix now covers, and if corrections are off it says so rather than pretending.

### Steps 3 and 4: see what it learned

Corrections are easy to make and easy to forget. The **Memory** tab opens with
**"What HoldSpeak learned"**, a digest of the loop over a window you choose (this
week or all time). It shows how many corrections you made, how many dictations
you corrected, where they landed (by block and by target), and for each
correction a real **"learned from N similar"** count.

![The "What HoldSpeak learned" digest: a window toggle, three headline counts
(corrections made, dictations corrected, utterances nudged), a breakdown by
block and target, and per-correction "learned from N similar"
rows.](assets/screenshots/learning-digest-week.png)

The same "learned from N similar" signal rides the places the work happens: the
dry-run result, each journal entry, and the Memory list. It shows up only when a
correction actually reaches past utterances, and stays quiet at zero. Nothing
here is decorative; every count is the real reach of your correction (see the
limits note below).

![Inline trust signals: journal entries each carry a "learned from N similar"
chip, while an unrelated utterance carries none.](assets/screenshots/trust-signals-journal.png)

### Step 5: replay, and prove it learned

The promise of a learning copilot only feels real when you can *see* it get
better. Press **↻ Replay** on any journal entry to re-run that utterance's
stored transcript through the **current** pipeline, in dry-run mode, so nothing
is typed and no new journal row is created, and see a **before / after** diff.

![A replayed utterance: the before → after diff shows the routed target changing
from terminal_shell to browser after a correction, with "Preview only — nothing
was typed."](assets/journal/replay-before-after.png)

The satisfying loop: **correct** an utterance, **replay** it, watch the routing
change to your corrected target. Replay reuses the same dry-run path, so it
automatically reflects everything the copilot knows *now* (your corrections,
project context, and config). Re-insert is **preview plus copy**: copy the
improved result and paste it where you want. HoldSpeak never types into your
active app from a background click.

### How the learning works, and its limits

The learning is real, local, and bounded. Be clear-eyed about what it is:

- **It is token overlap, not a model that retrains.** A correction matches a new
  utterance by Jaccard similarity (the fraction of words they share) above a
  threshold. The "learned from N similar" count everywhere in the UI is that same
  measure, run over your journal. There is no hidden training and no embedding
  model, which is also why the count is honest and easy to reason about.
- **It is off by default for routing.** A correction is stored the moment you
  make it, but it only nudges routing once you turn on **Use corrections when
  routing** (`dictation.corrections_enabled`) in the Memory tab. Until then the UI
  says a fix *would* nudge N utterances, not that it does.
- **It is local.** Corrections and the journal live on your machine, gist-only
  and secret-filtered, like everything else in this loop. A secret-shaped
  correction teaches nothing, and the confirmation says so.

## Good First Configuration

For daily coding-agent dictation, use:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["intent-router", "kb-enricher"],
      "max_total_latency_ms": 600,
      "target_profile_override": "auto"
    },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "http://127.0.0.1:8000/v1",
      "openai_compatible_model": "qwen2.5-7b-instruct",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 8,
      "warm_on_start": false
    }
  }
}
```

Then validate:

```bash
holdspeak doctor
holdspeak dictation runtime status
holdspeak dictation dry-run "ask codex to summarize what changed and suggest a next test"
```

> **Optional: add `project-rewriter` stage.** The default stage list
> (`intent-router`, `kb-enricher`) classifies your utterance and stamps in your
> project facts without invoking the LLM for rewriting. Add
> `"project-rewriter"` to the `stages` array to also ask the runtime to rewrite
> rough speech using `.hs/` context before enrichment. This adds one extra LLM
> round-trip; only enable it when an OpenAI-compatible runtime is configured and
> you have populated `.hs/instructions.md`.

## See also

- [Getting Started](GETTING_STARTED.md): install and basic voice typing first.
- [The Dictation Copilot](DICTATION_COPILOT.md): see the pipeline turn rough speech
  into a project-grounded task, end to end.
- [Models (bring your own)](MODELS.md): choosing and pointing at an LLM.
- [Agent Hook Install](AGENT_HOOK_INSTALL.md): feed Claude/Codex context into the
  rewriter.
- [Security & Privacy](SECURITY.md): what's stored and what can leave your machine.
