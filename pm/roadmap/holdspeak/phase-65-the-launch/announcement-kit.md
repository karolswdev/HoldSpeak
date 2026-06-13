# HoldSpeak v0.3.0 — announcement kit

Drafts for the owner to post. Nothing here is published by the agent. Each
draft is in the POSITIONING voice: one copilot two modes, written for
developers, comparisons named honestly, no superlative without a proof
point behind it. Pick, edit, post.

---

## 1. GitHub release notes (paste into the v0.3.0 release)

**HoldSpeak v0.3.0**

One local copilot with two modes: dictation that types in any app and
learns how you work, and meetings that end with decisions, actions, and
follow-ups instead of a recording. Whisper runs on your machine and the
LLM is yours (GGUF in-process, MLX on Apple Silicon, or any
OpenAI-compatible endpoint, including one on your LAN).

This is the first release since 0.2.x, and it gathers fourteen development
phases. Highlights:

- **The wake word.** Say a phrase and it listens hands-free for a short,
  visible window. The result is previewed, never typed, until you confirm.
  Detection runs locally; the only network moment is a one-time ~7 MB model
  download.
- **Speak your language.** Pin any of Whisper's ~99 languages for dictation,
  meetings, and imports, plus a spoken-symbol dictionary that types your own
  vocabulary (say "double colon", get `::`).
- **Send to Slack.** A meeting's aftercare digest or follow-up draft can go
  to a Slack incoming webhook, on the same propose, approve, execute flow as
  every action: the preview is the exact message, and nothing sends until
  you approve it.
- **Bring your archive.** Import recordings and transcript files
  (`.vtt`/`.srt`/`.txt`, keeping their real timestamps and speaker names)
  into the full meeting-intelligence pipeline. The archive is searchable
  and filterable by date, speaker, tag, and open actions.
- **Voice command macros** and **activity pre-briefing** for the dictation
  side; **Qlippy**, an optional and entirely opt-in presence mascot, for the
  moments that need a decision.
- **Quiet trust.** Cards say where data goes with a small badge, not a
  paragraph.

Everything new is off by default, and nothing acts without your approval.
Install: `pip install holdspeak`, then `holdspeak doctor`.

Full notes in [CHANGELOG.md](../../CHANGELOG.md). It is 0.x: mature
features, but config and defaults can still move before 1.0. Upgrades back
your database up first.

---

## 2. Show HN

**Title:** Show HN: HoldSpeak – local voice dictation and meeting notes, bring your own LLM

**Body:**

HoldSpeak is one local copilot with two modes. Hold a hotkey and speak: it
types into whatever app is focused, and with the pipeline on it routes rough
speech by intent, grounds it in your project's context, and rewrites it for
its target (a coding agent, the terminal, your editor). Record a meeting and
it comes back as typed artifacts (decisions, action items, risk registers)
plus an aftercare digest of what is open, decided, and changed since last
time.

The part I care about: the intelligence is local too. Whisper transcribes
on your machine, and the LLM is one you run (GGUF in-process, MLX on Apple
Silicon) or an OpenAI-compatible endpoint you point at, including one on
your own LAN. No account, no telemetry.

It learns how you work and shows the receipts: every dictation is journaled
(what you said, what it typed, where it routed, how long it took), one tap
teaches a correction, and you can replay an old utterance through the
updated pipeline to watch the routing change rather than trusting that it
improved.

Honest about what it is not: it is 0.x, the smart parts need a model you
provide, setup is heavier than a menu-bar app, there is no Windows build
today, and Wayland limits global hotkeys to best effort. Compared to
superwhisper / MacWhisper / VoiceInk, the difference is that the AI stays
local and there is a meeting side and a visible learning loop; compared to
Wispr Flow / Aqua Voice, your voice never leaves the machine and there is no
subscription; Talon is far deeper for hands-free control, this is
prose-first with LLM rewriting.

Python, Apache-2.0, macOS and Linux. `pip install holdspeak` then
`holdspeak doctor`. Repo: <REPO_URL>

I would most like feedback on the two-modes framing (does one tool spanning
dictation and meetings make sense to you, or should they be two projects?)
and on the model-bring-your-own setup friction.

---

## 3. lobste.rs

**Title:** HoldSpeak: local dictation + meeting intelligence, you bring the LLM

**Tags:** audio, privacy, python, release

**Body:**

A local voice copilot with two modes, just tagged v0.3.0.

Dictation: hold a key, speak, it types into the focused app; optionally
route the speech by intent and rewrite it for a target (coding agent,
terminal, editor) using a model you control. Meetings: capture or import
audio and transcripts, get typed artifacts and an aftercare digest that
tracks what is still open across meetings.

Local by construction: Whisper on-device, and the LLM is GGUF in-process,
MLX, or any OpenAI-compatible endpoint you choose (LAN endpoints included).
No account or telemetry. Every dictation is journaled and correctable, and
you can replay an utterance through the updated pipeline to see the routing
change.

It is honestly 0.x and developer-facing: assumes a shell, a config file,
and that you will run a model or point at one. macOS and Linux, Apache-2.0.
The README carries a date-stamped comparison section against the obvious
alternatives, trade-offs in both directions.

`pip install holdspeak`. Repo and docs: <REPO_URL>

---

## 4. r/LocalLLaMA

**Title:** HoldSpeak v0.3.0 — voice dictation + meeting notes that run on your own LLM endpoint

**Body:**

If you already run a local or LAN LLM, this plugs straight into it.

HoldSpeak is a local voice copilot with two modes. Dictation types into any
app from a hotkey, and with the pipeline on it rewrites rough speech for its
target using your model. Meetings (live capture or imported recordings and
transcripts) come back as typed artifacts plus an aftercare digest.

The LLM is entirely yours: GGUF in-process, MLX on Apple Silicon, or any
OpenAI-compatible endpoint, so pointing it at your own llama.cpp / Ollama /
vLLM server on the LAN is a first-class setup, not a workaround. Whisper
runs on-device too. No account, no telemetry, and the meeting-intel egress
posture is visible in `holdspeak doctor` (local stays local, and it tells
you when a cloud endpoint is configured).

New in 0.3.0: a wake word (local detection, previewed before it types),
~99-language transcription, Send to Slack for meeting digests on an
approval flow, and recording/transcript import into the full pipeline.

0.x, developer-facing, macOS + Linux, Apache-2.0. `pip install holdspeak`,
then `holdspeak doctor` to see it find your endpoint. Repo: <REPO_URL>

Curious what model + endpoint combos people would point this at, and whether
the intent-routing rewrite is useful or just gets in the way for dictation.

---

## Posting notes (for the owner)

- Replace `<REPO_URL>` with the public repo link.
- The honest-comparison and "0.x, here is what it is not" paragraphs are
  load-bearing for these audiences; keep them even when trimming for length.
- Post the GitHub release first (it is the canonical link the others point
  at), then the rest at your own pace.
- A README demo GIF was attempted this phase; see the story-03 evidence for
  the outcome and the honest fallback.
