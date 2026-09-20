# HS-201-11 - A quiet desk for the sitting

- **Project:** holdspeak
- **Phase:** 201
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Small things that make the sitting noisy: every desk load 500s in holdspeak/web/routes/roadmaps.py:147 (`next_data.get` on None; 34 tracebacks in two runs; a console error on every page); eight 404s for /desk/sfx/*.ogg; `1 need you` while two rows ask and `Nothing needs you` printed twice on one 393 screen; the script's step 1 does not mention the First Sentence gate ("Continue later" is the way to the desk); `HAS OPEN ACTIONS` on a meeting with zero actions. Tenets 3, 6; Article VI.

## Scope

- **In:** the None guard; the sfx files present or the references removed; the headline count equals the rows that ask; one "Nothing needs you" per screen; `HAS OPEN ACTIONS` only when there are; SITTING-07.md updated to what the rehearsal saw (step 0: Continue later; step 2: the real Models labels; step 3: Import allowed; step 7 as is).
- **Out:** anything else the rehearsal listed.

## Acceptance criteria

- [x] A cold desk load produces zero hub tracebacks and zero console errors (fence).
- [x] The headline count equals the asking rows (vitest).
- [x] SITTING-07.md matches the faces at 321247d2 + stories 09/10.
- [x] Shots at 1440 and 393 in assets/story-11-shots/.

## Test plan

- **Unit:** pytest for roadmaps route with no next story; vitest for the headline count.
- **Integration:** a console/log fence in the existing one-thing glass rig.
- **Manual / device:** shots.

## Notes / open questions

Lane B (Opus). Files: holdspeak/web/routes/roadmaps.py, the sfx assets, web/src/desk/chair/ChairHome.tsx (headline count only), history/helpers.ts HAS OPEN ACTIONS, SITTING-07.md. Do not touch the Concierge, meeting_import.py, ImportSection.tsx.
