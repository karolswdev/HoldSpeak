# HS-70-08 — Naming + positioning coherence (the docs story)

- **Status:** todo
- **Priority:** MED (the dedicated docs story — after the features, before closeout)
- **Depends on:** HS-70-01 … HS-70-07
- **Evidence:** _(added at close)_

## Goal

Lock the new front door into canon so it can't silently drift back. The IA is
recorded in POSITIONING, "Studio" becomes a canonical name, and the user-facing
entry points (README, docs index, Getting Started) reflect Home + the two modes
+ the Studio tier. Owner rule: every phase gets a dedicated docs story, and
feature docs stories must touch the *entry* points, not just deep guides.

## Scope

- **POSITIONING.md:** record the web IA (Home · Dictation · Meetings · Studio ·
  Settings) as the surface expression of "one copilot, two modes"; add
  **Studio** to the canonical-name table (name, not "advanced panel" /
  "power tools" as alternating synonyms) with its intent; note that Studio is
  the advanced tier *below* the two modes, not a third pillar.
- **README + docs index + Getting Started:** the front door now describes
  landing on Home, the two modes as the primary path, and Studio as where the
  power features live. Retire any tour that implies a flat many-page surface.
- Nav labels + page `<title>`s + on-screen headings use the canonical names
  consistently (Meetings, not History; the dictation journal; etc.).
- Under the live voice guard: no em/en dashes in prose, no AI-vocab, canonical
  names both-ways. Any embedded screenshot showing the old nav is re-shot.

## Proof required

The voice/doc guards green; POSITIONING carries the IA + the Studio row; the
README/index/Getting Started reflect the new front door (no stale flat-surface
tour); grep shows canonical names in nav + titles; re-shot screenshots
committed.

## Done

_(filled at close)_
