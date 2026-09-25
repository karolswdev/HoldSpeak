# PHILO-7-02 round two — Astra's check on built (r1), conditions paid

- **Check:** `checks/story-02-built-astra-r1.md` — BOUNCE at `86ec4ee5`. It independently verified the main implementation: 244 scoped tests passed, one operation plus one receipt per write, the T9 fault, the restart, and the module split.
- **Branch:** `feat/philo-7-02-article-xi`. The code and fences are in `7a1ff8a9`; this record is in the commit after it. The story was already `done`, so the gate keeps `evidence-story-02.md` as it was. This file is the round-two record.
- **Author:** the Fedaykin lane (Opus 5.5) for Muad'Dib.

## Finding 1 (P0) — a grant body could name another agent

**Cause.** `holdspeak/services/desk_delegation.py:46` (round one) spread the body over the payload, so `{"agent_identity": "body-agent"}` replaced the path identity.

**Repair.** `desk_delegation.py:50`: any body field other than `expires_at` is refused by `_refuse_body` (`:33`). The refusal is `invalid_arguments` with its receipt, targeted at the PATH's agent. A DELETE body with any field is refused the same way (`:65`).

**Fence.** `tests/unit/test_philo7_round_two.py::test_a_grant_body_cannot_name_another_agent` asserts 400 `invalid_arguments`, the receipt (`target_ref=agent:path-agent`) read back durably, and zero grant rows. **Red on round one:** `AssertionError: {"success":true,"operation_id":"op_…","receipt":{…"state":"succeeded"…` (the grant went to body-agent).

## Finding 2 — refusals that escaped admission

| Path | Repair | Red on round one (`red-round-two.txt`) |
|---|---|---|
| HTTP supersede of a missing decision | `holdspeak/web/routes/decisions.py:95`: an id that names NO decision goes to the desk contract. Its NotFound leaves the receipt (MCP already did). Still 404 `decision_not_found`, now with `operation_id` and `receipt`. | `no receipt in the response: {'error': 'decision_not_found'}` |
| Supersede body `[1]` on a desk decision | Same route; the body param is `Any`. A non-object body on a desk decision gets a receipt with `target_ref=decision:<id>`. Still 422 with FastAPI's `detail` shape. Meeting decisions keep 422 without a receipt. | `no receipt in the response: {'detail': [{'type': 'dict_type', …}]}` |
| Decision create with `tags: 42` | `holdspeak/web/routes/primitives/decisions.py:28` `_as_list` and `:88`: the route's own coercion is unchanged for every value main accepted. A value it cannot iterate (a 500 on main) is refused by name: 400 `Invalid arguments for decision.create: tags must be a list`, with a receipt. | `{"error":"'int' object is not iterable"}` (500) |
| MCP delete of a Thought's note with an unexpected field / an authority field | `holdspeak/operations.py:1504`: `consequential` asks the stored state (`thought_owns_note`) when the admission condition is stored-state. When the id names a Thought's note, its contract refusal owes the receipt. | `no receipt in the response: {'error': "Invalid arguments for note.delete: Additional properties are not allowed …"}` and `… owner cannot be an argument …` |

Each fence asserts three things: the response fields, the durable receipt (`GET /api/kernel/read`), and the unchanged state (no decision rows; the Thought not tombstoned).

## Finding 3 — refusal receipts the caller could not read

**Repair.** Every refusal response of an admitted operation now carries `operation_id` and `receipt`:

- HTTP non-object bodies: `primitives/decisions.py:71,119,155`; the conditional routes answer the same way when a receipt exists.
- MCP: `mcp/tools.py:886,912,1336` attach the refusal's kernel fields to the `ToolError`. `mcp/server.py:418` adds them to the palette error's `data` and to the tool result. `:434` handles contract refusals, and non-object arguments are handled at `server.py` before dispatch.
- The inherited tombstoned-Thought HTTP 500: `primitives/directories.py:152` keeps main's 500 and puts the receipt in the body. The BACKLOG row is filed in `pm/roadmap/holdspeak/BACKLOG.md`, "PHILO-7-02 round two follow-ups".

**Fences.** Six in `test_philo7_round_two.py`, one per path: non-object create, schema refusal, non-object arguments, contract refusal, palette refusal, tombstoned 500. Each was red on round one (`no receipt in the response: …`; the palette case `KeyError: 'receipt'`).

`tests/unit/test_philo5_one_decision.py::test_palette_refusal_through_the_http_jsonrpc_handler_is_mcp_005` pinned the exact palette `data`. It now asserts `code` and `tool` plus the receipt: an additive change for admitted tools only.

## Finding 4 — the real scroll-edge position

**Cause.** The footer overlaps the body's scrollport edge. A control that is scrolled into view minimally (`block: nearest`) stopped with its lower target corners under `surface-footer-layout`.

**Repair.** `web/src/desk/components/window-chrome.css:381` adds `scroll-padding-block: 24px` on `.desk-next .desk-surface-body`. This is a library change and applies desk-wide: every surface window's minimally scrolled control now clears the footer, including its 44 px target.

**Fence.** `tests/e2e/test_philo7_02_grant_glass.py:357` `test_a_minimally_scrolled_verb_clears_the_footer[1440|393]` scrolls the body to its top, then moves `Issue credential` into view with `block: nearest`. It checks `elementFromPoint` and a real `pointermove` at the centre and four corners, using the 44 px target at 393. **Red on round one (`red-scroll-edge.txt`), both widths:** `elementFromPoint does not reach it at {'x': 40, 'y': 634.078125 …}` (1440) and `{'x': 16, 'y': 680.578125 …}` (393).

**F23 and board 5d rendered (Astra confirmed they already worked):**

| Fence | What it covers | Red |
|---|---|---|
| `:380` `test_an_expired_grant_reads_stopped_on_both_rows` | Stored LIVE past its expiry: FILING STOPPED `idle` on the credential row and on the orphan row, with no verb on the orphan | mutation mf3: `'FILING STOPPED' not in '✓\nFILING ALLOWED'` |
| `:413` `test_remote_off_keeps_a_credential_with_a_live_grant` | With remote OFF, the credential with a LIVE grant stays (Stop, Revoke credential); `sweep-runner` is hidden | mutation mf4: the row is absent (timeout) |

Both mutations are recorded in `red-mutations-round-two.txt`.

## Finding 5 — generated docs and records

- `docs/generated/api-reference.json` is regenerated, in order: `gen_api_surface` → `philo_openapi_reference` → `philo_api_reference` → `philo_boundary_census` → `philo_graph_reference` → `gen_operations_json` → `gen_mcp_sidecar_doc`.
- Every `--check` is green: `API reference checked`, `Boundary candidate census checked`, `graph join checked`, `OK docs/generated/operations.json`, `RESIDUAL FENCE GREEN: 284`.

**The authority changes are TWO, not one.** The story's acceptance criterion is amended to say so, in full:

1. **R1:** an AGENT write is refused without a grant and executed with a delegation receipt with one.
2. **Admission's consequence for principals no transport produces:**
   - a NODE principal on an ADMITTED operation → `declared_capability_required` (403) with a receipt;
   - a missing principal → `principal_required`, with no receipt.

Main let both of these write. Astra ruled them lawful (a NODE has only `NODE_LINK`; an unauthenticated caller cannot supply authority), so no owner round is needed. The round-one compat table in `evidence-story-02.md` has the NODE and missing-principal rows, but its header line "THE ONE NAMED CHANGE" is superseded by this record.

**The story's acceptance boxes, flipped honestly (16 of 17).**

- **Fence-law box: UNCHECKED in round two. CORRECTED in round three:** the round-two sentence here said nothing on four boundary paths (unknown tool, unknown operation, failed read, palette refusal of a read) "identifies a consequential operation, so no plausible mutation reaches the receipt path". That was WRONG (Astra r2 finding 2): broadening refusal journaling at each of those refusal sites turns its fence red (Round three, below). The other four were red under m24 / m24b.
- **Face box: flipped.** The rendered fences cover allow, stop and a refused stop. A refused ALLOW is not rendered-fenced; the criterion reads "a refused grant OR revoke", so the box stands.

## MISSED 3 — one fence per path

The multi-path fences in `tests/unit/test_philo7_article_xi.py` are split into parametrized per-path fences:

- `ADMISSION_PATHS` (`:198`, 26 paths)
- `CLASS_2` (6), `CLASS_3` (3), `CLASS_4` (6)
- `BOUNDARY` (8)

**On a `git archive` copy of main (`red-main-per-path.txt`):** 41 failed, each with its own first line, and 8 boundary paths green by design. The boundary's mutation reds per path: m24 reddens `malformed exempt operation` and `palette refusal of an exempt write`; m24b reddens both non-object conditional paths.

## MISSED 4 — the restart with a request already waiting

`tests/unit/test_philo7_grant_restart.py:144` changes the fence:

- The first hub process runs with the fence's hold: its approval of a `zone.file` never returns.
- A REAL agent `zone.file` request goes over `/api/mcp` on a background thread. The fence waits until that request sits in `awaiting_decision`, then SIGKILLs the process with it in flight.
- The new process ends the request `indeterminate / hub_restart_during_decision` with its receipt, then files under the original grant.

**Mutation m27** (startup recovery skipped): `assert [] == [('indeterminate', 'hub_restart_during_decision')]`.

## Runs (isolated HOME)

| Run | Result |
|---|---|
| Scoped set (101 files + `test_philo7_round_two.py`, `-n 8`) | **1999 passed**, 0 failed, 0 errors |
| Glass (`test_philo7_02_grant_glass.py` + the HS-174 rig) | **16 passed** |
| Web baseline (`check_web_baseline.py --run`) | **2872 passed, 0 failed**; `VERDICT: baseline-subset, zero branch-new`; no `Errors` line in the vitest output |

The HS-174 rig's shots went to `.tmp/evidence-shots` (no evidence write). `pm/roadmap/holdspeak/` changes only by the BACKLOG row. The full suite is CI's; its run is to be read before merge (Astra's condition 4).

## Disagreements

None with the findings.

One judgment call, stated: decision creation with a non-iterable list field changes from a crash (500) to a named 400. Main did not "accept" it; it crashed. Every value main accepted is still accepted, because the coercion is unchanged.


## Round three — Astra's check on built r2 (`checks/story-02-built-astra-r2.md`, RATIFY-WITH-CONDITIONS)

**Finding 1 — a false-negative fence.** The unknown-operation boundary fence called `invoke(None, …)`. `services/desk_kernel.py` `refuse` writes nothing without an authenticated principal, so journaling broadened to that refusal could never show on it. Astra's broadening through the real broker left the fence green, while an authenticated owner call wrote a wrong receipt. **Rewritten:** `tests/unit/test_philo7_article_xi.py:528` has two separate paths, `unknown operation, owner` and `unknown operation, agent`. They use `_OWNER` / `_AGENT` (authenticated `Principal`s) and assert the named error through `_refused_as(…, "unknown_operation")` (`OperationRefused.code`). Like every boundary path, they also assert zero operations and zero receipts. Every other boundary path already ran under an authenticated principal (the owner's hub client, or the PROJECT agent credential).

**Finding 2 — every boundary path now has its own red.** Each mutation broadens refusal journaling through the REAL broker (`desk_kernel.refuse`, authenticated principal, a desk operation name) at ONE refusal site. Each was applied, run and restored by copy (`red-mutations-round-two.txt`):

| Mutation | Site | Fence (path) | Red |
|---|---|---|---|
| mb1 | `mcp/server.py`, the `Unknown tool` ToolError | `[unknown tool]` | `AssertionError: an exempt or protocol-refused call made a kernel operation` |
| mb2 | `mcp/server.py` (`/api/mcp` handler), the ServiceError answer | `[failed read]` | the same line |
| mb3 | `mcp/tools.py` `dispatch_for_palette`, every palette refusal | `[palette refusal of a read]` | the same line |
| mb4 | `operations.py` `invoke`, the unknown-operation refusal | `[unknown operation, owner]` | the same line |
| mb4b | the same site | `[unknown operation, agent]` | the same line |
| m24 | `operations.consequential`, exempt made consequential | `[malformed exempt operation]`, `[palette refusal of an exempt write]` | (round two, `red-main-per-path.txt`) |
| m24b | `operations.consequential`, non-object conditional made consequential | `[non-object payload, conditional operation]`, `[http non-object body, conditional operation]` | (round two) |

All nine boundary paths have a demonstrated red. The fence-law box in the story is FLIPPED in this round. Every behavioural fence is red pre-fix through the real producers (`red-main-behaviour.txt`, `red-main-per-path.txt`, `red-round-two.txt`, `red-face.txt`, `red-scroll-edge.txt`); every structural invariant is red under a named mutation (`red-mutations.txt`, `red-mutations-round-two.txt`).

**Finding 3 / CI.** Astra read the fast jobs green on `5b0d6ff5`: Documentation Navigation, Web Quality (2872 passed), G0, Linux Smoke, Route screenshots. Unit, Integration and macOS E2E were pending at its check, and remain for the orchestrator to read before merge.
