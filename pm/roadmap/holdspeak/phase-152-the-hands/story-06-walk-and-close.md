# HS-152-06 - The walk and the close

- **Project:** holdspeak
- **Phase:** 152
- **Status:** done
- **Depends on:** HS-152-05
- **Unblocks:** HS-153-01
- **Owner:** unassigned

## Problem

Art. IX. Counsel's four legs (settled-design D6), the door-walk leg,
docs, close counsel, and the honest tool-qualification of the `.43`
deployment.

## Scope

### In

- Real `.43`: a `people.*` read + a `door.*` effect with receipts; control without tools.
- People boundary under profile switch with the captured payload.
- Safe-mode decision box: once/always/deny semantics on glass.
- Glass 1440 + 393: tool rows, decision box, elicitation, error, status line; door-walk leg; docs; close sweep vs baselines; close counsel; `ToolQualification` for the `.43` deployment seeded by a real eval.

### Out

DC-03+.

## Acceptance criteria

- [x] Four legs recorded with artifacts; the safe-mode leg shows one policy row after Allow-always and none after Allow-once.
- [x] Door walk green ×3 with the extended thread leg.
- [x] Close sweep: zero unresolved branch-new; web checker zero branch-new.
- [x] Close counsel recorded; must-fixes fixed in-round; owner has the shot exhibit.

## Test plan

- **Unit / integration:** full sweep; the 152 rig; the metal script; the door walk
- **Manual / device:** `.43` legs 1–3; owner shot verdict.

## What shipped (2026-08-30)

**Counsel's four legs, all on record:**

1. **Real `.43`** (`assets/story-03-hub-leg.py` LIVE, Qwen3.6-35B-A3B
   through the production legacy-LAN path, 15/15): `people.readiness`
   called by the model → real dispatch → receipt, part `sensitive=1`;
   `door.add_item` chosen by the model → the effect ran as a kernel
   child with a receipt → an `action_items` row with
   `source_type='thread'`; a control turn made no call. Payloads under
   `assets/story-03-hub-payloads-live/`. RULING: no `ToolQualification`
   eval — `chat.turn` does not `require.structured_tools`; llama.cpp
   emits native `tool_calls` for Qwen3.6 (probed directly, 0.3 s).
2. **People boundary under profile switch** — the same LIVE run: the
   override is honored at admission (`egress=cloud`); the unit pins in
   `test_thread_people_fence.py` carry the captured payload.
3. **Safe mode on glass** (`tests/e2e/test_hs152_hands_glass.py`, 5 legs
   + renderers 2 = 7): Allow once → receipted, no policy row; Allow
   always → receipted, exactly one `thread_tool_policy(allow)` row, the
   next call auto-admits with no box; Deny → `tool_denied`; the
   elicitation form; the error row. Shots `assets/story-06-shots/`.
4. **Glass both widths** — every room of 04/05/06, reviewed; the owner's
   exhibit: https://claude.ai/code/artifact/cf089f7c-3d39-4eff-9322-23a8b4ddfb97

**Door walk** (`scripts/door_walk_hs144.py`, `leg_thread` extended: yolo
`desk.list` receipted with the note block + RAW fold, then safe
`desk.create` held → Allow once → receipted, both widths): 10/10 legs
×3 by the worker, and one captured run (341 PASS / 0 FAIL,
`assets/story-06-walk/`).

**Docs:** USER_GUIDE "The Thread has hands"; the Desk Chat plan §6.4 +
§6.7 marked SHIPPED; tool counts 142 / 31 (drift guard 26 green);
`git grep -i warpdrv` = plan + phase records only.

**Close counsel** (`assets/counsel-close.md`): RATIFY-WITH-CONCERNS,
zero must-fix, two should-fixes applied in-round (S1 `/decide` 409 on a
non-pending handle; S2 the sentinel key stripped on every redactor
path), seven recorded notes.

**The honest sweep** (isolated HOME, `-n 6`, metal excluded): 13 failed /
7205 passed vs main's 41 failing names → 3 branch-new after the fixture
pass, all resolved: `test_reconcile…calendar_events` (the pre-pass
below must also flip `shape_changed` — fixed), the refinement
coordinator test (xdist timing; passes alone — recorded), and the
HS-144 door glass — a REAL defect: the Agents lane counted the four
seeded mode recipes as **CREW 4** on a fresh desk; modes are practices,
not crew (`AgentsLane.tsx`, `CompanionCore.tsx` exclude `kind='mode'`).
The 18 first-pass branch-new names were 153-groundwork fixture drift
(seed counts, the door tool list, frame allowlist, API-surface manifest,
the recipe `kind` in the sync contract + UAT ledger) plus two design
fixes: **`chat.guardrail`/`chat.compact` moved to their own `internal`
group `chat_practice`** — inside `thoughts_notes` they made the Thoughts
& notes starter bundle refuse any plain local model and broke the
group's retry-policy intersection (the owner points them from a
contextual editor in 153-03, not the seven-row roster). Web checker:
zero branch-new.

**Found on the way — a Tuesday blocker for the owner, fixed:** the
owner's real desk DB could not be opened by this branch OR main —
`reconcile_schema` ran `SCHEMA_SQL` (which carries `CREATE INDEX IF NOT
EXISTS … scheduled_recordings(calendar_event_id)`) before the additive
column pass, so an older DB died with "no such column". HS-142-02 had
special-cased one such index; the pre-pass (`_add_missing_columns(…,
existing_only=True)` before the script) closes the class. Proven on a
COPY of the real DB (`~/.local/share/holdspeak/holdspeak.db`, 33 MB):
column added, index built, every row kept, `threads` created.

Ledgered for 153: `door.add_item` from a thread leaves `source_ref`
empty (the loop should stamp the message id — 153-05 `/todo`); the
People paraphrase R2 (153-03 `egress-guard`); historical tool-role
messages replay without `tool_call_id` (strict cloud providers may
400 — fold into 153-05's assembler work).
