# HS-S13 · Find and inspect a project's existing Programs

**Detailed conditional proposal; implementation not assigned.** Epic: [HS-E10](../epics/HS-E10-context-and-navigation.md). Pending D15/G13 in [Decisions](../DECISIONS.md). Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. This connects the project → work → review/delivery journey without adding a dashboard, lifecycle owner or storage model. Source inspection is not runtime reproduction.

## Job and evidence

While reviewing a project, the owner can see the Programs already filed to it and open the exact Program to inspect its work, requirements and delivery. Preserve the existing action → Run as a program entry. Merely opening the overview or a Program creates, starts, accepts, merges or retries nothing.

The data path already exists: `ProjectService.room` includes a fault-isolated `programs` section; `ProgramService.for_project` filters by exact stored `project_id` over **all** stored Programs and returns ordered summaries. `ProgramStore.list_programs` has no query limit at this pin. It does not infer membership from repository, title, person, action provenance or project collection entries. Terminal/parked Programs are not filtered out. Changing project association does not migrate a Program's repository or worktree.

The active Room controller already reads this section through `fetchProjectRoom`/`decodeRoomSnapshot`, but the active Room does not render it. `RoomPrograms` renders an array of rows in its own fold and is found only in the legacy drawer and an isolated test. Its existence is not proof of a current visible overview. The global Programs surface does not already accept a project-scoped navigation contract; selecting that alternative needs real context propagation, not an invented link parameter.

Current Room refresh also already admits Program `desk_changed` frames through `frameNames`' unknown-kind compatibility fallback. Real HTTP frames can coalesce several changes: use the full frame and `deskChanges`, not an assumption that its top-level kind is Program. Adding an explicit local `program` kind is ownership clarity, **not a repair of a proven absent refresh**. A real gap relevant to this newly visible data is that a failed quiet Phase 1 read silently keeps the last snapshot. Missing, degraded, malformed and successfully empty Programs must not be presented as the same outcome. A missed notification is different from an observed failed read: this slice cannot detect every stale snapshot or guarantee delivery. S11’s global Programs reload is not a Room reread. Explicit Room Refresh or a genuine remount can discover persisted work only if a current read succeeds; merely raising the same Room need not remount it.

Evidence: [workflow trace](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#workflow-follow-up-context-carried-through-real-work). Exact pinned source/proof map: [V13](../VALIDATION.md#v13-project-program-continuity-verification).

## D15 and G13 choices

- **A, inline continuity, fully specified here:** put the existing Programs summary in the active Room's filed-work area, after Files and before Sources. Reuse the existing nonempty fold/rows and Program detail destination. Keep one Room request and one debounced refresh subscription.
- **B, deliberate scoped transition:** navigate to the existing Programs surface with explicit project context. This needs a separately agreed scope/filter/reopen contract because today's `ProgramsCore` does not consume it. Do not simulate it through the global filter's incidental state. Selecting B stops A's implementation briefs.

G13 must accept A's local presentation and read semantics:

1. Display every returned Program, preserving producer order and exact identity, including Drafting, Parked and terminal rows. No arbitrary top-N, state filter, repository-derived membership or separate count query. The count is returned Programs, not total project work or current owner obligations.
2. The successful nonempty fold is initially open as the reused component already is. Successful empty data has a concise explicit “No Programs filed to this project” state, without a new Create/Start action. Absent/older-hub capability and degraded/malformed reads are named unavailable states, not zero. Retry uses the existing Room Refresh behavior. Exact copy remains reviewable.
3. Tighten only Programs decoding: an unknown section state, non-array `programs`, invalid/missing row identity, duplicate IDs or invalid numeric counts makes this section unavailable instead of silently dropping/coercing rows into a convincing empty/count. Preserve valid existing state words and unknown nonempty row state values as provider words through the existing neutral fallback; do not create a new lifecycle enum or reinterpret Done as delivered. Extra fields remain compatible. G13 accepts this narrowly stricter malformed-wire behavior.
4. Keep a last successful Room on current Phase 1 failure, but visibly identify it as the last read. An initial failure with no retained Room uses the existing load failure, never a fabricated last-read view. Clear this freshness warning only after a current Phase 1 success. Detail/extras failures do not falsely stale the Room snapshot. Late older success/failure cannot overwrite newer read truth. A retained row may still be opened for inspection; its current detail is authoritative, not the stale list.
5. The section introduces no independent fetch, timer, cache, read registration, global refresh rule or shell change. Preserve the existing mounted-read layout gate and draft/read-marker semantics. Explicit Refresh may retain its current read-marker behavior; this slice does not promise that a Room visit is entirely mutation-free.

D13 creation, D14 completion, G25 review and G32 delivery decisions remain separate. This view may expose their existing states but cannot resolve or claim to implement them.

## Narrow implementation design

Use three existing production owners only:

- `web/src/features/project-room/model.ts`: a cohesive local Programs-section decode branch/helper, exact name proposed. Preserve absent/degraded representation and valid wire fields; reject malformed identity/count evidence for this section without throwing away the whole Room or rewriting generic `decodeSection`.
- `web/src/features/project-room/useProjectRoomController.ts`: a bounded current Phase 1 freshness/read-error signal. Apply it under the same `loadSeq` identity as the successful snapshot. Distinguish full/quiet Phase 1 failure from later detail/extras failures; avoid clearing valid retained data. The component is already keyed by scope; do not add a parallel per-project cache.
- `web/src/features/project-room/ProjectRoomCore.tsx`: render current state/empty/unavailable/last-read presentation in the filed-work area. Successful nonempty rows reuse `desk/programs/RoomPrograms.tsx` unchanged, without nesting its existing `FoldGadget` inside another fold. Use the existing debounced refresh hook with a stable local kinds declaration including `program`, not an extra RuntimeBus subscriber or a shared global-kind expansion.

No new production module, CSS file, route, DTO, backend query or schema is planned. If the existing row layout fails the required narrow-window proof, stop for a specifically reviewed style-path amendment rather than copy the row UI or hide Programs on phone. No arbitrary file-size rule requires splitting cohesive local helpers.

The Program count, state word, `done/total` and `your_turn` come from the existing summary. They are not new evidence of delivery, private People obligations, accepted action fulfillment or current external review. Open delegates the exact ID to existing `openProgram`/store/host behavior. A void opener return is not mounted-window acknowledgement; actual content/focus is verified separately. Preserve existing repeated-open and hidden-window behavior rather than invent a new navigation contract here.

## Acceptance matrix

| ID | Required outcome and proof |
| --- | --- |
| C13-01 | Real admitted `/room` response for project A includes only Programs whose stored project_id is A, with matching detail IDs and producer order; same repository/project B or unfiled work is excluded |
| C13-02 | Existing repository/action launcher remains; reading or opening rows dispatches no Program creation/start/accept/merge/delivery command. Existing Room read markers/window persistence are separately allowed and identified |
| C13-03 | Nonempty/empty/absent/degraded/malformed are distinguishable; malformed rows or duplicate IDs cannot manufacture an empty/all-clear state. Unrelated Room sections remain usable |
| C13-04 | All producer rows remain accessible, including parked/terminal and a fixture larger than incidental UI limits. State/progress/turn words do not become delivery status or project-wide obligation coverage |
| C13-05 | Actual full `desk_changed` frame containing a Program change, through its `changes` list or legacy top-level shape, causes one existing debounced Room reread, including new/moved-in unknown IDs and moved-out rows. Windows-only and known unrelated frames retain existing filtering; unknown-kind compatibility stays unchanged |
| C13-06 | Current full/quiet Phase 1 failure retains rows with last-read warning; current recovery clears it. Delayed old failure/success cannot corrupt newer data or freshness. Later detail/extras failure alone does not stale the successful Room |
| C13-07 | The active Room renders the rows and one press reaches the exact Program detail through the real store/host. Same-name Programs cannot redirect by title; repeat/hidden-window behavior remains the existing contract |
| C13-08 | Initial load/read-layout gate, late sibling reads, collapsed section, History wing, Refresh and scope-keyed remount preserve drafts, stable tap ownership and the existing read-marker baseline |
| C13-09 | 1440×900, 393×852 and a genuinely narrowed Room window retain visible state, usable fold/row controls, keyboard focus and correct hit ownership; no clipped count/title or hidden-open affordance |
| C13-10 | Existing archived-project read/admission and current Program detail refusal/absence are preserved. Archive is not Stop; no invented multi-user/private-data authority follows from this overview |
| C13-11 | Backend raw response → actual decoder/controller → active Room plus real host navigation is proved. The old isolated `RoomPrograms` fixture or a mocked `openPullout` alone is insufficient |

## Order and bounded proof

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T13-01 contract](../tasks/HS-T13-01-contract.md) → accepted G13-A → [HS-T13-02 current-Room implementation](../tasks/HS-T13-02-room-continuity.md) → [HS-T13-03 independent proof](../tasks/HS-T13-03-verification.md).

The implementation task owns its producer cases and one proposed synthetic wire bundle as well as the three UI files. V13 names exact test/edit ownership and commands; commands are source-defined or plan-composed, not executed results. Serialize Room/model/controller/fixture/browser edits with S12/S41/S42/S52 and Program test consumers with S11/S21/S25/S32. No other slice must be implemented first. If S11 and S13 are both accepted and assigned, [the creation-to-Room integration gate](../VALIDATION.md#creation-to-room-integration-gate) additionally joins one project-only request, acknowledgement, Room row and detail ID. T13-02 owns that bounded test/capture amendment, coordinated with S11’s app-test owner; T13-03 verifies it. Standalone slice completion does not establish this composed journey, and S12 is not its prerequisite.

## Rollback and stop conditions

Reverse only the assigned UI/test/fixture diff; no data migration or effect replay is required. Rolling back hides the active overview and restores any old silent/coercive read behavior; record that limitation. Never delete Programs, alter project association or migrate repository/worktree data as rollback. Already visited/acknowledged read markers and window state are not fabricated away.

Stop for unresolved G13 choice, source drift, unexpected strict consumers, any need to change backend scope/caps/permissions, new privacy payload, unverified provider/test isolation, or geometry that requires an undeclared production path. Preserve historical/proposed distinctions: this is not evidence the current product displayed the fold, that missing refresh was reproduced, or that this plan authorizes implementation/shipping.
