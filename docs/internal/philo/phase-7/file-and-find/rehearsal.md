# PHILO-7-04 — File it and find it, the cold-context rehearsal

**REHEARSED; OWNER-REVIEWED.** The owner reviewed the rerun on 2026-09-26:
"Reviewed — it's right". No sitting is claimed. The owner ruled R6 ("Claude closes it"): the closing client is a
cold-context Claude session on Opus 5.5, not Codex. The owner reviewed the
first closing run's shots: "the decision is thin — a decision put on my
review list should carry its context, not just a title." The repair
(below) changed the owner's words, the catalogue and the readback. The
closing run
`pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/final/20260926T015522Z-file-and-find/`
completed both legs in 94.8 s. The first run is kept under `attempts/` with
the note "owner review: the decision is thin".

## The claim (R6, with R3's qualification intact)

This story claims exactly: "a cold-context Claude session (an empty scratch dir, a scratch HOME with only the auth file, no user or project instructions, `--strict-mcp-config` with the one holdspeak server, no preamble), ZERO repository reads in the retained log, discovery from the catalogue alone".

The claim is observational (R3). The setup keeps the repository out of the
session's context and instructions. The zero-read fence over the retained
event log is the proof that no read happened. This record makes no claim
about what the session could reach.

## How Claude authenticates on this Mac

Claude Code 2.1.281 keeps the owner's login in the macOS login keychain
(generic password, service `Claude Code-credentials`). There is no
`~/.claude/.credentials.json` and no `ANTHROPIC_API_KEY`. The keychain
entry is not found from a scratch HOME: a scratch HOME with nothing in it
answers "Not logged in · Please run /login" (probed). `security` also finds
the login keychain through `$HOME`.

The driver reads that keychain entry with the account's own home, keeps
`accessToken`, `expiresAt`, `scopes`, `subscriptionType` and
`rateLimitTier`, drops `refreshToken` and `refreshTokenExpiresAt`, and writes
the result to `<scratch HOME>/.claude/.credentials.json` (mode 600). With
the refresh token dropped, a scratch session can never rotate the owner's
login. The driver refuses to run with less than 20 minutes left on the access
token. The run had 325.8 minutes (`claude-auth.json`, which holds no secret).
Every scratch credentials file and MCP config file is deleted when the run
ends. Nothing else under `~/.claude/` is copied.

## The launch setup, as run

| Step | What the driver does | Retained (per leg / session) |
|---|---|---|
| Working root | `claude -p` with `cwd = $TMPDIR/philo7-04-*/cold-<leg>/work`, empty. The driver checks it and every parent up to `/`, as given and resolved, for `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `.claude`, `.codex` and `.git`. All clear. `git rev-parse` exits 128. | `<leg>/launch-setup.json` |
| Scratch HOME | At launch it holds exactly `.claude/.credentials.json`. Env keys: `HOME`, `LANG`, `PATH`, `TMPDIR`, `USER`. The parent session's `CLAUDE_CODE_*` variables do not reach it (`env -i` form). | `launch-setup.json`, `claude/<stage>/environment.json`, `home-at-launch.json` |
| Flags | `-p --model claude-opus-5-5 --output-format stream-json --verbose --strict-mcp-config --mcp-config <file> --permission-mode bypassPermissions`, plus `--resume <session>` for turns 2-4. Built-in tools are not restricted: Read, Glob, Grep, Bash, WebFetch and Task are all in the init tool list, so the zero-read fence is meaningful. | `claude/<stage>/command.txt` |
| The one MCP server | OWNER: `{"type":"stdio","command":"<worktree>/.venv/bin/holdspeak-mcp","args":[],"env":{"HOME":"<hub HOME>"}}`. AGENT: `{"type":"http","url":"http://127.0.0.1:<port>/api/mcp","headers":{"Authorization":"Bearer <DESK credential>"}}`. The config goes in a file beside the work dir, so the bearer is never in the process arguments. | `<leg>/mcp-config.redacted.json` (bearer shown as a sha256 prefix) |
| No preamble | The stdin is the owner's words alone. | `claude/<stage>/owner-prompt.txt` |
| Events | The stream-json stdout of every turn, stderr, the final answer, and Claude's own session transcript. | `events.jsonl`, `stderr.log`, `last.md`, `session-transcript.jsonl` |

**The init event** (every session): `mcp_servers = [{"name":"holdspeak","status":"connected"}]`,
`permissionMode = bypassPermissions`, `model = claude-opus-5-5`,
`apiKeySource = none`, 229 `mcp__holdspeak__*` tools among 257. Its plugins
are Claude's two built-ins (`agents-md@builtin`, `telemetry@builtin`); no
`AGENTS.md` exists in the root or any parent. The memory path points into
the scratch HOME, where no memory exists.

**The initial context** (`initial-context.jsonl`: the session transcript
before the first answer, including Claude's `prompt_snapshot` of the full
system prompt): Claude's own system prompt, its built-in skill and agent
listings, the account's synced skills (the account's own, downloaded after
login; not repository material), the date, the account e-mail
(`session_context`), and the scratch working root. There is no instruction
attachment (`nested_memory`, `claude_md`, `memory`), no "Contents of …
CLAUDE.md / MEMORY.md", and no repository path.

## The ordinary requests

The prompt fence checks each turn before it runs: there is no operation name,
tool name, argument, id or clock in the prompt. The zone and the notes are seeded
through the real producers (`POST /api/directories`, `POST /api/notes`,
`seed.json`) and named by their human names.

| Leg | Turn | The owner's words |
|---|---|---|
| OWNER | file | File my note Runner capacity numbers into my Platform Migration zone. |
| OWNER | find | Now find that note for me and tell me where it is. |
| OWNER | decide | Put this decision on my review list: move the nightly build to the shared runners, because our own runners are full every night and the shared pool has spare capacity after 8 PM. |
| OWNER | brief | Make my brief and tell me what is on it. |
| AGENT (twice) | file | File my note Build cache sizing into my Platform Migration zone. |

## The owner's review and the repair ("the decision is thin")

In the first closing run the decision had a title only. There were two causes. The
owner's words gave no reason, and the catalogue did not lead a client to
fill a decision's parts. The repair:

1. **The owner's words** carry the decision and its reason in one ordinary
   sentence (the table above). The prompt fence still refuses operation and
   argument names, ids and clocks.
2. **The catalogue** (`holdspeak/mcp/tools.py` `desk.create`, `desk.update`;
   `holdspeak/operations.py` `_DECISION_FIELDS`) names a decision's parts in
   plain words. `desk.create` now says: "Write the reason for a decision
   (kind=decisions) in data context_markdown: why, and the facts behind it.
   Write what you will do in data decision_markdown and what follows from it
   in consequences_markdown. Keep the title short; do not put the reason in
   the title." Its `data` argument and `desk.update` name the same parts. The
   decision descriptor fields read "The reason for the decision…", "What you
   will do…", "What follows from the decision…". The catalogue-only discovery
   fence (`tests/unit/test_philo7_discovery.py`) maps the new job "the
   reason for a decision" to `desk.create` kind=decisions, data
   `context_markdown`. It is RED on a copy of main (`red-discovery-reason-main.txt`:
   "is named by [], expected ['desk.create']"). `docs/generated/operations.json`
   and `docs/generated/api-reference.json` are regenerated, and every `--check` is green.
3. **The readback** (`decision_reason_findings`, over the durable
   `decision.read` through the contract): the context is not empty. It names
   that the runners are full and names the shared pool (or its spare capacity).
   The reason is not in the title. The check is RED on the thin run's decision
   ("the decision has no context: its reason is missing").
4. **The shots** are split. The OWNER leg's result is shot before the agent leg
   files (the zone shows the owner's note alone). The agent leg's result is
   shot after. The decision window's context is proved readable at both
   widths: the text is found, visible, in the viewport, hit-tested, 13 px,
   opacity 1.

## Each turn (the tools Claude chose, in order)

| Session | Tools (`hs:` = `mcp__holdspeak__`) | Wall | Client |
|---|---|---|---|
| OWNER file | ToolSearch, ToolSearch, hs:desk_list (notes), hs:desk_list (directories), hs:zone_file | 9.2 s | 7.4 s |
| OWNER find | hs:zone_list_members | 4.9 s | 3.5 s |
| OWNER decide | ToolSearch, hs:desk_create (decisions: title, status proposed, context_markdown, decision_markdown) | 8.0 s | 6.6 s |
| OWNER brief | ToolSearch, hs:monday_brief_generate | 8.0 s | 6.7 s |
| AGENT ungranted | ToolSearch, ToolSearch, hs:desk_list ×2, hs:zone_file → refused | 16.2 s | 15.4 s |
| AGENT granted | ToolSearch, ToolSearch, hs:desk_list ×2, hs:zone_file | 8.5 s | 7.6 s |

`ToolSearch` is Claude's client-side lookup over the listed MCP tools (Claude
defers large MCP catalogues). It reads the catalogue, not a file, and the
fence names it as allowed. Every chosen holdspeak tool is in the session's
init tool list. The pairing audit pairs every holdspeak call with one server
`tools/call` row by name, arguments and the answer text Claude received
(3, 1, 1, 1, 3, 3 of 3, 1, 1, 1, 3, 3). No non-MCP HTTP write happened in any
turn window.

## The zero-read verdict per session

ZERO findings in all six sessions (`mcp-audit.json` `zero_read_findings: []`).
The only tool uses were `mcp__holdspeak__*` calls and `ToolSearch`. A read of
a holdspeak resource is a catalogue read, EXCEPT a resource whose body is a
repository document: `holdspeak://desk/constitution` returns
`docs/internal/CONSTITUTION.md` from the checkout
(`holdspeak/mcp/resources.py:475`), so the fence counts a read of it as a
repository read (`REPO_DOC_RESOURCES`; C1 of the Astra-role check;
`red-constitution-resource.txt`: 0 findings before, 1 after). No session read
it.

**What discovery means here (the Astra-role ruling on ToolSearch).**
`ToolSearch` is a catalogue lookup: every call was `select:mcp__holdspeak__…`
over the names in Claude's `deferred_tools_delta` (its rendering of the
server's `tools/list`), and its results are tool references only. Claude
chose its tools mostly by NAME from that deferred list and saw a tool's
description only after selecting it. So the names did most of the
discovery. The new description words were decisive only for where the reason
went (`context_markdown`). That placement is confounded with the changed
owner's words: there was no run of the new words against the old catalogue.

**"Find it" means "find it again".** The find turn resumed the session and
called `zone_list_members` with the zone id from the first turn. It did not
search the Desk. This proves "find it again", not "find it cold".

## Readbacks through the contract

| Readback (`op`, over `/api/mcp` as the owner) | Result |
|---|---|
| `zone.members` of Platform Migration | `note:<Runner capacity numbers>`; after the AGENT leg also `note:<Build cache sizing>` |
| `note.read` | the owner's note |
| `decision.list` | exactly one decision about the nightly build, `decision_32cacbceb68d`, status `proposed` |
| `decision.read` | title "Move nightly build to shared runners"; context "Our own runners are full every night. The shared runner pool has spare capacity after 8 PM."; decision "Move the nightly build to the shared runners." |
| `brief.latest` | "1 decision waiting."; a row with `source_ref = decision:decision_32cacbceb68d` |
| the find turn | the server's `zone.list_members` answer names the note and the zone by id |

## The receipts (read back through `kernel.receipt`)

| Operation | Receipt | Actor | Authority |
|---|---|---|---|
| OWNER `zone.file` (`op_027cf7bd…`) | `succeeded` | owner / `owner-session` | `authenticated_principal+declared_capability+hard_prerequisites+interruption_policy` |
| OWNER `decision.create` (`op_05e57df1…`) | `succeeded` | owner / `owner-session` | the same |
| `delegation.grant` (the owner, `PUT /api/settings/remote/delegations/claude-desk-agent`) | `succeeded` | owner | — |
| AGENT `zone.file` without the grant (`op_d67ce56e…`) | `refused`, outcome `desk_delegation_required` | agent / `claude-desk-agent` | `refused_at_admission` |
| AGENT `zone.file` with the grant (`op_6140cca5…`) | `succeeded` | agent / `claude-desk-agent` | `desk-delegation:deskdeleg_87740697…:sha256:a254fdaa…`, `delegator_kind=owner` |

One operation per logical write, each terminal. Without the grant, the note
was not filed and no operation was left `awaiting_decision`. The only brief
write is the brief itself, which is not an admitted operation.

The DESK credential was issued through `POST /api/settings/remote/credentials`
(identity `claude-desk-agent`, palette `DESK`). Claude sent it as the bearer
from the MCP config's `headers`: every `/api/mcp` POST answered 200/204, and
the credential's `last_used_at` is set. No owner token was used on the AGENT
leg.

## The Desk, reopened (a fresh read, not an already-open refresh)

OWNER leg, shot before the agent leg files:
- `shots/owner-zone/1440.png`, `shots/owner-zone/393.png`: Platform
  Migration, "1 member": Runner capacity numbers.
- `shots/owner-decision/1440.png`, `shots/owner-decision/393.png`: the
  decision, `proposed`. DECISION CONTEXT: "Our own runners are full every night. The
  shared runner pool has spare capacity after 8 PM." DECISION: "Move the
  nightly build to the shared runners."
- `shots/brief/{1440,393}.png` (the `-receipt` and `-row` files are full-shot copies, byte-identical to the shot): BRIEF · 1
  THING WAITING, "Review decision: Move nightly build to shared runners",
  "Brief ready · 1 item".

AGENT leg, shot after the delegated filing:
- `shots/agent-zone/1440.png`, `shots/agent-zone/393.png`: Platform
  Migration, "2 members": Build cache sizing and Runner capacity numbers.

## The engine

The LAN engine `192.168.1.43:8080` answered (`engine-preflight-curl.txt`).
The four jobs call no model: filing, finding and recording a decision are
desk writes, and the brief producer is deterministic
(`holdspeak/services/monday_brief_service.py` `generate`). The run is
labelled `engine_mode: none`. It is neither a real-engine run nor a replay.
The Desk's "No engine for summaries" row is true for the rig hub.

## Isolation

The hub HOME, DB and lock are under `$TMPDIR/philo7-04-*/hub-home`
(`hub-proof.json`, `hub-proof-final.json`, `db-proof.sqlite`,
`db-owner.lock`). The owner's desk was never used.

## Account redaction (the repository is public)

Claude's own records carry the signed-in account: its e-mail (the
`session_context` attachment), its organisation id (`credential_org`, the
synced skill folders), and the names of the account's synced skills. The driver
rewrites every retained file at the end of a run (`redact_run`). Every e-mail
address becomes `<owner-account-email>` (product addresses become
`<email-address>`). Every account or organisation id becomes `<account-id>`.
The account's synced skill names become a count
(`<N account skills, names redacted>`). Tool names, the MCP server list and
attachment types stay; no fence reads what is removed. The first closing run
(now under `attempts/`) was captured before this step existed, so the same
redaction was applied to its retained files afterwards (18 files). The
closing rerun was redacted at capture (`redaction.json`: 17 files, 2 ids, 14
skill names). By the owner's ruling, the branch was rebuilt from main with the
clean tree only, so its history holds no e-mail. The fence `account_leak_findings` checks every file under
`story-04-shots/` for an e-mail address or a JWT-, `sk-ant-`- or
bearer-shaped string. It was RED on nine files before the redaction
(`red-account-scan.txt`) and is green after.

## The fences and their reds

`tests/unit/test_philo7_file_and_find.py`:

- **Zero reads (Claude):** RED on a real `claude -p` in the same cold setup
  told to read `<repo>/CLAUDE.md` (it ran `head -n 1 <repo>/CLAUDE.md` through
  Bash; `red-claude-read/`). Seven injected tool uses (Read, Glob, Grep, Bash,
  WebFetch, Task, a resource read of another server, a holdspeak read of
  `holdspeak://desk/constitution`) each turn it red.
- **Zero reads (Codex, kept):** RED on the Phase 5 logs (25 + 3 = 28,
  `red-zero-read-phase5.txt`). The combined fence reads both formats.
- **Tools from the init list:** if a chosen tool is removed from the init list, the check is red.
- **Init:** a second server, a failed server or an API key each turn it red.
- **Initial context:** an instruction attachment, an instruction file's
  contents, a memory file's contents or the repository path each turn it red.
- **Launch (Claude):** nine mutations each turn it red: `CLAUDE.md` or `.claude`
  in a parent, `AGENTS.md` in the root, a settings or memory file in the scratch
  HOME, a second server, a sidecar pointed elsewhere, an AGENT server without a bearer or
  at another URL. The Codex launch fences are kept.
- **Pairing:** one changed server answer is refused.
- **AGENT receipts:** the closing run's receipts pass. Swapped receipts,
  another grant, another actor or a missing run each turn it red (over
  receipts minted by the real hub through the real remote route).
- **The reason (the owner's review):** `decision_reason_findings` is RED on
  the thin run's decision and on three mutations (no context, the reason in
  the title, a context without the reason). It is green on the closing
  decision, read back through `decision.read`.
- **Discovery:** "the reason for a decision" maps to `desk.create`
  `context_markdown` from `tools/list` alone. It is RED on main
  (`red-discovery-reason-main.txt`).
- **The shots:** the owner zone shot is taken before the agent files (the agent note is
  absent). The decision context is readable at both widths. The agent zone
  shot shows both notes.
- **Wording:** this record and the evidence state the claim verbatim and
  say nothing forbidden.

## The Codex attempt (superseded by R6)

Before R6, the same driver ran the Codex client
(`assets/story-04-shots/attempts/20260925T215624Z-file-and-find/`). Every
session launched lawfully and completed the MCP handshake. Then the Codex
account refused the model call (usage limit). First-run answers from that
attempt: Codex 0.155.1 sends the bearer from `bearer_token_env_var`, and a
scratch `CODEX_HOME` with the auth file alone authenticates. R6 retires the
Codex rerun. The Codex path stays in the driver (`--client codex`).

## Reviews

- The owner, 2026-09-26, on the rerun: "Reviewed — it's right". The first
  closing run had bounced: "the decision is thin".
- The Astra-role check on built (`pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/checks/story-04-built-astra-role-r1.md`):
  RATIFY-WITH-CONDITIONS; C1-C5 paid.
