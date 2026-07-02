# Evidence — HS-73-02 — The arrival: the Desk is the front door

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **`/` IS the Desk.** `index.astro` mounts the island under a new
  `immersive` AppLayout prop (no TopNav — the island renders its own
  compact chrome; `main` is full-bleed; every shell widget still mounts).
  Phase 70's orientation Home is retired; its two duties live on:
  - **The first-run guard, verbatim**: the same inline early script
    (`/api/setup/status` → `/welcome` on `first_run`, `/setup` on
    blocked), running before the island mounts.
  - **The guiding empty state** (`EmptyDesk`): a fresh desk answers "what
    is this" in the world's own voice — the wordmark, the POSITIONING
    short form ("Hold a key, speak, it types. Record a meeting, it closes
    the loop." — the tagline tier; the egress badge carries the trust
    answer, so no privacy sentence), and two next-action chips.
- **The chrome** (`DeskChrome`): top-left the HoldSpeak mark opening a
  compact menu of the rooms (Dictation, Meetings, Studio, Settings —
  keyboard reachable), the hub dot (live/degraded/connecting), and the
  canonical egress badge (the faithful port of the Alpine
  `egressBadge()` over `/api/setup/status` trust). Top-right the create
  chips (`+ Note / + KB / + Agent / + Zone`, wired to instant-create —
  the strict subset HS-73-03 extends with the in-world editor + beat) and
  Tidy/Refresh. Bottom: ONE whispered hint.
- **Routes**: `/desk` → 307 redirect to `/` (old links land on the front
  door); the frozen Alpine desk moved to `/desk-legacy` (out of nav,
  deleted in HS-73-08); `/desk-next` retired. Pre-flight updated; API
  manifest regenerated.
- **Nav on the other pages**: the first door's label is **Desk** (`/`);
  the Studio tier drops its separate Desk row (the front door now; the
  studio card points home).

## Verification artifacts (Playwright against the real app, scratch DB)

- **The guard, both ways**: a fresh profile loading `/` landed on
  `/welcome` (asserted); after marking the real first-dictation milestone,
  `/` stays and renders the world.
- **The empty state**: `.desk-empty` present with the canonical line;
  screenshot `02-arrival-empty.png`.
- **The populated arrival**: full-bleed (TopNav asserted ABSENT), 4
  floating objects + the zone tray, the menu opens with exactly the 4
  rooms; screenshot `02-arrival-world.png` — the egress badge honestly
  showed this machine's real configured endpoint during the run.
- **Routes**: `/desk` redirected to `/`; `/desk-legacy` still serves the
  frozen Alpine desk. Zero page errors across the whole run.
- `npm run build`: **18 pages**. Manifest regenerated; api-surface +
  pre-flight **7 passed**; full suite **3066 passed, 37 skipped, 0
  failures**.

## Acceptance criteria — re-checked

- [x] `/` is the Desk, full-bleed, immersive chrome; shell widgets mount.
- [x] The first-run guard ports first and is proven both ways.
- [x] The guiding empty state answers "what is this" (in-world, not a page
      of copy).
- [x] Old links survive (`/desk` → `/`); the legacy desk stays reachable
      until the cutover; nav reshaped (Desk is the first door).

## Deviations from plan

- The nav is a compact always-visible cluster (mark + menu) rather than an
  auto-hiding TopNav overlay: simpler, keyboard-honest, and closer to the
  iPad's actual grammar (a small fixed mark, not a hidden bar). The
  auto-hide idea from the scaffold added state for no felt gain.
- The create chips ship WIRED (instant-create + refresh) rather than
  disabled — a strict subset of HS-73-03's behavior, not throwaway work.

## Follow-ups

- HS-73-03 turns instant-create into create-in-world (editor + NEW beat).
- `/welcome`'s closing copy still says it lands on Home — HS-73-09 (docs)
  sweeps the entry points.
