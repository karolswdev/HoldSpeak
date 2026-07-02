# HS-73-09 — Docs + the locks (the docs story)

- **Status:** done
- **Priority:** MED (the phase's dedicated docs story — after features, before closeout)
- **Depends on:** HS-73-01 … HS-73-08
- **Evidence:** [evidence-story-09.md](./evidence-story-09.md)

## Goal

Document the inhabited desk, the desk-first IA, and the stack decision —
and **lock the two owner rules mechanically** so they cannot return to this
surface. Phase 71 shipped banned prose and banned modals onto `/desk`
because nothing mechanical stopped it; after this story, something does.

## Scope

- **In:** `docs/WEB_DESK.md` rewritten; the stack decision + standing rule
  recorded in `docs/ARCHITECTURE.md` (and the web architecture doc if one
  exists); POSITIONING updated for desk-first; the no-prose and no-modal
  locks; entry points; refreshed screenshots.
- **Out:** HS-IDs in `docs/*.md` (the voice guard rejects them — reference
  phases by name); user-guide rewrites beyond the desk + arrival.

## Tasks

- [ ] Rewrite `docs/WEB_DESK.md` for the inhabited desk: arrive at `/`,
      create in place, open the pull-out, record from the orb, run from
      the rail, file/dive, Tidy, "Open full" as the one exit. Short,
      task-shaped, screenshots from the closeout walk.
- [ ] Record the stack decision where the next contributor will look:
      `docs/ARCHITECTURE.md` (or its web section) states the rule —
      interactive surfaces are React + Vite islands (`web/src/desk/` is
      the pattern); document pages stay Astro; **no new Alpine**;
      `/history`/`/live` migrate in a future phase. Update the component
      map diagram if it names the frontend stack (mermaid guard green).
- [ ] POSITIONING: the web-surface section leads with the Desk as the main
      surface (owner decision, 2026-07-02); the Phase-70 four-door
      paragraph amended. Dash-free, canonical names, voice guard green.
- [ ] **The no-prose lock:** extend the Phase-62 banned-copy lock (find
      the tests that REFUSE the old privacy prose — grep `tests/` for the
      banned phrases) with a desk-scoped check over `web/src/desk/**`:
      no sentence-like rendered string literals (heuristic: multi-clause
      strings with `. ` + a denylist — "first-class", "your desktop hub",
      "Saves to", "nothing leaves"). Prove it fails on the deleted
      Phase-71 lead paragraph (scratch run, captured, reverted).
- [ ] **The no-modal lock:** a test asserting zero `aria-modal` /
      `role="dialog"` under `web/src/desk/**` (the shell ConfirmDialog
      lives outside the desk tree and stays exempt).
- [ ] Entry points (the Phase-64 lesson): the docs index, `README.md`'s
      surface tour (it must now say the Desk is the web's front door),
      GETTING_STARTED's first-web-visit description, and `/welcome`'s
      closing copy — all consistent with arriving in the world.

## Proof required

Voice/doc/mermaid guards green; both locks green AND proven red on the old
copy (captured output); the docs diffs; refreshed screenshots committed;
full suite green.

## Done

Shipped. GETTING_STARTED's arrival section and route table speak the Desk
(the Phase-64 entry-point lesson applied; README/welcome/ARCHITECTURE
checked and already true). The rules are tests now:
tests/unit/test_desk_locks.py locks no-dialog-takeovers, no-browser-mic,
no-privacy-narration (setup.ts the single badge-string home), the bare
hs.diorama.pos contract (persist middleware banned), and the
Desk-as-front-door with the inline guard. Locks 5/5; doc guards 85 passed
on the updated prose; full suite 3071 passed (3066 + the 5 locks), 37
skipped. See
[evidence-story-09.md](./evidence-story-09.md).
