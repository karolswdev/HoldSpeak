# Source journeys — bounded implementation

Active under KICKOFF.md. HOLD FOR SHIP; no staging or commit.

Tuesday: inspect the exact cited held task or output and return with work intact.
Tenets 3/5/7: existing windows, existing controls, truthful stored facts.

## Settled work

- `FollowThroughService.board` and `/api/follow-through/board`: retain candidate
  `focus_id` contract; only the canonical focused open action bypasses holds.
  Return snooze/defer stamps without writes. Existing filters still apply.
- `FollowThroughView.tsx` (`reload`, focus effects, `visibleLanes`, row facts):
  read the focused ID, expand that target despite the ordinary overdue filter,
  show hold stamps, and give missing/read failure an exact read Retry. Keep
  drafts, selected row context and failed write requests separate from reads.
- `SyncService.get_artifact` and sync router: retain candidate exact GET with
  existing hub authentication, mapper, and NotFound handling; no lifecycle write.
- `api.ts` held-object pass and `shell.ts` opener: read exact artifact IDs,
  retain the qualified request and material through refreshes, name failure
  locally and preserve exact read Retry. No public sync visibility widening.
- `ArtifactPullout.tsx`: Awaiting review/Rejected StateChip from stored status;
  known material remains readable after a failed read. Missing material has
  its own visible outcome. Opening does not accept, publish or invent review.

Line anchors drift while the three workers share the worktree: use declarations
above as anchors and re-read before editing. Canvas/root face GO precedes JSX.

## Boundaries

Owned paths are the services/routes above; their named unit tests; desk api,
shell and openObject; FollowThroughView and its test; ArtifactPullout and its
focused test; heldObjects and shell tests. Request root before extending files.
Composition owns intelligence.css and Brief/Day/Memory; reading owns capture,
Material/AgentWords; root owns docs/atlas/harness/release. No edits in those lanes.

Integration requests: absent artifact cannot open the existing compositor until
there is a canonical-ID local source shell or compositor support; cold `?open`
must hold its artifact before DeskApp's first refresh. Root settles these seams.

Root approved `lib/primitives.ts` local source-read metadata, `objectWindows.ts`
cache-backed window stand-in, `DeskApp.tsx` cold/restored holds and cache-first
artifact rendering. No compositor change: qualified refs already resolve.
Unavailable shells stay out of item collections. `artifact-reading.css` scopes
existing SurfaceWell to paper/ink without its nested vertical scroll cap.

Root also approved `IntelligencePullout.tsx` retained visited views using installed
React 19.2 Activity. Per-view frame-foot targets hide portal actions separately
(Activity alone leaks portals). Drafts, Brief selection and scrolling DOM remain
mounted; inactive effects stop. No new navigation framework.

## Focused checks

Notify root ready-to-test first; machine work serial under scripts/test_lock.py.
Python: tests/unit/test_follow_through_service.py and test_web_routes_sync.py
(and existing follow-through route tests if changed). Frontend: FollowThroughView,
ArtifactPullout, heldObjects and shell only. Isolated HOME for every run; report
collection and run tails. No full suite, test_metal, owner state or serving builds.
Approved additions: existing DeskApp.test.tsx and IntelligencePullout.test.tsx.
