# HS-92-05 — One place for every useful thing

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress (pre-close implementation; native contextual actions and physical cross-device walk pending)
- **Depends on:** HS-92-01, HS-92-04
- **Unblocks:** HS-92-06, HS-92-09
- **Owner:** unassigned

## Problem

Directory, Zone, folder, KB, Knowledge, Project, project context, and grounding
all group material for different reasons. Their difference is valuable, but the
clients do not teach it consistently and membership/placement state can live in
parallel stores. Users need one predictable answer to where something is, what
can ground a run, and which endeavor it belongs to.

## Scope

- **In:** Canonical Placement, Knowledge membership, and Project relationship
  adapters; Zone product language over `directory` wires; many-to-many
  Knowledge membership where required; Desk create/file/move/dive/list/search;
  Project association; grounding pickers and lineage; sync fidelity; keyboard,
  VoiceOver, and non-drag actions.
- **Out:** A general-purpose filesystem, forced decorative spatiality, merging
  Project into Zone, or using Knowledge as a placement tree.
- **Paths:** `holdspeak/db/primitives.py`,
  `holdspeak/web/routes/primitives/directories.py`,
  `holdspeak/web/routes/primitives/kbs.py`, `holdspeak/web/routes/projects.py`,
  `holdspeak/web/routes/sync.py`, `holdspeak/grounding.py`, `web/src/desk/`,
  `apple/Sources/Contracts/Primitives.swift`,
  `apple/App/MeetingCapture/DeskPrimitive.swift`,
  `apple/App/MeetingCapture/DeskSync.swift`, and placement/grounding/sync tests.

## Acceptance criteria

- [x] One object may have one current Zone placement, zero or more Knowledge
      memberships, and zero or more documented Project relationships without
      any write mutating another axis.
- [x] Web and Swift show `Zone`, `Knowledge`, and `Project` with concise first-use
      explanations; wire aliases remain readable and round-trip without field
      loss.
- [x] Create, rename, file, unfile, move, dive, search/list, add/remove Knowledge,
      and assign/remove Project are available from the Desk object or its
      contextual panel on both clients.
- [x] Every drag action has a named menu, keyboard, and VoiceOver equivalent;
      client geometry remains local while identity/membership syncs.
- [x] Grounding can select a Meeting child, Artifact, Note, Knowledge collection,
      Zone contents, or Project material; it prices actual resolved content and
      refuses stale/unknown references by name.
- [x] A kept Result records exact QualifiedRefs and the membership/placement
      snapshot needed for truthful lineage, without copying a whole collection
      into a hidden context field.
- [ ] Cross-device create/refile/membership changes round-trip and conflicts are
      explicit; a missing/deleted Zone never strands an invisible object.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_db_primitives.py tests/unit/test_grounding_shared.py tests/unit/test_web_routes_primitives.py tests/unit/test_web_routes_sync_primitives.py`; Web Desk placement/grounding/list tests; Swift DeskSync/DeskRecords tests.
- **Integration:** `uv run pytest -q tests/integration/test_primitive_framework_sync.py tests/integration/test_web_project_kb_api.py`; UAT `pack-desk/02`, `pack-desk/03`, `pack-desk/04`, and native DeskOS CRUD/zone scenarios updated to the canonical axes.
- **Manual / device:** File by drag and by non-drag menu, add the same Note to two
  Knowledge collections, assign a Project, sync, ground a run, and verify the
  kept Artifact/lineage on Web, iPhone lane, and iPad Desk.

## Notes / open questions

Project cardinality must be chosen from current repository behavior before the
wire is frozen. Do not silently assume one Project if existing records support
several.

## Implementation evidence — 2026-07-10

- Added collision-safe QualifiedRefs and separate `directory_memberships`,
  `knowledge_memberships`, and `project_resources` stores; Knowledge and Project
  are many-to-many, while Zone remains a single placement edge, and tests prove
  that changing any one axis leaves the other two unchanged.
- Web object pull-outs now explain and edit Zone, Knowledge, and Project
  independently, and filing by drag or named “Move to…” action writes the same
  qualified identity. Deleting a Zone tombstones its live filing edges and
  reparents child Zones so no object is stranded off the Desk.
- The shared grounding resolver now hydrates Meeting, Transcript, Artifact,
  Note, Knowledge, Zone, and Project refs from current canonical content,
  recursively resolves container membership, prices the resolved payload, and
  refuses stale/unknown members by exact ref; the Web picker exposes all of
  those root objects and collections alongside Meeting children and Artifacts.
- Kept Web Ask results re-resolve refs at Keep time, reject stale context, and
  persist exact QualifiedRefs plus a per-ref Zone/Knowledge/Project snapshot in
  artifact lineage rather than copying collection content into a hidden field.
- Relationship edges now ride the sync wire with tombstones and LWW clocks;
  Project identity rides beside them; JSON schemas, Python taxonomy, and Swift
  `SyncKind`/`ChangeSet` are locked together, while native filing converts its
  legacy display ids at the boundary to the same canonical `meeting:`,
  `artifact:`, `note:`, and `knowledge:` refs.
- The native object pull-out now carries the same concise three-axis explanation
  and named, VoiceOver-labelled add/remove Knowledge and assign/remove Project
  buttons; pulled Project metadata and both relationship arrays persist locally
  and re-enter subsequent sync snapshots instead of vanishing after one pass.
- Native and Web grounding pickers now expose root Artifacts, Notes, Knowledge,
  Zones, and Projects as well as Meeting children; desktop runs ship refs to the
  shared resolver, local native runs hydrate current synced content, both gauges
  price that resolved content, and stale local or hub refs refuse by name.
- Native kept Results now rewrite legacy display ids to exact QualifiedRefs and
  freeze the same per-ref Zone/Knowledge/Project snapshot in structured artifact
  lineage that Web Keep records.
- Automated proof green: focused relationship/grounding/API and sync-contract
  Python tests; focused Web tests, TypeScript check, and production build; the
  527-test Swift package suite (9 documented skips); and the complete iOS
  simulator application build.
- Still required before completion: owner-visible recovery presentation for an
  induced equal-clock Project/relationship conflict, and the physical Web/iPhone/iPad
  file/multi-membership/project/ground/Keep round-trip with owner evidence.
