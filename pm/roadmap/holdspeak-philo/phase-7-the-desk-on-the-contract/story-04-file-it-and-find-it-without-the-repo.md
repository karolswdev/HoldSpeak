# PHILO-7-04 - File it and find it without the repo

- **Project:** holdspeak-philo
- **Phase:** 7
- **Status:** in-progress
- **Depends on:** PHILO-7-03
- **Unblocks:** the phase close
- **Owner:** Astra (Luna); Muad'Dib checks
- **Council tag:** the owner's D4 as amended by R3; R1; Astra's check of the drafts, finding 7 and MISSED 1, 4; Astra's charter check r2, findings 4 and 7

## Problem

The Phase 5 rehearsal proved ordinary prompts with client discovery in this repository; "it does not prove discovery without repository access" (`docs/internal/philo/phase-5/his-words/rehearsal.md:49-50`). Codex read repository docs and source, and the `scripts/astra ask` preamble led it to the canon documents (`rehearsal.md:49`); the decision turn took 201 s (`:43`) and 25 repository reads (`pm/roadmap/holdspeak/BACKLOG.md:1216`). In the Phase 6 driver run Codex chose `door.add_item` for a desk decision (`BACKLOG.md:1225`). D4 makes discovery from the catalogue alone an acceptance criterion. The owner narrowed what that proves (R3, 2026-09-25): the claim is observational, not a filesystem sandbox. And the loopback sidecar forwards the hub's owner token (`holdspeak/mcp/server.py:144-190`), so a sidecar run proves only the OWNER path; R1's AGENT path needs its own leg (Astra r2 finding 4).

### The claim (R6: Claude closes it; R3's qualification intact)

R6 (the owner, 2026-09-25 evening, by AskUserQuestion): "Claude closes it" — the closing client is a cold-context Claude session on Opus 5.5, not Codex. The claim for the closing run, reworded for Claude: this story claims exactly "a cold-context Claude session (an empty scratch dir, a scratch HOME with only the auth file, no user or project instructions, `--strict-mcp-config` with the one holdspeak server, no preamble), ZERO repository reads in the retained log, discovery from the catalogue alone". It is observational, as R3 ruled: the setup keeps the repository out of the session's context and instructions, and the zero-read fence over the retained log is the proof that no read happened.

### The claim as R3 worded it for Codex (kept; the Codex path stays in the driver)

This story claims exactly: "cold context (an empty scratch dir, scratch HOME/CODEX_HOME with only the auth file, `--ignore-user-config --ignore-rules`, no preamble), ZERO repository reads in the retained log, discovery from the catalogue alone". It is NOT a filesystem sandbox: the setup withholds the repository from Codex's context and instructions, and the zero-read fence over the retained log is the proof that no read happened. The story never claims that repository access was unavailable.

## Scope

- **In:** Astra drives Codex from a cold-context session (the claim above), launched as named below, through ordinary requests: "file this note into <zone>", "find it", "put this decision on my review list", "make my brief"; TWO legs (below): the OWNER leg through the sidecar and the AGENT leg through a DESK credential; the MCP transcript, the Codex event log and the Desk shots at 1440 and 393 retained; readbacks through the contract; the receipts of the filed and decided writes read back; Muad'Dib checks; the owner reviews the shots.
- **Out:** "attach it to a meeting" (dropped: no durable relationship in this slice); already-open Desk refresh (D4: a reopened Desk read); a live sitting; any face change.

### The launch setup (D4 as amended by R3, concrete)

An outside working directory alone does not withhold the repository (`checks/charter-astra-r1.md` finding 5). The session is launched so that nothing points it at the repository:

1. **Working root:** `codex exec --skip-git-repo-check -C <an empty scratch directory>` created under the run folder's temp root, OUTSIDE any checkout. No `AGENTS.md`, `CLAUDE.md` or `.codex/` exists in it or in any parent directory (the driver checks every parent up to `/` and records the check).
2. **Codex's own config:** a scratch `CODEX_HOME` (and a scratch `HOME` for the Codex process) that holds ONLY the auth file Codex needs to reach its engine; no `config.toml`, no project trust entries, no rules, no profiles, so `~/.codex` project trust cannot pull the repository in. `--ignore-user-config` and `--ignore-rules` are passed as well. The effective config is dumped and retained (Phase 5 precedent: `effective-codex-config.json`).
3. **No preamble:** the first prompt is the owner's words alone. Not `scripts/astra ask`: its preamble led the Phase 5 session to the canon documents (`docs/internal/philo/phase-5/his-words/rehearsal.md:49`).
4. **The MCP server** is the ONLY configured server, pointed at the isolated hub only. OWNER leg: the built sidecar (`-c mcp_servers.holdspeak.command=<the built holdspeak-mcp>`, `-c mcp_servers.holdspeak.env.HOME=<the isolated hub's HOME>`), which forwards the hub's OWNER token. AGENT leg: the hub's real `/api/mcp` route with the DESK credential as the bearer, no sidecar and no owner token. The server is product, not context: its own process working directory is not the model's.
5. **Retained:** the complete initial context (the exact command, environment, prompt, the effective config and the working-root listing) and every event (`events.jsonl`, rollout) per turn.

The setup withholds the repository from Codex's context and instructions; it is not a filesystem sandbox (R3). The zero-read fence over the retained event log is the proof that no read happened.

### The two legs

1. **The OWNER leg** (the Tuesday job). The sidecar forwards the hub's owner token (`holdspeak/mcp/server.py:144-190`; accepted only on loopback, `holdspeak/web/routes/mcp_http.py:127-131`), so this leg proves the OWNER path: each admitted write approved inline as the owner's gesture (`docs/internal/CONSTITUTION.md:184-187`), executed, terminal receipt with the owner principal.
2. **The AGENT leg** (R1). A SECOND Codex session with the same cold context, whose MCP server is the real `/api/mcp` route with a DESK credential issued through the real settings route (`POST /api/settings/remote/credentials`, `holdspeak/web/routes/mcp_http.py:270`), the Phase 5 boundary-fence form (`../phase-5-the-one-service-layer/current-phase-status.md:219`). The same ordinary request ("file this note into <zone>") is run twice:
   - **without the grant:** REFUSED; the refusal receipt names `desk_delegation_required`; the note is not filed; nothing is held.
   - **with the grant** (the owner grants it through `delegation.grant`, story 02, before the second run): the write executes at once; its receipt names the delegation (`authority_basis = desk-delegation:<id>:<terms_sha256>`, `delegator_kind = owner`), and the actor on the receipt is the agent identity.
   Both outcomes fenced through the real remote route and read back through the contract.

## Acceptance criteria

- [ ] The claim is worded exactly as R3 (above) in the evidence and the rehearsal record; no record calls it a sandbox or says repository access was unavailable.
- [ ] The requests are ordinary words; no operation name, argument, id or test clock appears in them.
- [ ] The launch setup above is used and its initial context retained: the working root is empty and outside every checkout; no `AGENTS.md`/`CLAUDE.md`/`.codex/` in it or its parents; the scratch `CODEX_HOME` has no config, trust entries or rules; the MCP server is the only server and points at the isolated hub.
- [ ] Discovery from `tools/list` alone: the Codex event log shows ZERO reads of repository files, source or roadmap documents (a fence over the retained event log). The fence MUST FAIL on the Phase 5 rehearsal's logs (`pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/codex/*/events.jsonl`: 25 completed shell commands in `decision_thought`, 3 in `import`). Every tool chosen appears in the session's `tools/list` answer.
- [ ] The note is filed into the named zone and found again; the decision is on his review list; the brief is made; each read back through the contract (`op`), not from Codex's own text.
- [ ] OWNER leg: the receipts of the filed and decided writes (the admitted set) are read back; one per logical operation, each terminal. The principal on each receipt is the OWNER the transport derived (the loopback sidecar forwards the hub's owner token, `holdspeak/mcp/server.py:144-190`), unchanged.
- [ ] AGENT leg: the second session's DESK credential is issued through the real settings route; without the grant the write is refused with a refusal receipt naming `desk_delegation_required` and the note is not filed; with the grant the same request executes and its receipt names the delegation. Both fenced through the real remote route (not the sidecar), each receipt read back through the contract. The agent session also meets the cold-context claim and the zero-read fence.
- [ ] Run against an isolated HOME; the effective HOME, lock and DB path retained; never the desk.
- [ ] The Desk reopened and shot at 1440 and 393: the note in its zone, the decision in the review rows, the brief. Real-engine and replayed runs labelled separately.
- [ ] Technical rehearsal completes with Muad'Dib's check recorded; the evidence reads "REHEARSED; OWNER REVIEW PENDING", never an observed sitting.
- [ ] The owner reviews the published shots; the review recorded in the tree.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

PROVISIONAL: 1–2 engineering days (the phase estimate). Phase 5's rehearsal (326 s run; about 1 engineering day with its repairs) is the precedent; the new launch setup and the AGENT leg add the rest.

## Test plan

- **Unit:** the no-repository-read fence over a Codex event log (it must fail on the Phase 5 logs named above); the AGENT-leg receipt check (refusal without the grant, the delegation named with it); the launch-setup check (working root, parents, `CODEX_HOME` contents); the transcript-to-server pairing audit carried from Phase 5.
- **Integration:** the rehearsal driver against an isolated hub; the transcript, config, DB and lock proof, and shots retained under this phase's assets.
- **Manual / device:** the owner reviews the shots (rehearsed, owner-reviewed).

## Notes

- 2026-09-25 — drafted by Muad'Dib from handover XXVIII r2 §Road B, Astra's check of the drafts and the owner's D4; unratified. "Attach to a meeting" dropped from the closing job (Astra MISSED 4).
- 2026-09-25 — r2: the launch setup made concrete (Astra's charter check, finding 5). Unknown until the first run: whether Codex 0.155's `--ignore-user-config` with a scratch `CODEX_HOME` holding only the auth file reaches its engine; the driver records the answer.
- 2026-09-25 — r3 (the owner's R3 and R1; Astra's charter check r2, findings 4 and 7): the claim worded exactly as R3 (observational, not a sandbox); the OWNER leg through the sidecar named for what it proves; the AGENT leg added (a second session with a DESK credential, refused without the grant, executing with a delegation receipt with it). Unknown until the first run: whether Codex 0.155 sends a bearer credential to an HTTP MCP server from the cold-context config; the driver records the answer, and the AGENT leg's transport is settled there.
- 2026-09-25 — r4 (Astra's charter check r3, finding 7): the observational claim RATIFIED as worded; the AGENT leg must use a real DESK bearer on `/api/mcp` — an owner-token fallback does NOT satisfy it; bearer handling stays a first-run unknown. The file name "without the repo" is a label; the claim is R3's, never "without repository access" unqualified.
- 2026-09-25 — built by the Fedaykin lane (`feat/philo-7-04-cold-context`): the driver `scripts/philo7_file_and_find.py` and the fences `tests/unit/test_philo7_file_and_find.py`. The first attempt is BLOCKED at the model call by the Codex account's usage limit (until Sep 26, 2026, 8:50 PM); the launch setup, both legs' MCP handshakes and the grant are retained. First-run answers: Codex 0.155.1 sends the DESK bearer from the cold config; a scratch `CODEX_HOME` with the auth file alone authenticates. Lane report: `lane-report-story-04.md` (the evidence file ships with the rerun); record: `docs/internal/philo/phase-7/file-and-find/rehearsal.md`. Status stays in-progress: the rerun, both checks and the owner's review are owed.
- 2026-09-25 evening — R6 ("Claude closes it"): the driver drives a cold-context `claude -p --model claude-opus-5-5` session with the same launch discipline (empty root outside every checkout; a scratch HOME holding only `.claude/.credentials.json` with the access token; `--strict-mcp-config` with holdspeak alone; `--permission-mode bypassPermissions`; stream-json retained; no preamble). The closing run `assets/story-04-shots/final/20260926T014230Z-file-and-find/` completed both legs. REHEARSED; OWNER REVIEW PENDING; status stays in-progress (the owner's review of the shots is owed). The gate refuses `evidence-story-04.md` while the story is in progress ("Orphan evidence"), so the captures are in `lane-report-story-04.md`.
- 2026-09-25 evening — the owner reviewed the shots: "something's wrong — the decision is thin: a decision put on my review list should carry its context, not just a title." Repaired on both sides: the owner's words carry the reason; the catalogue (`desk.create`/`desk.update` and the decision fields) names a decision's parts, with the discovery job "the reason for a decision" → `context_markdown` (red on main); the readback checks the durable context; the OWNER leg is shot before the agent leg files. The rerun `final/20260926T015522Z-file-and-find/` completed both legs; the thin run is under `attempts/`. By the owner's ruling, the branch was rebuilt from main with the clean tree only. The owner's review of the new shots is owed; status stays in-progress.
