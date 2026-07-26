# HS-104-08 - The icon family reforged — Workbench 2.0, but amazing

- **Project:** holdspeak
- **Phase:** 104
- **Status:** done
- **Depends on:** none (chartered mid-sitting)
- **Unblocks:** HS-104-07 (the sitting's acceptance rider)
- **Owner:** the owner's own verdict, 2026-07-26

## Provenance (the bar)

Chartered by the owner at the Phase-104 sitting gate, the HS-103-07
precedent (a story born from the sitting verdict itself): *"Gone are
the 'crystals' for KB, gone are cute-ass bitmojis, in are more
Workbench 2.0-but-amazing icons."* The sitting is accepted only with
this shipped.

## Recipe

1. **The law already written governs** (`web/ICON-DISCIPLINE.md`,
   DESK_GRAMMAR §1): 64×64 cell art rendered 1:1, distinct silhouette
   per kind, the Pixellab prompt formula, candidate packs picked
   against the document, states derived by
   `gen-sprite-states.py`, the iconCell guard.
2. **Two metaphors replaced, the rest restyled in one language:**
   - `kb`: the crystal is OUT. In: a bound reference TOME (spine +
     bookmark ribbon) — a silhouette no other kind wears.
   - `agent`/`recipe`/`coder`: the avatar bitmoji is OUT. In: an
     angular mechanical AUTOMATON head — a machine handle, not a
     mascot.
   - `meeting` (cassette), `note` (page), `artifact` (paper),
     `model`/`chain`/`workflow` (cartridge), `directory` (drawer)
     keep their proven silhouettes, regenerated in the one
     Workbench-2.0-modern language (slate body, kind-glow accent,
     top-left light, clean dark outline).
3. **Variant pools** stay hash-stable in shape: 16 per big family
   (meeting drops 17→16), singles for cartridge/paper/drawer.
   `sprites.ts` VARIANTS updated in the same commit.
4. **The pipeline:** Pixellab 48px candidate packs → picked → padded
   to the 64 canvas → banked under `public/desk/sprites/` → the
   state script rerun → the guard green.

## Acceptance

- No crystal and no avatar sprite remains referenced; the new
  silhouettes render on the REAL staged desk at 1440 + 393
  (screenshots read before any flip).
- `iconCell` guard + desk suite + build + tokens gate green; the
  state set complete on disk for every base sprite.
- The owner's word on the art is the final gate (this story exists
  because of it).

## Test plan

- `npx vitest run src/desk` (the iconCell guard rides it), build,
  `gen-sprite-states.py` idempotence, the screenshot walk.
