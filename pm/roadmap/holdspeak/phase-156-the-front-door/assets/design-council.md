# The Design Council ruling — the component-library reform (2026-08-31)

Convened on the owner's ruling ("council-led… including soliciting
feedback from the codex CLI"). Voices: **codex `gpt-5.6-sol`**
(read-only over the tree; memo in [design-council-codex.md]
(./design-council-codex.md)) and **Opus counsel** (full repo
investigation; memo in [design-council-opus.md](./design-council-opus.md)).
Synthesized by the orchestrator; the owner ratifies. The north star is
the owner's, verbatim: "Amiga was so freakin' streamlined… summon the
very best of that spirit, plus modern, delighting patterns… a truly
unique and beautiful and HONESTLY GREAT feeling." Amiga's streamlined
honesty + modern delight — never nostalgia cosplay.

## Where the voices CONVERGED (ratified as settled)

1. **`surface/` is the library, promoted in place.** A public barrel
   (`surface/index.ts`) becomes the only supported feature import
   path; a written `surface/contract.md` states the component law
   (states, a11y, tokens, motion, container behavior). No competing
   `components/lib/` — one center of gravity. Fix the dependency
   inversion (MicButton moves inward as a control; CallChip stays a
   thread composition over library `StateChip`).
2. **The ratchet fence.** guard-architecture.mjs gains a checked-in
   baseline of legacy violations that can NEVER grow: new code must
   import through the barrel, must not restyle library-owned states/
   chips/folds/plans in feature CSS, must not reimplement roving.
   Touched features adopt; untouched mega-components are left alone.
   No flag-day rewrite.
3. **The delight layer is behavior, not decoration.** The v1 patterns
   (union of both memos, codex's contracts adopted):
   `StateChip` + `ActionNotice` (closed state vocabulary, icon+text,
   at most ONE named next action), `Disclosure/Fold` (RAW/advanced,
   in-flow, focus law), `ProgressPlan` (stable step ids, byte
   progress, receipt/egress slots, one resume action),
   `ChoiceCardGroup` (real radio semantics, recommended state,
   separate confirmation verb), `ProvenanceChip`/`Receipt`
   (promoted, composing into SurfaceFooter's existing law), in-flow
   `Popover` (the chrome-menus monolith's replacement), and
   `TopologySurface` (DOM nodes / SVG edges, bounded pan, keyboard
   pan-select-repoint, add-node + inspector slots — presentation and
   interaction only). Roving lives INSIDE the composites.
4. **Visual gates are first-class at three boundaries** (codex's cut,
   opus's mechanics): a new/materially-changed library component; a
   UI story's acceptance; a phase close with an altered journey.
   The artifact is a named, deterministic SHOT SHEET (1440 + 393, the
   states, keyboard focus, before/after when relevant, reviewer +
   verdict) stored with the phase evidence. Judged by eyes — the
   orchestrator's at story acceptance, the owner's at phase close —
   never by pixel-diff equality.
5. **The reform is a PREREQUISITE of the front door.** The v1
   patterns + the fence land as a story BEFORE the door surface and
   topology stories build — the first customer proves the library
   contract instead of minting more one-off furniture.

## Where they DIVERGED — orchestrator's ruling

- **Scope of the prerequisite:** opus cut four pieces, codex seven.
  RULING: the prerequisite story ships codex's seven for the door
  (they are the door's exact furniture) but `TopologySurface` is
  scheduled INSIDE the topology story as its first act (it is big,
  and only that story consumes it) — sequencing per opus, contracts
  per codex.
- **Directory split now vs later:** codex wants primitives/controls/
  patterns/graph subdirs immediately; opus only the barrel. RULING:
  barrel + contract.md + `patterns/` for the NEW pieces now; the
  existing files move opportunistically (organization must not stall
  the door).
- **Token shim:** codex retires desk-tokens.css after an import
  census. RULING: adopted, as a checklist item in the plain-words
  story, not a story of its own.

## What changes in the charter

Story 03 becomes **The library patterns** (the v1 pieces + the barrel
+ the fence + the gallery shot-sheet); the door surface, plain words,
topology, and the walk shift to 04–07. The walk's exit criteria gain
the shot-sheet law. Phase 156 remains the reform's first customer;
the ratchet then carries every future phase.

## Standing law (beyond 156)

Visual inspection at the three boundaries is process from now on, in
every phase — a gate without its looked-at sheet is not passed. The
delight layer grows only through the library; a room-local delight is
a defect with a deadline.
