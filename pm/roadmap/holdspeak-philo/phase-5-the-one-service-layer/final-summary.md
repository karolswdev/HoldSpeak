# Phase 5 — The One Service Layer — final summary

**Status:** four of four stories merged 2026-09-24 (#634, #635, #636, #638). Exits 1–4 flipped on retained evidence. **Exit 5 is open pending the owner's review of the rehearsal shots** (https://claude.ai/artifact/Q6AqpXtUmtTQgrrR9WhzKM). This phase closes on his word that he has looked; it is recorded as "rehearsed, owner-reviewed shots", never as a sitting.

## What the owner's ruling bought

"Things have to flow through services." One declared application-operation contract now sits under the whole Phase 3+4 meeting loop: import, meeting read, summary run, decisions (create/update/read/list), the brief with the producer clock, the shelf, and the Thought's create/save/read/workbench/list — 17 descriptors in one ~600-line module, bound once at hub composition to the hub's live service instances. HTTP routes, MCP tools, the five MCP resources and the rig's `op` step all reach the same registry and the same objects inside the hub. The hand-written MCP decision and loop branches are gone; the residual set of hand-wired paths shrank 334 → 320 with a fence that fails on any new bypass. The stdio proxy is proxy-only (standalone composition retired).

## What he can do now that he could not on 2026-09-23

- Ask for the meeting job in ordinary words through an MCP client and get the same durable objects the face makes: rehearsed by Astra through Codex — import, the LAN summary on the row without refresh, a decision on the Chair linked to the meeting, an edited Thought, tomorrow's brief leading with the decision — 15 calls, all through `/api/mcp`, 326 s, every object read back through the contract and matching its shot at 1440 and 393.
- Import a recording by naming a file the hub can read (`meeting.import`), owner-only, with named refusals.
- Acknowledge or defer brief rows through MCP (`monday_brief.shelf`, `shelf_read`).
- Trust the rig's headless operation tier: 18 named atlas pairs agree on durable outcome, identity relationships and refusals between the browser path and the operation path; ~2.7 s per no-engine op case.

## Both brains, per story

| Story | Built by | Checked by | Verdicts | Merged |
|---|---|---|---|---|
| 01 One decision through one contract; the Codex path proved | Muad'Dib | Astra | BOUNCE (HTTP list truncated at 500; the descriptor narrowed accepted inputs) → RATIFY-WITH-CONDITIONS (the authority-field narrowing ratified), paid | `6e707ff3` #634 |
| 02 The loop shares the contract | Muad'Dib | Astra | BOUNCE (P1: `meeting.import` reachable by a remote DESK agent; `thought.list` shape false; shelf traversal unfenced; the admission "exemption" unlawful) → RATIFY-WITH-CONDITIONS (Owner only in the description; the record corrected), paid | `c4d46498` #635 |
| 03 The atlas proves the three paths | Astra | Muad'Dib | RATIFY-WITH-CONDITIONS (the LAN-receipt check's meaning; the older-atlas-bytes fact; the ledger carried into 04 as work), paid | `9c653937` #636 + `29380711` #637 |
| 04 The owner asks in his own words | Astra | Muad'Dib | RATIFY-WITH-CONDITIONS (census regenerated; the record's heading; S4's cause unknown; the reads named; eight BACKLOG rows), paid | `6162239f` #638 |

## What was found and is NOT fixed (ledgered with homes)

- **Article XI debt:** `decision.create/update` leave no kernel operation and no receipt through either transport; whether a desk decision write "acts under Article V" is UNRULED — the owner's ruling (BACKLOG; Decisions deferred). No exemption is claimed.
- **The face:** a failed import shows SAVED; the meeting-ready toast counts zero and covers the summary at 393; the brief head says 5 while the receipt says 6 and the caption and receipt use two time formats; a raw pipeline item is counted; the decision body is empty ~1 s after Done at 393; the Info-window rename sends `name` and is ignored; two broke rows for one missing decision read (BACKLOG, PHILO-5-01/02/04 follow-ups).
- **The contract:** the shelf enum refuses before the registry while the descriptor says it will not pre-empt; the `op` tier's forced `viewport: 1440` label; `philo5_his_words.py` loads the registry in-process for a read-only catalogue read, outside the AST fence.
- **Discoverability:** Codex needed 25 repository reads and 201 s to learn that "a decision on my review list" is `desk.create kind=decisions status=proposed`; a client without the repo would not find it (BACKLOG).
- **Not proven:** an already-open Desk refreshing its brief after an agent write (the owner accepted a reopened read for this phase); usefulness of the summaries (partial, as Phase 3 measured); a live sitting; discovery without repository access.

## Fences that failed pre-fix (exit criteria 1–4)

01: the presence/identity/compat fences (`docs/internal/philo/phase-5/one-decision/`, compat 11/11 base → 9 failed r1 → 11/11). 02: 19 failed / 4 passed on base via real producers; the owner-boundary fence red with a real DESK credential (`the-loop/round-2/`); M12–M15. 03: `op` removed → BLOCKED; a headless snapshot at a face → FAIL; equivalence skew → FAIL (`story-03-lane-report.md`). 04: the prompt fence and the write-path audit with mutation reds; the receipt seam 3/18 red → green (`his-words/`).

## Laws learned

- A contract that narrows accepted inputs or slices an already-limited list breaks clients silently: every migrated operation ships a three-state compatibility table (base, round one, built).
- A boundary belongs in the operation, before any side effect, and is fenced with a genuinely issued credential from the wrong side.
- A declared result shape is a promise: every braced shape runs its real producer in a fence.
- The rig's operation tier proves durable state, never a face; its label must not read as one.
- The gate refuses amending a done story's evidence file; corrections live in `checks/` and lane reports. Read `git log -1` after every gated commit.
- Never symlink `node_modules` into a worktree or archive and then run `uv`; the build hook follows the link.
