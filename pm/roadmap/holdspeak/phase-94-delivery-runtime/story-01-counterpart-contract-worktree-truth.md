# HS-94-01 — Counterpart contract and worktree truth

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** Phase 94 activation gates; accepted Delivery Workbench counterpart
- **Unblocks:** HS-94-02, HS-94-05

## Problem

The current integration is contract-shaped but not robust across the locations
the product intends to manage. Delivery Workbench events assume `.git` is a
directory, HoldSpeak evidence containment assumes `pm/roadmap` is directly under
the repo root, events have no version/cursor, and accepted statuses/verbs are
hard-coded on both sides.

Building node transport first would distribute these defects.

## Scope

- In:
  - joint Delivery Workbench capabilities, events, and evidence schemas;
  - git-dir/common-dir behavior defined and fixed for linked worktrees;
  - standard and self-hosted roadmap root resolution;
  - cursor/event IDs with the existing privacy allow-list;
  - evidence manifest/asset CLI contract;
  - accepted status/mutation vocabulary in capabilities;
  - shared fixture pack and compatibility matrix;
  - HoldSpeak provider adapter proven against current v1 and counterpart v2.
- Out:
  - node transport;
  - new Desk UI;
  - changing Delivery Workbench's Markdown or gate;
  - Work attempt semantics.

## Acceptance criteria

- [x] A real `git worktree add` fixture flips a Story, captures evidence, and
      emits cursor-addressable events; no `.git is a directory` assumption
      remains in consumed Delivery Workbench code.
- [x] Evidence manifest resolves a conventional `pm/roadmap` tree and Delivery
      Workbench's `pmo-roadmap/pm/roadmap` self-hosted tree without weakening
      path containment.
- [x] Manifest includes story/evidence/phase/final-summary members, parsed
      captured runs, and safe linked/declared assets with size/MIME/hash.
- [x] Events reject any non-allow-listed content field and carry no prompt,
      transcript, diff, or arbitrary external path.
- [x] `dw capabilities --json` declares schemas, statuses, verbs, and optional
      features; unknown required versions yield typed incompatibility.
- [x] Existing `feed_schema: 1` consumers still pass unmodified.
- [x] Python integration fixtures run against real scratch repositories
      (standard, self-hosted, and linked-worktree layouts) driving the
      vendored dw by subprocess in this repo's suite; the second-repository
      CI leg pinning an upstream counterpart commit is candidate-Y scope
      (upstream adoption).

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the upstream reusable-processes adoption of this contract moves to
[BACKLOG candidate Y](../BACKLOG.md); the vendored dw in this repo is the
operative counterpart and implements it fully.

## Test plan

- Delivery Workbench unit/property tests for git-dir resolution, cursors,
  privacy, manifests, symlink escape, MIME/size, status capabilities.
- HoldSpeak provider contract tests against golden CLI documents.
- Live scratch repo with primary checkout and linked worktree.
- Live self-hosted Delivery Workbench evidence read for a WLA story.
- Regression probes reproducing both failures recorded in the integration
  overview before the fix.

## Implementation direction

- Resolve git paths with git plumbing already used by Delivery Workbench hooks;
  do not parse the `.git` file manually in HoldSpeak.
- Let Delivery Workbench resolve its own roadmap root and manifest paths.
- Version events and evidence independently from `feed_schema`.
- Prefer opaque manifest asset IDs. If the CLI returns local resolved paths to a
  node adapter, those paths never cross the hub client API.
- Keep `dw context` as compatibility/detail, not the new evidence API.
- Record the counterpart version in a machine-readable fixture, not prose only.

## Evidence required

- captured counterpart and HoldSpeak test runs;
- event log from primary and linked worktree;
- manifests from standard and self-hosted trees;
- one refused path/symlink/content-smuggling crown case;
- compatibility output from the current vendored v1.12 rails.
