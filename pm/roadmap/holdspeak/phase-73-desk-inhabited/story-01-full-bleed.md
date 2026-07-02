# HS-73-01 — Full-bleed: the world owns the screen

- **Status:** todo
- **Priority:** HIGH (roughly half the felt gap, and it is mostly deletion)
- **Depends on:** —

## Goal

When `/desk` loads, the user is IN the world — not reading a document about
it. Kill the header stack and the pill bar; the stage owns 100% of the
viewport; chrome becomes a floating minimal cluster the way the iPad does it
(reference: `phase-20-one-app-every-size/screenshots/2001-ipad-wide.png` —
a gear, small create chips, one whispered hint, nothing else).

## Scope

- **In:** an immersive-chrome variant of `AppLayout.astro`; the removal of
  `.desk-head` and `.hub-bar`; the in-world chip cluster; the page rebuilt
  as `components/desk/` partials; the one-line hint; a11y for the hidden
  nav.
- **Out:** the create flows behind the chips (HS-73-02 — this story may
  temporarily keep the existing `openCreate()` drawers wired to the new
  chips); zones (HS-73-05); any other page's chrome.

## Tasks

- [ ] Add an `immersive` prop to `web/src/layouts/AppLayout.astro` (used
      only by `desk.astro`): the TopNav renders as a translucent overlay
      that auto-hides after ~2s idle and reappears on mouse-to-top-edge,
      any keyboard focus entering it (it must stay in the tab order — do
      NOT `display:none` it, use transform/opacity), or touch near the top.
      Shell widget mounts (QueueHud, Qlippy, Waveform, GenerationTheater,
      ConfirmDialog — `AppLayout.astro:~80-119`) are untouched.
- [ ] Delete the `.desk-head` block (`desk.astro:~49-83`): the eyebrow, the
      H1, the lead paragraph (banned prose), the stat counter, and the
      toolbar buttons. Delete the `.hub-bar` pill row.
- [ ] Replace with the in-world cluster, all Alpine-rendered so CSS is
      `<style is:global>`:
      - Top-right: small chips `+ Note`, `+ KB`, `+ Agent`, `+ Zone`
        (wired to the existing `openCreate('note'|'kb'|'agent')` and the
        directory-create path for now; HS-73-02 replaces the drawers).
      - Top-left: a quiet cluster — the HoldSpeak mark (links Home), the
        hub dot (`hubState()`/`hubLabel()` from `desk-app.js:432/440`
        collapsed to a dot + tooltip-on-hover, no text row), the egress
        badge (`egressBadge()`, `desk-app.js:152`), and the Refresh +
        Tidy controls as icon buttons (`tidyDesk()` keeps its
        only-when-positions-exist visibility).
      - Bottom-center, under the wordmark position: ONE whispered hint,
        max one line, e.g. `drag onto a zone · tap to open` — mirroring
        the iPad's. No other sentence anywhere on the surface.
- [ ] Rebuild `desk.astro` into partials as you go:
      `components/desk/DeskStage.astro` (the HS-71-01 atmosphere),
      `DeskChrome.astro` (the cluster + hint), `DeskWorld.astro` (objects +
      zones markup), keeping the `?raw` + `new Function` factory load and
      the `<style is:global>` blocks with each partial. Target: no single
      desk file over ~600 lines after HS-73-04 lands.
- [ ] The stat counter dies; if the count matters it lives in the hint area
      as a bare number on the zone legend, not a labeled stat block.

## Proof required

Before/after full-viewport screenshots (the header stack gone; the world
starting at y=0). The nav auto-hide captured (hidden at idle; revealed on
top-edge hover and on keyboard Tab). A keyboard-only pass: Tab reaches the
nav and every chip. Route pre-flight green, zero page errors on `/desk`;
full suite green; `npm run build` green.
