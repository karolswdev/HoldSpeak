# Phase 174 - Reach

**Last updated:** 2026-09-05.

## Goal

HoldSpeak outgrows one Mac and two connectors. MCP remote over
Streamable HTTP lets the .43 box run the overnight sweep and drafter
while the MacBook sleeps; a third CLI-backed connector brings another
tool into SOURCES; companion notifications over the LAN mesh reach the
phone when the companion track wakes. Nothing leaves without a badge
(Article III); no remote principal is OWNER (Article XI); one
implementation across stdio, web, and remote.

## Status

**ACTIVE 0/11 — STACKED on 173 (PR #556) on 172 (#555) on 171 (#554) on 170 (#553); branch `feat/reach` off `feat/the-stewards-hand`.**

**Depends on:** Phase 171 (the heartbeat's cadence) + Phase 173 (the
steward's hand and voice).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday. The MacBook is closed overnight; the .43 box on the tailnet
ran the sweep and the drafter; his phone buzzed once at 07:40 with the
count; at his desk command-K "gov" lands in the Room. His team's
Confluence shows up in SOURCES like GitHub does.

Census facts from THE-TUESDAY-ARC.md section 0 that this phase pays:
the sidecar is stdio ONLY (holdspeak/mcp/server.py:116-151); no
Streamable HTTP transport exists; the AgentCredentialStore
(principals.py:89-172) mints per-identity tokens with TTL + revocation
but always for AGENT principals on the same machine; the hub already
serves authenticated HTTP off loopback for companions
(web_server.py:367-386, web_auth.py:73-89); the Bonjour mesh advertises
`_holdspeak._tcp` to the iPad (mesh.py:1-45) but carries no
notification push; connectors today are GitHub (gh) and Jira (acli);
the .43 box runs llama.cpp (Q6, 24k context) but no HoldSpeak runner.

## Scope

- In:
  - MCP remote transport: a Streamable HTTP route on the hub (FastAPI),
    behind the existing `_web_auth_gate`, calling the
    transport-agnostic `handle_message()`; the remote handler composes
    on the web runtime's live services, never the sidecar's bare
    instances (pays the 165 fetcher-seam debt); the protocol version
    bumped honestly.
  - Scoped remote identity: non-OWNER principals per remote client
    minted from AgentCredentialStore (TTL, revocation, owner-issued
    from the desk), palette-restricted (PROJECT_PALETTE or a configured
    subset); the kernel derives authority from the credential (Article
    XI:3); OWNER is never a remote principal (Article XI:4).
  - Egress badges on remote reads: every remote call kernel-admitted
    with a terminal receipt (Article XI:2) and an EGRESS badge at the
    point of decision (Article III:2); local stdio stays badgeless.
  - The long-running contract over HTTP (MCP-003's run_id + polling;
    SSE push only if the spec's mechanism is ratified).
  - The .43 runner as the live proof: the .43 Linux box on the
    tailnet drives a sweep + drafter run while the Mac sleeps; receipts
    land on the desk; the transcript is the evidence; the OWNER
    VERDICT.
  - ONE third connector chosen by the team's reality (CLI-backed only,
    the switch-and-verify law from Jira parity); a decision story
    evaluates the candidates (acli confluence, linear, glab) against
    what the owner actually uses; then the implementation story.
  - LAN companion notifications via the Bonjour mesh when the
    companion track wakes (CONDITIONAL on that track).
  - The design on the library before build (canvas at 1440 + 393):
    the remote badge, the credential scope face, the third connector's
    Door card.
  - His walk on his desk: the .43 runner's receipts on his desk in the
    morning.
- Out:
  - A hosted relay or proxy (Article III:1; no cloud dependency).
  - OWNER as a remote principal (Article XI:4).
  - OAuth or token capture of any kind (gh, acli, and the third CLI
    hold the tokens; Article III).
  - Push notifications to iOS/iPad (that is the companion track, not
    this phase; this phase wires LAN notifications only).
  - Ecosystem publication beyond self-hosted discoverability.
  - New watch source types beyond the third connector.
  - MCP Tasks integration (verify against the current spec before
    designing; never build to a draft).

## Exit criteria (evidence required)

- [ ] A Streamable HTTP route on the hub serves MCP remote; the
      protocol version is bumped; `handle_message()` composes on the
      web runtime's live services (the 165 fetcher-seam debt paid).
- [ ] Scoped non-OWNER credentials minted from AgentCredentialStore
      (TTL, revocation, owner-issued) restrict a remote client to
      PROJECT_PALETTE or a configured subset; OWNER is never a remote
      principal.
- [ ] Every remote call carries a kernel receipt and an EGRESS badge
      at the point of decision; local stdio stays badgeless.
- [ ] MCP-003's run_id + polling works over the Streamable HTTP
      transport; the long-running contract is documented and tested.
- [ ] The .43 box on the tailnet drives a sweep + drafter run while
      the Mac sleeps; receipts land on the desk; transcript is evidence.
- [ ] ONE third connector (CLI-backed) is connected, watched, and
      producing entities in SOURCES like GitHub and Jira.
- [ ] LAN companion notifications fire when the needs-you count
      crosses the edge (CONDITIONAL on the companion track).
- [ ] The design on the canvas at 1440 + 393 is ratified by the owner
      before the build.
- [ ] His walk on his desk: the .43 runner's receipts on his desk in
      the morning; the third connector in SOURCES; his word.
- [ ] Zero hosted relay (Article III); no OWNER remotely (Article XI).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-174-01 | The design (the remote badge, the credential scope face, the third connector's Door card) | done | [story-01-the-design](./story-01-the-design.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-174-02 | The transport (Streamable HTTP on the hub behind scoped credentials) | done | [story-02-the-transport](./story-02-the-transport.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-174-03 | Scoped remote identity (non-OWNER principals, palette-restricted, owner-issued) | done | [story-03-scoped-remote-identity](./story-03-scoped-remote-identity.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-174-04 | Egress badges on remote reads (kernel receipt + badge; local stdio badgeless) | in-progress | [story-04-egress-badges](./story-04-egress-badges.md) | -- |
| HS-174-05 | The long-running contract (run_id + polling over HTTP) | done | [story-05-the-long-running-contract](./story-05-the-long-running-contract.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-174-06 | The third connector decision (candidates, CLI-backed, switch-and-verify) | done | [story-06-the-third-connector-decision](./story-06-the-third-connector-decision.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-174-07 | The third connector (implementation: WatchSource, Door card, templates) | in-progress | [story-07-the-third-connector](./story-07-the-third-connector.md) | -- |
| HS-174-08 | The .43 runner (the live proof: sweep + drafter overnight, receipts on the desk) | done | [story-08-the-43-runner](./story-08-the-43-runner.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-174-09 | LAN companion notifications (Bonjour mesh push; CONDITIONAL on the companion track) | done | [story-09-lan-companion-notifications](./story-09-lan-companion-notifications.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-174-10 | The docs (MCP_SIDECAR.md extended, the guide's companions section, remote in the architecture) | done | [story-10-the-docs](./story-10-the-docs.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-174-11 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | in-progress | [story-11-the-close](./story-11-the-close.md) | -- |

## Where we are

**2026-09-05 20:45 — 7/11 DONE (01 · 02 · 03 · 05 · 06 · 08 · 09); PR #557.**
The receipts/Door/Rhythm faces are built but their rigs were hollow
(no shade open; no Confluence seeded) — being redone on the wire that
carries origin on projection rows, a Room RECEIPTS section, and
`runs_on` on the heartbeat settings (landing). Then 04/07 flip →
counsel-on-built → docs verify → the runner fill + his-desk walk →
suite → 11 close.

**2026-09-05 20:40 — 6/11 DONE; PR #557 OPEN** (`--base feat/the-stewards-hand`).

**2026-09-05 20:35 — 4/11 DONE (01 · 06 · 08 · 09).** The runner is proven
on this machine (the real hub on loopback, a SWEEP credential, receipts
origin=remote, the owner token refused off-loopback); the .43 leg waits
for his sitting. The Settings → System face is checkpointed with two
last fixes landing; the receipts/Door/Rhythm faces building. Then
counsel-on-built → docs verify → his-desk walk (the probe credential
only if remote is already ON) → suite → close → PR.

**2026-09-05 20:45 — 2/11 DONE (01 design · 06 the decision); the wire
LANDED for 02/03/04/05 (2cc6f07c: POST /api/mcp on the live runtime,
hashed scoped credentials, origin on receipts, MCP-005), 07 (1dabc8f7:
the Confluence connector, page listing typed unsupported_by_cli), 08/09
(2175bf3d: the stdlib runner client + the mesh event); docs 10 drafted;
the walk runner drafted (one guarded reversible write). Faces for the
System module and the receipts/Door/Rhythm building; the runner's
loopback proof filling. Then counsel-on-built → his-desk walk → suite →
close → PR `--base feat/the-stewards-hand`. The 171 notify-loop P0 found
by this phase's runner lane is paid on feat/the-heartbeat (d0f6d89f) and
merged forward through 172 · 173 · 174.**

**2026-09-05 19:35 — ACTIVATED, STACKED.** Under the standing goal the
faces build to counsel-ratified boards and his word gates the MERGE (the
decision recorded for 170–173). Eleven boards for D2 (a)–(d) on the canvas
(https://claude.ai/code/artifact/5719ec5d-4d70-4acc-9f7a-fbffa2d863a0),
counsel reading; wire lanes follow the 173 suite. Story 06 (the third
connector) proceeds on the design's leading candidate, Confluence, as a
reversible default; his word on the choice is owed. Story 08 (the .43
runner) builds the client and proves it against the hub on this machine;
the leg on the .43 box itself waits for his sitting (the sandbox does
not reach the LAN). Merge order stays his: #553 → #554 → #555 → #556 →
174's.

Earlier: 
PLANNED. Waiting for Phase 171 (the heartbeat's cadence — without it
the .43 runner has nothing to run unattended) and Phase 173 (the
steward's hand and voice — without it the drafter has no model-drafted
prose to produce overnight). The recon is complete:

**MCP transport today:** stdio only. The server speaks newline-delimited
JSON-RPC over stdin/stdout (holdspeak/mcp/server.py:116-151, protocol
`2024-11-05` at server.py:14). `handle_message()` (server.py:30-107) is
transport-agnostic (dict in, dict out) — the Streamable HTTP route
calls this directly. No HTTP, SSE, or WebSocket exists in the MCP
layer. The hub's real-time channel for the web UI is the WebSocket at
/api/ws (web_server.py).

**Hub auth today:** the hub already serves authenticated HTTP off
loopback for companions. Non-loopback bind requires a token
(web_auth.py:73-89). The auth middleware derives principals from
credentials (web_server.py:560-590): owner token, then agent
credentials, then node tokens, else UNAUTHENTICATED.
`AgentCredentialStore` (principals.py:89-172) mints per-identity tokens
with TTL (12 h default) + revocation — the substrate for scoped remote
identity. But today it always issues AGENT-kind principals, never
restricted to a palette or scope.

**The .43 box:** runs llama.cpp (Q6, 24k context) at 192.168.1.43:8080.
No HoldSpeak runner or MCP client exists on it. It serves inference only.

**CLI-backed connector candidates on this machine:** `gh` (found,
already a connector), `acli` (found, already a connector for Jira;
also has `confluence` subcommand — a live candidate for the third
connector), `linear` (not found), `glab` (not found), `gitlab` (not
found), `az` (not found), `op` (not found), `jira` (not found),
`confluence` (not found). The only real candidate on this machine today
is `acli confluence` (the Atlassian CLI already installed, with
Confluence Cloud commands).

**The companion/LAN notification seam:** the Bonjour mesh
(mesh.py:1-45) advertises `_holdspeak._tcp` on off-loopback binds for
the iPad's NWBrowser. The mesh is discovery only — it carries the
device name, port, and requiresToken in the TXT record but has no
notification push channel. The desktop presence host
(desktop_presence_cocoa.py) has AppKit but zero notification SEND calls
to the companion. The iPad app (the companion) is dormant.

**The connector grammar:** GitHubWatchSource (watch_sources.py:58-171)
and JiraWatchSource (watch_sources.py:294-431) are the two
implementations. The file is 443 lines. The census in
THE-TUESDAY-ARC.md:195 priced a new CLI-backed provider at ~730 lines
(adapter + WatchSource + templates + Door card + provider routes).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| Credential surface on the remote transport | Medium | Scoped non-OWNER principals with TTL + revocation; never OWNER remotely (Article XI); the kernel derives authority, the caller never supplies it; counsel reviews before the owner | A remote principal reaches an OWNER-only operation |
| The .43 box's tailnet connectivity | Low | The tailnet is already established (the llama.cpp endpoint at .43 is reachable from the Mac); the runner is a MCP client on the .43 side | The .43 box cannot reach the hub's off-loopback bind |
| Third connector scope creep | Low | The decision story evaluates candidates first; the switch-and-verify law binds it; one connector, not two; CLI-backed only, no REST/token | The chosen connector needs a REST API or token capture |
| Companion track dependency | Medium | LAN notifications are CONDITIONAL on the companion track waking; the story is marked conditional and can be deferred without blocking the phase | The companion track does not wake before this phase ships |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- Which third connector ships (Confluence via acli is the leading
  candidate on this machine; Linear would require installing its CLI;
  the decision story resolves this).
- Whether SSE push for run state ships (only if the Streamable HTTP
  notification channel is ratified in the MCP spec at charter time;
  never build to a draft).
- The exact credential scope granularity (PROJECT_PALETTE as the
  floor; finer scopes decided at design time from the remote use
  cases).
- LAN notification payload shape (count only by default, Article III;
  decided on the canvas).
