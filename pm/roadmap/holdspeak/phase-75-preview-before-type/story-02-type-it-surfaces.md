# HS-75-02 — Type it / Discard on the cockpit and the desk

- **Status:** done
- **Severity:** HIGH
- **Depends on:** HS-75-01
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## What

(See the phase status doc's exit criteria row for HS-75-02 — the scaffold
keeps the contract there; this file carries the build notes and the Done
record.)

## Test plan

- Story-specific tests per the exit criteria row; the full suite green at
  ship; every proof read, not assumed.

## Done

Shipped as ONE shell surface (the QueueHud idiom): PreviewCard mounts in
AppLayout so the armed preview is visible on every route — the desk, the
cockpit, everywhere — which supersedes both the desk-island card and a
Qlippy mirror (Qlippy is double-gated and cannot be the unconditional
home). Type it consumes the server-minted token through the real route;
Discard and Escape burn it; the primary takes focus on arrival; a 404
settles quietly; failures show an honest inline error; the badge is the
only trust copy. Proven on / and /dictation with real broadcasts and a
capturing store; two screenshots; zero page errors. See
[evidence-story-02.md](./evidence-story-02.md).
