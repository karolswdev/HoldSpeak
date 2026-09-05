# Phase 169 - The Streamlined Door

- **Project:** holdspeak
- **Status:** ACTIVE 3/7
- **Chartered:** 2026-09-04 off feat/connections-door `1f9798f9` (168 The Connections Door at 5/7: both of the owner's bounces paid, the branch green on its gates, its merge and story 05 waiting on his word; this phase supersedes 168's door and the 167 Room face)
- **Canon:** docs/internal/CONSTITUTION.md (Articles III, VI, VII, VIII); docs/internal/DESIGN_SYSTEM.md (the interior canon: type scale, composition rules, the aerogel receipt, the banned left rail); web/src/desk/surface (the library); assets/settled-design-streamlined-door.md (D0-D6); the owner's laws: face-design-before-build; every verb is the library Button; no prose in the UI; no modals; "will you use this on a Tuesday?"

## The charter

The owner walked Phase 168's door and the Room on his real desk
(2026-09-04) and bounced both, verbatim: **"I really don't understand
why everything's still so complicated... this stuff is still not
streamlined at all"**; on the Room: **"that interface I really didn't
honestly like and/or understand"**. His mandate, verbatim: **"I want
us to really refine and really streamline the UX. This is, by far,
the biggest obstacle to me accepting it. It's horrible. And we need
this module to be the first one that we BOTH will be proud of."** —
**"Just make sure the interface to all of this is absolutely
world-freaking-class."** He ratified the thesis in conversation:
"I like where that's going. For sure." / "Okay, I like it."

What he hit (measured): from New Project to two live Watches on a
connected desk took 17 face steps; the Sources screen held ~60
objects (a four-step plan, two answered rows, a TOOLS row, nine
suggestion cards with four chips each, a wizard with its own plan,
a brief repeating everything). The Room after activation showed four
counters reading zero (including `0 Watches` seconds after activating
three), `REV 1`, a raw journal line (`Created · name, source,
watches_activated`), an empty timeline, and four wings (TIMELINE ·
DECISIONS · SEARCH · ASK) it never explained. Under it, the 168
re-walk found the Jira Watch born dead (paid @1cd03962) and a native
`meeting` Watch the face let him activate that can never evaluate.

The thesis (assets/settled-design-streamlined-door.md):

1. **The Door is ONE screen**: the outcome line (which becomes the
   name), source rows with in-world pickers and default Watches, the
   count as the test, `Create Project`. Five clicks on a connected
   desk. No Notice question, no cards, no brief, no wizard, no Review.
2. **The Room answers four questions** in order: what needs me now;
   what am I watching and is it working; what changed since I last
   looked; what did we decide and what do I owe. Then one ask box.
   Two wings: ROOM · HISTORY. The headline is the ONE display-step
   fact. Empty states are one true line. The name is said once.

The chain: 01 the design + the canvas (OWNER RATIFIES) → 02 the Door
∥ 04 the wire for the four questions → 03 the Room → 05 the walk on
his desk (5 clicks; the first paint; OWNER VERDICT) → 06 docs → 07
close (168's debts folded).

Exit: the owner's word on his real desk that this is the first
module we are both proud of.

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-169-01 | The settled design + the canvas (the one-screen door; the Room as four questions; eight artboards at 1440 + 393; counsel first; OWNER RATIFIES) | done | [story-01-the-settled-design](./story-01-the-settled-design.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-169-02 | The Door built to the canvas (one screen: the outcome line; source rows with in-world pickers and default Watches; the count is the test; Create Project) | done | [story-02-the-door](./story-02-the-door.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-169-03 | The Room rebuilt to the canvas (the head with the one headline; NEEDS YOU; SOURCES; SINCE YOU LOOKED; DECISIONS & COMMITMENTS; the ask well; two wings ROOM · HISTORY) | backlog | [story-03-the-room](./story-03-the-room.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-169-04 | The wire for the four questions (needs-you items derived from real Watch entities; the read marker; the health inputs; the meeting Watch never offered until it evaluates; MCP twins) | done | [story-04-the-wire-for-four-questions](./story-04-the-wire-for-four-questions.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-169-05 | The walk on the owner's desk (the door in 5 clicks; the Room's first paint; the stopwatch; OWNER VERDICT — "the first one we are both proud of") | in-progress | [story-05-the-walk](./story-05-the-walk.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-169-06 | The docs (the guide's New Project + Project Room sections re-shot; MCP_SIDECAR regenerated; the design doc canonized) | backlog | [story-06-the-docs](./story-06-the-docs.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-169-07 | The close (gates, the sweep, counsel, the debt ledger, final summary; 168 folded) | backlog | [story-07-the-close](./story-07-the-close.md) | [evidence-story-07](./evidence-story-07.md) |

## Where we are

**ACTIVE 3/7.** Branch `feat/the-streamlined-door` off
feat/connections-door `1f9798f9`. **01 DONE:** the settled design,
eleven artboards over three rounds (every PNG read at true width),
counsel RATIFY-W-C paid before the owner saw it, the canvas published
(aa41070b-…), and his word — "Okay yeah this does look a lot better…
perfect it even one more time" → "Just. Be excellent." → the
excellence round → **"word"**. **04 DONE:** the wire for the four questions (needsYou / sources with
zero-omitted tokens and nextCheckAt / health with its inputs / the
room_read_at column + read route / decisions via meeting_projects /
target / `branch_ci` via `gh run list` / the meeting template retired /
MCP parity / model.ts decode) — 152 tests read. **02 DONE** (three rounds against the artboards: boxed rows, the
token toggles as a library variant, the stroke chevron, the four-line
393 grammar with a no-intersection probe, the receipt at the left edge
through a footer class hook, the window at 580 so the picker fits; the
rig: 5 clicks, no body scroll at 1440; evidence 15 passed). In flight:
03 the Room (round 2: the glass rig, zero branch-new,
no dead verb, NEXT CHECK from the wire). The build opened on his word: 02 the
Door (the face + its two seams: the count through the evaluation
compile; Create as one service call) in parallel with 04 the wire for
the four questions (needsYou / sources / health / sinceRead read
marker / decisions via the meeting link / `branch_ci` / the meeting
template retired / MCP parity); then 03 the Room; then 05 his desk.
