# HoldSpeak v0.3.0 — announcement kit

Drafts for the owner to post. The agent publishes nothing here. Replace
`<REPO_URL>` with the repo link and `<tested model/backend>` with a real
setup you have run (or cut that line), trim to taste, post the GitHub
release first since the others point at it.

A note on voice: these are written to sound like one person who built a
thing and is showing it, not like a launch. Two things are deliberate and
worth keeping. The honest limits and the named comparisons stay in even
when you cut for length, because they are why a developer audience trusts
the rest. And the network claims are precise on purpose: HoldSpeak's local
modes are local, but Slack export, the wake-word model download, and a
remote LLM endpoint are real network use, so the copy says "local stays
local" rather than "nothing ever leaves," which a careful reader would
immediately catch.

---

## 1. GitHub release notes (paste into the v0.3.0 release)

**HoldSpeak v0.3.0**

HoldSpeak is one local voice copilot with two modes. Hold a key and it
types what you say into the focused app. Record a meeting and you get back
decisions, action items, and open questions, plus a digest of what is still
unresolved, instead of only a transcript. Whisper runs on your machine, and
the LLM side is whichever backend you configure: a local GGUF, MLX on Apple
Silicon, or any OpenAI-compatible endpoint, including one on your LAN.

This is the first release since 0.2.x and it pulls in a lot. The headline
additions:

- A **wake word**, so you can start a dictation hands-free. It listens
  locally, arms for a few visible seconds, and shows you the result before
  it types anything. The one network moment is a ~7 MB model download the
  first time you turn it on.
- **Languages.** Pin any of Whisper's ~99, for dictation, meetings, and
  imports alike, and teach it your own spoken symbols (say "double colon",
  get `::`).
- **Send to Slack.** A meeting's digest or follow-up draft can post to a
  Slack incoming webhook, but only after you approve that exact message.
  What you see in the preview is what gets posted, byte for byte.
- **Import what you already have.** Drop in recordings or transcript files
  (`.vtt`, `.srt`, `.txt`, timestamps and speaker names preserved) and they
  run through the same meeting pipeline as a live capture. The archive is
  searchable and filterable.

Everything new is off until you turn it on. The local modes stay local;
the network features (the wake-word model download, Slack export, a remote
LLM endpoint) are explicit choices you make, and nothing takes an outbound
action without you approving it first.

Install: `pip install holdspeak`, then `holdspeak doctor`.

This is still 0.x: features work, but config and defaults may move before
1.0, so upgrades back your database up before touching it. Full notes are
in
[CHANGELOG.md](https://github.com/karolswdev/HoldSpeak/blob/main/CHANGELOG.md).

---

## 2. Show HN

**Title:** Show HN: HoldSpeak – local voice dictation and meeting notes, you bring the model

**Body:**

I kept wanting one tool for two related jobs: dictation that types into my
editor and routes the rough speech into something a coding agent can use,
and meeting recording that ends in decisions and action items rather than
another transcript I never open. And I wanted both to run on a model I
control. So I built HoldSpeak.

Hold a hotkey, talk, and it types into the focused app. Turn on the
pipeline and it routes what you said by intent, grounds it in the project
you are in, and rewrites it for where it is going. Every dictation is
recorded with what you said, what it typed, and where it sent it, so when
it gets something wrong you fix it once and can replay the old utterance to
watch the routing change. That is the part I am most attached to: you see
it improve instead of being told it did.

Transcription is local Whisper. The LLM is whichever backend you point it
at: in-process GGUF, MLX, or an OpenAI-compatible endpoint, so a box on
your own LAN is a supported path. Worth being precise, since people here
will check: the local modes are local, but Slack export and a remote
endpoint are real network use you opt into, and `holdspeak doctor` tells
you when a cloud endpoint is configured.

What it is not: it is 0.x and a little rough. The smart parts need a model
you supply. Setup is more involved than a menu-bar app. There is no Windows
build, and on Wayland the global hotkey is best-effort. Next to
superwhisper, MacWhisper, or VoiceInk, the differences are that it is built
for local and self-hosted inference and there is a whole meeting side. Next
to Wispr Flow or Aqua Voice, your audio is not going to a service and there
is no subscription. Talon is far better than this if what you want is
hands-free control of the machine; HoldSpeak is aimed at prose.

Python, Apache-2.0, macOS and Linux. `pip install holdspeak`, then
`holdspeak doctor`. <REPO_URL>

Two questions I would genuinely like answers to: does one tool covering
both dictation and meetings make sense to you, or are those two different
products in a trenchcoat? And is bring-your-own-model too much friction to
bother with?

---

## 3. lobste.rs

**Title:** HoldSpeak: local voice dictation and meeting notes, bring your own LLM

**Tags:** audio, privacy, python, release

**Body:**

I tagged v0.3.0 of HoldSpeak, a local dictation and meeting-notes tool.
Two modes: hold a key and it types your speech into the focused app
(optionally routing and rewriting it for a coding agent or terminal
first), and meetings come back as decisions, action items, and open
questions with a digest of what is still unresolved across them.

The default path is local: Whisper runs on-device, and the LLM backend can
be a local GGUF, MLX, or an OpenAI-compatible endpoint (a LAN box counts).
That last option can point at a cloud service if you choose, so the precise
claim is local-by-default, not local-only. Dictations are journaled and
correctable, and you can replay one through the updated pipeline to see the
routing change rather than trust that it did.

It is honestly 0.x and aimed at people who will read a config file and run
their own model. macOS and Linux, Apache-2.0. The README has trade-off
comparisons with superwhisper, MacWhisper, VoiceInk, Wispr Flow, Aqua
Voice, and Talon, including the cases where the other tool wins.

`pip install holdspeak`. <REPO_URL>

---

## 4. r/LocalLLaMA

**Title:** HoldSpeak v0.3.0: voice dictation and meeting notes that run on your own LLM endpoint

**Body:**

If you already have a local or LAN model running, this is built to point at
it.

HoldSpeak does two things: types your speech into the focused app from a
hotkey (and can rewrite the rough version for a coding agent using your
model), and turns meetings, live or imported, into notes and a running list
of open items. Whisper is on-device and the LLM is whichever backend you
configure: in-process GGUF, MLX, or any OpenAI-compatible endpoint.
Pointing it at your own llama.cpp, Ollama, or vLLM server is the intended
setup, and `holdspeak doctor` will tell you whether it can actually reach
the endpoint and model you configured.

No HoldSpeak account, no app telemetry. The network behavior is meant to be
visible rather than taken on faith: local backends stay local, and doctor
calls out when you have a cloud endpoint configured.

New in 0.3.0 if you saw an earlier version: a local wake word that previews
before it types, ~99-language transcription, Slack export for meeting
digests behind an approval step, and importing recordings or transcripts
you already have.

I have mostly run it against `<tested model/backend>`; curious what people
here would put behind it instead, and whether the intent-routing rewrite
earns its place for dictation or just gets in the way.

0.x, macOS and Linux, Apache-2.0. `pip install holdspeak`, then
`holdspeak doctor`. <REPO_URL>

---

## On the demo GIF

Skipped, deliberately. The moment worth showing is speaking and watching
text land in a real editor, which is a one-take screencast with real audio.
A staged or sped-up fake would be less useful than the real thing, and the
README already carries real product screenshots. A screencast is a good
thing to record by hand when there is a quiet minute.

## What Codex flagged (incorporated)

A second-pass review (`codex exec`, feedback in
`/tmp/codex-fdb-human-starterkit.md`) caught the load-bearing problem: the
first draft overclaimed "nothing leaves your machine" while the release
ships Slack export, a model download, and remote-endpoint support. That is
now precise everywhere (local-by-default, not local-only). Also cut on its
advice: "typed artifacts", "local by construction", "meeting-intel egress",
and most repeated uses of "copilot" (kept once, in the canonical lead, per
the owner's positioning decision). The `<tested model/backend>` placeholder
in the r/LocalLLaMA post is left for the owner to fill with a real setup or
cut, rather than invent one.
