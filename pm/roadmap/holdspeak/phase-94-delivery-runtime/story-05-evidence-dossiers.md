# HS-94-05 — Evidence dossiers and safe asset browsing

- **Project:** holdspeak
- **Phase:** 94
- **Status:** backlog
- **Depends on:** HS-94-01, HS-94-02, HS-94-03
- **Unblocks:** HS-94-08, HS-94-09

## Problem

The Desk exposes an `evidence_exists` check and raw Markdown for current-phase
Stories. It cannot browse prior phases, final summaries, screenshots, JSON
walks, logs, captured-run structure, or remote evidence. One configured
self-hosted repository is refused by the current path check.

## Scope

- In:
  - hub evidence manifest cache and authorized asset proxy;
  - Delivery Workbench manifest as sole membership/path authority;
  - story spec, evidence Markdown, captured runs, phase status/final summary;
  - safe PNG/JPEG/WebP, JSON, plain text/log, Markdown, and bounded video support
    if present in the accepted manifest;
  - MIME/extension/content sniff, byte caps, range requests, hash/ETag;
  - sanitized Markdown rendering with relative asset resolution;
  - committed versus live-uncommitted revision labels;
  - commit/gate/remote-verify/PR/CI receipt join;
  - current and historical Story/Phase browsing;
  - explicit grounding from a dossier using the existing grounding spine;
  - offline remote-asset metadata and recovery.
- Out:
  - arbitrary repo file browser;
  - recursive repository download;
  - deriving delivery status from evidence body;
  - automatic background download of every asset;
  - editing evidence from HoldSpeak.

## Acceptance criteria

- [ ] Standard, self-hosted, local worktree, and remote-node evidence manifests
      open through one API and view.
- [ ] Evidence Markdown is readable and safe; its manifest assets open inline or
      download/preview according to type; inert relative links are eliminated.
- [ ] Passing and failing captured runs are parsed and visibly distinct with
      command, timestamp, exit code, index tree, and bounded output.
- [ ] A Phase dossier groups every Story dossier and final summary without
      loading every asset eagerly.
- [ ] Asset path traversal, symlink escape, unsupported MIME, oversize file,
      hash mismatch, and changed bundle all refuse by typed reason.
- [ ] Node offline leaves manifest metadata visible and asset state unavailable,
      not missing.
- [ ] Raw node/repo paths never reach the browser/native payload.
- [ ] A chosen evidence member grounds a steer through the existing capped,
      provenance-labeled grounding contract.

## Test plan

- manifest and asset authorization;
- path/symlink/MIME/size/hash/range/ETag cases;
- Markdown sanitization and relative links;
- standard/self-hosted/worktree/remote fixtures;
- offline/change-mid-read recovery;
- rendered Web desktop/compact and native fixture;
- grounding byte/cap/provenance parity.

## Implementation direction

- Cache manifests by bundle/source revision; stream bytes, do not read an
  unbounded file into memory.
- Generate thumbnails deliberately or render originals within browser limits;
  never mutate source evidence.
- Keep GitHub receipts optional and independently stale.
- Use semantic sections and keyboard/touch navigation; no modal-only gallery.
- Attach the dossier to Project/Story/Phase objects and Receipts, not only the
  compatibility conveyor.

## Evidence required

- gallery capture with Markdown, pass/fail runs, PNG, JSON, log, and final summary;
- standard/self-hosted/remote fixture manifests;
- crown-case refusal matrix;
- offline-node asset state;
- grounded steer preview naming the dossier member.
