# Changelog

All notable changes to HoldSpeak are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Pre-release.** HoldSpeak has not been formally released or published to PyPI.
> Everything below is **Unreleased** — install from source. Version `0.2.1` in
> `pyproject.toml` is an in-development marker, not a published tag.

## [Unreleased]

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
