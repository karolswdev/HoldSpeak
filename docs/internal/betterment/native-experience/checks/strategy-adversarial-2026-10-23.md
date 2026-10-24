# Native-experience strategy: adversarial review

**DRAFT — advisory strategy review, not Muad’Dib check.**

Scope: review of the proposed strategy and its package boundaries. This is not
a re-run of the 47 family reviews, and the 204 challenges in that packet are
not tests (`docs/internal/betterment/native-experience/adversarial/README.md:8-14`).
The evidence here is the strategy packet, its audit, and selected family
counterexamples.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **P0 — application identity and lifecycle are not settled before the first
   checkpoint.** The strategy correctly says that the missing layer joins
   identity, navigation, selection, commands and operations
   (`docs/internal/betterment/native-experience/README.md:96-101`), and the
   model proposes separate application, window, resource and location
   concepts (`docs/internal/betterment/native-experience/APPLICATION-MODEL.md:54-71`).
   It does not decide the hard case that makes “two windows” real: two
   locations of one repository, instance deduplication, and restoration of a
   stale location. The explorer review shows the current key is
   `repository:${repositoryId}` and that file opening is not wired, while
   `windows` shows that mounted views, dirty documents and retained operations
   are currently different lifetimes (`docs/internal/betterment/native-experience/adversarial/explorer_repo.md:12-35`; `docs/internal/betterment/native-experience/adversarial/windows.md:42-53`).
   Yet package 0 already requires a second window and cross-window handoff
   (`docs/internal/betterment/native-experience/DELIVERY-PLAN.md:62-68`).

   **Intervention 1 (most consequential):** settle one identity/lifecycle
   table before implementation: `applicationKey`, stable `windowId`,
   qualified resource/document identity, mutable location/history, and the
   owner of draft, operation and receipt retention. Option A is multiple
   instances of the same provider (the native-feeling choice, with more
   persistence and stale-identity work). Option B is one provider instance
   with location tabs (less first-wave state, but it changes the requested
   window model and hides the same-instance problem). Recommend A for the
   pilot, while keeping mounted view state separate from domain operation
   retention and feature-owned close guards. Without this decision, “native”
   means a frame around ambiguous work.

2. **P0 — “shared interaction contracts” still risks flattening unlike jobs.**
   The proposed command contract says menus, shortcuts, context menus and
   voice proposals resolve the same target set (`docs/internal/betterment/native-experience/APPLICATION-MODEL.md:58-65`),
   but the navigation review documents three different scopes: front-window
   object, Desk selection, and configured voice macro
   (`docs/internal/betterment/native-experience/adversarial/navigation_commands.md:14-25`).
   The existing selection is also global/singular in places while collection
   views need local sets and range anchors (`docs/internal/betterment/native-experience/APPLICATION-MODEL.md:41-47`).
   A universal target would make a repository command, an Ask handoff, and a
   Desk command look reusable while acting on the wrong object. Voice macros
   also auto-fire configured actions, whereas contextual proposals require
   confirmation (`docs/internal/betterment/native-experience/adversarial/navigation_commands.md:41-55`).

   **Intervention 2:** make the shared contract a small typed context, not a
   page template: command scope (view-local, Desk-global, or explicitly
   targeted), origin, primary/set target, focused control, availability and
   refusal reason, consent mode, operation/receipt identity, and return focus.
   Define selection/history as window-local and preserve Desk selection as a
   separate projection. Option A is one precedence rule (predictable, but
   surprising for global actions). Option B is explicit command classes (a
   little more metadata, but honest and testable); recommend B. Share target,
   outcome and receipt facts with voice, but retain separate macro versus
   contextual-proposal consent and recovery. This preserves specialized
   editors, terminals and media while giving RepoWindow and Ask a real common
   seam.

3. **P0 — honest state and quality proof are named, not yet bounded.** The
   plan has useful pattern ownership—adapter/domain authority versus visible
   edit state (`docs/internal/betterment/native-experience/DELIVERY-PLAN.md:79-98`)—
   but it does not establish a state boundary for read failure, stale data,
   operation outcomes, and domain-specific partial work. The feedback review
   warns that an operation ledger already exists and that “partial” is not a
   universal kernel state (`docs/internal/betterment/native-experience/adversarial/feedback.md:12-23`).
   The synthesis already names the safer direction: distinguish honest read
   states, retained work, and domain outcomes without a universal status enum
   (`docs/internal/betterment/native-experience/adversarial/SYNTHESIS.md:56-67`).

   **Intervention 3:** require each first consumer to map provider read states
   (loading, known empty, stale, unavailable, failed) separately from
   operation terminal states and domain states such as stopped, saved, partial
   or indeterminate. Reuse existing receipt, egress, source and operation
   identities; do not add a second ledger. Then judge craft with a paired task
   record, not geometry: one real job at 1440 and 393 plus a constrained
   floating width, populated/empty/busy/failed/resumed states, pointer and
   keyboard paths, voice/IME where relevant, and preserved focus,
   selection, draft, scroll and return. The existing proof tiers explicitly
   distinguish source/tests, automated task behavior, and live owner task
   evidence (`docs/internal/betterment/native-experience/USE-CASE-AUDIT.md:130-150`).
   This is evidence for the fast cycle, not a new approval gate or invented
   performance budget. A local timing trace and the owner’s live shot can
   establish ergonomics and delight; a green geometry floor cannot.

## Pilot and second-consumer choice

The proposed order is directionally right: finish the already demonstrated
high-cost repairs, then prove a real resource job with Settings and a shared
reference (`docs/internal/betterment/native-experience/adversarial/SYNTHESIS.md:69-98`).
The strategy should make the falsification sequence explicit:

* First, keep the bounded Settings/capture/operation repairs separate from
  framework extraction. They are evidence of particular losses, not a reason
  to invent a universal controller.
* Next, use RepoWindow plus the production Settings pattern and Components
  fixture adapter. RepoWindow stresses identity, history, selection and
  provider refusal; Settings stresses dirty, revision, retry and return.
  Components must consume the same model, not a local catalogue imitation;
  its review found no fixture-adapter seam and no proof of production parity
  (`docs/internal/betterment/native-experience/adversarial/components_reference.md:27-50`).
* Before broad collection rollout, use the active Thought workspace as the
  adversarial second consumer. It breaks the false assumption that every
  app is a collection or form: caret/selection, IME, voice-at-caret, undo,
  dirty document and close/reopen all have different ownership. Ask/source
  handoff should follow as the async/source/egress consumer. Choosing Ask
  instead is a valid faster test of async work, but leaves the most dangerous
  input abstraction unchallenged; choosing People next would mostly confirm
  the collection abstraction.

## Settled, proposed, unknown

**Settled:** React/TypeScript/DOM, current Desk compositor, Zustand, RuntimeBus,
FastAPI and native adapters remain (`docs/internal/betterment/native-experience/README.md:6-24`); Workbench meets Pop!_OS
material, illustrated icons, library components, no modal/prose UI, and the
owner’s live aesthetic judgment remain canon (`docs/internal/UX-CANON.md:17-48`).
Presence stays disabled. Existing command registry, compositor, mic authority,
native editing, receipts and specialized terminal/editor/media boundaries are
to be preserved, not replaced (`docs/internal/betterment/native-experience/README.md:96-108`; `docs/internal/betterment/native-experience/DELIVERY-PLAN.md:27-31`).

**Proposed:** application/view contracts; explorer as an acceptance workload;
typed provider adapters; per-window selection/history; explicit command
context; pattern/reference adoption; optional headless behavior sources; and
the pilot and evidence sequence. None is shipped canon (`docs/internal/betterment/native-experience/README.md:21-24`).

**Unknown:** same-resource multi-window identity; exact supported Git/file
mutation boundary; lifecycle ownership across minimize/unmount/reload; command
scope precedence; read/operation/domain state mapping; and whether the first
patterns are pleasant. No owner-state walk, quantitative performance run,
assistive-technology run, WebKit application task, or native-host validation
was performed (`docs/internal/betterment/native-experience/README.md:49-56`).

CONDITIONS:

1. Settle the identity/lifecycle table and same-resource instance policy before
   package 0 is briefed.
2. Settle the command-context/selection/voice boundary and the read-versus-
   operation state map using existing receipts and provider authority.
3. Name the RepoWindow → Settings → Thought/Ask falsification sequence and
   its paired task evidence; keep Components fixture-backed by the production
   models. Do not turn these conditions into a 47-stage gate.

MISSED:

1. The active-versus-parked route boundary (Thought workspace vs retained
   NoteEditor; Project Room vs DrawerWindow) can send a worker to the wrong
   consumer (`docs/internal/betterment/native-experience/adversarial/SYNTHESIS.md:41-49`).
2. Repo branch/stage/commit and file read/write authority need a provider
   matrix before “editing” or “transfer” is promised (`docs/internal/betterment/native-experience/adversarial/explorer_repo.md:27-35`).
3. Narrow lookup and target visibility in Components are ergonomics risks,
   not merely catalogue polish (`docs/internal/betterment/native-experience/adversarial/components_reference.md:52-63`).

TUESDAY: Not yet—the packet points at the right work, but the owner cannot yet rely on two resource windows, a preference edit, and a return path sharing one honest framework.

UNKNOWN: This is a source-level strategy review. I ran no tests, build, live
Desk walk, provider/native action, assistive-technology run, performance
benchmark, or owner acceptance session; I did not repeat the 47 independent
reviews or claim their 204 challenges were executed.

## Re-check — refined strategy draft, 2026-10-23

**DRAFT — advisory strategy re-check, not Muad’Dib check; still UNCHECKED —
awaiting Muad’Dib.**

RECHECK VERDICT: RATIFY-WITH-CONDITIONS

The refinement substantively answers the owner’s request. It is now a strategy
with choices, counterexamples and an order, not a paraphrase of the audit. The
three consequential decisions are explicit: (1) two same-repository locations
have separate stable window instances while view, document and operation
ownership remain distinct (`docs/internal/betterment/native-experience/STRATEGY.md:44-55`);
(2) commands are classified by scope and voice macros remain distinct from
contextual proposals (`docs/internal/betterment/native-experience/STRATEGY.md:48-53`); and (3) provider reads, drafts,
requests, operations and domain outcomes are not collapsed into one status
(`docs/internal/betterment/native-experience/STRATEGY.md:51-54`). The sequence now genuinely falsifies the abstraction:
resource first, Settings and active Thought next, then Ask/source handoff
(`docs/internal/betterment/native-experience/STRATEGY.md:86-118`). This is supported by counterexamples rather than
generic warnings: repository deduplication and unwired file opening
(`docs/internal/betterment/native-experience/adversarial/explorer_repo.md:27-35`), the Components reference’s missing
fixture seam (`docs/internal/betterment/native-experience/adversarial/components_reference.md:27-50`), and active Thought
versus retained editor input semantics (`docs/internal/betterment/native-experience/adversarial/native_input.md:10-19`). It
also keeps the existing W/F/S/N/C/E/V/T/X/A/O/K/P evidence axes and
separates render correctness, task completion and delight rather than adding a
new catalogue or acceptance rail (`docs/internal/betterment/native-experience/STRATEGY.md:65-84`; `docs/internal/betterment/native-experience/STRATEGY.md:138-150`).

FINDINGS:

1. **P1 — provisional performance-budget language remains a boundary risk.**
   The strategy correctly says to collect production traces before choosing a
   budget (`docs/internal/betterment/native-experience/STRATEGY.md:138-150`), but the revised delivery plan still carries
   numeric working targets for 100ms feedback, INP 200ms, frame periods, and
   1/5/10/20-window cost (`docs/internal/betterment/native-experience/DELIVERY-PLAN.md:136-148`). They are labelled
   proposed, not gates, so this is not a contradiction in the architecture;
   it is still easy for a later brief to turn them into invented owner
   acceptance or a merge budget. Keep them observational only, or remove the
   target numbers until a real scene and owner job justify them. No new budget
   or approval process is warranted by this strategy.

2. **P1 — the design checkpoint and Thought counterexample need one explicit
   sentence of sequencing.** The immediate design step asks for resource and
   preference compositions (`docs/internal/betterment/native-experience/STRATEGY.md:86-93`), while the next challenge is
   active Thought with IME, voice and undo (`docs/internal/betterment/native-experience/STRATEGY.md:101-106`). UX-CANON
   requires the face canvas before build (`docs/internal/UX-CANON.md:56-59`).
   If Thought is only a later challenge, say so; if it is the second pilot,
   include its settled canvas and ownership decisions in the design packet
   before implementation. Otherwise the refined order can still permit the
   exact “build then discover the exception” cycle it is meant to prevent.

CONDITIONS:

1. Mark the delivery-plan performance numbers as non-acceptance observations
   (or defer them); do not let them become owner budgets, merge gates or a new
   approval rail.
2. Align the immediate design checkpoint with the stated pilot: resource,
   Settings and Thought compositions/ownership must be settled before their
   respective implementation, with Ask remaining the later transition job.
3. Preserve the current explicit boundaries: provider/Git mutation authority,
   Components fixture adapters, active-versus-parked routes, and specialized
   editor/terminal/media behavior. These are the source/fixture counterexamples
   that keep the three decisions honest, not a new backlog of guards.

TUESDAY: Yes as a plan, conditionally—the owner can now see a short path from resource inspection through editing and Ask, but the plan must prevent provisional timing numbers and an unsurfaced Thought canvas from becoming implementation law.

UNKNOWN: No tests, build, live Desk walk, provider/native action, performance
measurement, accessibility task, or owner acceptance was run for this
re-check. The refined documents remain proposals; no product lane was started,
and this re-check does not redo or upgrade the 47 independent reviews.

## Root disposition after the re-check

Astra removed the provisional timing targets from the delivery plan and
retained a local measurement protocol. The immediate design checkpoint now
explicitly includes the active Thought editing counterexample alongside the
resource/preferences canvases. These are proposed design deliverables, not
completed canvases or executed user evidence. The advisory conditions do not
constitute Muad'Dib's check; the strategy remains DRAFT and UNCHECKED.
