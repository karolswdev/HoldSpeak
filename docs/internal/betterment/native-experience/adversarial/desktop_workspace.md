# desktop_workspace

job: Open the Desk and find the work surface  
baseline: `555728021`  
reviewer task: `review_desktop_workspace`  
evidence class: source and representative assertions inspected; no tests executed, no live walk, no owner observation, no native/provider action.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The real job is: arrive at `/` (or return from a deep link), wait for the
Desk/setup read, understand whether first use or the normal Chair owns the
glass, choose a task, open or raise it, and later return without losing task,
scope, or recovery state. `web/src/routes.tsx:20-29` makes Desk the normal surface;
`web/src/App.tsx:18-46` demotes paths and stages intent; `web/src/desk/DeskApp.tsx:122-160,213-241`
separates pending, failure, first value, and normal arrival. The inventory
record (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:3083-3117`) names only “open”, not completion,
return, or recovery.

The audit is also over-broad at its edge: “complete task views and resource
contracts” belongs to `explorer_repo` and `windows`, not proof that the Desk
itself is findable. Keep one Desk/Chair screen and the existing compositor;
do not turn this workflow into a native process or a multi-window mandate.

FINDINGS:

1. **High — the evidence corpus cannot support its current-behavior claim.**
   The brief cites only `web/src/desk/DeskApp.tsx:1-120` and `web/src/desk/applications.ts:1-58`, while
   trigger/finish paths are in `web/src/routes.tsx:20-85`, `web/src/App.tsx:18-70`,
   `web/src/desk/components/SurfaceWindows.tsx:92-181`, and `web/src/desk/chair/ChairHome.tsx:66-131`. Owner cost: an
   implementation may lose deep-link staging or first-use recovery (Tenets 3
   and 7). Correction: extend the source map through trigger → paint → first
   action → task-open → return; link `web/src/desk/DeskApp.test.tsx:160-248,296-354` as
   guards, not execution evidence.

2. **High — APP_ID is named but workflow identity is not converged.**
   Distinguish the Desk screen, application, window instance, and resource
   scope. The contract separates `applicationKey`, fixed `id`, and `scope`
   (`web/src/desk/store/types.ts:26-35`), creates them in `web/src/desk/store/compositorSlice.ts:434-452`, and
   maps hub refs in `web/src/desk/compositor/hubWindows.ts:236-254`. Owner cost: restore or
   deep link can be treated as a duplicate “work surface” and lose task
   identity (Tenets 5, 6, and 7). Correction: add an identity table for
   `desktop_workspace`, with `windows` as lifecycle consumer and scope as data.

3. **Medium — recovery and return are omitted despite useful guards.**
   `web/src/desk/DeskApp.tsx:153-160` keeps a failed read retryable, and
   `web/src/desk/components/SurfaceWindows.tsx:126-152` consumes a staged link after registration.
   Neither proves the round trip; the brief has no reload, offline-return, or
   scoped-task scenario. Owner cost: Tuesday recovery can reopen the wrong task
   (Tenets 3 and 7). Correction: make these falsifiable paths and preserve
   “not executed”.

## Convergence

Converge with `windows` on `WindowInstance`/compositor persistence and
front-window authority; first consumer is Desk restore/raise. Converge with
`navigation_commands` on the manifest-to-Go/Dock/menu/shortcut projection
(`web/src/desk/applications.ts:570-640`); first consumer is the first-task fast path.
Converge with `objects_pullouts` and `explorer_repo` only on resource identity
and command context. Keep this as the screen/arrival workflow: merging with
`windows` hides lifecycle failures, while merging with `explorer_repo` forces
explorer features on capture or Today (Tenets 1 and 3). `components_reference`
is reference, not production proof.

## User experience

Source inference is promising: the single Desk route and Chair are a coherent
Workbench model. Captures show a full-bleed 1440 Desk with bottom Dock
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/desk-1440.png`) and a compact 393 Go/Dock path (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/desk-393.png`). They do not
prove first-task findability, focus, or craft under return. Keep the first
action visible and make intent survive demotion and recovery.

CONDITIONS: Add the complete trigger/exit/recovery map, the app/window/resource
identity table, and the four scenarios below to the audit. Bound explorer and
native claims to their related workflow records.

MISSED:

1. Fresh `/` at 1440 and 393: can a tired architect identify and perform one
   useful first action without narration?
2. Setup pending/failure → Retry → normal Desk, including a staged deep link.
3. `/history?meeting=m1` → Desk → registered Meetings window with the same
   meeting scope after reload and return.

TUESDAY: Likely yes for the normal Chair, but the audit cannot yet prove the
first action or safe return when setup, routing, or persistence is involved.

## Acceptance challenges

1. With a resolved fresh Desk at 1440 and 393, the owner can identify one
   first action, open it once, and see the same Desk/compositor rather than a
   second route or manager.
2. Start with setup unresolved, then fail and Retry; the Desk stays honest,
   reveals normal arrival after success, and does not duplicate a staged open.
3. Open `/history?meeting=m1`; after demotion, exactly one
   `surface-meetings` instance has `meeting:m1` scope, and reload preserves it.
4. Minimize or background that task, receive a normal Desk return, and raise
   it again; application id, window id, resource scope, and focus all converge
   without inventing a second instance.

UNKNOWN: No test was run, no live walk or owner first-use session occurred, and
no performance, accessibility, native, or provider claim was made. The captures
are visual context only; omission in this audit is not an observed product bug.
