# PHILO Phase 13 — The Desk: the proposal

**Status:** DRAFT r1, Muad'Dib, 2026-10-01 — UNCHECKED, awaiting Astra; then the owner's rulings on §5. Grounding checks: plan (Astra r1, paid), structure (Muad'Dib RATIFY), faces (Astra r1 RATIFY-WITH-CONDITIONS, paid).
**Grounding:** [PLAN.md](grounding/PLAN.md) · [inventory.md](grounding/inventory.md) + [structure.md](grounding/structure.md) (Astra, merged #722) · [faces.md](grounding/faces.md) → [faces-surfaces.md](grounding/faces-surfaces.md), [faces-jobs.md](grounding/faces-jobs.md) (Muad'Dib, #723).

## 1. What he asked

> "I do want us to restructure and refine our Desk experiences. We've been soooo heavily investing into the floor, and totally ignoring the desk..."
> "Make sure we want an incredible exeprience. The whoe Workbench 2.0+ on steroids needs to really lean on steroids. Get it?"

The Desk is everything except the Floor: the windows he works in and the frame around them. Phase 12's window-side intent folds in; its Floor work is parked.

## 2. What the grounding found (one paragraph per truth)

**The machinery is good; the Desk does not hold together.** A shared window frame, snap, Exposé, a switcher, a verb registry, a live WebSocket bus and a full component kit already exist (structure §2–§4). But the five Tuesday jobs walked end to end show the joins are broken:

1. **Work is destroyed or forgotten.** Meetings and Workbench items hard-delete. After a reload, open meeting, person, thought, Repo and Workbench windows are gone, and so are drafts: the 1:1 note was typed four times (J3).
2. **The Desk does not tell one truth.** "Needs you" means a different thing on the Chair, the bell, the Dock and Meetings, so on one screen he reads "8 need you" beside "5 of 7", and Meetings says "Nothing needs you". Settings says summaries ON, Trust says OFF. Record shows a running timer after the hub refused to record (501).
3. **What he reads does not open.** Brief, calendar and commitment rows on the Chair are inert; "Open person" in the brief dispatches nowhere. J1 the morning only works through the palette: 5 dead taps at 1440.
4. **A closed window stays, invisible, and swallows taps** until a reload. At 393 it blocks the whole Chair.
5. **On the phone the frame takes a third of the screen.**
6. **It does not look or behave like Workbench.** The Chair at 1440 is a black web dashboard of rows and chips. There is no depth gadget, no zoom between two remembered sizes, no Amiga-key menu shortcuts, no live AppIcons. This is the gap he named.

## 3. The phase: from a web dashboard to a Workbench desk

Four waves. Each later wave stands on the earlier one; waves A and B are the price of C and D being believable.

### Wave A — Trust (repairs that come first)

| Story | Job | Observable outcome |
|---|---|---|
| **A1 Park, never delete** — meetings and Workbench items park, restore from the same face; a truthful receipt | J2, J4 | Delete a meeting → it is in Parked with its segments, summary and artifacts; Restore brings it back. No SQL DELETE on the normal path. |
| **A2 One meaning of "needs you"** — one projection defines it and feeds the Chair, bell and Dock; a window that counts something narrower names it ("2 need a summary"), never "needs you" | J1, J2, J4 | Every "needs you" on a shot agrees; narrower counts say what they count. |
| **A3 Faces that do not lie** — Record reads `res.ok`; summary/destination/agent status from one source; failures named in plain words with a verb, never raw server text | J2, J3 | A refused start shows "Not recording" + the reason; Settings, Trust and Chair agree. |
| **A4 Close means gone** — the closed-window ghost fixed at its seam, proven by a failing test first | all | After Close, `elementFromPoint` at the old centre hits the Desk. |

### Wave B — Everything opens, everything returns

| Story | Job | Observable outcome |
|---|---|---|
| **B1 One open grammar** — every named row (brief, calendar, commitment, Room activity) opens its object in its own window; Brief→People fixed | J1, J3, J4 | J1 dead taps 5 → 0; J1 path 7 → 3 gestures; J3 prep 5 → 1. |
| **B2 The Desk remembers** — open windows, their place (selected meeting, person + tab, send pick) and unsent drafts survive reload and close (Workbench *Snapshot*, automatic) | all | Reload mid-job: 0 re-navigation, 0 lost drafts. |
| **B3 Decide where the meeting is** — a Decide verb in the meeting record; no "New decision" placeholders | J2 | Decision 5 → 2 gestures; the decision carries its meeting and project. |
| **B4 The 1:1 finds its person** — the calendar 1:1 links to the report; Prep shows what they owe | J3 | No false "No 1:1 planned"; prep from the Chair in 1 tap. |
| **B5 The update writes the week** — the deterministic draft reads linked meetings, decisions and owned actions (no engine) | J4 | He edits a draft; 111 typed characters → 0. |

### Wave C — Workbench 2.0+, on steroids (the face of the phase)

| Story | Job | Observable outcome |
|---|---|---|
| **C1 The Workbench look** — the frame and window chrome redesigned on the canvas as true Workbench 2.0+: screen title bar, window gadgets (close, depth, zoom), bevelled material, one gadget set; the Chair becomes a desk of windows, not a page of rows. **Canvas first, his ratification before build.** | all | He looks at it and sees Workbench 2.0 on steroids. Shots at 1440 and 393. |
| **C2 The gadgets that are missing** — depth (send to back), zoom (alternate two remembered rects, on top of maximize), right-button = the active window's menu bar, Amiga-key shortcuts on every menu verb | all | Each gadget works by mouse, key and touch; shortcuts shown in the menus. |
| **C3 A live Dock (AppIcons)** — per-app live state from the bus: REC only when the hub confirms, the 1:1 time on People, one AppIcon per active project with its count; no polling where a frame exists | J1, J2, J4 | A meeting becoming ready or a send settling shows on the Dock within ~1 s with every window closed. |
| **C4 A palette that knows his week and does verbs** — people, thought text, attendees; verb rows (`Prep 1:1 with Priya`, `Send <front document> to …`, `Draft update for …`). A `Send …` row only **opens the exact preview** in the document's SEND well; he presses Send (Article V) | J1, J3–J5 | "Priya" → her window; a word inside a thought finds it; `send` → the front document's preview, in view. |
| **C5 Send to ▸ from any document window** (the Phase 12 fold) — in the title-bar menu and the Object menu; the preview arrives in view; he presses Send in the well | J2, J4 | Send from an open meeting in 3 gestures at both widths. |
| **C6 Capture from anywhere** (a Commodities pop-key) — a global key opens a new thought, titled from its first words | J5 | A thought in 1 key press; no more "Thought ×3". |
| **C7 The phone desk** — at 393 the frame takes at most a sixth of the screen; one window at a time, swiped | all at 393 | Window content ≥ 700 of 852 px. |

### Wave D — Screens for his day (the stretch)

**D1 Screens** — named window sets (Morning, Meeting, 1:1, Project) saved on top of B2, offered from Places and the Chair's NEXT line; drag a screen down to see the one behind (Intuition). Never rearranges his desk by itself. *Observable:* a 1:1 set in 1 press instead of 4–5.

### Consolidation (rides Waves B and C; no story of its own)

Per structure §6: Live meeting joins Meetings; Rhythm, Context, Commands and Processes move under Settings or their running work; Components leaves daily view; the two Models rows become one; Ask is contextual first. Old doors stay until the new path is walked; nothing is deleted.

**Not walked, so not touched yet** (Astra faces check r1): Calendar snapshot (J1/J3 import), Roadmap, Repository, Delivery dossier and terminal (J4 context), Chain, Coder, Directory/Zone and Info windows. They keep their doors as they are. Wave B's first story walks them (atlas `run` mode, both widths) before any consolidation reaches them.

### The Phase 12 fold

Story 01 (merged) carries as-is. The F–J canvases are kept as evidence, never ratified. In-window Send to ▸ is designed fresh in C5's canvas. Floor destination icons, the drop, the brief icon on the Floor and the drag leg of the closing use are **parked**, with their records. Old stories 05 (atlas) and 06 (closing use) become C5's proof: face cases per window kind at both widths (touch at 393), and the real sends by Send to ▸. Phase 12 closes as "folded into Phase 13" once this charter is ratified.

## 4. Lanes (per TWO-BRAINS §4)

| Lane | Stories | Owner | Checker |
|---|---|---|---|
| Trust + data | A1, A2, A3 (backend half), B4, B5, C3 (bus/producers) | Astra → Luna | Muad'Dib |
| Faces + frame | A3 (face half), A4, B1, B2, B3, C1, C2, C4, C5, C6, C7, D1 | Muad'Dib → Fedaykin | Astra |
| Canvases | C1 first (it sets the look every later face obeys), then B1/B3/C5/C7 | Muad'Dib | Astra, then **the owner ratifies** |

Order: canvases for C1 start at once (they gate C), while Wave A builds. A → B → C → D, with C1's canvas ratification as the only owner gate inside the build. The forecast is 3–4 weeks elapsed; D1 is cut if the phase runs long.

## 5. Forks for the owner (five, each with the recommended default)

1. **How far does the Workbench look go?** **Default: all the way (C1)** — real Workbench 2.0+ chrome, gadgets and material, redesigned on canvas first. Alternative: keep today's black material and fix only behaviour.
2. **What does a tap on a name do?** **Default: opens the object in its own window.** Alternative: unfolds under the row.
3. **What does the Desk remember across a reload?** **Default: every window, its place and any unsent draft, automatically.** Alternative: windows only.
4. **Screens for his day: in this phase?** **Default: yes, as the last wave (D1), cut first if time runs short.** Alternative: a later phase.
5. **Should the project update draft read the week without the engine?** **Default: yes (B5).** Alternative: wait for the engine.

## 6. Still owed elsewhere (not this phase)

Phase 10's close (the Resend send), Phase 11's close (shots + the WEBHOOK SET deviation). Both wait on his word; neither blocks this phase.
