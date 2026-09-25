# PHILO-7-02 canvas: the delegation grant on the Remote Access ledger

**Status: PROPOSED. The owner ratifies before the face is built** (UX canon A.2, E.1). Every decision below is proposed; none is ratified.

Review page (all boards embedded, both widths, both word sets): `docs/internal/philo/phase-7/grant-canvas/index.html`.

## What the boards are, exactly

- **Frame:** the production window. `DeskChrome`, `DeskWindowFrame` with the Settings classes (`desk-surface-window desk-settings-window`), the foot slot and the wing slot wired as `SurfaceWindowHost` wires them (`web/src/desk/components/SurfaceWindows.tsx:155-211`), the real `useCoreWings` (SETTINGS / GUIDE), `Dock`. CSS: `styles/global.css`, `styles/react-app.css`, `desk/desk.css` (the product entry imports, `web/src/main.tsx:8-9`) plus a 15-line canvas `main.css` (page floor, the receipt well's token run).
- **Board 0 (today)** mounts the REAL `RemoteAccessModule` (`web/src/pages/cores/SettingsCore.tsx:478`) fed the REAL producer's wire.
- **Boards 1-7** mount `ProposedRemoteAccess` (`harness/main.tsx`): the same JSX as the real module, composed of the same library species (`GadgetGroup`, `GadgetRow`, `CycleGadget`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `Button`, `SurfaceWell`, `Receipt`, `SurfaceFooter`), plus the proposal. Nothing is hand-drawn; no product file changes.
- **Credential half of the wire: the real producer.** `harness/produce_remote_wire.py` boots the real hub over an isolated database (the Phase 5 fence fixture), issues `desk-agent` (DESK, 12 H) and `sweep-runner` (PROJECT, 24 H) through `POST /api/settings/remote/credentials`, uses `desk-agent` once from a non-loopback host, and saves `GET /api/settings/remote` to `harness/fixtures/remote-wire.json`.
- **Grant half of the wire: NOT a producer (unbuilt).** Orphan rows use the beat's decided shape `delegations: [{identity, state, grant_id, expires_at}]` (`design/grant-lifecycle-beat.md:155`). The per-credential field `credentials[].delegation: {state, grant_id, expires_at} | null` is a **canvas assumption**: the beat decides the chip's rule (`by_identity`, time-aware), not its wire field. Story 02 names the field.
- **Clock:** `Date.now` is frozen at the capture's last use + 2 h (stable `LAST USED 2 H AGO`); `timezone_id=UTC`. The menu-bar clock is the real clock. Receipt times (`14:05`, `14:07`, `14:09`) are fixture strings.

## Boards (`shots/<set>/<board>-<set>-<width>.png`, set `a` and `b`; board 0 in `shots/today/`)

| # | Board | Row(s) |
|---|---|---|
| 0 | Today (real module) | caption `CREDENTIALS`; `Revoke` only |
| 1 | No grant ever | no chip; `Allow filing`, `Revoke` |
| 2 | LIVE | `FILING ALLOWED`; `Stop filing`, `Revoke`; foot receipt `FILING ALLOWED 14:05 ℹ` |
| 3 | Stopped (REVOKED) | `FILING STOPPED`; `Allow filing`; foot receipt `FILING STOPPED 14:07 ℹ` |
| 4 | Expired by clock, credential active | `FILING STOPPED`; `Allow filing`; no receipt (expiry is not an owner act) |
| 5 | LIVE, no credential, remote ON | idle `●`, `FILING ALLOWED`, `NO CREDENTIAL`; `Stop filing` only |
| 5b | LIVE, no credential, remote OFF | the ledger still renders (the beat: whatever the switch says); no `Issue credential` |
| 5c | No credential, grant past its expiry (stored LIVE) | `FILING STOPPED`, `NO CREDENTIAL`; no verb (the beat: the verb only while not expired) |
| 6 | Refused | `desk-agent`: `✗ CAN'T STOP` `NO GRANT` (`data-code=desk_delegation_required`), the row re-read to `FILING STOPPED`; `sweep-runner`: `✗ CAN'T ALLOW` `OWNER ONLY` (`owner_principal_required`); foot `REFUSED 14:09 ℹ` |
| 7 | Last row gone | no ledger; foot `FILING STOPPED 14:07 ℹ` opened: a `SurfaceWell` `RECEIPT` with `✓ SUCCEEDED`, the act, `desk-agent`, `BY OWNER`, `SEP 25 14:07` |

`shots/facts.json` records per board and width: the caption, each row's text, grant chip, verbs (with their Button species class), refusal code and chip order, the foot, the receipt well, raw buttons, horizontal overflow. Measured: 38 renders, 0 browser errors, 0 raw `<button>`, 0 horizontal overflow.

## The strings (proposed)

| Slot | Set A (the charter, `current-phase-status.md:269`) | Set B (recommended) |
|---|---|---|
| Verb, no LIVE grant | `Allow filing` | `Allow filing and decisions` |
| Verb, LIVE grant | `Stop filing` | `Stop filing and decisions` |
| Chip, LIVE (`StateChip success ✓`) | `FILING ALLOWED` | `FILING AND DECISIONS ALLOWED` |
| Chip, REVOKED or EXPIRED (`StateChip idle ○`) | `FILING STOPPED` | `FILING AND DECISIONS STOPPED` |
| Chip, never granted | none | none |
| Refusal chip (`StateChip failure ✗`) | `CAN'T ALLOW` / `CAN'T STOP` | same |
| Refusal token (`surface-token`) | `owner_principal_required` → `OWNER ONLY`; `desk_delegation_required` → `NO GRANT`; `desk_delegation_revoked` → `GRANT STOPPED`; `desk_delegation_expired` → `GRANT EXPIRED`; `invalid_arguments` → `BAD REQUEST` | same |
| No-credential cell | `NO CREDENTIAL` | same |
| Ledger caption | `AGENTS` (was `CREDENTIALS`) | same |
| Foot receipt | library `Receipt`: the chip word + `HH:MM` + `ℹ`; `REFUSED HH:MM` for a refusal | same |

**Why B (proposed).** R5 put `decision.delete` in the grant; the set is file/unfile plus record/update/status/supersede/DELETE decisions plus the placement effects. `FILING ALLOWED` names half of it, and the half it hides can delete a decision. The owner's own D3 names the pair ("writes that FILE or DECIDE"). The verb and the chip use the same word pair, so the chip reads as the result of the verb (Allow → ALLOWED, Stop → STOPPED). Measured cost: at 393 the B chip takes one full line and the B verb sits beside `Revoke` without a wrap (shots `b/*-393.png`); at 1440 (the window renders 1392 px wide) the row stays one line; a narrower window wraps the cells under the name, as the room ledger does today. A stays available at no build cost.

**Why `AGENTS`.** The grant is keyed by the agent identity and survives a reissue and a restart (beat, invariant 5), and a reissue replaces the old credential, so there is one row per identity. A row with no credential (boards 5, 5b, 5c) is still an agent, not a credential. One caption at all times, no branch. `N ACTIVE` still counts active credentials (board 5b omits it: no counter of zero); the toggle row's `N CREDENTIALS` token is unchanged.

**Why this order.** Lead: the credential status `●` (unchanged, `SettingsCore.tsx:630`). First cell: the grant chip, so authority reads before the credential facts (palette, expiry, last use). Then a refusal, when one exists, beside the chip it concerns. Trailing: the grant verb, then `Revoke` last (the destructive credential verb stays at the edge, where it is today). The two columns stay independent: board 4 shows credential `●` active with `FILING STOPPED`; board 5 shows `●` idle with `FILING ALLOWED`.

**Where the receipt lives (proposed).** The Settings foot already "carries the receipt and the refusals" (`SettingsCore.tsx:1-5`; `PrefStatusBar`, `settingsPrefs.tsx:607-658`). The proposal puts the library `Receipt` (`desk/surface/patterns/ProvenanceChip.tsx:37`) in that centre after each grant act, and its `ℹ` unfolds a `SurfaceWell` under the Remote access group (no modal). It is in-session; the durable read is `GET /api/kernel/read?refs=operation:<id>&view=receipt`, which F23 asserts at the API.

## Three questions for the owner

1. Words: set A (`Allow filing` / `FILING ALLOWED`) or set B (`Allow filing and decisions` / `FILING AND DECISIONS ALLOWED`)? Recommended: B.
2. Caption: `AGENTS` in place of `CREDENTIALS`, always? Recommended: yes.
3. Order: credential `●` lead, grant chip first cell, grant verb before `Revoke`? Recommended: yes.

## What could not be rendered faithfully

- The grant producer does not exist; the grant half of every board is the beat's shape plus one canvas assumption (above). Board 6's refusals are fixture codes, not kernel refusals.
- The window is not a hub walk: no click drives a transition; each board is a state.
- The Settings face above Remote access (the `This device` display, hub chips, runtime identity, Mesh) is omitted; the board shows the `System` module title and the Remote access group only.
- **Inherited, measured, not this canvas's to fix:** the library chip species render at 10 px, under the 12 px floor, on board 0 (the real module) as on every board: `.surface-token[data-chip]` (`web/src/desk/surface/surface.css:587`, `font: 600 10px/1`), `.desk-next .surface-state-chip` (`web/src/desk/surface/patterns/state-chip.css:15`), `.gadget-group-label` (`web/src/desk/surface/gadgets.css:26`), `.surface-well-head` (`surface.css:372`). `facts.json` lists every sub-12 px text per board.
- **Inherited, measured:** the real producer labels a DESK credential `ALL`: `resolve_palette("DESK") == resolve_palette("ALL")` (228 tools each), so the reverse map in `holdspeak/web/routes/mcp_http.py:209-214` returns the later name. The boards show the producer's `ALL` as it is.

## Fence sketch for story 02 (not built)

Rendered assertions after each transition, through the real hub and the real route, at 1440 and 393, on `readable_text` (visible, in viewport, not obscured):

| After | Assert on the rendered row (`credential-row-<id>` / `delegation-row-<grant_id>`) |
|---|---|
| Load, never granted | no `[data-testid=grant-chip]`; `[data-testid=grant-verb]` reads the Allow verb; the ledger caption reads `AGENTS` |
| Allow (grant) | the chip reads the LIVE word with `data-state=success`; the verb reads the Stop verb; the foot `Receipt` reads the LIVE word; the `delegation.grant` receipt exists with `result_ref=desk-delegation:<id>` |
| Stop (revoke) | the chip reads the STOPPED word with `data-state=idle`; the verb reads the Allow verb; the foot `Receipt` reads the STOPPED word; the `delegation.revoke` receipt exists (`owner_revoked`) |
| Clock past `expires_at` | the chip reads the STOPPED word while the stored state is still LIVE (F23 mutation: reading `state` says ALLOWED) |
| Credential gone, grant LIVE (self-revoke; TTL cleanup) | the `delegation-row` renders with idle `●`, `NO CREDENTIAL`, the LIVE word and the Stop verb; repeat with remote OFF |
| Stop on that row | the row is gone; with no credential left, `.surface-ledger` is absent; the foot `Receipt` and its `ℹ` well read the STOPPED act, `desk-agent`, `BY OWNER`, `SUCCEEDED` |
| Refused grant / refused stop | `[data-testid=grant-refused]` on THAT row, `data-code` equal to the kernel's code, the plain token beside the failure chip; no modal, no toast; the chip equals `by_identity` after the re-read (F15) |
| Every state | every verb in the row is `.btn` (library Button); no text reads `desk writes`; chip order: lead `●`, grant chip first cell; `Revoke` last in trailing; no horizontal overflow |

## Reproduce

```bash
# 1. the real producer's wire (isolated HOME, isolated DB)
HOME=$(mktemp -d) uv run pytest -q -s -p no:cacheprovider pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/produce_remote_wire.py
# 2. serve the harness (from web/)
cd web && ./node_modules/.bin/vite --config ../pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/vite.config.mjs
# 3. shoot
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/shoot.py pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/shots a b
# 4. the review page
uv run python pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/build_review.py
```
