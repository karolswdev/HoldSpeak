# Muad'Dib handover XXIX — 2026-09-25 (one day): Phase 7 chartered, ratified, two of four stories on main; the grant, the canvas, the three inherited reds; the laws the day taught

Read with `docs/internal/TWO-BRAINS.md`, XXVIII (the method; Roads A and B), `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md` (the canon of the phase), its `design/grant-lifecycle-beat.md`, `assets/story-02-canvas/README.md`, `checks/` (every Astra round verbatim), and `pm/roadmap/holdspeak/BACKLOG.md` (the PHILO-7 rows). Memory: `project_philo_phase3_closed_phase4_morning.md` is the running state.

## Where the day ended (main `f6695090`)

| Story | State | Merged | The proof |
|---|---|---|---|
| Phase 7 charter | RATIFIED ("Ratify, build it"), R5 `decision.delete` IN the grant | #650 `8482a2f1`, #655 `dcf3eaeb` | Astra r1–r3 paid in rounds 2–4 |
| 01 Notes and directories on the contract | DONE | #657 `9800a603` | 15 descriptors; residual 320→293; the rename interleaving fences red on main; `create_directorie` (MCP zone writes never worked on main) found and repaired; Astra r1 RATIFY-W-C paid (the rig BLOCKS unrepresentable read/delete args by name; `kb.create` admission covers dict `member_ids`), r2 RATIFY-W-C |
| 02 lifecycle design beat | MERGED | #656 `cc8ff6a3` | Astra r1–r3: atomic terminal writes T1–T9 via `transition_and_receipt` (+`strict`, `decision`, `effect`, `warrant_revoked`) and `create_refused_with_receipt`; explicit `BEGIN IMMEDIATE` order; one-connection callback; frozen `authority_basis` parsed with `split(":", 2)`; codes ordered required→expired→revoked; durable-first credential revoke; identity-keyed grants survive reissue and restart; no default expiry |
| 02 the grant canvas | RATIFIED by the owner | #658 `c806c380` | Astra r1 BOUNCE (the ℹ under the window grip / 6 px at 393; OFF hid credential-backed grants; posed expiry; 10 px species) → r2 RATIFY-W-C; HIS ANSWERS: **set A** words ("Allow filing"/"Stop filing"; FILING ALLOWED/STOPPED) — he overruled both brains' set B; `AGENTS · N ACTIVE CREDENTIALS`; `Revoke credential`; the order; the receipt as the footer's centre Button; the DESK-WIDE 12 px library repair ratified with it |
| 02 Membership and decisions under Article XI | DONE, the owner reviewed the built face ("Reviewed — merge it") | #659 `f6695090` | 9 descriptors + `kernel.receipt` (+1 public tool, 229); residual 293→284 (223 MCP + 61 HTTP); the grant table/ops/routes; admission with one op + one receipt per logical write both transports; refusal classes 1–4 with receipts in the responses; F13 a real SIGKILL restart with a request waiting; Astra r1 BOUNCE (P0: the PUT body could grant another agent; escaping refusals; receipts discarded by adapters; the 393 scroll edge; api-reference drift) → r2 RATIFY-W-C (the boundary fence ran with no principal) → round three: authenticated boundary fences + nine mutation reds |
| 03 The atlas for the desk | Astra's lane RUNNING (`.tmp/astra-lane-philo-7-03.out`, `../wt-philo-7-03`) | — | brief `.tmp/astra-lane-philo-7-03-brief.md` |
| 04 File it and find it | after 03 (Astra) | — | the OWNER leg via the sidecar; the AGENT leg via a real DESK bearer on `/api/mcp` (an owner-token fallback does NOT satisfy it); the R3 observational claim; the zero-read fence must FAIL on the Phase 5 logs |

Also on main today: the Phase 5 rehearsal driver's resource-catalogue reconciliation (#653 `02a862f2`: Codex's built-ins `list_mcp_resource_templates`/`list_mcp_resources`/`read_mcp_resource` are JSON-RPC `resources/*` on the wire; exact two-way result equality; the exact Codex error wrapper) — story 04 needs it; and the THREE inherited reds of the DeskOS Web Quality chain (#654 `4d427d9c`: a z-index literal; a test's `innerHTML` cleanup; an UNHANDLED vitest error from a sparse fixture in `mergeRefreshItems`) — the first green Web Quality since the Phase 6 closure.

## The road to the close

1. **03** (Astra builds; Muad'Dib checks on built): the named browser cases at both widths or "not on the face" with the source line; `.op` siblings reading the kernel receipts; real vs replay folders; the counts over both atlas files. Watch for: the rig's faithful carriage of revision-bearing writes (story 02 put delete revisions in `data`); "not on the face" never waiving story 04's shots.
2. **04** (Astra drives Codex; Muad'Dib checks): the launch setup (empty scratch root outside every checkout, scratch `CODEX_HOME` with only the auth file, `--ignore-user-config --ignore-rules`, no preamble, the isolated hub the only server); two legs; first-run unknowns to RECORD (Codex 0.155's bearer to an HTTP MCP server from the cold config; reaching its engine with a scratch `CODEX_HOME`). The owner reviews the shots; the evidence reads "REHEARSED; OWNER REVIEW PENDING".
3. **The close:** `final-summary.md` with both brains' verdicts per story, the pre-fix reds, the ledger of what he still cannot do; the exits from the phase status; his word by AskUserQuestion; the README "Current phase" line; memory + handover XXX.

## Debts filed today (BACKLOG, in order of owner cost)

- The six NON-DESK two-step terminal writes (admission refusal, native failure, reject, claim refusal, `recover_invalidated`, the reaper) leave `refused` with `receipt=NULL` when interrupted — "PHILO-7-02 lifecycle beat follow-ups"; a kernel story after Phase 7.
- A DESK credential is labelled `ALL` (`resolve_palette("DESK") == resolve_palette("ALL")`; `mcp_http.py:209-214`) — "PHILO-7-02 canvas follow-ups"; fix at the issue/store/read boundary, never by reversing the map.
- An HTTP filing of a tombstoned Thought's note returns 500 as on main (now with its receipt) — story 02's round two.
- The 11/10 px rules that do not render in the Settings window (the canvas README lists them) — the library's next pass.
- Story 03 must give the rig faithful MCP carriage for every admitted write (Astra on lane 01).

## The laws the day taught (add to the method)

1. **Read vitest's `Errors` line.** 2872 passed with `Errors 1 error` is a failure; a grep for `Tests` alone reported a red chain as green and I wrote it on a PR. Every web-chain claim reads the whole summary.
2. **A record commit is checked with `git show --stat`.** A python edit whose assert fails leaves a commit whose message claims what it did not write. I did it twice today (the canvas ratification; the lane's BACKLOG row).
3. **A generated-doc drift is a Documentation Navigation red.** `web/src` edits change `docs/generated/boundary-candidates.json`; run every `--check` before pushing a web change.
4. **The grant belongs to the agent, not the token.** Keyed by the principal identity; survives reissue and restart; an owner revoke of the credential revokes it durably FIRST; the chip derives from the kernel's time-aware check, never from stored state.
5. **A boundary fence runs with an authenticated principal.** With `principal=None` the refusal path writes nothing by construction and a wrong-journaling mutation stays green (Astra's false-negative catch).
6. **The face's canvas carries the library fixes it needs.** The 12 px floor was the library's debt; the canvas could not be ratified geometry while violating it, so the canvas PR carried the token change desk-wide (baseline clean, sampled on two other surfaces).
7. **The owner overrules both brains and that is the record.** Set A over set B; the reason (short) stands beside the ruling, never re-argued.
8. **A lane's own checks are labelled.** Astra-invoked `claude -p` checks are never written as Muad'Dib's counsel; the checks directory holds both, named.

## Open on the owner's desk

- None owed. The next word is the phase close after 03 and 04 (his review of the story 04 shots).

## Late addendum (2026-09-25 evening): Astra out of quota; the day parked

- **Astra's Codex account hit its usage limit at 15:38 MDT mid-lane on story 03** ("try again at Sep 26th, 2026 8:50 PM"). The owner ruled (AskUserQuestion): **"Build on; Astra checks on return"** — 03 and 04 build with Muad'Dib's workers and Muad'Dib's own counsel on built; the PRs STAY OPEN and merge on Astra's verdict.
- **03 The atlas for the desk — BUILT, PR #663 @ `ae1c99a8` (open):** `atlas-phase7.json` 27 cases (9 face + 18 `.op`), 85 + 36 + 27 = 148; 8/9 face cases pass at both widths; `case.p7.decision_delete.gone` FAILS at both — a real Desk defect (the undo receipt renders at y=−12, `WorldStage.tsx:245-250`; filed, BACKLOG "PHILO-7-03 follow-ups" with two more face findings); every `.op` reads its receipt with actor checks, the supersede receipt names the successor; equivalence 18/18 pair-widths over 9 shared op runs, the refusal leg not applicable on 6 (stated); rig 1.4.0 (two more carriage faults refused by name; `op_facts`; `capture_more`; `focus`; `at_width`). Muad'Dib's counsel: RATIFY-W-C (`checks/story-03-built-muaddib.md`; F2/F3 paid in `checks/story-03-round-two-muaddib.md`). **For Astra:** C1 rule on "each admitted write" — the admitted writes with no atlas receipt read (HTTP `decision.status`, `zone.delete`, kb create/update with members or id, zone move/create-with-id, the Thought-note delete, delegation grant/revoke); C2 the new-file placement (`atlas-phase7.json` vs adding to the two files); Astra's own untracked `design.md`/`orientation.md`/baselines are parked in `../wt-philo-7-03`, never deleted.
- **04 File it and find it — BUILT, BLOCKED, draft PR #661 @ `42965f5a` (open):** the driver `scripts/philo7_file_and_find.py` + 46 fences (the zero-read fence RED on the Phase 5 logs, as required); every Codex session reached the isolated hub and its `tools/list`, then failed at the first model call on the SAME quota (the rehearsal runs on the owner's Codex account). First-run answers: Codex 0.155.1 SENDS the DESK bearer over HTTP (the AGENT leg needs no sidecar); a scratch `CODEX_HOME` with only `auth.json` logs in; the LAN engine reachable; `--disable apps --disable plugins` is required (Codex's own connectors would be a second server). The driver is untested past the handshake. **The rerun (after Sep 26 20:50, after 03 merges and 04 rebases):** `npm --prefix web run build`, then inside `.githooks/dw evidence capture holdspeak-philo 7 04 -- env HOME=$(mktemp -d) HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright .venv/bin/python scripts/philo7_file_and_find.py run --out pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/final --codex-auth $HOME_REAL/.codex/auth.json`.
- Also merged: the `docs/README.md` tool count 229/42 (#662), which the drift guard had flagged since #659.

## For the next session

Read this, then the running memory. **If Astra's quota is back (after Sep 26 20:50):** `scripts/astra check` on PR #663 (brief: the story, my counsel's C1/C2, the round-two record); pay rounds; merge on the fast jobs; then rebase #661 on main, run the story 04 rerun command above, check it (Astra + Muad'Dib), publish the shots for the owner, his review, merge; then the close (`final-summary.md`, both brains' verdicts per story, the reds, the ledger; his word). **If not yet:** nothing merges; the Desk defects on the backlog (the delete receipt off-screen first) are lawful Muad'Dib work meanwhile. Worktrees: `../wt-philo-7-03`, `../wt-philo-7-04`.
