# Floor diagnostic: two PHILO-7-03 follow-ups (PR #663 BACKLOG)

- Worktree: /Users/karol/dev/tools/wt-floor-diag @ d524846b (origin/main), detached.
- Web: real `npm ci --ignore-scripts && npm run build` (exit 0). Python: `uv sync --extra test`.
- Hub: `HOME=$(mktemp -d) uv run python scripts/graph_walk.py serve --port 48731 --token diagtok`,
  DB `/var/folders/.../tmp.DZqdtHDfu7/.local/share/holdspeak/holdspeak.db` (isolated; the owner's HOME and DB were not touched).
  `backend_revision d524846b`, `schema_version 79`. The hub is stopped now.
- Browser: Playwright Chromium, a new context per path (clean localStorage), 1440x900 and 393x852.
- Probes: `.tmp/floor-diag/probe.py` (first run: F1 + F2) and `.tmp/floor-diag/probe_f1_clean.py` (F1 again, and the probe
  renames any existing "New zone" through the API before each create, see side finding S1). Logs: `.tmp/floor-diag/probe-f1-clean.log`.
- Shots: `/Users/karol/dev/tools/wt-floor-diag/.tmp/evidence-shots/floor-diag/` (`f1c-*` = the clean F1 run; `f1-*` = the first run, it shows S1; `f2-*` = F2).

---

## Finding 1: "New Zone" from the Chair shows no rename field. VERIFIED DEFECT

### What each surface shows (observed)

| Width | Surface | After `New Zone` | Hub | Shot |
|---|---|---|---|---|
| 1440 | Chair | No change on the face. No `input.desk-zone-rename`, no `.desk-zone-rename-row`, no receipt, the zone is not visible. Focus = `BODY`. | `POST /api/directories` made `dir_4e77b625b5f3` "New zone" | `f1c-1440-02-chair-after-new-zone.png` |
| 1440 | Chair, then go to the Floor | The rename field appears LATE, over the new zone, and takes focus (`INPUT.desk-zone-rename val=New zone`). The field is narrow and clips the name ("ew zone"). | — | `f1c-1440-03-floor-after-chair-zone.png` |
| 1440 | Floor (spatial) | The rename field appears at once and has focus. Fill "Diag zone 1440" + Enter gives the name on the hub. | `dir_c0d4748cde82` → "Diag zone 1440" | `f1c-1440-07-spatial-after-new-zone.png` |
| 393 | Chair | No change on the face (same as 1440). | `dir_43b50e1469e7` "New zone" | `f1c-393-02-chair-after-new-zone.png` |
| 393 | Chair, then go to the Floor | The Floor opens as the LIST (the rig desk has more than 16 objects). No rename field. | — | `f1c-393-03-floor-after-chair-zone.png` |
| 393 | Floor (list) | `New Zone` from the list: no rename field either. | `dir_ef1513a13584` "New zone" | `f1c-393-05-list-after-new-zone.png` |
| 393 | Floor list → `Spatial view` | The stale rename field for the list-made zone appears after the toggle. | — | `f1c-393-06-spatial-after-list-zone.png` |
| 393 | Floor (spatial) | The rename field appears at once and has focus; Enter gives the name. | `dir_ac51f6a354b6` → "Diag zone 393" | `f1c-393-07-spatial-after-new-zone.png` |

Console errors in the clean run: none.

### Source lines that decide it

- The verb: `web/src/desk/verbRegistry.ts:203-212` `desk.new-zone`, `scope: "floor"`, `run: createPrimitive("zone")`. The toolshelf palette offers it on the Chair too (the probe clicked `#desk-palette-option-desk.new-zone` on the Chair and the hub made the zone).
- The create: `web/src/desk/store/dataSlice.ts:322` (body `{name: "New zone"}`), `dataSlice.ts:370` `if (kind === "zone") get().setRenamingZone(createdId);`. This only sets store state `renamingZoneId` (`store/deskSlice.ts:117-118`).
- The only reader that draws the field: `web/src/desk/gl/WorldStage.tsx:206-207` (`renameZone = scene.zones.find(z => z.id === renamingZoneId)`), `WorldStage.tsx:279-280` `{renameZone && (<ZoneRenameOverlay …`, and the overlay `WorldStage.tsx:403-476` (`input.desk-zone-rename`, Enter commits `renameZone`, blur commits, Escape cancels).
- The mount condition: `web/src/desk/DeskApp.tsx:192-206`. `WorldStage` mounts only when `showFloor` and `defaultViewFor(...) !== "list"`; else `DeskListView` (no reference to `renamingZoneId`) or `ChairHome` (no reference to `renamingZoneId`). `grep renamingZoneId web/src/desk` finds only WorldStage, sceneModel, the store.
- The list default at phone width: `web/src/desk/store/types.ts:65-72` (`compact && objectCount > 16` → list, when there is no saved choice).

### Defect or designed?

A defect. Nothing in the code or canon says the Chair should make an unnamed zone. The Chair and the list offer the verb, the hub writes the zone, and the face gives no sign of it and no way to name it. The rename state is not cleared, so the field comes up later on a different face and takes focus with no cause the user can see. UX-CANON §4 "No modals; edit in-world" (`docs/internal/UX-CANON.md:32-34`): the in-world edit exists only on one of the three faces that offer the verb. UX-CANON §11 "A verb that does nothing is a lie" (`UX-CANON.md:50-52`): on the Chair the verb does something on the hub but nothing that the user can see. The gap is on the LIST view too (393 default), not only on the Chair. The lane's BACKLOG line names only the Chair.

### Side finding S1 (VERIFIED, a result of Finding 1)

The zone name must be unique. The default name is always "New zone" (`dataSlice.ts:322`). After a Chair or list create leaves a zone called "New zone", the NEXT `New Zone` from any face fails: `POST /api/directories {"name":"New zone"}` → **409** `{"error":"zone_name_taken","existing_name":"New zone"}` (probed with curl). The face shows `CREATE ZONE FAILED · HTTP 409  Retry  OK` in the bar (`f1-1440-07-spatial-after-new-zone.png`, first run). Retry fails in the same way. So a user who makes one zone on the Chair cannot make a second zone anywhere until they find the first one on the spatial Floor and rename it.

### Reproduction (atlas step vocabulary; `case.p7.zone_create.visible` in `atlas-phase7.json` on `feat/philo-7-03-atlas` has the same steps with the Floor detour)

```json
[
  {"kind":"ui","action":"goto","adapter":"ui-navigation","url":"/"},
  {"kind":"ui","action":"click_role","adapter":"ui-pointer","role":"button","name":"Continue later","optional":true},
  {"kind":"check","predicate":{"kind":"protocol_field","path":"arrival_required","value":false},"observe_at":"protocol: GET /api/setup/status","timeout_s":10},
  {"kind":"ui","action":"click","adapter":"ui-pointer","selector":"[aria-controls=desk-tool-shelf]"},
  {"kind":"ui","action":"fill","adapter":"ui-keyboard","selector":"[aria-controls=desk-palette-listbox]","value":"New Zone"},
  {"kind":"ui","action":"click","adapter":"ui-pointer","selector":"[id='desk-palette-option-desk.new-zone']",
   "why":"on the Chair (no chair-floor-toggle click first): the Chair is the default face"},
  {"kind":"ui","action":"wait_for","adapter":"ui-pointer","selector":"input.desk-zone-rename",
   "why":"FAILS today at 1440 and 393: the field is drawn only by WorldStage (WorldStage.tsx:279)"},
  {"kind":"ui","action":"fill","adapter":"ui-keyboard","selector":"input.desk-zone-rename","value":"Chair zone"},
  {"kind":"ui","action":"press","adapter":"ui-keyboard","key":"Enter"},
  {"kind":"api","method":"GET","path":"/api/directories","body":null,"adapter":"http-route","capture_match":{"name":"Chair zone"},"capture_as":"zone_id","capture_path":"directories"}
]
```

A second case for the list face: the same steps with `click [data-testid=chair-floor-toggle]` before the palette, at 393 (the list is the default there when the desk has more than 16 objects; at 1440 use the palette `List view` / `desk.toggle-view` first). A third case for S1: two `New Zone` in sequence with no rename between; expect the second one to make a zone, today it gets 409.

---

## Finding 2: the list view's row-menu Delete does nothing. VERIFIED DEFECT (at 393 and at 1440)

### What happens today (observed)

At 393 (the Floor opened as the list with no toggle) and at 1440 (after the palette `List view`):

1. `POST /api/decisions {"title":"Diag delete decision 393","status":"accepted"}` → 201, `decision_1fb934d294f9` (1440: `decision_fd62afa5339a`).
2. Right-click on the row's name button. The row menu opens: `Open, Get Info, Ask this project · Select a Project, Ask AI · Ask unavailable, Continue in thread, Edit · Not editable, Rename · Not renameable F2, Duplicate, Move to Zone, Delete Delete`. `Delete` is enabled (no `aria-disabled`). Shot `f2-393-01-list-row-menu.png`.
3. Click `Delete`. The menu closes. Then **nothing**:
   - no network write: the probe logged every DELETE/POST/PUT/PATCH request after the click; there were none;
   - no receipt: the page text has no "Removed", "Removal committed" or "Undo" at 600 ms (`f2-393-02-after-delete-600ms.png`) or after 6 s;
   - the row is still in the list after 6 s (`f2-393-03-after-delete-6s.png`);
   - `GET /api/decisions/{id}` → **200** (the decision is still on the hub);
   - no console error, no page error.

The same at 1440 (`f2-1440-01..03`). So the defect is on the list view at any width, not only at 393. The user presses Delete, sees the menu close, and the decision stays, with no error and no sign that nothing happened.

### Source lines

- The list's row menu: `web/src/desk/components/DeskListView.tsx:266-274` (`openMenu`), `:316-320` (right-click), `:306-314` (`ContextMenu` / `Shift+F10`), `:324-334` (`<WorkMenu entries={objectMenuEntries(...)}>`).
- The entries: `web/src/desk/floorMenu.ts:59-71` `objectMenuEntries` → `item()` `onSelect: () => v.run(ctx)` (`floorMenu.ts:21-31`).
- The verb: `web/src/desk/verbRegistry.ts:546-566` `object.delete`. `run` does not delete; it only does `window.dispatchEvent(new CustomEvent(OBJECT_DELETE_REQUEST, …))` (`:562-564`; the name at `:47`, `"desk:request-object-delete"`).
- The ONLY listener: `web/src/desk/gl/WorldStage.tsx:137-152` (it gets the object and calls `queueDelete(... deletePrimitive ...)`). `grep -rn OBJECT_DELETE_REQUEST web/src` finds only the dispatch and this listener.
- `WorldStage` and `DeskListView` never mount at the same time (`web/src/desk/DeskApp.tsx:192-206`), so on the list the event goes to no listener.

### Defect or designed?

A defect. The menu shows an enabled `Delete` with a keycap, and it does nothing. UX-CANON §11 "A verb that does nothing is a lie. Withhold it (and ledger it) rather than ship it dead" (`docs/internal/UX-CANON.md:50-52`). The same dead path is probably true for the Chair (no `WorldStage`), but I did not exercise it there: unknown.

### Side note S2 (observed, not examined further)

At 393 the row menu opens near the bottom and the `Delete` row is partly under the bottom edge (`f2-393-01-list-row-menu.png`, the last row is cut at y≈852). Playwright could click it; I did not check if a thumb can.

### Reproduction (atlas step vocabulary)

```json
[
  {"kind":"api","method":"POST","path":"/api/decisions","body":{"title":"Atlas list-deleted decision","status":"accepted"},"adapter":"http-route","capture_as":"decision_id","capture_path":"decision.id","expect_status":201},
  {"kind":"ui","action":"goto","adapter":"ui-navigation","url":"/"},
  {"kind":"ui","action":"click_role","adapter":"ui-pointer","role":"button","name":"Continue later","optional":true},
  {"kind":"check","predicate":{"kind":"protocol_field","path":"arrival_required","value":false},"observe_at":"protocol: GET /api/setup/status","timeout_s":10},
  {"kind":"ui","action":"click","adapter":"ui-pointer","selector":"[data-testid=chair-floor-toggle]"},
  {"kind":"ui","action":"wait_for","adapter":"ui-pointer","selector":".desk-listmode",
   "why":"393 opens the list (store/types.ts:65-72); at 1440 first run the palette 'List view' (desk.toggle-view)"},
  {"kind":"ui","action":"click_role","adapter":"ui-pointer","role":"button","name":"Atlas list-deleted decision","button":"right",
   "why":"DeskListView.tsx:316-320 onRowContextMenu; keyboard alternative: focus the row + press Shift+F10"},
  {"kind":"ui","action":"click_role","adapter":"ui-pointer","role":"menuitem","name":"Delete"},
  {"kind":"check","predicate":{"kind":"http_status","value":404},"observe_at":"protocol: GET /api/decisions/{decision_id}","timeout_s":10,
   "why":"FAILS today: 200 — the list view has no OBJECT_DELETE_REQUEST listener"}
]
```

Note: the rig step `click_role` with `"button":"right"` and the `http_status` predicate are my assumption of the vocabulary; I did not check that `scripts/graph_walk.py` supports a right-click or that predicate kind. If it does not, use `focus` on the row + `press` `Shift+F10` (the list handles it at `DeskListView.tsx:310`), and the `decision_delete.gone` case's own 404 check.

---

## Could not verify / unknown

- The Chair's own object menu Delete (if the Chair offers one): not exercised.
- Whether `graph_walk.py` supports right-click and an HTTP-404 predicate: not checked (see the note above).
- The cause of the clipped rename field ("ew zone") at 1440: seen in the shot only; not examined.

---

**Filed by Muad'Dib, 2026-09-25 evening (main d524846b), from a read-only diagnostic through the real hub at 1440 and 393.** Both findings are VERIFIED DEFECTS; S1 (the 409 on the second unnamed zone) is the highest owner cost: one New Zone from the Chair blocks every further zone until the first is found and renamed on the spatial Floor. Repairs: a lane after PR #665 (the receipt seat, ratified) and PR #663 (story 03) merge, since the rename row and the delete listener both live in `WorldStage.tsx` and must be mounted for the Chair and the list view; the Chair's New Zone should open its rename at once (UX-CANON §4, §11). The BACKLOG rows on PR #663 ("PHILO-7-03 follow-ups") are upgraded from UNVERIFIED to VERIFIED by this finding when that PR merges.
