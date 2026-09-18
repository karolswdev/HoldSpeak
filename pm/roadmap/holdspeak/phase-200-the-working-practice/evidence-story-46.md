# Evidence - HS-200-46

- **Story:** HS-200-46 - A stale document fails CI instead of misleading the next agent
- **Status:** done
- **Date:** 2026-09-17

## Proof

### Captured run — 2026-09-17T22:53:11Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.IvdsPVqG3d uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_doc_claims.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4a5ecfafa2bb22851d0e3fde9c6c6d6752d7ad2

```text
.............................                                            [100%]
29 passed in 1.47s
```

### Captured run — 2026-09-17T22:53:41Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.wDNrPEhXWO uv run python scripts/doc_claims.py --measure`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4a5ecfafa2bb22851d0e3fde9c6c6d6752d7ad2

```text
| State | Where | What it claims | What is true |
|---|---|---|---|
| KNOWN FALSE (HS-200-45) | `holdspeak/web/routes/mcp_http.py:3` | JSON-RPC in -> handle_message_for_principal -> JSON-RPC out, composing on the web runtime's LIVE services (never the sidecar's bare serve() instances). | the route calls holdspeak.mcp.server.handle_message_for_principal, whose only parameters are {request, principal, palette} — no live-services handle is threaded in, so it composes exactly as the sidecar's serve() does |
| KNOWN FALSE (HS-200-45) | `holdspeak/db/connection.py:3` | Extracted from ``Database`` so the connection protocol (WAL pragmas, row factory, commit/rollback) lives in one place. | a connection opened through this factory reports journal_mode=delete; the module sets only PRAGMA foreign_keys=ON, and the 5000ms busy_timeout it reports is sqlite3.connect's own timeout=5.0 default, not a pragma this module applies |
| KNOWN FALSE (HS-200-45) | `docs/SECURITY.md:277` | The Streamable HTTP listener (`POST /api/mcp`) is opt-in and off by default. When enabled, it accepts connections on the tailnet address only. | bind_host is stored and echoed by the settings route in holdspeak/web/routes/mcp_http.py and mentioned by no other module, so nothing applies it to a bind or a peer check; the package's only tailnet CIDR (100.64.0.0/10, concierge_service.py:297) is an egress-advice helper, not a listener fence |
| KNOWN FALSE (HS-200-44) | `docs/internal/UX-CANON.md:132` | (ii) *Hard zeros*: DS6 (accent rail) and A9 (missing egress) must stay at 0; A1 (raw `<button>`) must stay within a named allowlist (4 residues with reasons). | the live web/src tree holds 203 raw <button> elements outside the Signal/gadgets library files; the canon scanner sees 4 of them because its A1 regex requires a character after `<button` on the same line, so every multi-line JSX tag is invisible to it |
| KNOWN FALSE | `holdspeak/mcp/resources.py:61` | Mirrors web/src/desk/verbRegistry.ts, including verbs derived from DESK_TOOLS. | the face registers 67 verbs and the catalog publishes 45: 22 registry verbs are missing from the catalog (the nine desk.* intelligence/thread/project verbs, go.change-places, go.open-project-memory, object.continue-in-thread and the ten thread.* verbs) and the catalog holds no phantoms — the audit's '13 phantoms' were the DESK_TOOLS-derived go.* verbs it did not resolve |
| KNOWN FALSE | `holdspeak/mcp/resources.py:160` | Canonical current Desk state, including its stored objects and layout. | the real resource returns seven lists of DB rows — chains, decisions, directories, notes, profiles, workbenches, workflows — and no key describing layout, windows, focus, panels, geometry or stacking |
| KNOWN FALSE | `docs/internal/DESKOS_COMPONENT_PATTERN.md:3` | The canon for how a surface on the iPad desk (DeskOS) should look and behave, distilled from the one we got right: **the ambient recorder**. | the doc names zero web/src faces; its reference implementation is apple/App/MeetingCapture/DeskDioramaStage.swift, so it documents the SwiftUI iPad desk while 'DeskOS' now means the web desk that is the spec |
| HOLDS (HS-200-46) | `CLAUDE.md:153` | MCP-capable agents: prefer the MCP tools over shelling out — `.githooks/dw-mcp` (NOT wired in `.mcp.json`, which declares only the `holdspeak` server by intent; add it to your own client config) serves the same core as structured tools with identical refusals | .mcp.json declares exactly one server, 'holdspeak'; dw-mcp is not wired there and the omission is intentional (corrected 2026-09-17, HS-200-46) |
| HOLDS | `docs/USER_GUIDE.md:977` | On `POST /api/mcp` the owner's web token is refused on a non-loopback request; no other route applies that refusal. | exactly one module under holdspeak/web refuses an OWNER principal on a non-loopback request: holdspeak/web/routes/mcp_http.py:93 |
| HOLDS | `docs/internal/DESK_GRAMMAR.md:52` | THE WINDOW REMEMBERS — view, sort, direction per zone and the open set (`hs.desk.workspace.v1`), rect via panels — and restores. The older `hs.desk.zone-views` / `hs.desk.zone-windows` keys are retired: they survive in `GHOST_LAYOUT_KEYS` so a reset still sweeps them, and nothing reads them. | DESK_WORKSPACE_STORAGE_KEY in web/src/desk/store/workspaceStorage.ts is 'hs.desk.workspace.v1'; both zone-* keys appear in web/src only inside GHOST_LAYOUT_KEYS (and its tests) |
| HOLDS | `docs/MCP_SIDECAR.md:854` | Owner discovery exposes 16 static resources and 21 resource templates. The default non-owner discovery filters that to 15 static resources and 19 templates, or 34 total. | the sentence's four numbers are read back out of the document and compared to holdspeak.mcp.resources.list_resources for OWNER and for the default non-owner principal, so they cannot drift again silently |
| HOLDS | `holdspeak/db/schema.py:1346` | `unavailable` -> `stale` on an undelete is DELIBERATE. The AU branch below reaches 'stale' only when NEW.deleted = 0 -- the record genuinely came back -- so the refresh a consumer would attempt CAN succeed. | driving the real SCHEMA_SQL: marking a note deleted sets context_dependents.stale_reason='unavailable', and undeleting it leaves 'stale' |
| HOLDS | `pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/settled-design-loop-closes.md:321` | FALSE — corrected 2026-09-14 (HS-200-42). The paragraph above was wrong when it was written and is kept only as the record of where the defect entered. ... `IntelQueueWorker` had zero production callers until HS-200-42. | HS-200-42 gave the worker a production caller: holdspeak/web_server.py calls start_intel_queue_conductor, which starts start_intel_queue_worker (holdspeak/intel_queue_conductor.py:138) |

13 claims — 7 known_false against a ratchet of 7 set 2026-09-17.
Ratchet reason: HS-200-45 owns three (mcp_http composition, connection WAL pragmas, SECURITY tailnet bind); HS-200-44 owns the UX-CANON A1 residue count; three are unowned and need a code change rather than a one-line doc correction (the verb-catalog mirror, desk_snapshot's layout, DESKOS_COMPONENT_PATTERN)

OK       known_false  holdspeak/web/routes/mcp_http.py:3
OK       known_false  holdspeak/db/connection.py:3
OK       known_false  docs/SECURITY.md:277
OK       known_false  docs/internal/UX-CANON.md:132
OK       known_false  holdspeak/mcp/resources.py:61
OK       known_false  holdspeak/mcp/resources.py:160
OK       known_false  docs/internal/DESKOS_COMPONENT_PATTERN.md:3
OK       holds        CLAUDE.md:153
OK       holds        docs/USER_GUIDE.md:977
OK       holds        docs/internal/DESK_GRAMMAR.md:52
OK       holds        docs/MCP_SIDECAR.md:854
OK       holds        holdspeak/db/schema.py:1346
OK       holds        pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/settled-design-loop-closes.md:321

0 drifted row(s).
```

## The fence fails in both directions (proven by mutating CODE, registry untouched; both reverted)

**A. A `holds` claim broken** — `web/src/desk/store/workspaceStorage.ts`, `hs.desk.workspace.v1` → `.v2`:

```
FAILED tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:DESK_GRAMMAR.md:52]
E  AssertionError: a documentation claim that used to HOLD is now FALSE: docs/internal/DESK_GRAMMAR.md:52
E      the sentence: THE WINDOW REMEMBERS — view, sort, direction per zone and the open set (`hs.desk.workspace.v1`), rect via panels — and restores. ...
E      what is true: DESK_WORKSPACE_STORAGE_KEY in web/src/desk/store/workspaceStorage.ts is 'hs.desk.workspace.v1'; both zone-* keys appear in web/src only inside GHOST_LAYOUT_KEYS (and its tests)
E      Fix the code, or correct the sentence AND its registry row (tests/unit/doc_claims/registry.py) in this same commit.
1 failed, 28 passed in 1.35s
```

**B. A `known_false` claim satisfied** — `PRAGMA journal_mode = WAL` added to `holdspeak/db/connection.py`:

```
FAILED tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[known_false:connection.py:3]
E  AssertionError: a KNOWN-FALSE documentation claim is now SATISFIED by the code: holdspeak/db/connection.py:3
E      the sentence: Extracted from ``Database`` so the connection protocol (WAL pragmas, row factory, commit/rollback) lives in one place.
E      what the registry recorded as true: a connection opened through this factory reports journal_mode=delete; the module sets only PRAGMA foreign_keys=ON, and the 5000ms busy_timeout it reports is sqlite3.connect's own timeout=5.0 default, not a pragma this module applies
E      owned by HS-200-45
E      This is good news and still a failure: fix the sentence in the same commit and move this claim to holds (state="holds", with truth rewritten to what the code now does, and lower KNOWN_FALSE_RATCHET).
1 failed, 28 passed in 1.50s
```

## What the measurement corrected in §7b itself

- Phase 172 settled design: FALSE when §7b was written, HOLDS now (HS-200-42 landed the conductor at `web_server.py:1278`).
- The schema lattice comment: corrected 2026-09-09; registered `holds`, proven by driving the real `SCHEMA_SQL`.
- Verb catalog: §7b said "20 missing, 13 phantoms"; measured **22 missing, 0 phantoms** (the 13 "phantoms" are the `go.*` verbs derived from `applications.ts`, which the audit did not resolve).
- Raw `<button>`: §7b said 187; measured **203** (scanner exclusions kept, `__tests__` dropped).
- `connection.py`: `busy_timeout` reads 5000 on a real connection, but that is `sqlite3.connect`'s default `timeout=5.0`, not a pragma the module sets; the claim is false on `journal_mode=delete` alone.
- SECURITY.md: "no CIDR check exists anywhere" was too strong (`concierge_service.py:297` builds the Tailscale CGNAT range for egress advice); the predicate measures what is actually false: nothing applies `bind_host`.

## Ratchet

`KNOWN_FALSE_RATCHET = 7` dated 2026-09-17: three owned by HS-200-45, one by HS-200-44, three unowned that need a code change (verb-catalog mirror, `desk_snapshot` layout, DESKOS_COMPONENT_PATTERN). The worker registered the CLAUDE.md dw-mcp claim as `known_false` (8) because an agent may not edit CLAUDE.md on a brief's authority; the orchestrator paid it (the sentence corrected, the row flipped to `holds`, the ratchet lowered to 7).

## Inherited red found on this tip

`tests/unit/test_doc_drift_guard.py` failed twice on 43's tip before this story touched anything (43's docs leaked `HS-200-43` and em dashes into `docs/ARCHITECTURE.md` and `docs/MCP_SIDECAR.md`). Paid on 43's branch @ b391632f.
