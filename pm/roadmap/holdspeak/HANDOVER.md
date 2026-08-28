# HANDOVER — the Door is open (written 2026-08-28)

For the next agent. This file supersedes the 2026-08-27 functional-era
handover (historical now). Read this whole file, then orient
(`.githooks/dw context holdspeak --compact` — ignore `dw next`'s stale
phase-91; the README "Current phase" line is truth), then go. The
owner's verb is still "gooo" — run the full arc without asking
permission at each step, and put a short menu in front of the owner
only where this file says the decision is theirs.

## 1. What the world looks like now

- **Phase 144 (The Dashboard Door) is COMPLETE, 6/6 — and UNPUSHED.**
  Main is still at `ab79c702` (Phase 143 close). The whole phase lives
  on a stacked branch line: charter `2fad6037` →
  `feat/hs144-01-door-read-model` (`dff2ac01`) →
  `feat/hs144-02-calendar-ingest` (`e2e1df79`) →
  `feat/hs144-03-kanban-glass` (`851178de`) →
  `feat/hs144-04-upcoming-rail` (incl. `fad9a2ed`) →
  `feat/hs144-05-docs` → `feat/hs144-06-walk-close` (close
  `3d8ca1df`). The tip contains everything; a single PR of the tip
  branch delivers the phase.
- **The product**: `/` opens First Sentence (untouched), then reveals
  the Door — the five-column board (`GET /api/door` + `door.get` MCP
  twin; every card affordance a server-named lawful verb; success =
  the board changing, failure = a named in-flow refusal), the
  UPCOMING rail (calendar EVENT + SCHEDULED RECORDING merged
  server-side, one fetch), a one-click Schedule-recording action, the
  393 Go navigator, and a deterministic `/meetings` deep-link
  (server registry fact). The first calendar code in the product's
  history: one ICS subscription (file/HTTPS) under
  Settings→Meetings, bounded parser, no-redirect wire posture,
  last-good-projection law. Inventories: 135 MCP tools / 30 families /
  538 API routes / 16+16 resources (29 non-owner listing vs 32 owner
  discovery — do NOT "correct" one to the other; docs/MCP_SIDECAR.md
  explains).
- **The record**: `phase-144-the-dashboard-door/final-summary.md`
  (the exit record: walk table, ten-audit/zero-bug posture, the
  seven judgment-call register, consolidated ledger),
  `current-phase-status.md` (settled design + decision log incl. the
  close-counsel verdict), `evidence-story-01..06.md` (each with an
  orchestrator triage note), `assets/story-06-walk-report.md` + the
  before/after pairs. The reusable cold walk:
  `scripts/door_walk_hs144.py` (7 legs, failable, prints cleanup).
- **Close counsel**: RATIFY-WITH-CONCERNS, ZERO should-fixes. Two
  concerns ledgered by recorded disposition (see §5).

## 2. OPEN OWNER GATES (do not act without the word)

1. **Shot verdicts.** Three shot sets were delivered (the board set,
   the rail/Go/settings set, the closing exhibit). "Good work!" at
   handover is praise, NOT a verdict — a flinch on any shot is a
   redo; the nod is the merge trigger.
2. **The merge word.** Push/PR/merge ONLY on the owner's explicit
   word. CI is dead (out of GH minutes) — merge without watching
   checks when told. The PR is the tip branch
   (`feat/hs144-06-walk-close`) → main.
3. The optional **attended speech leg** of the walk (real-model
   first-capture on `.43`) exists as a labelled addendum the owner
   may order; never run it unattended.

## 3. What to work on next (present a short menu)

1. **The Door polish pass** — the two counsel concerns (393 board
   scroll hint; a "connect calendar" affordance on the empty rail)
   plus whatever the owner's shot verdicts add. Small, high-joy.
2. **Phase 139 re-scope check** — the Settings Reckoning is recorded
   COMPLETE 8/8 (PR #465) in the repo; the previous handover's "0/7"
   claim was stale. Nothing to do unless the owner reopens it.
3. **Backlog candidates minted by 144** (add to BACKLOG.md when
   chartering): the scheduled-recording conductor shutdown gap
   (needs a web_server lifecycle test pattern first); the
   trust-destinations registry entry for the calendar fetch (build
   REAL enforcement, never a data-only entry); multiple calendar
   subscriptions; calendar-event → one-tap scheduled recording.
4. `pm/roadmap/holdspeak/BACKLOG.md` — the parking lot; don't
   mega-bundle.

The standing charter questions: **"will you use this on a tired
Tuesday?"** and **"does this operate with joy?"**

## 4. The standing laws (violate none — same as last era, plus new)

1. **YOLO bar + TIE-BREAKER.** Findings count only when a normal
   product action reproduces damage; races/crash-windows = ledger
   notes even when reproducible. YOU tie-break over all counsel/audit
   output. (This era: ten audits, zero product bugs, two counsel
   concerns ledgered by disposition — the bar works.)
2. **Ceremony budget.** Open choices become [ORCH-CALL]s the plan
   worker recommends and YOU rule, dispositions appended to the plan.
   Counsel: one close pass; the 144 close cost zero fix rounds.
3. **Models.** Terra workers (`model: "terra"` on general-purpose)
   only paired with opus legs in the same arc; `opus-worker` for
   audits/counsel; never Fable subagents; author PMO/roadmap content
   YOURSELF.
4. **CI is dead.** Local verification only. Push/merge only on the
   owner's word.
5. **Shots before merge** on every owner-facing surface — and LOOK at
   every shot yourself before the owner does (this arc: the
   orchestrator's eye caught a clipped column at 1440 and the counsel
   caught a shot showing the wrong surface; both were redone, not
   renamed). A shot must show what its name claims.
6. **Web is the spec**; Swift stays frozen.
7. **Never delete — park instead.**
8. **Isolated HOME always** for anything that can open a DB —
   generators included. Always `uv run --python 3.13.11`.
9. **No modals; no prose in UI; mic on every text input; one egress
   badge; errors in-flow; replace-never-sit-beside; height-cap
   grammar** (content obeys the working band, never the reverse —
   see `fad9a2ed`).

## 5. The consolidated ledger (carried, owner-visible)

| Item | Class |
|---|---|
| `_active_thoughts` pagination spin (needs concurrent write mid-page) | theoretical race |
| Calendar conductor global double-start (single call site) | theoretical race |
| Calendar conductor thread runs when unconfigured | sibling-consistent pattern |
| Scheduled-recording conductor shutdown gap | PRE-EXISTING; backlog candidate |
| trust-destinations lacks the calendar-fetch entry | named product gap; backlog candidate; NEVER fake a data-only entry |
| 393 board scroll hint absent | counsel concern → next polish pass |
| Calendar setup undiscoverable from the Door | counsel concern → next polish pass |

**xdist watch items** (serial-green flakes, one occurrence each in the
last sweeps): `test_phase143_inference_capability_census::…fixture_is_
complete_and_fail_closed` and `test_calendar_ingest_conductor::test_
boot_and_tick_contain_fetch_and_parse_failures`. Recurrence =
DIAGNOSE (the 143 hydration-race precedent), never a label.

## 6. Sweep + baseline mechanics (what changed since last era)

- **The baseline** is still `phase-143-intelligence-router/assets/
  story-08-inherited-failure-baseline.txt`. Every 144 close sweep
  came back baseline-exact; typical counts 11–14 failed with only
  baseline + named-family/flake names. Never call it "broken" or
  "green": say **baseline-exact, zero branch-new**.
- **Capture + readable sweep are a PAIR.** `dw evidence capture`
  truncates output before the pytest summary — you cannot triage from
  it. Run the plain readable sweep (nohup + Monitor on the PID) and
  READ its FAILED names, then the dw capture as the stamped record
  (it lawfully exits 1; plain contract, certify Tests-ran on the
  output you read; note the pairing in your triage note).
- **Env-ordering gotchas (both burned this arc, both in memory):**
  prefix assignments expand LEFT-TO-RIGHT — `HOME="$(mktemp -d)"
  PLAYWRIGHT_BROWSERS_PATH=$HOME/...` poisons the browser path; put
  `PLAYWRIGHT_BROWSERS_PATH="$HOME/…" npm_config_cache="$HOME/.npm"`
  BEFORE `HOME="$(mktemp -d)"`. And `HOME_REAL=$HOME nohup …
  $HOME_REAL/…` expands `$HOME_REAL` to empty (the assignment doesn't
  exist yet on the same line) — use plain `$HOME` inside `env`
  commands exactly as the recipe writes it.
- **After every sweep**: `git checkout --` the phase-141 assets AND
  phase-143 `story-12-shots` AND phase-144 `story-03-shots`/
  `story-04-shots` — the glass e2es clobber all of them.
- **Any new HTTP route drags `scripts/gen_api_surface.py` regen into
  the round** (the manifest guard caught the one we forgot — guards
  are friends). Any new MCP tool moves the `scripts/mcp_walk.py`
  exact-count guard. Regens are the LAST act of a round, isolated
  HOME mandatory.
- Known flake families: the previous handover's §6 list still holds
  (glass-under-load 1440/393 legs, refinement recovers-owner, etc.);
  serial ×2 is the protocol; the fixed assignments-overview 393 leg
  stayed fixed (its s5 SIBLING flaked under load twice — family
  behavior, not the fixed leg).

## 7. Orchestration knowledge (this arc's additions)

- **The story pipeline ran two-deep the whole phase**: build round N
  while the opus audit reads round N-1's COMMITTED diff and a Terra
  planner (read-only) pre-stages the NEXT story. Six stories closed
  in ~one day this way. Plan workers return [ORCH-CALL]s WITH
  recommendations; you rule and append dispositions; builders get
  "the dispositions are RULED" in their brief and don't relitigate.
- **Workers die on transient API errors** (WebSocket 1006/500,
  provider timeout — five times this arc). `SendMessage` to the same
  agent id ALWAYS resumes with full context. Resume brief: transient,
  not a refusal; `git status --short` first; dirty work beyond the
  named pre-existing files is yours — keep it.
- **Verify typecheck-provenance claims yourself**: `git stash` →
  count errors at HEAD → `git stash pop` → count dirty. One worker's
  "pre-existing" claim was TRUE this arc (13=13), another round
  REDUCED the count (14→11) — but the handover-era warning stands:
  workers misfile their own breakage.
- **The walk harness pattern**: standalone `scripts/` walker, a
  self-auditing ClickLedger as the ONLY click gateway, SHA-256
  byte-identical guard on before/after pairs, parity-vs-improvement
  marked honestly, cleanup that prints. Rerun it YOURSELF before the
  flip — the done call is never delegated.
- **Scope amendments are visible or they don't happen**: story 03's
  plan found `people.commitment.transition` was MCP-only; the fix
  entered as a named slice-0 amendment in the story file + decision
  log, owner-overrulable. Same for the walk's leg-1 model-less scope.
- **dw specifics**: the charter's story table MUST be the
  `## Story status` five-column format or dw can't parse stories;
  contract AFTER staging; one story flips done per commit; when all
  stories are done `dw check` demands `final-summary.md` — author it
  yourself before the last flip.

## 8. Memory

`~/.claude/.../memory/project_phase144_dashboard_door.md` holds the
arc detail (branch line, ledger, gotchas). MEMORY.md's Active list is
current as of this handover. The Phase-139 "IN PROGRESS" memory
staleness was corrected this arc — trust the repo over old memory
lines, always.

Go get the owner's verdicts, merge on the word, then open the next
functional door. The engine is proven; the front of the house finally
matches it.
