# HS-73-02 — The arrival: the Desk is the front door

- **Status:** done
- **Priority:** HIGH (the owner's IA decision, landed; plus half the felt gap)
- **Depends on:** HS-73-01
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## Goal

`/` is the Desk. A user who runs `holdspeak web` arrives in the world —
full-bleed, immersive chrome, no document header — and a brand-new user is
neither lost (the guiding empty state answers "what is this") nor stranded
(the first-run guard still routes them to `/welcome`). This story lands the
owner's decision: the Desk is the main surface, "not a shadow of a doubt" —
formally superseding Phase 70's four-door IA.

## Scope

- **In:** the route takeover; the first-run guard port; immersive chrome;
  the in-world chip cluster; the guiding empty state; nav + pre-flight +
  docs-link updates; the old Home's retirement.
- **Out:** the create flows behind the chips (HS-73-03 — chips may
  temporarily no-op to the legacy `/desk` create until 03 lands, or ship
  disabled); the cockpits themselves (`/dictation`, `/meetings`, `/live`
  unchanged as destinations).

## Tasks

- [ ] Route: `index.astro` becomes the desk page mounting
      `<DeskApp client:only="react" />`; the HS-73-01 temporary page is
      removed; the legacy Alpine desk moves to `/desk-legacy` (out of nav,
      frozen, deleted in HS-73-08). `/desk` redirects to `/` (one-line
      page, keeps old links alive until the cutover story decides its
      final fate).
- [ ] **The first-run guard ports first**: the current inline logic on
      `index.astro` (fetch `/api/setup/status` → redirect to `/welcome`
      when `first_run`, `/setup` when blocked) runs before the island
      mounts — same behavior, byte-equivalent conditions. Update the
      pre-flight + any setup tests that assert `/`'s content.
- [ ] Immersive chrome (in the island, not AppLayout): the world owns the
      viewport. Top-left: the HoldSpeak mark + a compact nav affordance
      (menu revealing Dictation / Meetings / Studio / Settings — the
      rooms), the hub dot (port `hubState/hubLabel` as a dot + hover
      detail), the egress badge. Top-right: `+ Note` `+ KB` `+ Agent`
      `+ Zone` chips. Bottom: ONE whispered hint (`drag onto a zone · tap
      to open`). Nav must remain keyboard-reachable (in tab order,
      revealed on focus).
- [ ] Shell widgets: the desk page still gets QueueHud / Qlippy / Waveform /
      GenerationTheater / ConfirmDialog (either via a minimal AppLayout
      variant or direct mounts) — verify each renders above the stage
      (z-index) on the new `/`.
- [ ] The guiding empty state (Phase 70's "what is this" duty, now
      in-world): a fresh desk shows a small welcome arrangement — the
      wordmark, one line of what HoldSpeak is (label-voice, no selling
      prose), and the create chips + Record orb slot glowing as the next
      actions. It must read as the world being empty, not as a page of
      copy.
- [ ] Retire the old Home: its two-mode cards and next-action logic are
      superseded by the world; grep for `/` links/copy that assumed the
      old Home (TopNav "Home", docs, `/welcome`'s Done destination, the
      Phase-71 "The Desk →" entry) and update each.

## Proof required

Fresh-profile arrival lands on `/welcome` (guard proven); a configured
profile lands in the world at `/`. Screenshots: the arrival (populated),
the empty state (fresh), the revealed nav, keyboard-only navigation out of
`/`. Route pre-flight updated + green (including the `/desk` redirect);
zero page errors; full suite green; `npm run build` green.

## Done

Shipped. `/` IS the Desk: the island mounts under a new `immersive`
AppLayout prop (no TopNav; full-bleed main; shell widgets intact), with the
first-run guard ported verbatim and proven both ways (fresh profile →
/welcome; milestone set → the world). The chrome is the iPad's arrival
grammar: the mark opening a compact rooms menu, the hub dot, the canonical
egress badge (the Alpine port over setup trust), the create chips (wired to
instant-create — HS-73-03's strict subset), Tidy/Refresh, and one whispered
hint. A fresh desk shows the guiding empty state with the POSITIONING
short form and two next-action chips. `/desk` 307-redirects home; the
frozen Alpine desk lives at `/desk-legacy` until the cutover; nav's first
door is Desk and Studio's separate row is gone. Proofs: the Playwright
arrival run (guard both ways, empty state, 4 objects + tray, menu = 4
rooms, redirect, legacy, zero page errors) + two screenshots; 18 pages;
manifest + pre-flight 7 passed; full suite 3066 passed, 37 skipped. Deviations: a compact
always-visible mark+menu instead of an auto-hiding TopNav (simpler,
keyboard-honest, closer to the iPad); chips wired, not disabled. See
[evidence-story-02.md](./evidence-story-02.md).
