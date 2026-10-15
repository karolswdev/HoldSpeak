# Reader surfaces — source audit

DRAFT; base `a81364a0d`, anchors checked 2026-10-15. HOLD FOR SHIP.
Only this report changed. No tests, browser, build or install ran.

**Tuesday:** the architect can read recorded changes and collection members,
but cannot currently tell an unavailable read/member from a quiet or empty
result. Both candidates fail Tenets 3/5/7, UX-CANON A10/B and Constitution VI.

**Room History — confirmed.** `ProjectRoomCore.tsx:2413` maps every non-OK
changes section to `[]`; `:2435` says Nothing today; `:2464` maps days with
no unavailable, empty or no-match face. The same unavailable read becomes
zero counts at `:2829`, then NOTHING THIS WEEK in the footer at `:2911–2930`.
Source-filter and search misses also draw a blank stream. Search is a raw
input plus MicButton (`:2449–2459`). Existing good material: FilterTokens,
SurfaceStream/Day/Entry and library Open remain; PLAN already offers a
named unavailable/Retry (`:1245–1257`), and whole-request failures already
use SurfaceState (`:2951`). StringGadget has `type="search"` and the existing
mic draft scope (`web/src/desk/surface/gadgets.tsx:260`). No Room redesign.

Root before setup: POST `/api/projects` with `{name:"History audit"}`;
GET `/api/projects/<id>/room`. The real changes producer is
`holdspeak/services/project_service.py:778`, `:883`; `_room_section` at
`:813–821` returns `{state:"degraded",error_code:"changes_read_failed"}`
when `_read_room_changes` fails. There is no failure-toggle route. Root can
capture a real isolated service answer under that fault, then replay only
that section; a response fabricated outside this producer is weaker proof.
The existing unit fault is `tests/unit/test_project_room_read.py:341`.
Open Projects → named project → Room, then History. `openProjectRoom(id)`
opens key `open-project-memory` with scope `project:<id>`
(`web/src/desk/shell.ts:129`); the direct request helper is
`openProjectRoomAt(id,"history")` (`openObject.ts:97`). Selectors:
`[data-testid=room-history]`, role tab History, aria Search history,
aria Source filter, `[data-testid=room-footer-receipt]`. A newly created
project supplies a real ROOM entry; JIRA yields a source miss, an absent
phrase yields a search miss. Preserve History item opening and folded Writes.

**Knowledge reader — confirmed.** `KbPullout.tsx:34–36` drops unresolved
stored refs. If all are unresolved, `:66` says No entries; Copy at `:81`
also omits them. The reader itself makes no membership request: it uses
the `/api/kbs` aggregate decoded by `web/src/desk/api.ts:288–299`, `:801`.
Therefore a failed `/members` request is currently an editor state, not a
reader state. Keep this repair to the stored refs unless design explicitly
names a reader read. Existing good material: `KbEditor.tsx:99–112` retains
each ref, draws Item unavailable without Open, and has membership-read
failure/Retry (`:104`); its Open flushes the writer (`:109`). Retain the
reader's filing strip and footer Copy/Edit/Dictate and their receipts.

Root before setup: POST `/api/kbs` with
`{name:"Knowledge audit",member_ids:["note:missing-audit"]}`. This is a real
accepted producer: `holdspeak/web/routes/primitives/kbs.py:52–66` →
`primitive_service.py:287–305`; membership validates qualified identity,
not resource existence (`holdspeak/db/relationships.py:28–37`, `:88–113`).
For mixed membership add a real Note ref alongside the missing ref. Confirm
GET `/api/kbs/<id>` and `/members`, then open `/?open=knowledge:<id>`
(`shell.ts:134`); New → New Knowledge → Done is the normal creation path
(`verbRegistry.ts:213`). Current reader has no dedicated testid: use the
named pullout region, text No entries and footer Edit/Copy; unavailable
rows will need identity selectors in the settled build.

**Focused tests proposed, not run:** extend the recorded-wire app harness
in `web/src/features/project-room/__tests__/room.app.test.tsx` for degraded
→ Retry → restored, true empty, source miss and search miss (including the
footer). Existing `ProjectRoomCore.test.tsx:288` demonstrates the same
health-failure retry seam. Add a focused `KbPullout.test.tsx` beside the
reader for mixed/all-unavailable/empty membership, honest Copy and real
Open. Existing `web/src/desk/components/InlineEditor.test.tsx:81` covers
in-pullout editor/Done; `editors/editorRepair.test.tsx:128` covers real member
write/flush custody. Root names exact files before any locked collection/run.

Unknown: live fit, narrow targets and rendered state transitions. Root owns
before shots, settled library canvas, exact test scope, quick check and release.
