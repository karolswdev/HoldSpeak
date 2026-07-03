# Changelog

All notable changes to HoldSpeak are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **0.x, early but real.** HoldSpeak is published on PyPI (`pip install
> holdspeak`). APIs, config, and defaults can still change while it is pre-1.0;
> upgrades are safe by default (your database is backed up first).

## [Unreleased]

### Added
- **File an issue from the iPad.** The companion's meeting aftercare card
  can turn an accepted action item into a GitHub-issue proposal (repo
  typed inline, remembered for the session). Filing only records a
  proposal you approve separately — same consent model as the web.
- **Search and filter meetings from the iPad.** The companion's desktop
  archive gains transcript search and the speaker/tag facet chips the web
  has had since 0.2 — narrowing happens on the desktop, so the list is
  never a stale page filtered locally.
- **Review proposals from the iPad.** A meeting's actuator proposals —
  wherever they were created — show as a queue on the companion with
  Approve/Reject on pending ones and honest decided/executed/failed
  states. Approving a Slack send executes immediately, so that control
  carries the cloud mark. iPad decisions are now attributed as
  `ipad-companion` in the actuator audit.
- **The Desk is the web front door.** Opening HoldSpeak lands on a spatial
  world at `/`: meetings, notes, knowledge bases, agents, and artifacts as
  objects you create, open, file, and arrange in place. The Record orb
  drives the hub recorder; the agent rail runs personas. (`/desk`
  redirects home; the previous orientation Home is retired.)
- **Run results persist.** An agent, chain, or workflow run saves its
  output as an artifact with lineage naming the capability that made it;
  the artifact lands on the Desk and syncs like any other. Runs also
  report honest progress frames to the UI. (Database schema v6; upgrades
  back the database up first, as always.)
- **Preview before it types** (Settings, Voice; off by default): a
  finished dictation shows its text on a card first, on every page. Type
  it commits; Discard drops it.
- Artifacts now say where they came from on every API surface: an
  `origin` field (`meeting` or `run`) rides sync pull and the meeting
  artifacts route, so clients no longer infer a run's output from an
  empty meeting id.
- Remote dictation can deliver verbatim: `raw: true` on
  `/api/dictation/remote` types exactly the given text, skipping the
  pipeline and macro dispatch. For companion clients that previewed a
  dry-run receipt — what previewed is what types. Without the flag the
  route behaves exactly as before.

### Fixed
- The dictation intent router works with more OpenAI-compatible models.
  The classify prompt's only example of `extras` was a per-block table, so
  a model that mirrored that nesting back was rejected, and a model that
  honestly answered "no match" with a null block id was rejected too. The
  hint now states the flat output shape, the validator unwraps the nested
  reading, and an honest no-match passes through. Measured live: a model
  that failed the classify five out of five times now runs five for five.
- "Dictate with this" now grounds remote dictations too. The activity
  nudge's selected record was consumed by the local dictation path but
  silently ignored on `/api/dictation/remote`; the remote lane now folds
  the selected record into the rewrite context the same way, one-shot.
- The preview card no longer renders as an empty box on pages with no
  armed preview.
- The settings loader no longer silently drops the preview toggle on
  restart.
- The `/api/settings` boundary, the artifacts store, and the sync pull
  gained coverage for all of the above.

## [0.3.1] - 2026-06-13

Documentation. No runtime change from 0.3.0.

### Added
- **An architecture map** (`docs/ARCHITECTURE.md`): the runtime view of how
  the pieces fit and how a single utterance flows through them, with
  rendered diagrams for the component map, the dictation and meeting
  pipelines, the learning loop, the device path, and the trust boundary.
  Linked from the docs index, the README, and CONTRIBUTING.
- A docs guard that renders every Mermaid diagram and fails on any that
  does not, so a broken diagram cannot ship.

## [0.3.0] - 2026-06-13

The first release since 0.2.x, gathering fourteen development phases. Both
modes grew: dictation gained hands-free entry and your language, meetings
gained imports and an outbound door, and the codebase paid down two large
god-objects. Everything below is off by default unless noted, and nothing
acts without your approval.

### Added
- **The wake word.** Say a phrase and HoldSpeak listens hands-free for a
  bounded, visible window, then runs your next sentence through the normal
  dictation pipeline. The result is previewed, never typed, until you
  confirm (typing directly is an explicit opt-in). Local detection
  (openWakeWord); the only network moment is a one-time ~7 MB model
  download on first enable. Measured zero false detections in 57 ordinary
  utterances at the default threshold.
- **Speak your language.** One setting pins any of Whisper's ~99 languages
  for dictation, meetings, and imports (the default auto-detects per
  utterance). Plus the spoken-symbol dictionary: map your own spoken
  phrases to symbols or snippets (`"double colon"` becomes `::`), merged
  over the built-ins.
- **Send to Slack.** The meeting aftercare digest or follow-up draft can go
  to a Slack incoming webhook, on the same propose, approve, execute flow
  as every actuator: the preview is the exact message, and nothing is sent
  until you approve that one send.
- **Voice command macros.** Map a spoken keyword to a real action (open a
  URL, launch an app, run a command, type a snippet) on a dedicated board;
  it fires when you say the keyword while dictating.
- **Activity pre-briefing.** A quiet, source-cited read of what you touched
  recently, above the dictation cockpit; one tap pins a record as context
  for your next dictation. Gated by the activity-tracking toggle.
- **Meeting and transcript import.** Bring recordings (WAV native, others
  via ffmpeg) or transcript files (`.vtt`/`.srt`/`.txt`, keeping their real
  timestamps and speaker names) into the full intelligence pipeline, via
  the web UI or `holdspeak import`. The archive gained server-side facets
  (date, speaker, tag, open actions).
- **Qlippy, the optional presence mascot.** An ambient pixel-art dock and
  one-at-a-time cards for the few moments that need you (an approval, a
  result, something learned, a meeting that left open items). Double opt-in,
  focus-safe, and he never acts on his own.

### Changed
- **Quiet trust.** Cards and notifications now state where data goes with a
  compact egress badge (local, local and cloud, or cloud with the target
  named) instead of repeated privacy paragraphs.
- **The front door.** A positioning canon ("one copilot, two modes"), a
  rewritten README with an honest, named comparison section, and a voice
  guard that holds every user-facing doc to one standard.

### Fixed
- A wake-word-era crash class where a library fault froze transcription,
  and a process-fatal cross-thread transcription path, both fixed during
  the wake-word work.
- The first-run welcome wizard's "copy install command" button (a parsing
  error made it a no-op), the dictation activity page (its script had
  silently failed to load), and the companion page (it threw on first
  paint) — all caught by a new pre-launch route sweep.
- A broken live-meeting-start path and a transcriber-construction race,
  both surfaced and fixed during a large internal decomposition.

### Internal
- The dictation frontend and the `web_runtime` / `meeting_session` backend
  were each decomposed from multi-thousand-line files into single-concern
  modules, behavior-preserving and locked by density guards.

## [0.2.2] - 2026-06-07

### Changed
- README is now PyPI-ready: `pip install holdspeak` is the headline install,
  every image uses an absolute URL so screenshots render on the PyPI project
  page, and every doc link resolves from PyPI. The "isn't on PyPI yet" status
  line is gone.

## [0.2.1] - 2026-06-07

First release published to PyPI, cut after Phase 50 (Release Readiness). The
items below shipped in this release.

### Added
- **Bring-your-own model contract** (`docs/MODELS.md`): GGUF in-process, MLX on
  Apple Silicon, or any OpenAI-compatible endpoint; model names are framed as
  suggestions rather than requirements.
- **Apache-2.0 `LICENSE`** and complete `pyproject` metadata (license, authors,
  classifiers, project URLs, keywords).
- **Documentation index** (`docs/README.md`) and a user-facing vs. internal
  (`docs/internal/`) split; a doc link-check guards against dangling links.
- **Meeting intelligence plugins** — 14 built-in, LLM-backed plugins producing
  reviewable artifacts (architecture diagrams, ADRs, requirements, action items,
  milestones, decisions, risk registers, incident timelines, stakeholder updates,
  and more), rendered read-only in the web UI.
- **Intelligent dictation pipeline** — project-aware intent routing, KB
  enrichment, and LLM rewriting with target-profile adaptation (Codex / Claude /
  terminal / browser / editor).
- **Meeting mode** — dual-stream capture, live transcript with speaker labels,
  AI-extracted topics and action items, deferred-intel queue, and local exports.
- **AIPI-Lite companion** — same-LAN remote audio ingest, device health/initiative
  protocol, and a coding-agent companion UX (first-class firmware + bridge).
- **Web runtime** as the sole interactive runtime, with a "Signal" dark-first UI.
- **Local activity intelligence** — private browser-history-derived work context
  with opt-in connectors and meeting candidates.
- **Trust & hardening** — web-runtime auth + bind guard, no silent cloud egress,
  a security/privacy posture doc (`docs/SECURITY.md`), and a CI core-path smoke
  test (real Whisper on a committed WAV, every push).

### Changed
- Default/example LLM models refreshed to a current small-instruct family and
  de-prescribed throughout user-facing strings.
- Persistence layer decomposed from a single `db.py` god-object into a `Database`
  container + per-domain repositories.
- `web_runtime.py` class-ified (`WebRuntime`); meeting code decoupled from the
  web server.

### Removed
- The Textual TUI and the macOS menu-bar app (the web runtime is now the only
  interactive runtime).

[Unreleased]: https://github.com/karolswdev/HoldSpeak/commits/main
