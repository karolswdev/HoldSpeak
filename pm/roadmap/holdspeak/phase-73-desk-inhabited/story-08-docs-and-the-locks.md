# HS-73-08 — Docs + the locks (the docs story)

- **Status:** todo
- **Priority:** MED (the phase's dedicated docs story — after features, before closeout)
- **Depends on:** HS-73-01 … HS-73-07

## Goal

Document the inhabited desk, and — more important — **lock the two owner
rules this phase enforced so they cannot return to this surface.** Phase 71
shipped banned prose and banned modals onto `/desk` because nothing
mechanical stopped it; after this story, something does.

## Scope

- **In:** `docs/WEB_DESK.md` rewritten; POSITIONING's desk paragraph
  updated; the no-prose lock extended to the desk; the no-modal lock
  created; screenshots in docs refreshed; entry points touched.
- **Out:** HS-IDs in `docs/*.md` (the voice guard rejects them — reference
  phases by name); any feature docs beyond the desk.

## Tasks

- [ ] Rewrite `docs/WEB_DESK.md` for the inhabited desk: arrive, create in
      place, open the pull-out, record from the orb, run from the rail,
      file/dive on zones, Tidy, "Open full" as the one exit. Short,
      task-shaped, screenshots refreshed from the closeout walk.
- [ ] Update POSITIONING's web-desk paragraph (it currently describes the
      Phase-71 renderer port) — the desk is now the web's in-world
      authoring surface, same grammar as the iPad DeskOS. Dash-free,
      canonical names, voice guard green.
- [ ] **The no-prose lock:** find the Phase-62 banned-copy lock (the tests
      that REFUSE the old privacy prose — grep `tests/` for the banned
      phrases) and extend it with a desk-scoped check: `desk.astro` +
      `components/desk/*` + `scripts/desk/*` may not contain sentence-like
      UI strings (heuristic: rendered string literals with `. ` +
      trailing-period multi-clause text, plus an explicit denylist —
      "first-class", "your desktop hub", "Saves to", "nothing leaves").
      Prove it fails on the deleted Phase-71 lead paragraph (paste it into
      a scratch run, watch it fail, revert).
- [ ] **The no-modal lock:** a test asserting zero `aria-modal` /
      `role="dialog"` occurrences under the desk source tree (the shell
      ConfirmDialog lives in AppLayout, outside the desk tree — the lock
      scopes to `components/desk/`, `scripts/desk/`, `pages/desk.astro`).
- [ ] Entry points (the Phase-64 lesson): the docs index line for the
      Desk, the Home "The Desk →" entry copy (label-style), and
      `README.md`'s surface tour if it names the desk — all consistent
      with the new grammar.

## Proof required

Voice/doc guards green; both new locks green AND proven red on the old
copy (captured scratch-run output); the docs diff; refreshed screenshots
committed; full suite green.
