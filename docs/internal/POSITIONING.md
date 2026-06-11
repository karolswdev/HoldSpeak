# HoldSpeak positioning canon

This document fixes what HoldSpeak's story is. Every user-facing doc (the
root `README.md` and the top-level `docs/*.md`) aligns to it; future docs
stories are measured against it. If a user-facing doc disagrees with this
canon, one of them is wrong on purpose and the disagreement must be
resolved, not ignored. The three load-bearing decisions below were made by
the project owner directly (2026-06-11) and are not up for relitigating in
a docs pass.

## The one-liner

> **One local copilot, two modes: dictation that types anywhere and learns
> how you work, and meetings that end with decisions, actions, and
> follow-ups instead of a recording. Nothing leaves your machine.**

Short form (taglines, social, `pyproject` description tier):
*"Hold a key, speak, it types. Record a meeting, it closes the loop. All
local."*

### Decision 1: the lead angle is "one copilot, two modes"

The pitch leads with breadth: HoldSpeak is one tool spanning the two
places a developer's voice does work, the keyboard and the meeting.
Privacy and the learning loop are pillars, one rung below the lead; they
support the headline rather than being it.

### Decision 2: the audience is developers

GitHub-native, terminal-comfortable, self-hosting, privacy-aware. Docs may
assume a shell, a config file, and the ability to run a local model or
point at an endpoint. Write for someone who will read the code if the doc
is wrong.

### Decision 3: comparisons name names, honestly

The README carries an explicit comparison section naming real tools, with
trade-offs stated in both directions, date-stamped so staleness is visible.
A comparison that hides the other tool's strengths is a lie of omission and
does not ship.

## The pillars (each claim has shipped proof behind it)

1. **Everything local, including the intelligence.** Whisper runs on your
   machine; the LLM is yours (GGUF in-process, MLX on Apple Silicon, or
   any OpenAI-compatible endpoint you point at, including one on your own
   LAN). No account, no telemetry, no cloud dependency in the product.
   *Proof points:* the models contract (`docs/MODELS.md`); the egress
   posture (`docs/SECURITY.md`); the server refuses non-loopback binds
   without an auth token; secret-shaped text is filtered before storage.
2. **It learns how you work, and shows you the receipts.** Every dictation
   is journaled (said, typed, route, latency). One tap teaches a
   correction; the learning digest reports "learned from N similar" using
   the same matcher that nudges routing, honest at zero; replay re-runs an
   old utterance through the updated pipeline so improvement is observed,
   not promised.
   *Proof points:* the dictation journal, the correction memory, the
   learning digest, replay (typing guide §12).
3. **Meetings end with their loops closed.** Live capture (mic + system
   audio, speaker labels) or import (recordings, and transcript files
   with their real timestamps and speaker names). Fourteen LLM-backed
   plugins turn the transcript into typed artifacts; meeting aftercare
   shows what is open, decided, and changed; an accepted action can become
   a filed issue through a propose-approve-execute flow that never acts
   without per-action human approval.
   *Proof points:* the meeting plugins, actuators (off by default,
   audited, executed == previewed), meeting aftercare, meeting import,
   faceted archive search.
4. **Honest by construction.** The product states its own limits where you
   meet them: the doctor reports what is actually broken, the import panel
   says which timestamps are approximate, the learning digest never
   inflates a count, upgrades back your database up before touching it and
   refuse downgrade-unsafe opens. The docs hold themselves to the same
   bar.
   *Proof points:* `holdspeak doctor`, the schema policy + backup/restore
   (`docs/RELEASING.md`), the honest-copy locks in the test suite.

## The competitive frame (as of mid-2026; architecture-level on purpose)

Feature lists churn; architecture does not. Comparisons stay at the level
of where the audio goes, what the tool spans, and whether it learns.

| Tool / category | What they do better | What HoldSpeak does better | Pick them if |
|---|---|---|---|
| **OS dictation** (Apple Dictation, Windows Voice Typing) | Zero setup, free, always there | Your own models, the learning loop, routing to targets, meetings | You dictate occasionally and trust the OS vendor |
| **Local Whisper menu-bar apps** (superwhisper, MacWhisper, VoiceInk) | Simpler setup, polished single-purpose UX | Fully local LLM rewriting (their AI modes often call cloud APIs), the visible learning loop, meetings, Linux | You want frictionless local transcription on a Mac and nothing else |
| **AI dictation services** (Wispr Flow, Aqua Voice) | Strong out-of-box accuracy and editing UX, no model management | Everything stays local, open source, no subscription, meetings | You are fine with your voice in their cloud in exchange for polish |
| **Talon** | The deepest hands-free coding and grammar control there is; mature ecosystem | Prose-first dictation with LLM rewriting, the learning loop, meeting intelligence; lower learning curve | You need full hands-free computer control (accessibility, RSI) |
| **Raw Whisper tooling** (whisper.cpp, faster-whisper scripts) | Total control, minimal surface | A product: typing integration, routing, journal, meetings, a web UI | You enjoy building your own pipeline |

HoldSpeak's honest trade-offs, stated wherever the comparison is made: it
is 0.x (APIs and defaults still move); the smart parts need a local model
or an endpoint you provide; setup is heavier than a menu-bar app; it is
macOS and Linux only (no Windows today); Wayland limits global hotkeys to
best-effort.

## Canonical feature names

One name per surface, used identically in every user-facing doc. The
left column is the name; do not alternate with the synonyms.

| Canonical name | Not |
|---|---|
| voice typing | "basic dictation", "simple mode" |
| the dictation pipeline | "intelligent typing", "DIR" (user-facing), "smart dictation" |
| target profiles | "destinations", "apps" |
| the dictation journal | "the history tab", "the log" |
| the correction memory | "the memory", "corrections store" |
| the learning digest | "What HoldSpeak learned" is its on-screen title; "the digest" after first use |
| replay | "re-run", "retry" |
| voice commands | "macros", "voice macros" |
| activity pre-briefing | "nudges" (the cards are "nudge cards") |
| meeting intelligence | "meeting AI", "intel" (user-facing) |
| meeting plugins | "analyzers", "extractors" |
| actuators | "actions" (an actuator *proposes* an action) |
| meeting aftercare | "follow-up panel", "next moves" |
| meeting import | "upload", standing alone |
| the archive | "/history" is the route; the surface is "the archive" |
| desktop presence | "the HUD" after first use is fine |
| Qlippy, the mascot | "the assistant", "the agent" |
| the spoken-symbol dictionary | "custom symbols", "symbol macros", "vocabulary" |
| the spoken language setting | "language mode", "locale" |
| AIPI-Lite | "the companion device" after first use |

## Voice rules (the editing standard for every user-facing doc)

- **The humanizer standard applies** (the vendored skill): no AI-vocab
  (delve, seamless, leverage, robust, comprehensive, supercharge…), no
  rule-of-three padding, no negative-parallelism tics ("it's not just X,
  it's Y"), plain copulas over "serves as / boasts", active voice.
- **No em or en dashes in prose.** Use periods, commas, colons, or
  parentheses. Code blocks and quoted UI strings are exempt.
- **The honesty bar:** every claim is backed by a shipped capability a
  guide or test can point to; superlatives without proof points do not
  ship; limits are stated next to the strengths they qualify; comparisons
  credit the other tool.
- **Ledes sell the why.** Every guide opens with one or two sentences on
  why the feature exists and what the reader gets, before any mechanics.
- **Developer register.** Direct, technical, unafraid of a config snippet;
  never corporate, never breathless.

## Maintenance

Revisit the comparison table when a named tool materially changes
architecture (goes local, adds meetings, opens source) and at every
release-readiness pass. The canonical-name table grows one row per new
user-facing surface, in the phase that ships it.
