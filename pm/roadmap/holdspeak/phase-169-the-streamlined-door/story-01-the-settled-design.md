# HS-169-01 - The settled design + the canvas (the one-screen door; the Room as four questions; eight artboards at 1440 + 393; counsel first; OWNER RATIFIES)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** done
- **Depends on:** -
- **Unblocks:** HS-169-02, HS-169-04
- **Owner:** unassigned

## Problem

The owner walked the 168 door and the Room and bounced both: "not streamlined at all"; "that interface I really didn't honestly like and/or understand". His mandate: "really refine and really streamline the UX... the first module we BOTH will be proud of... world-freaking-class". He ratified the thesis in words (2026-09-04): ONE screen for the door; the Room answers four questions.

## Scope

- **In:** assets/settled-design-streamlined-door.md (D0-D6, written); eight artboards as .dc.html on the 168 shell (Door · picked / picker open / cold / 393; Room · needs you / nothing needs you / 393; History) at true widths, shot and READ by the orchestrator against D3/D4 line by line; counsel reads the canvas against D5's hunts BEFORE the owner; the canvas published; THE OWNER'S WORD recorded verbatim. Bounces re-draw artboards, never code.
- **Out:** any product code.

## Acceptance criteria

- [ ] Eight artboards exist as .dc.html sources with shots at true width in assets/story-01-shots/.
- [ ] Every chip on every artboard names a fact the wire has (D5); every verb is the library Button look; zero sentences beyond D3/D4's copy; exactly one display-step element per face.
- [ ] Counsel's findings paid on the artboards before the owner sees them.
- [ ] The owner's verdict recorded verbatim; PASS is the exit.

## Test plan

Playwright shots of every artboard at its width (the shot script); a python check that every .dc.html uses only D2's hex values and no `border-left` accent; the orchestrator's read of every PNG.

## Delivered (2026-09-04)

- The settled design assets/settled-design-streamlined-door.md (D0-D6):
  the one-screen Door; the Room as four questions; the cuts and where
  they go; the type scale and palette from the ratified 168 shell;
  the four motion moments; the laws and counsel's hunts.
- Eleven artboards as .dc.html on the 168 shell, three rounds, every
  PNG read by the orchestrator at true width (assets/mockups/*.dc.html;
  assets/story-01-shots/): Door first open · checking · picked · picker
  open · Adjust open · cold desk · 393; Room 3-need-you · nothing needs
  you · 393; History.
- Counsel RATIFY-W-C, every M and S paid on the design and the
  artboards before the owner saw them (recorded in D5): CI on the base
  branch is new wire (`branch_ci`); decisions via the project ↔ meeting
  link; the server-side read marker; square mics; the meeting glyph;
  honest picker counts; the outcome said once; no host chips in the
  head; the health rule.
- The canvas published: https://claude.ai/code/artifact/aa41070b-9a9e-4946-824c-29f2578c8383
  (version "The excellence round").
- Evidence: the artboard check (palette-only hex, no accent edge, the
  exact head line, one display-step element per Room face, a shot per
  board) — 11 artboards, 0 failures.

## THE OWNER'S VERDICT (2026-09-04), verbatim

First canvas: **"Okay yeah this does look a lot better. I'm guessing we
can perfect it even one more time to nail out the last couple of
things, no?"** — then, handing the pen: **"Just. Be excellent. Be a
powerful UI and UX designer for this. Please."** The excellence round
(the Door's first open, checking and Adjust; the target token; the CI
row as a thing; verbs on every actionable row; the just-arrived
moment; the motion moments) — then his word on the canvas:
**"word"**. PASS. The build opens: 02 the Door ∥ 04 the wire.
