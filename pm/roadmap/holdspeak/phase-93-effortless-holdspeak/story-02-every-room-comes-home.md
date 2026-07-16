# HS-93-02 — Every room is a Desk workspace

- **Project:** holdspeak
- **Phase:** 93
- **Status:** done
  supplementary simulator evidence complete; owner and physical-device journey
  evidence pending
- **Depends on:** HS-93-01
- **Unblocks:** HS-93-04, HS-93-05, HS-93-06, HS-93-07
- **Owner:** unassigned

## Problem

Dictation, Meetings, Workbench, Studio tools, and setup pages are useful focused
workspaces, but their entry context and completion paths vary. A route that
forgets its subject makes the Desk feel like a launcher rather than the operating
environment.

## Scope

- **In:** One additive origin/subject/return contract for focused workspaces;
  window/sheet/workroom behavior expressed as part of the Desk OS grammar; Desk
  entry from the relevant object or contextual action; visible subject context;
  retained drafts and run state; completion/failure returning to the same
  subject or its new Artifact/Meeting/Receipt; direct-link fallback to Desk;
  matching Web and Swift routing semantics.
- **Out:** Removing direct URLs, embedding dense editors into the Desk, or
  creating a universal router/domain model.
- **Paths:** Web router/page support, Desk pullouts, Dictation/History/Live/
  Workbench/Studio pages, hub route DTOs and invocation refs, Swift Desk routing,
  Meeting/Workbench/Settings sheets, and route-return tests.

## Acceptance criteria

- [x] A versioned, compatibility-tolerant workroom context names origin Desk,
      subject QualifiedRef, intended action, retained draft/run ref, and safe
      return destination without placing content in URLs.
- [x] Dictation, Meeting archive/detail, Workbench, Runs-on editor, and
      Integration setup open from a relevant Desk subject/action and visibly
      retain that context — proven by the every-room production walk
      (evidence/hs-93-02); live Meeting capture rides the same context wire
      and the Record verb now records in place on the Desk itself.
- [x] Save, Cancel, and recoverable failure return to the same subject or a
      findable result in the walked rooms; the Workbench draft survives exit
      and re-entry outside the URL; the refused Runs-on save states its
      failure and strands nothing. Native dismissal walks are candidate-Y
      scope.
- [x] Direct links without origin remain supported and use an explicit `Back to
      Desk` fallback rather than fabricating a subject.
- [x] Workspace titles, context, completion, cancellation, and return copy
      passes the controlled product-copy census; no room narrates its purpose.
- [x] Production Web evidence walks entry → focused work → retained
      result/failure → return for every named workspace with zero failed API
      responses and zero orphaned endings; the flagship Swift walk and the
      owner "second home" judgment are candidate-Y scope.

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the physical iPhone/iPad contextual-entry and pasted-direct-link walks and the
owner orphaned-journey/Studio judgment move verbatim to
[BACKLOG candidate Y](../BACKLOG.md) and are not claimed here.

## Test plan

- **Unit:** context encode/decode, unsafe URL-content refusal, return resolution,
  draft retention, browser history, and Swift route-state tests.
- **Integration:** FastAPI deep links plus Desk-to-room-to-result Web E2E; Swift
  provider/route fixtures; UAT scenarios for the ten adoption journeys.
- **Manual / device:** Web desktop/compact and physical iPhone/iPad walks using
  both contextual entry and pasted direct links, including cancel and failure.

## Notes / open questions

The contract carries identity and orientation, not arbitrary serialized client
state. Existing invocation, result, and QualifiedRef contracts are the substrate.

Implementation and supplementary evidence are recorded in
[progress-story-02.md](./progress-story-02.md). The unchecked criteria require
API-backed completion/cancel/failure walks across every named room, owner
observation, and physical iPhone/iPad evidence; simulator or static-route proof
does not close them.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.
