# PHILO-7-02 canvas: the delegation grant on the Remote Access ledger

**Status: PROPOSED, round two. The owner ratifies before the face is built** (UX canon A.2, E.1). Every decision below is proposed; none is ratified.

- Round one: PR #658 `f493fb1f`. Astra r1: BOUNCE (`../../checks/story-02-canvas-astra-r1.md`). It supported the composition, no prose / no modal / no zero, the single screen, set B, `AGENTS` and the order. Round two pays its eight findings (ledger at the end).
- Review page (all boards embedded, both widths, both word sets, the limits): `docs/internal/philo/phase-7/grant-canvas/index.html`.

## What the boards are, exactly

- **Frame:** the production window. `DeskChrome`, `DeskWindowFrame` with the Settings classes, the foot and wing slots wired as `SurfaceWindowHost` wires them (`web/src/desk/components/SurfaceWindows.tsx:155-211`), the real `useCoreWings` (SETTINGS / GUIDE), `Dock`. CSS: the product entry's (`web/src/main.tsx:8-9`) plus a 15-line canvas `main.css` (page floor; the receipt well's token run).
- **Board 0 (today)** mounts the REAL `RemoteAccessModule` (`web/src/pages/cores/SettingsCore.tsx:478`) on the REAL producer's wire (its first two credentials).
- **The other boards** mount `ProposedRemoteAccess` (`harness/main.tsx`): the real module's JSX, composed only of library species (`GadgetGroup`, `GadgetRow`, `CycleGadget`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `Button`, `SurfaceWell`, `Receipt`, `SurfaceFooter`), plus the proposal.
- **Credential rows: the real producer.** `harness/produce_remote_wire.py` boots the real hub on an isolated database (the Phase 5 fence fixture). It issues `desk-agent` (DESK, 12 H), `sweep-runner` (PROJECT, 24 H) and `review-agent` (PROJECT, 1 s TTL, read after it lapses: the real store keeps it with `active=false`, the beat's matrix row :147). It uses `desk-agent` once from a non-loopback host, and saves `GET /api/settings/remote` to `harness/fixtures/remote-wire.json`.
- **Grant rows: stored rows + a clock, projected by the rule below.** The grant producer is unbuilt. Each board states STORED `kernel_desk_delegations` rows; `serve()` in `harness/main.tsx` projects them to the wire with `project()`, the beat's time-aware rule. No board poses an effective state. Boards 4 and 5c store `state=LIVE` with a real past `expires_at` (now − 1 h); the projection returns EXPIRED.
- **Clock:** `Date.now` frozen at the capture's last use + 2 h (`LAST USED 2 H AGO`); `timezone_id=UTC`. The menu-bar clock is the real clock. Receipt times and operation ids are fixture values.

## The wire contract (the backend lane implements this)

`GET /api/settings/remote` gains two things. Both carry the **EFFECTIVE** grant state, never the stored column:

| Field | Shape | Rule |
|---|---|---|
| `credentials[].delegation` | `{state, grant_id, expires_at} \| null` | The identity's grant through `by_identity(identity, now=read time)`, non-authoritative (beat :58, :154). `null` = never granted (`desk_delegation_required`). `state`: `LIVE` when the code is `""`; `EXPIRED` for `_expired` (incl. a stored LIVE row with `expires_at <= now`, check order row 2 before row 3, beat :52); `REVOKED` for `_revoked`. `grant_id` and `expires_at` are the selected row's. |
| `delegations[]` | `{identity, state, grant_id, expires_at}` | One per grant row that is LIVE in STORAGE and whose identity has no credential row (beat :155); `state` by the same projection, so a stored LIVE row past its expiry says `EXPIRED`. |

The face reads `state` only. The chip: `LIVE` → the ALLOWED chip; `REVOKED`/`EXPIRED` → the STOPPED chip; `null` → no chip. The grant verb: `LIVE` → Stop; else Allow; on a `delegations[]` row, the Stop verb only while `LIVE`.

**Visibility (proposed):** remote ON shows every credential row and every `delegations[]` row. Remote OFF shows every row whose effective state is `LIVE` (credential-backed or not) and hides the rest. The ledger renders when any row is visible (the beat's "any credential OR any delegation row"). A grant is authority; the owner must see it and be able to stop it whatever the switch says.

## Boards (`shots/<set>/<board>-<set>-<width>.png`, sets `a` and `b`; board 0 in `shots/today/`)

| # | Board | Stored grant → wire | Row(s) |
|---|---|---|---|
| 0 | Today (real module) | — | caption `CREDENTIALS`; `Revoke` only |
| 1 | No grant ever | none → `null` | no chip; Allow verb, `Revoke credential` |
| 2 | LIVE | LIVE → LIVE | ALLOWED chip; Stop verb; foot receipt `ALLOWED 14:05` |
| 3 | Stopped | REVOKED → REVOKED | STOPPED chip; Allow verb; foot receipt `STOPPED 14:07` |
| 4 | Grant expired, credential active | LIVE, `expires_at` = now − 1 h → EXPIRED | credential `●` active, STOPPED chip, Allow verb; no receipt (expiry is not an owner act) |
| 4b | Credential expired, grant LIVE (real `active=false` row) | LIVE → LIVE | `review-agent`: `●` idle, ALLOWED chip, `⚠ EXPIRED`, Stop verb (both truths, beat :147, :154) |
| 5 | LIVE, no credential, remote ON | LIVE → `delegations[]` LIVE | `●` idle, ALLOWED, `NO CREDENTIAL`; Stop verb only |
| 5b | LIVE, no credential, remote OFF | same | the ledger still renders; no `Issue credential` |
| 5c | No credential, grant past expiry | LIVE, `expires_at` = now − 1 h → EXPIRED | STOPPED, `NO CREDENTIAL`; no verb |
| 5d | Remote OFF, credential retained, grant LIVE | LIVE → LIVE | `desk-agent` stays (Stop verb, `Revoke credential`); `sweep-runner` (no grant) hidden; caption `AGENTS · 1 ACTIVE CREDENTIAL` |
| 6 | Refused on the row | REVOKED | `desk-agent`: `✗ CANNOT STOP` `NO GRANT` (`data-code=desk_delegation_required`); `sweep-runner`: `✗ CANNOT ALLOW` `OWNER ONLY` (`owner_principal_required`); foot `REFUSED 14:09` |
| 6b | Refused Stop, and the reread removes the row | LIVE, then REVOKED by another owner request → no `delegations[]` row | the `desk-agent` row is gone; foot `REFUSED 14:11` (expanded); the well: `✗ REFUSED`, `STOP FILING AND DECISIONS`, `NO GRANT`, `desk-agent`, `BY OWNER`, `SEP 25 14:11` |
| 7 | Last row gone | REVOKED; no credentials | no ledger; foot `STOPPED 14:07` (expanded); the well: `✓ SUCCEEDED`, the STOPPED words, `desk-agent`, `BY OWNER`, `SEP 25 14:07` |

## The receipt: where it lives, and its target

The Settings foot "carries the receipt and the refusals" (`SettingsCore.tsx:1-5`). The proposal: after each grant act, the footer's CENTRE slot (`SurfaceFooter`'s own `receipt` slot, `web/src/desk/surface/SurfaceFooter.tsx:24`) carries ONE plated library `Button` whose face is the library `Receipt` (lamp, outcome word, `HH:MM`). The whole receipt is the target; there is no `ℹ`. It toggles a `SurfaceWell` `RECEIPT` under the Remote access group (in-world, no modal, `aria-expanded`). One species for both outcomes: SUCCEEDED and REFUSED. The receipt lives outside the removable ledger, so it survives when its row disappears (boards 6b, 7). The durable read stays `GET /api/kernel/read?refs=operation:<id>&view=receipt`.

**Pointer ownership (measured, `shots/facts.json` `pointer`):** every Button in the window body and footer, on every board, at both widths: 260 Buttons, 1300 points, **all owned**. The points are the centre + four corners inset 1 px of the painted face at 1440, and of the 44 × 44 target at 393. Each point is checked with `elementFromPoint` AND a real pointer move (the `pointermove` target). The 70 footer Buttons are included. Footer receipt: face 129.06 × 24 px; target 129.06 × 24 at 1440, 129.06 × 44 at 393. `« PREFS`: face 73.45 × 20; target 73.45 × 44 at 393.

Round one's `« PREFS` verb (and any last footer verb) was under the window's resize grip at 1440: the bottom-right corner point hit `.desk-window-grip` on every board. This round measured it and paid it in the library (`surface-footer.css`, below).

## The 12 px floor: paid in the library

The whole window, footer included, now has **0** text nodes under 12 px on all 50 renders (`facts.json` `small_text`; a lone non-text glyph is exempt, UX-CANON C). The changes use the token `--desk-surface-label-size` (12 px, `web/src/styles/tokens.css:301`), the precedent of PHILO-4-01 (`924b8db6`, `.surface-section-head h3` and `.gadget-chip` 10 → 12):

| Species | File:line | Was |
|---|---|---|
| `.gadget-group-label` | `web/src/desk/surface/gadgets.css:26` | 10px |
| `.gadget-fact` | `web/src/desk/surface/gadgets.css:72` | 10px |
| `.surface-well-head` | `web/src/desk/surface/surface.css:372` | 10px |
| `.surface-token[data-chip]` | `web/src/desk/surface/surface.css:597` | 10px |
| `.prefs-back`, `.prefs-defaults` | `web/src/desk/surface/surface.css:2560` | 10px |
| `.desk-next .surface-state-chip` | `web/src/desk/surface/patterns/state-chip.css:15` | 10px |
| `.desk-next .surface-receipt` (footer receipt words + time) | `web/src/desk/surface/patterns/provenance.css:64` | 10px |
| `.desk-next .desk-wing` (the SETTINGS / GUIDE wings) | `web/src/desk/components/pullout.css:340` | 10px |

Two further library lines: `.btn > .surface-receipt { cursor: inherit; }` (`provenance.css`, a Receipt that is a Button's face takes the Button's cursor), and `.desk-next .surface-footer { padding-inline-end: 24px; }` (`surface-footer.css:3-7`, the grip's 20 px corner reserved).

Not changed (not in this window): `.surface-token` without `data-chip` (11px, `surface.css:570`), the provenance chip, `.desk-wing-door` (11px), and other 10 px rules in `surface.css` / `gadgets.css`. They are outside this canvas's window. The ratchet stays with the species owners.

**Blast radius:** these species render desk-wide; every chip, state chip, gadget-group label, fact, well head, wing tab and footer receipt grows 10 → 12 px. Web baseline: `uv run python scripts/check_web_baseline.py --run` → 2872 passed, 0 failed; `VERDICT: baseline-subset, zero branch-new` (5 HEALED). Guards: `test_design_system_guard`, `test_frontend_density_guard`, `test_ux_canon_ratchet`, `test_ux_canon_scan` → 45 passed.

**Set B at compliant sizes (measured at 393, 12 px):** the ledger line is 363 px; the B chip `FILING AND DECISIONS ALLOWED` is 259 px (one line); `Stop filing and decisions` (198) + `Revoke credential` (140) sit on one line; `Allow filing and decisions` (205) + `Revoke credential` (140) sit on one line. The receipt well wraps its tokens to three lines (board 6b). At 1440 every row is one line (board 4b's three rows included).

## The strings (proposed)

| Slot | Set A (the charter, `current-phase-status.md:269`) | Set B (recommended; Astra r1 supports) |
|---|---|---|
| Verb, effective state not LIVE | `Allow filing` | `Allow filing and decisions` |
| Verb, LIVE | `Stop filing` | `Stop filing and decisions` |
| Chip, LIVE (`StateChip success ✓`) | `FILING ALLOWED` | `FILING AND DECISIONS ALLOWED` |
| Chip, REVOKED or EXPIRED (`StateChip idle ○`) | `FILING STOPPED` | `FILING AND DECISIONS STOPPED` |
| Chip, never granted | none | none |
| Refusal chip (`StateChip failure ✗`) | `CANNOT ALLOW` / `CANNOT STOP` | same |
| Refusal token (`surface-token`) | `owner_principal_required` → `OWNER ONLY`; `desk_delegation_required` → `NO GRANT`; `desk_delegation_revoked` → `GRANT STOPPED`; `desk_delegation_expired` → `GRANT EXPIRED`; `invalid_arguments` → `BAD REQUEST` | same |
| Credential verb | `Revoke credential` (was `Revoke`) | same |
| No-credential cell | `NO CREDENTIAL` | same |
| Ledger caption | `AGENTS · N ACTIVE CREDENTIAL(S)` (was `CREDENTIALS · N ACTIVE`); the count omitted at zero | same |
| Foot receipt (the Button's face) | `ALLOWED` / `STOPPED` / `REFUSED` + `HH:MM` | same |
| Receipt well | `RECEIPT` · `SUCCEEDED` or `REFUSED` · the act (the chip words on success; the verb words, upper case, on a refusal) · the refusal token · identity · `BY OWNER` · `MMM D HH:MM` | same |

**Why B.** R5 put `decision.delete` in the grant. The set is file/unfile, record/update/status/supersede/DELETE decisions, and the placement effects (beat :14). `FILING ALLOWED` names half of it, and the half it hides can delete a decision. D3 names the pair ("writes that FILE or DECIDE"). Verb and chip use the same pair, so the chip reads as the verb's result.

**Why `AGENTS`, and the count.** The grant is keyed by the agent identity and survives a reissue and a restart (beat invariant 5); a row with no credential is still an agent. One caption, no branch. The count names what it counts: `N ACTIVE CREDENTIAL(S)` (authentication), apart from the grant chip (authority). The toggle row's `N CREDENTIALS` token is unchanged.

**Why this order.** Lead: the credential status `●` (unchanged, `SettingsCore.tsx:630`). First cell: the grant chip, so authority reads before the credential facts. A refusal sits beside the chip it concerns. Trailing: the grant verb, then `Revoke credential` last, at the edge, where the credential verb is today. The two columns stay independent (boards 4 and 4b).

## Three questions for the owner

1. Words: set B (`Allow filing and decisions` / `FILING AND DECISIONS ALLOWED`) or set A (`Allow filing` / `FILING ALLOWED`)? Recommended: B.
2. Caption: `AGENTS · N ACTIVE CREDENTIALS` in place of `CREDENTIALS · N ACTIVE`, with `Revoke credential` on the row? Recommended: yes.
3. Order and receipt: credential `●` lead, grant chip first, grant verb before `Revoke credential`, and the last act's receipt as the footer's centre Button? Recommended: yes.

## Limits (what the boards are not)

- The grant producer does not exist. The grant half of every board is stored rows projected by the canvas's statement of the wire contract (above), not a server response.
- Refusals (boards 6, 6b), operation ids and receipt times are fixture values, not kernel refusals or kernel receipts.
- The boards are static states. No click drives a transition; the expanded receipt (boards 6b, 7) is rendered open, not opened by a click.
- The Settings face above Remote access (`This device`, hub chips, runtime identity, Mesh) is omitted.
- The typography repair above is real library CSS on this branch. It has not been walked on the owner's desk.
- Inherited, filed, not fixed here: the producer labels a DESK credential `ALL` (every board shows `desk-agent` as `ALL`). BACKLOG, "PHILO-7-02 canvas follow-ups".

## Fence sketch for story 02 (not built)

Every fence runs the real producers: the real hub, the real `PUT`/`DELETE /api/settings/remote/delegations/{identity}` and credential routes, the real kernel, and the real `GET /api/settings/remote`. It asserts on the RENDERED Settings window at 1440 and 393, on `readable_text` (visible, in viewport, unobscured). Each fence shows a demonstrated red: behavioural (red on a copy of main through the real producer) or a named mutation. The ratified words and their fences change together: the fence reads the words from one constant the face imports.

| After | Assert (rendered, and at the API) | Red |
|---|---|---|
| Load, never granted | no `[data-testid=grant-chip]`; the grant verb reads the Allow words; caption `AGENTS` | main: no grant verb |
| Allow | the chip reads the ALLOWED words, `data-state=success`; the verb reads Stop; the foot receipt reads `ALLOWED`; its `operation_id` equals the route's `{operation_id}` and the kernel receipt's (`delegation.grant`, `result_ref=desk-delegation:<id>`) | main: 404 |
| Stop | the chip reads the STOPPED words, `data-state=idle`; the verb reads Allow; the receipt is `delegation.revoke`, `revocation_reason=owner_revoked`, same operation id on face, route and kernel | mutation: the face reads the stored column |
| Revoke credential (a LIVE grant) | a SEPARATE fence: the grant's `delegation.revoke` receipt has `credential_revoked` (not `owner_revoked`); the grant is revoked BEFORE the credential is removed (F21a); the row is gone; the foot receipt and its well read the grant receipt | mutation: the credential removed first; the reason written as `owner_revoked` |
| Clock past `expires_at` | stored LIVE, the API says `EXPIRED`, the chip reads STOPPED (credential row and orphan row) | mutation: the projection reads the stored `state` (F23) |
| Credential expired, grant LIVE | `●` idle, `EXPIRED`, the ALLOWED chip (beat :147) | mutation: the chip follows `active` |
| Credential gone, grant LIVE (self-revoke; TTL cleanup) | the `delegation-row` renders with `NO CREDENTIAL`, ALLOWED, the Stop verb; repeat with remote OFF | main: ledger hidden (`SettingsCore.tsx:615`) |
| Remote OFF, credential retained, grant LIVE | that credential row renders with the ALLOWED chip and the Stop verb | mutation: OFF drops all credential rows |
| Stop on an orphan row | the row is gone; with nothing left, `.surface-ledger` is absent; the foot receipt Button is in view, `elementFromPoint` at centre + corners owns it; clicking it opens the well: `SUCCEEDED`, the STOPPED words, `desk-agent`, `BY OWNER`, the operation id matches | mutation: the receipt rendered inside the ledger |
| Refused on the row | `[data-testid=grant-refused]` on that row, `data-code` equal to the kernel's code, the plain token; no modal, no toast; after the reread the chip equals `by_identity` (F15) | mutation: the refusal dropped on reread |
| Refused Stop whose reread removes the row | the row is gone; the foot receipt reads `REFUSED`; its well shows `REFUSED`, the attempted act (the Stop words), `NO GRANT` (`desk_delegation_required`), the identity, `BY OWNER`; the operation id matches the route's refusal `{operation_id, receipt}` | mutation: the refusal rendered only on the row |
| Every state | every verb in the window is `.btn`; no text reads `desk writes`; no text under 12 px in the window incl. the footer; every Button owned at centre + corners (44 × 44 at 393); chip order: lead `●`, grant chip first cell; `Revoke credential` last; no horizontal overflow | the shoot probe of this canvas |

## Round two: Astra r1 → where paid

| Finding | Paid |
|---|---|
| 1. Receipt `ℹ` under the grip / 6.61 × 10 px | The receipt itself is the Button, in the footer's centre slot; the footer reserves the grip's corner; pointer ownership measured on every Button, footer included (above) |
| 2. Remote OFF hides a credential-backed LIVE grant | Visibility rule (wire contract); board 5d |
| 3. 12 px floor in the library, footer included | Eight species to the token; the scan covers the whole window; B's fit re-measured; baseline + guards green |
| 4. Expiry boards posed, not derived | Stored rows + `project()`; real past `expires_at`; the wire contract names the effective projection; board 4b from the real expired credential |
| 5. Refused Stop whose reread removes the row; credential Revoke | Board 6b; one receipt species for both outcomes, outside the ledger; the fence sketch separates `credential_revoked` from `owner_revoked` and requires real producers, matching ids, rendered inspection after disappearance and demonstrated reds |
| 6. Words | B kept; `Revoke credential`; `N ACTIVE CREDENTIAL(S)`; `CANNOT ALLOW` / `CANNOT STOP` |
| 7. DESK → ALL | `pm/roadmap/holdspeak/BACKLOG.md`, "PHILO-7-02 canvas follow-ups" |
| 8. Review page qualifications | The review page's Limits section; this README's board table, strings and Limits |

## Reproduce

```bash
# 1. the real producer's wire (isolated HOME, isolated DB)
HOME=$(mktemp -d) uv run pytest -q -s -p no:cacheprovider pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/produce_remote_wire.py
# 2. serve the harness (from web/)
cd web && ./node_modules/.bin/vite --config ../pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/vite.config.mjs
# 3. shoot (renders, the whole-window 12 px scan, the pointer probe)
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/shoot.py pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/shots a b
# 4. the review page
uv run python pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/build_review.py
```
