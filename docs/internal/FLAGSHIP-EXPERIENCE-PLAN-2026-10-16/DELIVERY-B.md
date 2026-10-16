# Brief and connected source reading — delivery B

Verified for release, 2026-10-16. KICKOFF.md was invoked by the owner; the earlier
planning pause is over. Release identifiers and final checks are recorded below
when complete. This is a connected first delivery, not whole-product aesthetic
acceptance.

## Changed behavior

Brief leads with standing answers and changed work; Day puts the next meeting
before old finish work; Memory puts the title and rationale before metadata.
The actual-library direction used populated 1440, 600 and 393 compositions.
The source name is a library Button, with full text and readable states.

An explicit action citation can inspect its exact open snoozed/deferred task.
Ordinary board suppression and stored holds remain intact. The focused task
opens expanded with its hold date. Owner/date drafts survive view changes.
Brief retains its actual body, Send section and reading position on return.

An explicit output citation reads its exact artifact, including pending or
rejected output excluded from the public sync collection. The reader states
Awaiting review/Rejected; reading does not accept or publish. Missing/failed
reads have a local result and Retry read. A failed later read retains known
material as Last read. It does not leave a global error after the source closes.
The PR-context fixture explicitly says no review was completed.

New Codex Stop and transcript captures preserve line breaks and indentation.
Full AgentWords and Material share the existing CodeMirror Markdown parser and
one React document renderer: headings, paragraphs, nested lists, tables and
code. Supported object links use existing openers; labelled HTTP(S) links need
an explicit press. HTML remains text, images do not fetch, and unsupported
file/agent destinations remain labelled inert text. Compact agent summaries
keep their intentional selection. Old flattened captures are not reconstructed.

## What was actually exercised

All checks used isolated HOME, DB and provider switches under the machine lock.
The owner's served bundle, DB, microphone, credentials and Jupiter preview were
excluded from verification. A normal local delivery is a separate step.

- Baseline actual old frontend at 1440/393 reproduced both blocked source opens
  (`.tmp/flagship/before-{1440,393}-sources/`). The baseline used the old built
  frontend with candidate backend/capture; it is not an original-backend snapshot.
- Real Thought/Door producers prepared tasks. Inspection preserved their exact
  hold. The later populated tour uses a real Thread as the task source, writes
  Assign through the real UI/API, and reads the exact updated DB/board record.
- The pending artifact is declared stored output through the repository API,
  not evidence of a completed model run. Standing answers are explicitly
  replayed envelopes containing those exact created refs. Calendar material
  comes from a declared repository projection, not the owner's calendar.
- The phone tour retained Brief's nonzero reading position (419 → 419), its open
  Send section and an edited task owner. Assign persisted while the hold stayed
  unchanged. Exact pending output read, failed-read reload, read Retry and
  preserved review state passed. The real Codex Stop CLI producer retained the
  original payload; the actual Codex asks host rendered its table/list/code and
  exposed the answer field. Its Answer action correctly remained disabled for
  the isolated session with no terminal. No answer delivery is claimed.
- Official graph cases use one fresh hub per invocation, actual API producers
  and named UI triggers. The atlas is `atlas-brief-reading.json`; its27 scoped
  schema/reference checks pass. Observation and screenshots remain under
  `.tmp/flagship/graph-*`, never rewritten as owner observation.

The supplemental actual tour is `.tmp/flagship/tour.py`; complete observations
include build ID, source identity, state checks, screenshot paths and geometry.
The actual-library direction lives in `canvas/`. Root reads the actual images;
geometry/test counts alone do not establish pleasant design.

## Review and limits

Independent Sol counsel is `INTEGRATED-REVIEW.md`, distinct from formal
postmerge review. Its Brief-resume and global-source-error findings were fixed.
A late accepted assignment now rereads the current subject instead of replacing
it with the submitted subject. Actual screen review also corrected the title Button's native dark fill,
separated source groups from sentences, and removed a raw missing-source token.

The first broad quick run found stale transport/order/link assertions and a
fixture-induced exception; those tests were corrected to the new exact source
contract. All changed focused checks were rerun. The first complete green quick check passed4184 web tests,1508 affected Python,
109 sweeps and17 canon checks. A subsequent bounded review found the late-write
focus race: accepted Assign A could initiate a read of A after the owner had
opened B. The follow-up read now uses current focus while its receipt keeps A.
Its21-test focused file passes; the final ordinary quick check is rerunning
after this last product change. TypeScript passes.

Capabilities metadata, generated API surface and OpenAPI are updated. Graph
join/check are regenerated after metadata. The census records existing broad
graph debt (116 new, 5 removed, 5 miscited entries against its older snapshot;
no stale OpenAPI); this batch does not rewrite sealed historical passes.

Provider execution, native recording/keystrokes, formal postmerge review, full
main tape and owner visual acceptance remain separate. Batches C–E remain open;
read-only bounded follow-up notes preserve already healed behavior and name
concrete next work.

## Verification ledger

| Check | Result / local record |
| --- | --- |
| Capture backend |36 collected/passed; `.tmp/flagship-reading/scoped-check-output.txt` |
| Shared reading |28 passed; same worker run record |
| Focused source backend |44 Follow-through +15 sync passed; source lane brief/logs |
| Focused integrated frontend |79 source;63 composition; subsequent46 real Brief/related;25 route fixtures;8 shared host policy;21 final Follow-through regression file; these overlapping runs are not added into a unique-test total |
| Actual final desktop |10 states, no page errors; `.tmp/flagship/after-1440-complete/`, build83c762b011fa6095 before the late focus-only fix |
| Actual phone |8 states, no page errors; `.tmp/flagship/after-393-complete/`, build6574859af1917c48 before missing-token/focus fixes |
| Official exact-source graph |Missing source and held source pass at1440/393; respective `.tmp/flagship/graph-*` observations preserve their exact build/revision/boundary |
| Atlas |27 passed; `.tmp/flagship/atlas-check-final.log` |
| Generated inventories |API surface765 routes; OpenAPI629 paths; capability generation/freshness and coverage pass; graph join/check pass with14 inherited subtype conflict notes |
| TypeScript |Pass; `.tmp/flagship/typecheck.log` |

Final ship-build phone/narrow observations, final quick and release identifiers
follow below; the preceding proof is explicitly not relabelled as that build.

## Final build walkthrough

Build `c15a5e7c1ef79062` has the last Follow-through focus fix. The final phone
and resized-desktop tours each recorded10 states with all behavioral checks
passing and no page errors (`.tmp/flagship/after-phone-ship/` and
`.tmp/flagship/after-narrow-ship/`). The desktop Today/Brief window was actually
resized to600 px. Phone Brief retained419 →419 scroll position. Root viewed
final phone Memory, Codex document/answer controls, failed-source state and
narrow Brief. The reviewer viewed the complete final sets. The missing-source
official graph case also passes at393 on this build, with Source unavailable
and Retry read and no raw `not_found` token (`.tmp/flagship/graph-missing-ship/`).

Geometry diagnostics are not reported as universally zero: the failed-source
inline chip and wrapped message have overlapping union boxes but visibly
separate glyphs. The narrow output's recorded clipping belongs to the second
Send preview below the viewport; the visible full reader fits. Memory's compact
search excerpt can include Markdown delimiters; it is not the full document.

The final quick run passed4185 web,1507 affected Python,109 sweeps and17 canon,
but one upload-to-Brief test observed an intermediate import row. Its cause and
resolution are recorded below before release; that run is not called green.

The import failure was a real publication race, not a timing assertion problem.
The import writer committed finished transcript/end before normalizing the
placeholder start. It now uses the existing repository transaction for both.
A separate-reader commit observer fails deterministically before the fix and
passes after it. All147 import/Monday tests passed; Monday's existing upload
assertion was unchanged (`.tmp/flagship/sources-import-race-{red,green}.log`).
The ordinary quick check is rerun after that backend correction. No web source
changed, so the final browser build identity remains `c15a5e7c1ef79062`.

## Release check

Final ordinary quick check GREEN (`.tmp/flagship/quick-release.log`):4185 web
in426 files,1599 affected Python,109 desktop/phone sweep cases,17 canon checks.
The imported-meeting regression expands the affected Python selection. Root
read the result and deterministic before/after regression. Build remains
`c15a5e7c1ef79062`; a separate digest of the current web source exactly matches
its build stamp (`.tmp/flagship/source-build-equality.json`). This closes the
independent counsel's sole remaining release-check condition. Merge and local
runtime identifiers follow after delivery; no provider result is inferred.

PR: [#1220](https://github.com/karolswdev/HoldSpeak/pull/1220). The source branch
is `fix/brief-reference-open-20261016`. Normal idle-hub delivery follows its
merge and exact tree/build comparison; the runtime receipt is recorded separately.

## Delivered

PR#1220 merged at2026-10-16 18:49:46 UTC as
`1c20a595c88048241b44251201e852f9a75f53e3`. The verified branch and merged main
have identical tree`d8d069ea1efae3095d3efa00193332092848902f`. Normal local
replacement observed the previous hub idle, then served build
`c15a5e7c1ef79062` from the first implementation worktree, PID52533. Health,
Desk, Conductor and Models returned200; served stamp and HTML matched the
verified bundle. Receipt: first worktree `.tmp/flagship/deployment.json`.
That worktree is now the serving tree and is frozen. Follow-up implementation
uses `wt-flagship-daily-recovery-20261016`, based on the merged commit.

The full postmerge suite was dispatched on that exact main head:
[run38950387547](https://github.com/karolswdev/HoldSpeak/actions/runs/38950387547).
It was in progress when this record was written; no result is claimed here.
