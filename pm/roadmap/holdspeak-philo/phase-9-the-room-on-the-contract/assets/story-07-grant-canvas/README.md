# PHILO-9-07 canvas: the project delegation grant on the Remote Access ledger

**Status: DRAFT, for the owner's ratification** (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code. The review page is `index.html` in this folder (every board, both widths, both word sets).

Sources: the charter's "The project delegation grant" (`../../current-phase-status.md`), story 07 (`../../story-07-the-project-delegation-grant.md`), the pre-canvas condition R4-3, and the ratified Phase 7 canvas it extends (`../../../phase-7-the-desk-on-the-contract/assets/story-02-canvas/README.md`: set A words, the credential row, the footer receipt).

## What the boards are, exactly

- **Frame:** the production Settings window: `DeskChrome`, `DeskWindowFrame` with the Settings classes, the foot and wing slots as `SurfaceWindowHost` wires them, the real `useCoreWings`, `Dock`. CSS: the product's (`web/src/styles/global.css`, `react-app.css`, `desk/desk.css`) plus a 20-line canvas `harness/main.css` (page floor, the receipt well's token run, the project line's flex run).
- **Board 0 (today)** mounts the REAL `RemoteAccessModule` (`web/src/pages/cores/SettingsCore.tsx:621`, with Phase 7's built desk grant) on the REAL wire.
- **The other boards** mount `ProposedRemoteAccess` (`harness/main.tsx`): the real module's JSX (`SettingsCore.tsx:780-898`), composed only of library species (`GadgetGroup`, `GadgetRow`, `CycleGadget`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `Button`, `SurfaceWell`, `Receipt`, `SurfaceFooter`). The desk grant's words come from the real constant `GRANT_WORDS` (`SettingsCore.tsx:286`).
- **Credential rows and projects: the real producer.** `harness/produce_wire.py` boots the rig hub (`scripts/graph_walk.py serve`) with `HOME=tempfile.mkdtemp()`. Through the real routes it turns Remote Access ON, issues `desk-agent` (DESK, 12 H) and `sweep-runner` (PROJECT, 24 H), uses `desk-agent` once over `/api/mcp`, gives `desk-agent` the Phase 7 desk grant, creates "Payments ledger cutover" and "Hiring loop", and saves `GET /api/settings/remote` and `GET /api/projects` to `harness/fixtures/` (steps: `fixtures/produce-log.json`).
- **Project grant rows: stored rows + a clock, projected by the rule below.** The producer is unbuilt. Each board states STORED `kernel_project_delegations` rows; `serve()` projects them with `project()`, Phase 7's time-aware rule per `(identity, project)`. No board poses an effective state. Board 5 stores `LIVE` with a real past `expires_at` (now − 1 h); the projection gives `EXPIRED`.
- **Clock:** `Date.now` frozen at the capture's last use + 2 h; `timezone_id=UTC`. Receipt times and operation ids are fixture values.

## The wire contract (story 07's backend lane implements this)

`GET /api/settings/remote` gains, beside Phase 7's `delegation` / `delegations[]`:

| Field | Shape | Rule |
|---|---|---|
| `credentials[].palette` | string | The **issued** palette name, stored at issue (the DESK = ALL repair). Never reverse-mapped from the resolved tool set (today `mcp_http.py:221-248` maps DESK's set back to `ALL`). |
| `credentials[].project_delegations` | `[{project_id, project_name, state, grant_id, expires_at}]` | One per project with any stored grant row for this identity: the latest row, projected to its EFFECTIVE state at read time (a stored `LIVE` row with `expires_at <= now` is `EXPIRED`; `REVOKED`/`EXPIRED` pass through). Absent project = never granted. |
| `project_delegations[]` | `{identity, project_id, project_name, state, grant_id, expires_at}` | One per `(identity, project)` whose latest row is `LIVE` in storage and whose identity has no credential row; `state` by the same projection. |

The face reads `state` only. Chip: `LIVE` → ALLOWED; `REVOKED`/`EXPIRED` → STOPPED; none → no chip. Verb: `LIVE` → Stop; else Allow; on a `project_delegations[]` row, Stop only while `LIVE`.

**Visibility (Phase 7's rule, widened):** Remote Access ON shows every credential row. OFF shows every credential row with a LIVE desk grant or a LIVE project grant, and every `project_delegations[]` row. A grant is authority; the owner must see it and be able to stop it whatever the switch says.

**Where the pick lives:** a credential row whose issued palette holds the project tools (`PROJECT`, `ALL`) expands in place (the ledger row's own expansion, `SurfaceLedgerRow` `open`). The expansion lists every project that is not archived, one `GadgetRow` each: the project name, its chip, its verb. A `DESK` or `SWEEP` credential has no project lines (it cannot call a project tool, so the verb would do nothing, UX-CANON §A.11).

## Boards (`shots/<set>/<board>-<set>-<width>.png`, sets `a` and `b`; board 0 in `shots/today/`)

| # | Board | Stored → wire | What shows |
|---|---|---|---|
| 0 | Today (real module) | — | desk grant only; `desk-agent` reads `ALL` |
| 1 | No project grant | none | `sweep-runner` open: each project line has the Allow verb, no chip; `desk-agent` reads `DESK`, no project lines |
| 2 | Granted on one project, row closed | LIVE (Payments) | closed row: ALLOWED chip + `PAYMENTS LEDGER CUTOVER`; foot `ALLOWED 14:05` |
| 3 | Same, row open | LIVE (Payments) | Payments: ALLOWED + Stop; Hiring: no chip + Allow (per-project independence) |
| 4 | Stopped | REVOKED | STOPPED chip, Allow; foot `STOPPED 14:07` |
| 5 | Expired | LIVE, `expires_at` = now − 1 h → EXPIRED | STOPPED chip, Allow; no receipt (expiry is not an owner act) |
| 6 | Live, no credential, ON | LIVE → `project_delegations[]` | `sweep-runner` `●` idle, ALLOWED, `PAYMENTS LEDGER CUTOVER`, `NO CREDENTIAL`, Stop |
| 7 | Live, no credential, OFF | same | the ledger still renders, with Stop; no `Issue credential` |
| 7b | OFF, credential kept, live | LIVE | the credential row stays (live authority); its lines keep Stop |
| 8 | Stop refused | LIVE, then REVOKED by another owner request | Payments line: STOPPED, `✗ CANNOT STOP` `NO GRANT` (`data-code=project_delegation_required`), Allow; foot `REFUSED 14:11`; the RECEIPT well open: `REFUSED`, `STOP RUN AND PUBLISH`, `NO GRANT`, project, identity, `BY OWNER`, `SEP 27 14:11` |
| 9 | Two projects | LIVE × 2 | closed row: ALLOWED + `2 PROJECTS` |

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
| Receipt well | `RECEIPT` · outcome · the act · refusal token · project · identity · `BY OWNER` · `MMM D HH:MM` | same |
| Palette token | the issued name (`DESK`, `PROJECT`, …) | same |

"Stop run and publish" covers the whole bound: `project.stop_steward` stops only a run the agent started (R4-1), so it rides with "run".

## Three questions for the owner

1. **Words:** set A (`Allow run and publish` / `RUN AND PUBLISH ALLOWED`) or set B (`Allow project work` / `PROJECT WORK ALLOWED`)? **Recommended: A.** It uses your own ruling's words ("Run, stop, publish") and says what the agent can do; B hides it.
2. **The pick:** the PROJECT credential's row opens in place with one line per project, each with its own Allow or Stop (no popover, no modal), and the closed row shows only live grants (name, or `N PROJECTS`)? **Recommended: yes.**
3. **Scope of the lines:** project lines only on credentials whose issued palette holds the project tools (`PROJECT`, `ALL`); a `DESK` credential gets none? **Recommended: yes** (a verb that can do nothing is a lie, UX-CANON §A.11).

## Measurements (`shots/facts.json`, `summary`)

42 renders (board 0 once; boards 1–9 and 7b in both sets; 1440 × 900 and 393 × 852):

- Text nodes under 12 px in the whole Settings window, footer included: **0**.
- Raw `<button>` without the library `.btn`: **0**.
- Horizontal overflow (page or window body): **0**.
- Contrast: **604** chips and tokens (`StateChip`, `surface-token`, `gadget-fact`, `Receipt`, the ledger caption), text against the background composited from its ancestors: lowest **5.33:1**; none under 4.5:1.
- Pointer: **304** Buttons, **1520** points (centre + four corners; the painted face at 1440, the 44 × 44 target at 393), each by `elementFromPoint` AND a real pointer move: **all owned**.
- Browser errors: **0** (an earlier draft nested a ledger inside the row's expansion and made `<li>` inside `<li>`; the lines are now `GadgetRow`s).

## Limits (what the boards are not)

- The project grant producer, its table and its routes do not exist. Project grant rows are stored rows projected by the canvas's statement of the wire contract, not a server response.
- The DESK palette name is the canvas's statement of the repair; the real wire says `ALL` (board 0).
- Refusals, operation ids and receipt times are fixture values. The boards are static states; no click drives a transition; board 8's well is rendered open.
- The Settings content above Remote access is omitted.
- The closed credential row shows no mark that it opens (the ledger species' own look; `aria-expanded` is set). Inherited, not changed here.
- Inherited, not in scope: the Phase 7 desk verb (`Allow filing`) is on every credential row, the `PROJECT` one too, where the desk tools are not in its palette.
- Observed, not investigated: `POST /api/settings/remote/credentials` answered `expires_at` 567176.6 for a 12 H credential while `GET /api/settings/remote` answered an epoch time (`fixtures/produce-log.json` against `fixtures/remote-wire.json`). Unknown whether a face reads the POST value.

## Fence sketch for story 07 (not built)

Real hub, isolated HOME, real credentials, the real `PUT`/`DELETE /api/settings/remote/delegations/{identity}/projects/{project_id}`, the real `GET /api/settings/remote`; assert on the rendered Settings window at 1440 and 393; the words from one constant the face imports.

| After | Assert | Red |
|---|---|---|
| Load, no grant | `sweep-runner` opens; each project line has the Allow words, no chip; `desk-agent` has no project lines and reads `DESK` | main: no lines; `ALL` |
| Allow on Payments | Payments ALLOWED + Stop; Hiring unchanged; closed row names Payments; foot receipt's `operation_id` = the route's = the kernel's | main: 404 |
| Stop | STOPPED + Allow; receipt `owner_revoked` | mutation: the face reads the stored column |
| Clock past `expires_at` | the API says `EXPIRED`; the chip STOPPED | mutation: the projection reads stored `state` |
| Credential revoked with a live project grant | the grant revoked first (`credential_revoked`); the orphan row renders with Stop, ON and OFF | mutation: credential removed first; OFF hides the row |
| Refused Stop | `[data-code=project_delegation_required]` on the line; the foot `REFUSED`; its well matches the route's refusal | mutation: the refusal dropped on reread |
| Every state | 0 text under 12 px; 0 raw buttons; every chip ≥ 4.5:1; every Button owned; no overflow | this canvas's probe |

## Reproduce

```bash
# 1. the real producer's wire (the script boots the hub with HOME=mkdtemp)
uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/produce_wire.py
# 2. shoot (starts vite on 127.0.0.1:4442; renders, the 12 px scan, contrast, pointer)
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/shoot.py a b
# 3. the review page
uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/build_review.py
```
