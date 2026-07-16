# HS-93-02 progress record — Every room is a Desk workspace

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `1e6a28f3` plus the uncommitted HS-93-01 working tree<br>
**After build:** current Phase-93 working tree; no commit identity claimed<br>
**Acceptance status:** in progress — automated and simulator evidence is not
owner or physical-device acceptance.

## What changed

Focused rooms now receive one versioned, identity-only workroom context instead
of inferring where a person came from. Its version-1 wire shape is:

```text
version, origin=desk, subject_ref, action, draft_ref, run_ref,
return_to=desk, return_ref
```

The Web, Hub, and Swift implementations share those names and constraints:

- [`web/src/workrooms/context.ts`](../../../../web/src/workrooms/context.ts) owns
  browser encoding, safe internal return resolution, direct-link fallback, and
  refusal of authored-content fields in either the envelope or URL.
- [`holdspeak/workrooms.py`](../../../../holdspeak/workrooms.py) mirrors the
  compatibility-tolerant DTO and QualifiedRef boundaries for the Hub.
- [`WorkroomContext.swift`](../../../../apple/Sources/Contracts/WorkroomContext.swift)
  mirrors the contract for flagship native routing and ignores unknown future
  metadata while refusing authored content.

Unknown non-content metadata is tolerated for compatible future senders. Draft
or prompt text never enters the route; the browser URL carries only a base64url
identity envelope. Unsafe external return paths and content-bearing query keys
are refused. Workbench draft and run input are retained in session storage,
separate from navigation identity.

## Visible behavior

- Desk Dictate and Record starts, the room menu, the tool shelf, and object
  pull-outs now open focused routes with an action and relevant subject when one
  exists.
- Meeting pull-outs open the requested saved Meeting, Workflow pull-outs open
  the requested Workbench workflow, and the tool shelf opens Runs-on and
  Integration settings as Desk workrooms.
- Every React `PageHero` renders either `From Desk` with subject/action and
  `Back to subject on Desk`, or the factual direct-link fallback `Opened
  directly` with `Back to Desk`.
- Live capture retains the Meeting identifier after stop and offers `Return to
  saved Meeting`. Workbench retains the selected workflow, layout, and run input
  through browser navigation.
- Flagship Swift presents Dictation, Meeting, Workbench, and Settings with
  item-based route state, so context and sheet presentation arrive atomically.
  The native bar states `From Desk` and `Close returns to Desk`; Meeting,
  Workflow, and Integration actions carry their QualifiedRef subjects.
- QualifiedRef parsing now preserves identifiers containing additional colons,
  and `integration` is an additive Hub resource kind.

## Captures

The Web frames come from the production bundle served by a real
`MeetingWebServer` against an isolated config and database. The capture runner
uses ordinary pointer clicks from Desk → Tools → Integrations and aborts if any
API response fails or request-error copy becomes visible. That gate caught and
led to a fix for the delivery belt intercepting clicks over the Tools shelf.
[`phase93_workroom_evidence.py`](../../../../scripts/phase93_workroom_evidence.py)
is the repeatable capture path; the disconnected Vite layout-shot harness is
not accepted as runtime evidence.

| Surface | Evidence | What it establishes |
|---|---|---|
| Web contextual desktop | [Integration Settings](./evidence/hs-93-02/after-web-context-desktop.png) | A user-operable Desk entry reaches a connected Settings workroom with origin, subject, action, and subject return |
| Web contextual compact | [compact Integration Settings](./evidence/hs-93-02/after-web-context-compact.png) | The same connected contract remains legible without overflow |
| Web direct route | [direct Dictation](./evidence/hs-93-02/after-web-direct-fallback.png) | A connected direct route fabricates no subject and explicitly returns to Desk |
| iPhone simulator | [Settings workroom](./evidence/hs-93-02/after-iphone-simulator.png) | Production app sheet visibly states Desk origin and dismissal result |
| iPad simulator | [Settings workroom](./evidence/hs-93-02/after-ipad-simulator.png) | Item-based iPad presentation retains the same context |

The simulator captures are supplementary implementation evidence. They are not
physical-device evidence and do not satisfy the manual/device test plan.

## Verification

| Lane | Result |
|---|---|
| Web `npm run check` with the repository's NVM Node 22.21.0 | architecture guard passed for 96 source files; typecheck passed; 21 files / 132 tests passed; production build passed |
| API-backed Web evidence runner | desktop contextual, compact contextual, and direct fallback captures passed with ordinary clicks and zero failed API responses |
| Focused Hub/Python contracts and integration routes | 23 passed |
| Full Swift package | 538 passed, 9 skipped, 0 failed |
| Flagship simulator app build | generated `HoldSpeakMeetingCapture.xcodeproj` / `HoldSpeakMobile` Debug iPhoneSimulator build succeeded after the item-based route correction |
| Patch hygiene | `git diff --check` passed |

The contract-specific tests cover round-trip identity, future metadata,
authored-content refusal, unsafe returns, direct fallback, and bounded actions.
React tests cover contextual and direct room bars. Static native contracts lock
the item-based route state and first-use entry points.

## Acceptance still required

HS-93-02 remains open. Before its remaining criteria can close, evidence must
walk every named workspace—not only Integration Settings and direct
Dictation—on an API-backed production Web root and physical iPhone/iPad through
contextual entry, focused work, Save/Run/Keep/Send, cancel/dismissal,
recoverable failure, and return. Those walks must also prove browser Back and
native dismissal retain drafts and make results findable. Owner observation
must confirm no journey ends on an orphaned administrative page and Studio does
not feel like a second home.

## Closure — 2026-07-16 (owner-rescoped)

The standing owner close directive rescopes this story to its
machine-verifiable scope; the physical-device walks and owner judgments move
verbatim to BACKLOG candidate Y.

The closing slice extended scripts/phase93_workroom_evidence.py to every
named room against the production bundle with the zero-failed-API gate:
contextual Dictation (subject named, return reopens the same pull-out),
direct-URL Dictation (explicit Back to Desk, no fabricated subject), Meeting
archive/detail via Review meeting, Workbench edit with the draft retained
outside the URL across exit and re-entry, Runs-on editor cancel with nothing
stranded, Integration setup on desktop and compact, and a refused Runs-on
save that states its failure while the return still lands on the subject.
Nine screenshots in evidence/hs-93-02/. No product gaps were found — every
room already carried its contextual entry and working return.
Captured run: [evidence-story-02](./evidence-story-02.md).
