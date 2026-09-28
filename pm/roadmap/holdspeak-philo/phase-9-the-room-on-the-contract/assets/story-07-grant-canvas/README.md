# PHILO-9-07 canvas: the project delegation grant on the Remote Access ledger

**Status: RATIFIED 2026-09-27 by the owner ("Ratify as drawn"), after Codex Astra r1 DNR → r2 DNR → r3 RATIFY** (`../../checks/canvases-astra-r1.md`, `../../checks/canvases-astra-r2.md`, `../../checks/canvases-astra-r3.md`; AskUserQuestion; review page https://claude.ai/artifact/ADQeZoxRYmWfYKEfL8wePT). His pick, verbatim: "Ratify as drawn (Recommended)", all seven recommendations. This canvas: Q4 the grant words set A (`Allow run and publish` / `RUN AND PUBLISH ALLOWED`); Q5 the per-project list behind a visible `▸ Projects`. Build exactly this. The seven answers across the four canvases: Q1 items after NEEDS YOU, omitted when empty; Q2 DELIVERED ×N; Q3 To + Mark delivered above the body; Q4 grant words set A; Q5 per-project list behind a visible ▸ Projects; Q6 the accent selection colours; Q7 at 393 the fold line.

Earlier status: (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code. The review page is `index.html` in this folder (every board, both widths, both word sets). Round two pays Codex Astra r1 findings 2 and 3 (`../../checks/canvases-astra-r1.md`).

Sources: the charter's "The project delegation grant" (`../../current-phase-status.md`), story 07 (`../../story-07-the-project-delegation-grant.md`), the pre-canvas condition R4-3, and the ratified Phase 7 canvas it extends (`../../../phase-7-the-desk-on-the-contract/assets/story-02-canvas/README.md`: set A words, the credential row, the footer receipt).

## What the boards are, exactly

- **Frame:** the production Settings window: `DeskChrome`, `DeskWindowFrame` with the Settings classes, the foot and wing slots as `SurfaceWindowHost` wires them, the real `useCoreWings`, `Dock`. CSS: the product's (`web/src/styles/global.css`, `react-app.css`, `desk/desk.css`) plus a 20-line canvas `harness/main.css` (page floor, the receipt well's token run, the project line's flex run).
- **Board 0 (today)** mounts the REAL `RemoteAccessModule` (`web/src/pages/cores/SettingsCore.tsx:621`, with Phase 7's built desk grant) on the REAL wire.
- **The other boards** mount `ProposedRemoteAccess` (`harness/main.tsx`): the real module's JSX (`SettingsCore.tsx:780-898`), composed only of library species (`GadgetGroup`, `GadgetRow`, `CycleGadget`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `Button`, `SurfaceWell`, `Receipt`, `SurfaceFooter`). The desk grant's words come from the real constant `GRANT_WORDS` (`SettingsCore.tsx:286`).
- **Credential rows and projects: the real producer.** `harness/produce_wire.py` boots the rig hub (`scripts/graph_walk.py serve`) with `HOME=tempfile.mkdtemp()`. Through the real routes it turns Remote Access ON, issues `desk-agent` (DESK, 12 H) and `sweep-runner` (PROJECT, 24 H), uses `desk-agent` once over `/api/mcp`, gives `desk-agent` the Phase 7 desk grant, creates "Payments ledger cutover" and "Hiring loop", and saves `GET /api/settings/remote` and `GET /api/projects` to `harness/fixtures/` (steps: `fixtures/produce-log.json`).
- **Project grant rows: stored rows + a clock, projected by the rule below.** The producer is unbuilt. Each board states STORED `kernel_project_delegations` rows; `serve()` projects them with `project()`, Phase 7's time-aware rule per `(identity, project)`. No board poses an effective state. Board 5 stores `LIVE` with a real past `expires_at` (now − 1 h); the projection gives `EXPIRED`.
- **Clock:** `Date.now` frozen at the capture's last use + 2 h; `timezone_id=UTC`. Receipt times and operation ids are fixture values.

## The wire contract (story 07's backend lane implements this)

`GET /api/settings/remote` keeps Phase 7's `credentials[].delegation` and `delegations[]` (the desk-grant orphans, `SettingsCore.tsx:279`, rendered at `:869`) unchanged, and gains:

| Field | Shape | Rule |
|---|---|---|
| `credentials[].palette` | string | The **issued** palette name, stored at issue (the DESK = ALL repair). Never reverse-mapped from the resolved tool set (today `mcp_http.py:221-248` maps DESK's set back to `ALL`). |
| `credentials[].project_delegations` | `[{project_id, project_name, state, grant_id, expires_at}]` | One per project with any stored grant row for this identity: the latest row, projected to its EFFECTIVE state at read time (a stored `LIVE` row with `expires_at <= now` is `EXPIRED`; `REVOKED`/`EXPIRED` pass through). Absent project = never granted. |
| `project_delegations[]` | `{identity, project_id, project_name, state, grant_id, expires_at}` | One per `(identity, project)` whose latest row is `LIVE` in storage and whose identity has no credential row; `state` by the same projection. |

The face reads `state` only. Chip: `LIVE` → ALLOWED; `REVOKED`/`EXPIRED` → STOPPED; none → no chip. Verb: `LIVE` → Stop; else Allow; on a `project_delegations[]` row, Stop only while `LIVE`.

**Visibility (Phase 7's rule, widened):** Remote Access ON shows every credential row. OFF shows every credential row with a LIVE desk grant or a LIVE project grant. Always: every `delegations[]` row (Phase 7's desk orphans, Stop filing) and every `project_delegations[]` row, side by side (boards 6, 7). The ledger renders when any credential, desk orphan or project orphan row is visible. A grant is authority; the owner must see it and be able to stop it whatever the switch says.

**Where the pick lives:** a credential row whose palette holds the project tools carries the library `Disclosure` trigger `▸ Projects` (`web/src/desk/surface/patterns/Disclosure.tsx`, default variant, `controlsId` = the row's own expansion slot, the HS-200-15 pattern of `web/src/desk/chair/ChairHome.tsx:1688-1697`). It opens the row in place: every project that is not archived, one `GadgetRow` each (the name, its chip, its verb). No popover, no modal.

**Palette compatibility (settled; a correctness rule, not a question):** a grant's controls show only where the credential's issued palette holds the tools that grant covers. Measured on this tree with `holdspeak.mcp.palettes.resolve_palette` (`holdspeak/mcp/palettes.py:40-55`): the three bound tools (`project.run_steward`, `project.stop_steward`, `project.publish_update`) are in `PROJECT`, `SWEEP`, `DESK` and `ALL` (DESK resolves to every top-level tool); the desk family (`desk.*`, `zone.*`, `decision.*`, `note.*`, `kb.*`) is in `DESK` and `ALL` only. So: `▸ Projects` on all four; the desk chip and `Allow filing` / `Stop filing` on `DESK` and `ALL` only. A `PROJECT` credential no longer shows `Allow filing` (board 2).

## Boards (`shots/<set>/<board>-<set>-<width>.png`, sets `a` and `b`; board 0 in `shots/today/`)

| # | Board | Stored → wire | What shows |
|---|---|---|---|
| 0 | Today (real module) | — | desk grant only; `desk-agent` reads `ALL` |
| 1 | No project grant | none | `sweep-runner` open: each project line has the Allow verb, no chip; `desk-agent` reads `DESK`; `sweep-runner` has no desk verb |
| 2 | Granted on one project, row closed | LIVE (Payments) | closed row: ALLOWED chip + `PAYMENTS LEDGER CUTOVER`; foot `ALLOWED 14:05` |
| 3 | Same, row open | LIVE (Payments) | Payments: ALLOWED + Stop; Hiring: no chip + Allow (per-project independence) |
| 4 | Stopped | REVOKED | STOPPED chip, Allow; foot `STOPPED 14:07` |
| 5 | Expired | LIVE, `expires_at` = now − 1 h → EXPIRED | STOPPED chip, Allow; no receipt (expiry is not an owner act) |
| 6 | Live grants, no credentials, ON (a restart or a lost credential with the grants still LIVE) | desk LIVE → `delegations[]`; project LIVE → `project_delegations[]` | `desk-agent`: FILING ALLOWED, `NO CREDENTIAL`, Stop filing; `sweep-runner`: ALLOWED, `PAYMENTS LEDGER CUTOVER`, `NO CREDENTIAL`, Stop run and publish |
| 7 | The same, OFF | same | both orphan rows still render, each with Stop; no `Issue credential` |
| 7b | OFF, credential kept, live | LIVE | the credential row stays (live authority); its lines keep Stop |
| 8 | Stop refused | LIVE, then REVOKED by another owner request | Payments line: STOPPED, `✗ CANNOT STOP` `NO GRANT` (`data-code=project_delegation_required`), Allow; foot `REFUSED 14:11`; the RECEIPT well open: `REFUSED`, `STOP RUN AND PUBLISH`, `NO GRANT`, project, identity, `BY OWNER`, `SEP 27 14:11` |
| 9 | Two projects | LIVE × 2 | closed row: ALLOWED + `2 PROJECTS` |
| 10 | The last orphan stopped | project LIVE, then REVOKED by this Stop; no credentials; OFF | the row is gone; nothing left, so no ledger; foot `STOPPED 14:13` and its well open: `SUCCEEDED`, `RUN AND PUBLISH STOPPED`, the project, `sweep-runner`, `BY OWNER` |
| 11 | The owner revokes a credential | `sweep-runner`'s project grant LIVE, then REVOKED (`credential_revoked`) before its credential is removed | `sweep-runner`'s row is gone; no orphan remains; foot `STOPPED 14:15` and its well open: `SUCCEEDED`, `RUN AND PUBLISH STOPPED`, `CREDENTIAL REVOKED`, the project, `sweep-runner`, `BY OWNER` |

| 12 | Archived project, grant LIVE, ON (board `12-archived`) and OFF (`12b-archived-off`) | LIVE (Payments, archived) | Payments line: `ARCHIVED` word chip, ALLOWED, `Stop run and publish` (never Allow on an archived project); Hiring unchanged; OFF keeps the row (live authority) |

Board 12 **added 2026-09-28 by Muad'Dib's ruling, a stop-authority state the canvas omitted; the owner sees it with the closing shots** — the owner saw it with the closing shots, 2026-09-28 (PHILO-9-06, https://claude.ai/artifact/C66EYhCAcDBbPdkeZJFFYD) (Codex Astra r1 on PR #685, finding 2: archive keeps a project's grants, so a LIVE grant on an archived project must stay visible and stoppable). Shot with the same harness (`ONLY_BOARDS=12-archived,12b-archived-off shoot.py a`; facts `shots/facts-12-archived.json`: 4 renders, 0 small text, 0 raw buttons, contrast min 6.99, 234 points all owned). Set A only.

## The strings (proposed)

| Slot | Set A (recommended) | Set B |
|---|---|---|
| Verb, effective state not LIVE | `Allow run and publish` | `Allow project work` |
| Verb, LIVE | `Stop run and publish` | `Stop project work` |
| Chip, LIVE (`StateChip success ✓`) | `RUN AND PUBLISH ALLOWED` | `PROJECT WORK ALLOWED` |
| Chip, REVOKED or EXPIRED (`StateChip idle ○`) | `RUN AND PUBLISH STOPPED` | `PROJECT WORK STOPPED` |
| Closed-row summary | the LIVE chip + the project name in capitals (one live) or `N PROJECTS` (more); nothing when none is live | same |
| Refusal chip / token | `CANNOT ALLOW` / `CANNOT STOP` + `NO GRANT` (`project_delegation_required`), `GRANT STOPPED` (`_revoked`), `GRANT EXPIRED` (`_expired`), `OWNER ONLY` (`owner_principal_required`), `BAD REQUEST` (`invalid_arguments`) | same |
| Orphan cell | `NO CREDENTIAL` (Phase 7's) | same |
| Foot receipt | `ALLOWED` / `STOPPED` / `REFUSED` + `HH:MM` (Phase 7's) | same |
| Receipt well | `RECEIPT` · outcome · the act · refusal token · `CREDENTIAL REVOKED` (when the grant ended by a credential revoke) · project · identity · `BY OWNER` · `MMM D HH:MM` | same |
| Palette token | the issued name (`DESK`, `PROJECT`, …) | same |
| Opening affordance | the library `Disclosure`: `▸ Projects` (caret turns when open) | same |

"Stop run and publish" covers the whole bound: `project.stop_steward` stops only a run the agent started (R4-1), so it rides with "run".

## Two questions for the owner

1. **Words:** set A (`Allow run and publish` / `RUN AND PUBLISH ALLOWED`) or set B (`Allow project work` / `PROJECT WORK ALLOWED`)? **Recommended: A.** It uses your own ruling's words ("Run, stop, publish") and says what the agent can do; B hides it.
2. **The pick:** a `▸ Projects` Disclosure on the credential row opens it in place, with one line per project, each with its own Allow or Stop (no popover, no modal); the closed row shows only live grants (name, or `N PROJECTS`)? **Recommended: yes.**

## Measurements (`shots/facts.json`, `summary`)

50 renders (board 0 once; boards 1–11 and 7b in both sets; 1440 × 900 and 393 × 852). The scans cover the whole Settings window with its footer, and any open menu or popover (none is open on these boards):

- Text nodes under 12 px: **0** (the Disclosure's `▸` caret, 11 px, is a lone glyph, exempt under UX-CANON C). The `dense` Disclosure variant was tried first: its label is 10 px (`disclosure.css:119`), so the canvas uses the default variant (12 px, `disclosure.css:24`).
- Raw `<button>` without the library `.btn`: **0**.
- Horizontal overflow (page or window body): **0**.
- Contrast: **736** chips, tokens and labels (`StateChip`, `surface-token`, `gadget-fact`, `Receipt`, the ledger caption, the Disclosure label), text against the background composited from its ancestors: lowest **5.33:1**; none under 4.5:1.
- Pointer: **292** controls, **2628** points (nine per control: centre, four corners and four edge midpoints, each inset 1 px; the painted face at 1440, the 44 × 44 target at 393), each by `elementFromPoint` AND a real pointer move: **all owned**. This includes every `▸ Projects` trigger, every desk and project grant verb, every orphan Stop, and the footer receipt Button and `« PREFS`.
- Browser errors: **0** (an earlier draft nested a ledger inside the row's expansion and made `<li>` inside `<li>`; the lines are now `GadgetRow`s).

## Limits (what the boards are not)

- The project grant producer, its table and its routes do not exist. Project grant rows are stored rows projected by the canvas's statement of the wire contract, not a server response.
- The DESK palette name is the canvas's statement of the repair; the real wire says `ALL` (board 0).
- Refusals, operation ids and receipt times are fixture values. The boards are static states; no click drives a transition; board 8's well is rendered open.
- The Settings content above Remote access is omitted.
- The credential `expires_at` mismatch between `POST` and `GET /api/settings/remote` goes to the BACKLOG (the orchestrator files the row).

## Fence sketch for story 07 (not built)

Real hub, isolated HOME, real credentials, the real `PUT`/`DELETE /api/settings/remote/delegations/{identity}/projects/{project_id}`, the real `GET /api/settings/remote`; assert on the rendered Settings window at 1440 and 393; the words from one constant the face imports.

| After | Assert | Red |
|---|---|---|
| Load, no grant | `sweep-runner` shows `▸ Projects` and no desk verb; opened, each project line has the Allow words, no chip; `desk-agent` reads `DESK` and keeps the desk verb | main: no lines; `ALL`; `Allow filing` on PROJECT |
| Allow on Payments | Payments ALLOWED + Stop; Hiring unchanged; closed row names Payments; foot receipt's `operation_id` = the route's = the kernel's | main: 404 |
| Stop | STOPPED + Allow; receipt `owner_revoked` | mutation: the face reads the stored column |
| Clock past `expires_at` | the API says `EXPIRED`; the chip STOPPED | mutation: the projection reads stored `state` |
| Owner revokes a credential with a live project grant | the grant is revoked first (`credential_revoked`), then the credential; the row is gone and NO orphan row appears; the foot receipt and its well read the grant's receipt | mutation: the credential removed first; the reason written as `owner_revoked` |
| Restart or lost credential, grants still LIVE | the desk orphan (Stop filing) and the project orphan (Stop run and publish) both render, ON and OFF | mutation: OFF hides them; the desk orphans dropped by the new renderer |
| Stop on the last orphan | the row is gone; `.surface-ledger` is absent; the foot receipt Button is owned at centre + corners; its well reads `SUCCEEDED`, the STOPPED words, the project, the identity | mutation: the receipt rendered inside the ledger |
| Refused Stop | `[data-code=project_delegation_required]` on the line; the foot `REFUSED`; its well matches the route's refusal | mutation: the refusal dropped on reread |
| Every state | 0 text under 12 px; 0 raw buttons; every chip ≥ 4.5:1; every Button owned at nine points; no overflow | this canvas's probe |

## Reproduce

```bash
# 1. the real producer's wire (the script boots the hub with HOME=mkdtemp)
uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/produce_wire.py
# 2. shoot (starts vite on 127.0.0.1:4442; renders, the 12 px scan, contrast, pointer)
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/shoot.py a b
# 3. the review page
uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/build_review.py
```
