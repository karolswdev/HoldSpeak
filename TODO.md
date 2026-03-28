# HoldSpeak TODO

This file is the current working roadmap for making HoldSpeak more unique, useful, and professional.

## Current Snapshot

HoldSpeak already has a solid functional base:

- Voice typing with hold-to-talk interaction
- Cross-platform TUI for voice typing and meeting control
- Meeting mode with mic + system audio capture
- Live transcript streaming
- Per-meeting web dashboard
- Meeting history and action item browsing
- Optional local-model meeting intelligence
- Deferred intelligence queue when no suitable local model is available

## Completed So Far

- [x] Built the core voice typing flow for macOS and Linux
- [x] Added punctuation commands and clipboard insertion
- [x] Added meeting mode with dual-stream capture
- [x] Added live meeting transcript handling with speaker labels
- [x] Added local LLM meeting intelligence for topics, action items, and summaries
- [x] Added a browser-based live meeting dashboard
- [x] Added meeting history and cross-meeting action item browsing
- [x] Added meeting metadata editing and exports
- [x] Added speaker diarization and cross-meeting speaker identity groundwork
- [x] Redesigned the web dashboard to feel more product-grade
- [x] Redesigned the history page to match the dashboard visual system
- [x] Added explicit intelligence status states in the web UI
- [x] Added deferred intelligence queue persistence and background processing
- [x] Updated the screenshot pipeline for web and TUI captures
- [x] Refreshed README and meeting-mode docs to reflect the new UI and intel behavior
- [x] Added tests covering DB persistence and deferred-intel session behavior

## Immediate Next Steps

- [ ] Make the TUI itself look as strong as the new web dashboard
- [ ] Add explicit intel status to the TUI, not just the web dashboard
- [ ] Productize the deferred-intel queue with manual retry and visibility in history
- [x] Add a CLI command to process queued meeting intelligence on demand
- [ ] Ensure deferred-intel workers also run in non-TUI entry points where appropriate
- [ ] Add integration tests for deferred-intel queue lifecycle
- [ ] Add screenshot generation instructions and dependency setup to docs
- [ ] Decide which screenshots are canonical for README, docs, and release materials

## Product Priorities

### 1. Make The TUI Worth Showing Off

- [ ] Replace the current flat terminal chrome with clearer hierarchy and stronger composition
- [ ] Improve the main voice-typing screen so it does not look empty when idle
- [ ] Improve the meeting cockpit so transcript and intel feel denser and more legible
- [ ] Improve modal layouts so screenshots do not look cramped or clipped
- [ ] Add more intentional sample states for screenshots and demos

### 2. Make Intelligence Reliable Instead Of Fragile

- [x] Add a first-class `holdspeak intel` command for queue inspection and processing
- [ ] Add job states such as queued, running, ready, failed, stale
- [ ] Re-run queued jobs automatically when the transcript revision changes
- [ ] Add better fallback messaging when llama-cpp or the model file is missing
- [ ] Surface queue state in history lists and meeting detail views
- [ ] Add a path for final-only intelligence when realtime inference is too expensive
- [ ] Add settings for lightweight model vs final-summary model

### 3. Make The App More Useful Day To Day

- [ ] Improve transcript search from simple text matching toward semantic search
- [ ] Let users jump from action items back to the exact transcript moment
- [ ] Add richer exports: markdown meeting notes, action item summaries, shareable recap
- [ ] Add auto-title quality improvements and manual title suggestions
- [ ] Add meeting templates or tags for recurring workflows
- [ ] Add saved speaker aliases and better speaker naming flows

## What Could Make HoldSpeak Truly Unique

### 4. Personal Meeting Memory

- [ ] Build a cross-meeting memory layer that can answer:
- [ ] What did we decide last time?
- [ ] What open actions still belong to me?
- [ ] When did this topic first come up?
- [ ] Which speaker usually owns this workstream?

### 5. Action Follow-Through, Not Just Extraction

- [ ] Turn action items into a lightweight personal task inbox
- [ ] Add statuses beyond pending/done/dismissed when the model or UI justifies it
- [ ] Add due-date review surfaces and overdue grouping
- [ ] Add “created from meeting” provenance everywhere
- [ ] Add meeting-to-meeting rollups so action items do not disappear after extraction

### 6. Meeting Preparation And Aftercare

- [ ] Generate pre-meeting briefings from prior meetings with the same tags or speakers
- [ ] Generate post-meeting recap packets optimized for sending to other people
- [ ] Add “What changed since the last meeting?” summaries
- [ ] Add decision logs separate from generic summaries

### 7. Voice Typing That Feels Smarter Than Dictation

- [ ] Add user-defined spoken macros for repeated phrases and workflows
- [ ] Add app-aware text actions where platform support makes sense
- [ ] Add rewrite modes such as concise, polished, email-ready, note-ready
- [ ] Add correction loops for “replace last phrase” or “undo last insertion”

## Professionalization Work

### 8. Operational Quality

- [ ] Tighten install flows for Linux and meeting dependencies
- [ ] Expand `holdspeak doctor` so it checks model availability and deferred-intel readiness
- [ ] Add release checklists for screenshots, docs, and dependency verification
- [ ] Add a clearer versioned changelog
- [ ] Add more integration coverage for web dashboard state transitions
- [ ] Add failure-mode tests for missing model, missing websockets backend, and queue recovery

### 9. Documentation And Demo Quality

- [ ] Keep screenshots reproducible and scripted
- [ ] Add a dedicated docs page for deferred intelligence behavior
- [ ] Add one “recommended setup” guide for users with no local model
- [ ] Add one “best quality local setup” guide for users with a capable machine
- [ ] Refresh the demo assets so they reflect the current UI instead of older screens

## Recommended Execution Order

- [ ] P0: TUI visual pass and better TUI screenshots
- [ ] P0: Queue management command and queue visibility in history/detail views
- [ ] P0: Deferred-intel integration tests and failure handling
- [ ] P1: Action follow-through improvements
- [ ] P1: Cross-meeting memory and better recall/search
- [ ] P1: Pre-meeting and post-meeting workflow features
- [ ] P2: Smarter voice-typing workflows and rewrite features

## Definition Of Done For “Professional”

- [ ] The TUI and web UI look like the same product
- [ ] Screenshots can be regenerated by script without manual cleanup
- [ ] Missing local-model capability no longer feels like a broken feature
- [ ] History and action tracking remain useful even without realtime intelligence
- [ ] New users can install, diagnose, and understand the product without source-diving
- [ ] The README shows the best surfaces of the app, not the most convenient ones to capture
