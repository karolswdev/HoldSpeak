# Reach -- the settled design (Phase 174, story 01)

> **DRAFT -- pending 171 + 173.**

The owner's Tuesday moment (THE-TUESDAY-ARC.md section 2, "Phase 174"):
the MacBook is closed overnight; the .43 box on the tailnet ran the
sweep and the drafter; his phone buzzed once at 07:40 with the count;
his team's Confluence shows up in SOURCES the way GitHub does. The face
canon binds (docs/internal/UX-CANON.md); the Door's, the Arrival's,
the Heartbeat's, the Loop Closes', and the Steward's grammar (Phases
169--173) are the ratified precedent.


> **ON THE CANVAS (2026-09-05)** — eleven boards published at
> https://claude.ai/code/artifact/5719ec5d-4d70-4acc-9f7a-fbffa2d863a0 ;
> counsel reading; faces build to the ratified boards under the standing
> goal; **his word gates the merge** (stacked on 173 #556).

## D0 -- the Tuesday moment

22:00. He closes the MacBook lid and leaves. The .43 box on the
tailnet (192.168.1.43) runs an MCP client against the hub's Streamable
HTTP endpoint, authenticated with a scoped credential restricted to
PROJECT_PALETTE. The hub stays alive: the web runtime is a daemon
thread and the Cocoa presence host keeps the process running even when
the display sleeps. The .43 client triggers the sweep (the cadence
tick from 171) and the steward's drafter (173's unattended run) for
each active Room. Every call is kernel-admitted; every receipt carries
`origin: remote` and the credential's identity label.

07:40. His phone buzzes once: "HoldSpeak -- 3 need you across 2
projects." The notification came over the LAN mesh (conditional on
179's companion track; without it, the macOS banner fires when he
opens the lid instead).

08:05. He opens the lid. The dock badge reads `3`. The shade's
PROJECTS section shows the overnight deltas. The receipts in each
Room's pipeline observer carry the `REMOTE` badge and name
`192.168.1.43`. The steward's drafted update waits in the Room, its
egress chip naming the model host. He edits two sentences and
publishes.

09:00. He types Cmd+K, "gov", lands in the Room. Under SOURCES,
alongside `karolswdev/holdspeak` and `GOV (Jira)`, a third row reads
`GOV (Confluence)` with host `karolswdev.atlassian.net`. Watches on
Confluence pages produce entities the same way GitHub PRs and Jira
issues do.


## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| No hosted relay | Constitution Article III:1 | The hub speaks Streamable HTTP on the tailnet only; the .43 box reaches the Mac directly; no intermediate server, no cloud relay, no proxy |
| Every remote read wears a badge | Article III:2 | The `REMOTE` badge (the fourth EgressChip state) on every receipt that came over the wire |
| A remote principal is never OWNER | Article XI:4 | The remote transport derives a scoped AGENT principal from the credential; the owner's web token is never accepted on the remote path; OWNER requires the local browser session |
| Nothing new leaves the machine | Article III:1 | The Streamable HTTP listener is opt-in (off by default); the .43 box reads and triggers; no data crosses to .43 beyond the JSON-RPC responses |
| Scoped credentials with a palette and TTL | Article XI:3 | The credential carries its allowed palette (e.g. PROJECT_PALETTE); the kernel derives authority from the credential; tools outside the palette are refused with a typed capability error |
| One egress vocabulary | UX-CANON.md, 170 settled counsel M1 | `THIS DEVICE` / `LAN` / a cloud host / `REMOTE` -- the same four states everywhere; `REMOTE` names the caller's IP |
| No counters of zero | UX-CANON.md rule A.8 | Credential count absent at zero; receipts absent when none |
| No prose | UX-CANON.md rule A.3 | Tokens, verbs, counts, names; the credential face is a ledger, not a wizard |
| No modals | UX-CANON.md rule A.4 | Credential mint is an in-world well; revoke is a row verb |
| Every verb the library Button | UX-CANON.md rule A.1 | `Issue credential`, `Revoke`, `Connect`, `Run now` -- all library Button |
| Design before build | UX-CANON.md rule A.2 | This document is the design; artboards at 1440 + 393 drawn from it; his word before any code |
| Ledger not gate | Owner ruling | Every remote call receipted; no ceremony beyond the receipt |
| The switch-and-verify law | Phase 166 | The third connector follows the same (site, email) identity and verify-before-trust pattern as Jira |


## D2 -- the faces (element by element, species named)

### (a) Settings -> System: the remote transport row

**Position:** inside the System module detail face (settingsPrefs.tsx,
module id `system`). The hub row on settingsPrefs.tsx:510 currently
shows `THIS DEVICE` and `MESH OFF` / `MESH ON`. The REMOTE row sits
below MESH, inside the System module.

**The hub row update:** the System hub row on settingsPrefs.tsx:510
gains a third cell when remote is configured:
`THIS DEVICE` `MESH OFF` `REMOTE OFF` (all surface-token[data-chip]).
When remote is on: `THIS DEVICE` `MESH OFF` `REMOTE ON`.

**The REMOTE section** (inside the System module detail, below MESH):

**Section caption:** `REMOTE ACCESS` (caption step, 11 mono uppercase
0.06em).

**The toggle row** (SurfaceLedgerRow):

- Primary (15/600): `Streamable HTTP`.
- Cells:
  - CycleGadget: `OFF` / `ON` (the transport toggle; off by default).
  - When ON: a muted token `100.x.y.z:PORT` (the tailnet address the
    hub listens on; secondary step, 12 mono).
  - When ON and credentials exist: a count token `N CREDENTIALS`
    (surface-token[data-chip]).
- Trailing: none (the toggle is the verb).

**Species used:** SurfaceLedgerRow, CycleGadget,
surface-token[data-chip].

**The credentials list** (SurfaceLedger, below the toggle row, present
only when remote is ON):

**Section caption:** `CREDENTIALS` (caption step) with a count token
`N ACTIVE` (secondary step). Absent when none (rule A.8).

**Each credential row** (SurfaceLedgerRow, 52px lead slot):

- Lead: StateChip `*` (success when active, idle when expired).
- Primary (15/600): the identity label (the name the owner gave at
  mint time; e.g. `sweep-runner`, `.43 overnight`).
- Cells:
  - A palette token: `PROJECT` (surface-token[data-chip], naming the
    allowed palette; secondary step). Multiple palette names
    space-separated if more than one family is allowed.
  - A TTL token: `EXPIRES SEP 12` (surface-token[data-chip], secondary
    step) or `EXPIRED` (warning tone).
  - A last-used token: `LAST USED 2 H AGO` (muted,
    surface-token[data-chip]) or `NEVER USED` (muted). Absent when
    never used (rule A.8: no counters of zero -- but `NEVER USED` is
    an honest state, not a counter of zero; use it).
- Trailing: `Revoke` (Button ghost dense).

**Issue credential** (Button ghost, below the credentials list):

- Label: `Issue credential`.
- Action: opens a SurfaceWell below the button (in-world, no modal;
  rule A.4).

**The issue well** (SurfaceWell):

- StringGadget: `Name` (the identity label; placeholder `e.g. sweep-runner`).
- CycleGadget: `Palette` -- cycles through available palette names
  (`PROJECT` / `DESK` / `ALL`). Default: `PROJECT` (the scoped
  palette; PROJECT_PALETTE from families/project.py:1857).
- CycleGadget: `TTL` -- cycles through preset durations (`12 H` /
  `24 H` / `7 D` / `30 D`). Default: `12 H`.
- Footer: `Issue` (Button primary) and `Cancel` (Button ghost).

**After issue:** the well replaces itself with a one-time display:

- A copyable token row showing the full token string (monospace,
  secondary step, a `Copy` button). The text: `TOKEN SHOWN ONCE --
  COPY IT NOW` (caption step, warning tone). No sentence, no
  explanation paragraph.
- The credential appears in the list above.
- The token is never shown again (AgentCredentialStore stores the
  hash; the plaintext is returned only at issue time).

**Species used:** SurfaceLedger, SurfaceLedgerRow, SurfaceWell,
StateChip, CycleGadget, StringGadget, Button (ghost, ghost dense,
primary), surface-token[data-chip].

**Widths:**

- 1440: the credential row is a single line (lead / name / palette /
  expires / last used / Revoke).
- 393: palette and expires wrap under the name; Revoke stays trailing.

### (b) The REMOTE badge on receipts

**Position:** the pipeline observer's receipt rows (the shade, the
Room's observer pane). Every receipt from a remote MCP call carries
a `REMOTE` EgressChip.

**The badge** (EgressChip, gadgets.tsx:736):

- Label: `REMOTE -- 100.x.y.z` (the remote caller's tailnet IP).
- Scope: `"remote"` (a new fourth value on the `scope` prop; the
  existing values are `"local"`, `"mixed"`, `"cloud"`).
- Color: a new semantic token for the remote scope (distinct from
  cloud; propose the same family as `local` but with a stroke or
  outline to say "your infrastructure, but across the wire").

**Where it appears:**

- The receipt row in the shade's pipeline observer:
  `READ -- project_list -- REMOTE -- 100.x.y.z`.
- The Room's observer pane on receipted operations.
- The steward run's receipt row: `STEWARD RUN -- draft -- REMOTE --
  100.x.y.z`.

**Where it does NOT appear:**

- Local stdio calls (they do not cross the network).
- The owner's web browser session (that is local).

**Species used:** EgressChip (the existing component; extended with
`scope="remote"`).

**Widths:** the badge wraps under the operation label at 393 (the same
wrap behavior as the existing `cloud` badge).

### (c) The third connector's Door row and Room SOURCES

**The Door row** (DoorCore.tsx, alongside the GitHub and Jira rows):

**Precondition:** the owner's decision (story 06) selects the connector.
This design uses Confluence as the leading candidate; if the owner
chooses otherwise, the grammar stays the same -- only the name, the
emblem, and the entity types change.

**The source row** (the same SourceRowComponent used for GitHub and
Jira at DoorCore.tsx:371):

- Emblem: `C` (Confluence) -- the two-letter token in the lead slot
  (matching `GH` for GitHub and `J` for Jira at DoorCore.tsx:46-47).
- Name: `Confluence`.
- Provider chip: the site host (`karolswdev.atlassian.net`) as a
  surface-token[data-chip].
- Connection state: StateChip (`SIGNED IN AS karolsane@gmail.com` /
  `SIGN IN` / `NOT INSTALLED`).
- Default watches (CONFLUENCE_WATCH_DEFS, alongside GITHUB_WATCH_DEFS
  at DoorCore.tsx:27 and JIRA_WATCH_DEFS at :32):
  - `RECENTLY UPDATED` (template `watch.confluence.recent_pages`,
    on by default) -- pages updated in the space within the watch
    cadence.
  - `MY PAGES` (template `watch.confluence.my_pages`, off by
    default) -- pages authored by the connected user.
- In-world pickers: the space picker (StringGadget for the space key
  or CycleGadget for discovered spaces) replaces the repository picker
  (GitHub) and the project picker (Jira).

**Not-connected row:** same grammar as GitHub/Jira: emblem + name +
StateChip (warning `SIGN IN` or idle `NOT INSTALLED`) + `Connect`
(Button ghost).

**The Room's SOURCES row:**

- Host chip: `karolswdev.atlassian.net` (EgressChip with
  `scope="cloud"`; the host is a cloud SaaS, not the owner's
  infrastructure).
- Provider glyph: the Confluence emblem.
- Entity kind label: `PAGES` (or `BLOG POSTS` if the watch template
  uses blog entities).

**The Connections face row** (ConnectionsPane.tsx):

- One row per Confluence connection (the same grammar as Jira's
  multi-account rows).
- Primary: the site host.
- Cells: StateChip (`CONNECTED` / `SIGN IN` / `NOT INSTALLED`), the
  account email.
- Trailing: `Recheck` (Button ghost dense).

**Species used:** SurfaceLedgerRow, StateChip, EgressChip, Button
(ghost, ghost dense), CycleGadget or StringGadget (space picker),
surface-token[data-chip].

**Widths:**

- 1440: the Door source row is a single line (emblem / name / host /
  state / defaults / Connect).
- 393: defaults wrap under the name; Connect stays trailing.

### (d) Settings -> Rhythm: the runner host row

**Position:** inside the Rhythm module detail face (settingsPrefs.tsx),
below the `Watch sweep` cadence row from 171's design (settled-design-
heartbeat.md D2d).

**The row** (SurfaceLedgerRow):

- Primary (15/600): `Runs on`.
- Cells:
  - CycleGadget: `THIS DEVICE` / `192.168.1.43` (the host selection;
    when `192.168.1.43` is selected the sweep and the drafter run from
    the .43 box via the remote MCP client instead of locally).
  - When a remote host is selected: a muted token `LAST RUN 2 H AGO`
    (surface-token[data-chip], secondary step) or absent when no run
    has occurred.
- Trailing: `Run now` (Button ghost) -- triggers one immediate remote
  run (or local, depending on selection).

**The receipt naming the host:**

- When the sweep ran remotely, the receipt row (in the Room's pipeline
  observer and the shade) reads:
  `SWEEP -- 32 ENTITIES -- REMOTE -- 192.168.1.43 -- 07:40`.
- When local: `SWEEP -- 32 ENTITIES -- THIS DEVICE -- 07:40`.

**Species used:** SurfaceLedgerRow, CycleGadget,
surface-token[data-chip], Button (ghost).

**Widths:**

- 1440: the row is a single line (Runs on / host picker / last run /
  Run now).
- 393: last-run wraps under the picker; Run now stays trailing.

### (e) The credential's face on the remote side

The .43 box is headless. It runs an MCP client script, not a desk. Its
face is the terminal transcript: timestamps, tool calls, results, and
receipts printed to stdout. No web UI, no notification, no shade. The
receipts from its operations land on the Mac's desk (the hub's DB,
visible in the shade and the Room's observer).

**The transcript shape** (the evidence for story 08):

```
[2026-09-05 22:15:01] CONNECT hub=100.64.0.2:8765 identity=sweep-runner palette=PROJECT
[2026-09-05 22:15:02] CALL cadence_run_now
[2026-09-05 22:15:14] OK sweep completed entities=32 receipts=4
[2026-09-05 22:15:15] CALL project_run_steward project=gov
[2026-09-05 22:17:42] OK steward_run completed run_id=abc123 status=terminal
[2026-09-05 22:17:43] DISCONNECT
```

No face species. The transcript is plain text.

### All faces: dimensions

Every artboard at 1440 (the window at its design width) and 393 (the
glass / phone-width container query on `surface`). Three type steps
minimum per face: display (26/650) for the section headline or the
credential token, primary (15/600) for names and rows, secondary
(12 mono) / caption (11 mono uppercase) for tokens and section labels.


## D3 -- the wire

### The Streamable HTTP route on the hub

**Seam:** The hub's FastAPI app (web_server.py:547-610). A new route
`POST /api/mcp` accepts JSON-RPC requests and returns JSON-RPC
responses. The route sits behind the existing `_web_auth_gate`
middleware (web_server.py:561-591), which derives the principal from
the request token.

**Transport mapping:**

- The MCP sidecar's `handle_message` (server.py:47-115) is
  transport-agnostic: it takes a `dict` and returns a `dict | None`.
- The stdio loop (server.py:116-151) wraps this with newline-delimited
  JSON on stdin/stdout.
- The Streamable HTTP route wraps the same `handle_message` with
  HTTP request/response: `request.json() -> handle_message(body) ->
  JSONResponse(result)`.
- ONE implementation, THREE transports: stdio (the sidecar), the web
  runtime's in-process call (the wired fetcher), and Streamable HTTP
  (the remote path).

**The fetcher-seam debt (HS-165):** the sidecar's `serve()` function
(server.py:116) starts its own bare service instances (the refinement
runtime, the inference capability registry). The web runtime has the
LIVE services (the conductor, the wired fetcher, the scheduler). The
remote HTTP route MUST compose on the web runtime's live services, not
the sidecar's bare instances. This means the route handler calls
`handle_message` with the request dict, but the tool dispatch
(tools.py) resolves services from the web runtime's state (the
`request.app.state` FastAPI pattern), not from the sidecar's module-
level globals.

**The service injection seam:** today the MCP tool dispatch
(mcp/tools.py, mcp/families/*.py) calls services directly (e.g.
`from holdspeak.services import watch_service`). For the remote path,
these imports resolve correctly because the web runtime has already
initialized the services in the same process. The gap is the
`set_scheduler_services` seam (conductor.py) -- the conductor's
scheduler services are wired at web runtime startup, and the sidecar's
bare `serve()` never calls it. The remote path inherits the web
runtime's wired state naturally; no additional injection needed.

**Auth flow on the remote path:**

1. The request arrives at `POST /api/mcp` with an
   `X-HoldSpeak-Token` header (or `Authorization: Bearer <token>`).
2. The `_web_auth_gate` middleware (web_server.py:561) extracts the
   token via `web_auth.extract_request_token` (web_auth.py:93).
3. It first tries `derive_owner(token, self.auth_token)` -- this
   returns the OWNER principal if the token matches the hub's web
   token. **For the remote path, this MUST be blocked**: a remote
   request must never derive OWNER (Article XI:4). The route handler
   checks `principal.kind == PrincipalKind.OWNER` and refuses with
   403 if the request came from a non-loopback source.
4. It then tries `agent_credentials.derive(token)` -- this returns an
   AGENT principal if the token matches a minted credential.
5. The AGENT principal carries the credential's palette restriction
   (story 03). Tool dispatch checks the palette before execution.

**Protocol version:** the MCP Streamable HTTP spec (2025-03-26 draft)
defines the transport. The response includes the negotiated protocol
version. The sidecar's `MCP_PROTOCOL_VERSION` (server.py:14,
currently `"2024-11-05"`) must be bumped to the Streamable HTTP
revision. Both stdio and HTTP transports announce the same version.

**Route path:** `POST /api/mcp`. No collision with existing routes
(verified: providers.py:3-13 lists `/api/providers/*`; no `/api/mcp`
exists).

### The credential scope (palette + TTL on AgentCredentialStore)

**Seam:** `principals.py:89-172` (AgentCredentialStore).

**Current shape:** `AgentCredential` (principals.py:83-87) carries
`token`, `principal`, `expires_at`. The `issue` method (principals.py:
113-126) accepts `identity` and `ttl_seconds` but no palette.

**What 174 adds:**

- A `palette` field on `AgentCredential`: `frozenset[str] | None`.
  `None` means full access (backward-compatible with existing
  credentials). A frozenset names the allowed tool families (e.g.
  `frozenset({"project"})` for PROJECT_PALETTE).
- The `issue` method gains a `palette` kwarg:
  `issue(identity, *, ttl_seconds=43_200.0, palette=None)`.
- The `derive` method returns the full `AgentCredential` (not just the
  `Principal`), so the caller can check the palette.
- The tool dispatch path (mcp/tools.py or the route handler) checks
  `credential.palette` before executing a tool: if the tool's family
  is not in the palette, return a typed capability error (MCP-005 JSON-
  RPC error code).
- OWNER is never derived from a remote credential: the route handler
  checks the request's source address; a non-loopback request that
  derived OWNER is refused with 403.

**The principal derivation rule:**

| Source | Token matches | Principal | Palette |
|---|---|---|---|
| Loopback (browser) | Owner web token | OWNER | unrestricted |
| Loopback (sidecar) | Agent credential | AGENT | from credential |
| Non-loopback (remote) | Owner web token | REFUSED (403) | n/a |
| Non-loopback (remote) | Agent credential | AGENT | from credential |
| Any | No match | UNAUTHENTICATED | refused |

### The badge on remote reads (kernel receipt gains `origin`)

**Seam:** the kernel receipt (kernel/broker.py). Today `receipt()`
takes `operation_id`, `outcome`, `result_ref`, and `node` (the
`LOCAL_NODE` principal at kernel/external_egress.py:37).

**What 174 adds:**

- An `origin` field on the receipt: `"local"` (default) or `"remote"`.
  Set by the transport layer: the Streamable HTTP route handler tags
  the request as `origin=remote`; the stdio and in-process paths
  leave it as `origin=local`.
- The pipeline observer event carries the `origin` field. The face
  reads it to decide the EgressChip scope: `origin=remote` renders
  `scope="remote"` with the caller's IP as the label.
- Remote reads are NOT kernel-admitted as new operations (they are
  still reads, exempt under Article XI:5). But the tool dispatch
  writes a pipeline_events receipt (the existing `pipeline_events`
  pattern) with `origin=remote` and the caller's identity. This is a
  read receipt, not an operation receipt -- it records what was read
  and by whom, without the full admission ceremony.

### The third connector via `acli confluence`

**Seam:** the Jira adapter pattern:

| Component | Jira (existing) | Confluence (new) |
|---|---|---|
| Connector pack | `connector_packs/acli_jira.py` (91 lines) | `connector_packs/acli_confluence.py` (~90 lines) |
| Provider adapter | `services/jira_provider.py` (1729 lines) | `services/confluence_provider.py` (~600 lines, read-only V0) |
| WatchSource | `services/watch_sources.py:294` (JiraWatchSource, 98 lines) | `services/watch_sources.py` (ConfluenceWatchSource, ~80 lines) |
| Provider routes | `web/routes/providers.py:8-13` (6 routes) | `web/routes/providers.py` (~4 routes: connections, recheck, discover, search) |
| Watch templates | `watch_templates.py` (jira.* patterns) | `watch_templates.py` (confluence.* patterns) |
| Door row defs | `DoorCore.tsx:32` (JIRA_WATCH_DEFS) | `DoorCore.tsx` (CONFLUENCE_WATCH_DEFS) |
| MCP twins | `mcp/families/project.py` (provider_jira_*) | `mcp/families/project.py` (provider_confluence_*) |

**The acli confluence CLI capabilities (verified on the owner's machine):**

| Subcommand | Available | Output | WatchSource-relevant |
|---|---|---|---|
| `auth status` | YES | Account status | Connection state |
| `auth switch` | YES | Switch accounts | Multi-account law |
| `space list --json` | YES | Spaces with keys, names | Discovery (space picker) |
| `space view --json --key K` | YES | One space detail | Validation |
| `page view --id ID --json` | YES | One page detail | Entity detail (by ID only) |
| `blog list --space-id S --json` | YES | Blog posts in a space | Entity listing (blogs only) |
| `page list` / `page search` | **NOT AVAILABLE** | n/a | **CRITICAL GAP** |

**The critical gap: no `page list` or `page search` command.**

The Confluence WatchSource needs to snapshot a list of entities (pages)
matching criteria (space, modified date, author). The Jira WatchSource
uses `acli jira workitem search` with JQL; the GitHub WatchSource uses
`gh pr list` with filters. `acli confluence` has NO page list or page
search command -- only `page view --id` (single page by ID).

**Consequences and the honest design:**

1. **Blog entities work:** `blog list` supports `--space-id`, `--title`,
   `--json`, `--limit`, cursor pagination. A WatchSource over blog
   posts is fully feasible.
2. **Page entities require an alternative path:** without `page list`,
   the adapter cannot discover pages. Two options at charter time:
   - **(A) Confluence REST API via `curl`:** make a direct Confluence
     Cloud REST API call using the same credentials `acli` holds. This
     violates Article III's spirit (the CLI holds the credentials, not
     HoldSpeak). **Not recommended.**
   - **(B) Watch only blog posts in V0:** the WatchSource supports
     `blog list` entities only. Pages are deferred until `acli` gains
     a `page list` command (or the owner chooses a different tool).
     **Honest but limited.**
   - **(C) Space-level metadata only:** the WatchSource tracks spaces
     via `space list` and pages via `page view --id` for known IDs
     (IDs discovered through meeting mentions or manual entry). No
     full-space page sweep. **Pragmatic but incomplete.**
3. **The owner decides in story 06.** This gap is documented as a
   constraint on the Confluence candidate. If the gap is too narrow
   for his team's needs, he may choose a different tool.

**The allowlist** (`acli_confluence.py` ALLOWED_SUBCOMMANDS):

```
("confluence", "auth", "status")
("confluence", "auth", "switch")
("confluence", "space", "list")
("confluence", "space", "view")
("confluence", "page", "view")
("confluence", "blog", "list")
("confluence", "blog", "view")
```

Read-only. No `page create`, no `blog create`, no `space archive`.

**Connection identity:** `(site, email)` serialized as `site|email`
(the same pattern as Jira; acli_jira.py docstring). Each combination
is one row in `watch_provider_connections` with
`provider_id="confluence"` and `external_connection_ref="site|email"`.

**Watch templates:**

- `watch.confluence.recent_blogs`: blog posts in a space updated
  within the cadence window. Query: `blog list --space-id S --json
  --limit L`.
- `watch.confluence.my_pages`: pages authored by the connected user
  (requires page IDs -- deferred if no page list).

**Entity shape** (from `blog list --json` output):

```json
{
  "id": "page-or-blog-id",
  "key": "",
  "title": "Release Notes Q3",
  "url": "https://site.atlassian.net/wiki/...",
  "status": "current",
  "space_key": "GOV",
  "author": "karolsane@gmail.com",
  "updated_at": "2026-09-04T15:30:00Z",
  "created_at": "2026-09-01T10:00:00Z",
  "labels": ["release-notes", "q3"]
}
```

### The .43 runner -- direction and architecture

**The question: who drives whom?**

The .43 box is the CLIENT. The Mac is the HUB. The .43 box runs an
MCP client script that connects to the Mac's Streamable HTTP endpoint
to trigger sweeps and the drafter. The Mac's hub has the DB, the web
runtime, and the services.

This is the correct direction because:

1. The Mac's hub is the single source of truth (the DB, the kernel,
   the receipts). The .43 box has no DB and no state.
2. The .43 box's llama.cpp is already configured as an inference
   endpoint at `192.168.1.43:8080`. The hub calls it for inference
   (the existing path). The .43 runner does NOT perform inference
   itself -- it triggers the hub's sweep and drafter, which in turn
   call the .43 model through the existing inference runner.
3. The reverse direction (the Mac driving the .43 box) would require
   running the full web runtime on .43, duplicating the DB, and
   pushing results back to the Mac. That is a mesh topology, not
   Reach.

**The overnight scenario:**

1. The owner closes the MacBook lid. The hub's web runtime stays
   alive (the Cocoa presence host keeps the process running; the
   daemon threads continue; macOS App Nap may throttle but does not
   kill daemon threads on AC power).
2. The .43 box connects to the hub's Streamable HTTP endpoint
   (`http://100.64.0.2:8765/api/mcp`, the tailnet address) with a
   scoped credential.
3. The client calls `cadence_run_now` -- triggers one sweep tick.
4. The hub's sweep evaluates all due watches, writes receipts.
5. The client calls `project_run_steward` for each active Room --
   triggers the steward's drafter.
6. The hub's drafter calls the .43 model at `192.168.1.43:8080` for
   inference (the round trip: .43 -> Mac hub -> .43 model -> Mac
   hub -> receipt).
7. The client disconnects. The receipts are on the Mac's desk.

**The long-running contract (MCP-003):**

The steward run is long-running (tens of seconds to minutes). The
MCP-003 contract:

- The tool call (`project_run_steward`) returns a `run_id` promptly
  (within the HTTP response timeout).
- The client polls `project_get_steward_run(run_id)` for state.
- Terminal states: `completed`, `failed`, `cancelled`.
- The polling interval: 5 seconds (configurable by the client).
- The credential's TTL bounds the run: if the credential expires mid-
  run, the poll returns 403 and the run completes but the client
  cannot retrieve the result. The run itself is not aborted (it runs
  on the hub's thread).

**The SSE question:** the MCP Streamable HTTP spec (2025-03-26) defines
an optional SSE notification channel for server-initiated events. If
ratified and stable at charter time, the steward run state can push
through SSE instead of polling. If not ratified, polling-only ships.
The design supports both: the route handler returns `run_id` in both
cases; the SSE channel is additive.

### Wire summary (seams, file:line)

| Seam | File:line | What 174 does |
|---|---|---|
| MCP handle_message | server.py:47 | Called by the HTTP route (transport-agnostic) |
| Stdio loop | server.py:116 | Unchanged; the HTTP route is parallel |
| Auth gate middleware | web_server.py:561 | Already derives principals; remote path blocks OWNER derivation |
| Off-loopback bind check | web_auth.py:73 | Already blocks unauthenticated non-loopback; remote path requires an agent credential |
| AgentCredentialStore.issue | principals.py:113 | Gains palette kwarg |
| AgentCredentialStore.derive | principals.py:128 | Returns full AgentCredential (with palette) |
| PROJECT_PALETTE | families/project.py:1857 | Used as default credential palette |
| Pipeline events | pipeline_events.py | Receipt gains `origin: remote` field |
| Mesh advertiser | mesh.py:1-45 | Unchanged; the Streamable HTTP route is independent of Bonjour |
| Desktop notify | desktop_notify.py | Unchanged in 174; the .43 runner triggers the hub's heartbeat, not its own |
| fetch_watch_snapshot | watch_sources.py:428 | Gains `"confluence"` branch |
| JiraWatchSource | watch_sources.py:294 | Pattern template for ConfluenceWatchSource |
| Jira connector pack | connector_packs/acli_jira.py | Pattern template for acli_confluence.py |
| Jira provider adapter | services/jira_provider.py | Pattern template for confluence_provider.py |
| Provider routes | web/routes/providers.py:3-13 | Gains /api/providers/confluence/* |
| DoorCore defs | DoorCore.tsx:27-37 | Gains CONFLUENCE_WATCH_DEFS |
| Door controller | DoorCore.tsx:39 | Gains `"confluence"` case |
| ConnectionsPane | connections/ConnectionsPane.tsx | Gains Confluence connection rows |
| EgressChip | gadgets.tsx:736 | Gains `scope="remote"` |
| Settings System row | settingsPrefs.tsx:510 | Gains REMOTE cell |


## D4 -- counsel's hunts

- **H1: An OWNER principal over HTTP.** A non-loopback request that
  presents the owner's web token MUST be refused (Article XI:4). The
  hunt: verify that `_web_auth_gate` blocks this path. Today the gate
  derives OWNER from the owner's web token regardless of source; the
  remote-OWNER block is NEW code. If missed, any machine on the
  tailnet with the web token has full OWNER authority.

- **H2: A credential without TTL.** If `ttl_seconds` is set
  unreasonably high (e.g. 10 years), the credential is effectively
  permanent. The hunt: cap TTL at 30 days in `issue()`. A credential
  that outlives its purpose is a standing privilege.

- **H3: A remote read without a badge.** Every remote MCP call must
  carry `origin: remote` in the pipeline event. The hunt: the tool
  dispatch path must tag origin before returning, not after. If the
  dispatch raises before tagging, the receipt is `origin: local` by
  default -- a false local badge.

- **H4: The relay temptation.** A future phase might propose a cloud
  relay for the phone when it is off the LAN. Article III:1 forbids
  this. The hunt: document the law in the architecture doc (story 10);
  the LAN companion notification (story 09) is the ONLY cross-device
  path, and it carries the count only.

- **H5: The .43 box reaching the Mac when it sleeps.** macOS puts the
  machine to sleep when the lid closes (unless power-nap settings or
  `caffeinate` keep it awake). If the Mac sleeps, the hub's web
  runtime is suspended and the .43 client cannot connect. The hunt:
  the overnight scenario requires `caffeinate -s` (prevent sleep on
  AC power) or the macOS "Prevent your Mac from sleeping automatically
  when the display is off" setting. Document this as a prerequisite,
  not as a code fix.

- **H6: The .43 box's credential and the hub restart.** If the hub
  restarts (crash, update), the in-memory AgentCredentialStore is
  wiped. The .43 client's credential is invalid. The hunt: the client
  script must handle 401/403 gracefully and log the failure. The owner
  re-issues the credential after a hub restart. Persisting credentials
  to disk is deferred (it adds a credential-at-rest surface).

- **H7: Palette drift.** If PROJECT_PALETTE changes (a tool is added
  or removed), existing credentials carry the old palette name. The
  palette name resolves at call time (the kernel looks up the current
  tools in the named palette). Credentials do not go stale when the
  palette's contents change -- only when the palette name is removed.
  Hunt: never remove a palette name; only add tools to it.


## D5 -- the walk on his desk

The walk proves the Tuesday moment on his real desk with his real
projects and the .43 box:

1. **The overnight sweep.** The .43 box runs the MCP client script
   overnight. In the morning, the owner opens the lid. The desk shows
   receipts from the overnight sweep with the `REMOTE` badge and
   `192.168.1.43`.
2. **The steward draft.** The Room shows a drafted update from the
   overnight steward run. The egress chip names the model host
   (192.168.1.43). He edits and publishes.
3. **The notification.** (Conditional on 179.) His phone buzzed at
   07:40 with the count. Without 179: the macOS banner fires when he
   opens the lid.
4. **The credential face.** He opens Settings -> System. The REMOTE
   section shows the active credential (`sweep-runner`, palette
   `PROJECT`, expires in 6 days). He mints a new credential for a
   teammate, copies the token, revokes an old one.
5. **Confluence in SOURCES.** He opens a Room. Under SOURCES, a
   Confluence row shows the connected space with entities from the
   most recent sweep. He clicks an entity; it opens in the browser.
6. **The Door.** He opens the Door. The Confluence source row shows
   `SIGNED IN AS karolsane@gmail.com` and the default watches.

Six beats at both widths (1440 + 393). Stopwatch per face (Article
IX.2). His words verbatim. His verdict.


## Honest sizes

| Story | Size | Rationale |
|---|---|---|
| 01 The design | S | Artboards from this doc; no code |
| 02 The transport | M | One FastAPI route + service injection; handle_message is already transport-agnostic; the fetcher-seam debt is paid by the route's natural composition on the web runtime |
| 03 Scoped remote identity | M | Palette field on AgentCredential + the OWNER-block on non-loopback + the credential mint/revoke face in Settings |
| 04 Egress badges | S-M | `origin` field on pipeline events + the `scope="remote"` on EgressChip + the route handler tagging origin |
| 05 The long-running contract | S-M | MCP-003 verified over HTTP (run_id + polling already work); SSE is additive if ratified |
| 06 The third connector decision | S | Census + the owner's word; no code |
| 07 The third connector | M-L | ~730 lines across the adapter, WatchSource, templates, Door row, provider routes, MCP twins (the Jira census priced it); the `page list` gap may shrink the scope to blogs only |
| 08 The .43 runner | M | The MCP client script + the overnight scenario + the evidence transcript; the hard part is the sleep/caffeinate prerequisite and the credential lifecycle |
| 09 LAN companion notifications | S (conditional) | The reverse Bonjour push; DEFERRED if the companion track stays dormant |
| 10 The docs | S | Re-shot + MCP_SIDECAR.md generator extension |
| 11 The close | S | Gates, sweep, the PR |


## Addendum — the orchestrator's rulings under the standing goal (2026-09-05)

- **Story 06, the third connector — Confluence as the reversible
  default; his word owed.** The `acli confluence` gap (no `page list` /
  `page search`) is real. V0 is honest and limited: the WatchSource
  watches **blog posts** (`blog list --space-id`) and **pages by known
  ID** (`page view --id`, IDs from meeting mentions, suggested sources,
  or the owner typing one) — option (B)+(C). No Confluence REST via
  `curl` (option A) — the CLI holds the credentials, not HoldSpeak. The
  Door row says what it can do: defaults `RECENT BLOGS` (on) and
  `PAGES BY ID` (off); never a `RECENTLY UPDATED` pages promise the
  tool cannot keep. If he chooses another tool, the grammar stays.
- **Story 08, the .43 runner — proven on this machine first.** The
  client script and the Streamable HTTP route are proven end to end
  against the hub on the Mac (loopback with an agent credential is the
  same path); the leg from the .43 box itself waits for his sitting
  (this sandbox does not reach the LAN). The transcript shape in D2(e)
  is the evidence either way.
- **Story 09 (LAN companion notifications)** is conditional on 179's
  companion; in 174 it ships the hub side only (the notification event
  with `origin` on the mesh bus) and records the dependency.
- **The REMOTE chip** is the fourth egress state everywhere (`REMOTE ·
  <caller ip>`); a remote principal is never OWNER; the listener is off
  by default and the toggle lives in Settings → System with the
  credentials ledger beneath it.
