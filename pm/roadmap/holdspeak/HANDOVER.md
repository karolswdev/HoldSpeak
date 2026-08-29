# HANDOVER — the value era (written 2026-08-29, after Phases 147+148)

For the next agent. Supersedes the "one tap" handover of earlier
today (historical). Read this whole file, orient
(`.githooks/dw context holdspeak --compact`; the README "Current
phase" line is truth), then go get the owner's pick — they said,
verbatim: **"If you need me, I'm here."**

## 0. THE PIVOT — read this section twice

The owner has re-aimed the roadmap, verbatim: *"start focusing on
things that will add a ton of value to me, a Senior Software
Architect, who now manages 3 people."*

That sentence is the new charter question. Every phase menu from
here leads with it, ahead of craft, ahead of debt: **does this make
the architect-who-manages-three measurably better at their actual
week?** The Tuesday question and the joy question still apply — but
they now serve THIS frame.

## 1. What the world looks like now

- **Main `387aa560`.** Phase 147 (One-Tap Record, PR #501) and
  Phase 148 (The Menu Grammar, PR #503) both merged 2026-08-29;
  close counsels zero must-fix ×4 (design+close, both arcs). A
  docs accuracy sweep (PR #502) also landed from another session.
- **The daily flywheel is WHOLE and polished:** `/` → First
  Sentence → the Door (five-column follow-through board + the
  UPCOMING rail from many calendars incl. the screenshot adapter) →
  **Record this** on any event → armed one-shot → captured meeting
  that KNOWS its calendar event → action items back onto the Door.
  Menus wear the Amiga grammar (C=Hybrid live; the owner's A/B/C
  flip stands as one attribute).
- **The People module EXISTS** — the owner asked and the answer is
  yes: Phase 138 (The People Ledger, 8/8, merged 2026-08-18) built
  relationships, 1:1s, agenda items, commitments with transitions,
  notes, readiness, requests, grounding — service
  (`holdspeak/services/people_service.py`), MCP family, and the
  desk's "Open People" verb. Phases 125–128 built follow-through,
  the Monday Brief, decision receipts, and Desk Intelligence.
- **The honest gap (the value era's thesis):** the People module
  was built BEFORE the flywheel and never woven into it. Nothing
  connects a recurring "1:1 w/ \<name\>" calendar event to a
  person; a recorded 1:1's commitments don't flow to that person's
  ledger; the Door has no per-person lane for "what I'm waiting on
  from A/B/C"; the Monday Brief doesn't brief the week's 1:1s. Two
  eras of machinery, one seam never sewn. (Also: the Phase-138
  owner sitting items were held and never revisited.)

## 2. The menu to put in front of the owner (they're HERE — ask)

Lead with the pivot question. Grounded candidates, most-leveraged
first:

1. **The 1:1 Loop (the natural keystone).** Calendar event ↔ person
   link (147's `calendar_event_id` machinery is the proven
   pattern); Record this on a 1:1 → the meeting knows the PERSON,
   not just the event → commitments/agenda items flow to their
   ledger → the NEXT 1:1 opens with an auto-built brief (open
   commitments, agenda backlog, last decisions, readiness). This
   sews 138 into 144–147 and is the single highest-value seam for a
   manager-of-three. Audit first: what people_* actually ships vs.
   what the 138 record claims, and whether the held sitting items
   bite.
2. **The delegation lane.** The Door learns "waiting on WHOM":
   per-person filters/chips on the follow-through columns; "what
   did I delegate, to whom, how stale" at a glance.
3. **The architect's decision practice.** Decision receipts (127)
   wired to people + meetings: "what did we decide, who owns it,
   which 1:1 do I chase it in." Possibly riding candidate W (JIRA
   Desk Sync, plan filed) if the owner's team tracks work there —
   ASK; W was the 147 menu's runner-up and fits the manager frame.
4. **The Monday Brief as chief-of-staff** (126): the week's 1:1s
   with readiness, stale delegations, decisions awaiting owners.

Debt that should ride ANY next arc (small, named):
- **The web-unit baseline blind spot** (148's discovery): three
  inherited vitest failures (chat egress / containerQueryLaw
  chair.css / writeReceiptGuard BriefLane, one from HS-135-07) are
  invisible to the pytest sweep baseline — establish a web baseline
  file or fix the three.
- 148 counsel ledger: the rAF inner-handle cleanup; the
  "majority"→plurality naming; unselected-radio when a real
  mutual-exclude group ships. 147 ledger stands (recurring-arm
  collision, snapshot uid collapse, the STARTS wrong-day label —
  now twice-observed). The real-metal vision probe has STILL never
  run.

## 3. Standing laws (all prior eras' — the 146/147 handovers'
lists stand — plus this pivot's)

1. **The value frame leads every charter** (§0). BACKLOG.md is the
   parking lot and menus source from it FIRST (the owner caught a
   bypass once; the 147 retroactive row is the scar).
2. Models law (opus-worker for ALL delegated work; author
   PMO/roadmap YOURSELF); guard files are ORCHESTRATOR-owned (three
   builder attribution misses this era); one commit lane, explicit
   paths; counsel design-beat BEFORE build pays (four zero-must-fix
   closes say so); shots cross-read; the walk leg BEFORE trusting
   units.
3. **jsdom lies about focus** — real-Chromium probes are mandatory
   for any focus/interaction work (native post-click focus lands
   after React's sync effect; the double-rAF pattern in
   DeskMenu.tsx is the precedent).
4. Detached sweeps (nohup+disown+done-file — the 10-min tool
   timeout kills backgrounded ones); stalled-wave recovery =
   TaskStop + SendMessage-resume (context survives); asset-clobber
   restore after every glass run (dirs 141–148 now).
5. Owner gates: shots before merge; merge on the word (147 had a
   pre-given goal word; 148 did not and HELD — match the arc's
   grant, never assume carry-over).

## 4. Mechanics (current)

- Cold walk: `scripts/door_walk_hs144.py`, NINE legs (menus leg
  newest; walk sources APPEND, never replace; list-view context
  targets OBJECT rows — zone rows don't wire it; the pair-manifest
  FAIL in `--only` partial runs is an artifact).
- Glass proofs: `tests/e2e/test_hs147_one_tap_glass.py`; the menu
  exhibit rig `phase-148-menu-glyphs/assets/story-03-rig.py`
  (variant flips via localStorage `hs:menu-glyphs` before boot).
- Sweep recipe + isolated-HOME + baseline vocabulary: per the 146
  handover; the inherited pytest baseline is still the 143 file
  (72 names); flake families gained `test_single_fire_across_
  multiple_ticks` (xdist, serial-proven).
- Memory: `~/.claude/.../memory/` — 147/148 arc files current;
  MEMORY.md Active list current as of this handover.

Go ask the owner which value seam to sew first. The desk is
beautiful and the loop is whole — now make it carry their team.
