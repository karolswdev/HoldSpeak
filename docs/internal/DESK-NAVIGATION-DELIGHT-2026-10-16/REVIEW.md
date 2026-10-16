# Desk navigation refinement — source counsel

Status: **UNCHECKED — awaiting Muad'Dib**.

Role: bounded source counsel, invoked by Astra with the owner's per-task
authorization for Sol xhigh. This is not Muad'Dib's check or the formal
post-merge review. This source verdict does not block the CLAUDE.md fast
cycle or replace root's production walk.

Reviewed 2026-10-16 in
`/Users/karol/dev/tools/wt-desk-navigation-delight-20261015`, against
`11984f33e86f6f9540dba44cfad45cbb67d90d10` (#1216). Scope was the seven
next-change source/test files named below, their direct library seams,
the settled DESIGN/BUILD records, and saved focused test evidence. The
one allowed fix re-check also covers the exact healed palette-393
exception removal in `tests/e2e/test_desk_sweep.py`. Review plus one fix
re-check is complete; Calendar is excluded. No product edits, tests,
browser actions, or delegated work were performed by this counsel.

VERDICT: RATIFY

FINDINGS: No failing source finding in the bounded diff. Verified:

1. Close uses the actual library Button, whose native `type="button"`
   and event props are preserved (`web/src/components/signal/Button.tsx:25`,
   `:41`). Its Enter handler stops propagation without preventing the
   native activation; the aside's selected-result Enter handler therefore
   does not run (`web/src/desk/components/DeskToolShelf.tsx:924`, `:990`).
   Click calls the existing close path, clears the query, and focuses the
   launcher (`:513`, `:994`). Closing still clears a name prompt through
   the existing subscription (`web/src/desk/chromeState.ts:52`). Prompt
   Save and input Enter retain `submitName` (`DeskToolShelf.tsx:890`,
   `:927`, `:1000`). The new tests exercise native Enter with user-event,
   focus restoration, exact selected-row nonexecution, Save, and prompt
   abandonment (`web/src/desk/__tests__/palette.app.test.tsx:134`, `:149`;
   `web/src/desk/__tests__/paletteRankHold.test.tsx:116`, `:127`). This
   supports Tenets 3 and 5 and UX-CANON A.1.

2. The named `surface` container scopes to the Search shelf and gives
   its StringGadget the existing shared narrow input/mic rules
   (`web/src/desk/components/attention.css:266`;
   `web/src/desk/surface/gadgets.css:1146`). Its desktop width is already
   at most 400 px, so those 44 px controls apply on the desktop shelf too
   (`web/src/desk/components/chrome-menus.css:371`). The input and mic
   share the flexible well; Close occupies a separate flex item with
   12 px spacing (`attention.css:269`;
   `web/src/desk/surface/gadgets.css:327`, `:361`, `:395`). There is no
   new mic geometry override. Actual hit ownership is still a browser
   question under UX-CANON C, not proved by this source review.

3. Meeting metadata reads the real Meeting fields: `startedAt` and the
   list row's `attendees` (`web/src/lib/primitives.ts:113`;
   `web/src/desk/api.ts:495`). It uses the existing local wire-time
   formatter and omits absent facts (`web/src/desk/components/DeskToolShelf.tsx:322`;
   `web/src/desk/surface/format.ts:51`). Choices retain `kind:id`, and
   each opens that qualified identity (`DeskToolShelf.tsx:675`). The
   same-title/time test retains two different meeting IDs and a note
   with a colliding bare ID, then opens each meeting exactly
   (`web/src/desk/__tests__/palette.app.test.tsx:197`). Metadata uses
   the existing mono type and selection colors at 12 px, with wrapping
   (`web/src/desk/components/attention.css:282`). No title/time dedup
   was added. This supports Tenets 3 and 7 and UX-CANON C.

4. Corrected Context rendering uses the previous null-safe revision
   read, with positive revision and nonempty usage facts
   (`web/src/pages/cores/ConstitutionalContextCore.tsx:158`).
   PUT content, Save/Restore enablement, History selection, Cancel,
   dirty/saved/refused outcomes, and limit conditions keep their existing
   paths (`:57`, `:83`, `:120`, `:146`, `:167`). The tests show failure
   retains the draft and retry, clearing retains unsaved, an empty Save
   sends `{ content: "" }` and keeps its real revision/saved outcome,
   and both History selections retain Cancel
   (`web/src/pages/cores/__tests__/constitutionalContextSave.test.tsx:30`,
   `:87`, `:112`). This satisfies the scoped zero-meter change under
   Tenet 3 and UX-CANON A.8 without a new state or write path.

5. Needs changes one declaration: its already 44 px painted verb tells
   the shared formula that painted height
   (`web/src/desk/needs/needs.css:68`). At the narrow viewport the
   existing formula then reserves 4 px on each side, versus 12 px,
   with the 44 px halo intact
   (`web/src/styles/global.css:184`; `web/src/styles/tokens.css:183`,
   `:194`, `:303`). No facts, actions, row identity, or shared Button
   rule changed. This supports Tenets 3 and 5; actual targets remain
   root's UX-CANON C pointer check.

6. Saved evidence matches the BUILD reports. Search collection contains
   68 cases across five files, including all six newly claimed cases
   (`.tmp/navigation/search-collected.json:155`, `:159`, `:171`, `:175`,
   `:223`, `:227`); its run tail reports 5 files and 68 tests passed
   (`.tmp/navigation/search-focused.log:5`). Context/Needs collection
   lists 41 Needs names and 3 Context names
   (`.tmp/navigation/context-needs-collect.log:3`, `:44`). The run
   log and parsed JSON agree on 2 files, 44 passed, 0 failed
   (`.tmp/navigation/context-needs-run.log:63`, `:66`;
   `.tmp/navigation/context-needs-run.json:1`). The existing Needs
   countdown and refused-Cancel cases emitted React act warnings
   (`context-needs-run.log:5`, `:27`); neither file failed. These are
   software results, not production geometry or persistence evidence.

7. Closed regression: the first version introduced a direct
   `ctx.revision` read. The existing `{}` scroll-ownership fixture leaves
   `ctx` undefined; `ctx === null` does not intercept that value, and
   the new dereference unmounted the body. The complete quick check
   captured that failure and its uncaught exception
   (`.tmp/navigation/quick/vitest.log:489`, `:514`;
   `web/src/pages/cores/ConstitutionalContextCore.tsx:37`, `:102`). The
   correction at `:158` restores optional access in both the condition
   and render. A missing-payload test now requires the empty editor to
   remain mounted, with no zero facts and disabled Save
   (`web/src/pages/cores/__tests__/constitutionalContextSave.test.tsx:75`).
   `scrollOwnership.test.tsx` is unchanged. Saved collection lists four
   Context tests plus three scroll-ownership tests
   (`.tmp/navigation/context-regression-collect.log:3`); the run log and
   parsed JSON show all seven passing in two files, with no unhandled
   exception (`.tmp/navigation/context-regression-run.log:6`, `:19`,
   `:21`; `.tmp/navigation/context-regression-run.json:1`). The run
   retains a DeskToolInspector act warning (`context-regression-run.log:7`).

8. The sweep edit removes only the exact palette-393 mic target excuse
   (`tests/e2e/test_desk_sweep.py:304`). The original quick sweep reported
   that excuse healed, with an empty failure dictionary
   (`.tmp/navigation/quick/sweep.log:84`, `:105`). The focused collection
   names only `test_every_window_holds_the_fences[palette-393]`, and the
   saved rerun passes it in 11.96 s
   (`.tmp/navigation/search-palette393-collect.log:1`;
   `.tmp/navigation/search-palette393.log:5`). No target fence was
   weakened: that fence still runs the shared edge/corner ownership
   probe (`tests/e2e/test_desk_sweep.py:759`;
   `tests/e2e/type_floor_rig.py:129`). Root's saved Search measurements
   also show 44 by 44 mic rectangles with nine owned samples at both
   widths and nine owned Close samples at 393
   (`.tmp/navigation/after-1440/observation.json:35`;
   `.tmp/navigation/after-393/observation.json:33`, `:80`). Those tour
   samples use 0.4-times-size offsets (`.tmp/navigation/tour.py:18`);
   the strict edge/corner evidence at 393 is the passing generic sweep.

CONDITIONS: None open within this source scope. The allowed fix re-check
is complete. The formal post-merge review remains fast-cycle work.

MISSED: The first source pass missed Context's new direct dereference on
the existing missing-payload fixture. A blanked editor fails Tenet 3;
the quick check caught it and the correction above closes it. No other
source issue was identified in this re-check. The first pass's focused
green counts did not prove compatibility with that fixture.

TUESDAY: Source supports explicit dismissal, distinct meeting choices,
and quieter Context/Needs; actual Tuesday usability awaits root's walk.

UNKNOWN: This counsel read the saved Search measurements and exact
palette-393 sweep output, but did not perform a browser or DB walk, read
the production PNGs, or independently verify real pointer activation at
each edge/corner, keyboard focus, meeting readability, Needs geometry,
Context persistence, or the final built whole-app task walk. Root owns
that evidence. The new Calendar face lane is explicitly excluded and
unreviewed here. No provider or audio execution is inferred. Week
geometry remains outside the source scope.
