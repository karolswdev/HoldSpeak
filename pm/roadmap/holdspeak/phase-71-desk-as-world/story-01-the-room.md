# HS-71-01 — The room: the warm atmospheric stage

- **Status:** todo
- **Priority:** HIGH (the foundation + the cheapest huge felt win)
- **Depends on:** —
- **Evidence:** _(added at close)_

## Goal

Replace `/desk`'s flat black background with the iPad diorama's warm, lit room,
so the surface stops reading as a webpage the moment it loads. This is the
cheapest change with the biggest felt impact, and every later story sits on it.

## Scope

- A full-bleed stage container behind the desk content: the `DioPal` vertical
  gradient (`#0B0D12` → `#16111F` → `#090A0E`) under an **animated warm radial
  spotlight** centered high (`~50%, 40%`), accent-tinted, softly pulsing
  (`sin`-driven, slow), screen/plus-lighter blend.
- **Rising dust motes** — a `<canvas>` of ~16 slow translucent specks (the one
  place a canvas is warranted; everything else is CSS).
- The stage is `<style is:global>` (it will sit behind Alpine-rendered content).
- Reduced-motion: the spotlight + motes hold still.
- No content change yet — the existing card-list still renders on top; this is
  the room it lives in. (The card-list becomes floating objects in HS-71-03.)

## Proof required

Before/after screenshots of `/desk` — flat black vs. the warm lit room. The
spotlight pulse + motes visible (a short capture or two frames). Reduced-motion
verified. Build green.

## Done

_(filled at close)_
