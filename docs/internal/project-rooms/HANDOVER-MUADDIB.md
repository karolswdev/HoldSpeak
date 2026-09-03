# HANDOVER: MUAD'DIB III — the orchestrator's mind, serialized a third time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-03 at the close of the
session that chartered, built, owner-verdicted, counsel-ratified and
PR'd Phase 166 The Jira Parity (P7) — the LAST §14 slice. Muad'Dib II
(below, kept verbatim) still holds; this edition carries what changed.

## 0. The soul, re-proven harder

OWNER TRUST is the only currency — and this session SPENT it once:
the first Jira face was assembled by a worker from label:value rows
and prose, I bounced pixels twice, and the owner said "I absolutely
hate the UX of this thing ... Walls of text..., complete disregard to
our component". The repair: HALT, write a settled design on the
surface library, publish MOCKUPS (the `design` canvas skill, real
token values, both widths), get his word ("HECK YES, a BIG YES to
this."), THEN rebuild — and read every PNG every round. LAW (in
memory as face-design-before-build): no new face is built before the
owner has ratified its design on the library.

## 1. The state of the world (2026-09-03)

- **PR #532 MERGED** → main `31c072f5` on the owner's word (2026-09-03,
  "yes the PR is fine, I gave my word..., you know?"); the next
  session chartered Phase 167 The Room in Use (his pick over the
  model-era collapse, 155 The Crew, Gate B). What follows was true
  at the close of the 166 sitting: PR #532 was OPEN
  on the local gates (suite 19f/9201p, sweep zero unexplained; web
  2358 zero branch-new; counsel RATIFY-W-C paid). **MERGE WAITS FOR
  THE OWNER'S WORD** on the two galleries (the face on the rig
  ba57d6bd-…; the live walk on his site da7d9db9-…). The design
  canvas he ratified: 85d15031-…. If he says merge: `gh pr merge 532
  --merge` (create and merge are SEPARATE gh calls — the classifier
  blocks a chained create+merge), then main = the merge commit, then
  update memory (arc: ELEVENTH phase merged; the SRS V0 slices
  P0..P7 all merged).
- **The arc after P7:** V0 COMPLETE. Post-arc menu (NO NEW CHARTERS
  WITHOUT HIS WORD): Gate B partner feedback; MCP-008 remote
  (deferred by design); the debt ledger (final-summary.md of 166 —
  incl. the second-target proof: the owner holds ONE acli account,
  multi-site was fixture-tested only; MCP_SIDECAR's stale
  per-family counts; the population toggles are visual state; the
  per-process acli lock); the parked backlog (155 The Crew, the
  model-era collapse).
- **The owner's practice site:** karolsaneapple.atlassian.net,
  project KAN (3 issues; KAN-1 due 2026-09-10). acli 1.3.36 at
  /opt/homebrew/bin/acli, OAuth; auth lives with HOME (an isolated
  HOME = unauthorized). The walk (tests/e2e/test_hs166_jira_walk.py)
  is LIVE: it transitions KAN-1 and reverts in a finally; it skips
  honestly (a collectable skipif) without acli auth.

## 2. The laws this session added (append to §7 of the old canon)

- **Design the face before building it** (above). Workers compose
  library species; the mockup sources (.dc.html) are the reference;
  zero sentences; the egress chip names the real host.
- **A rig that can skip a step is theater**: every step asserted,
  scrolled into view, shot at both widths; "no visual changes
  needed" from a worker means READ THE PNGS YOURSELF.
- **The live site is the only judge of some lies**: the URL-form
  identity split, `calls` dropped by a decoder whitelist, an empty
  test that was a fixture answering no JQL, a day-early date — none
  visible with fakes. Every provider story gets a live proof script.
- **The 163 same-watermark law (§9.3)**: a second MANUAL run at the
  same watermark IS created and RECONCILES at the act step; Gate 4's
  existing-run dedup belongs to the conductor DRAIN only. The walk's
  route-level dedup broke the 163 glass — counsel ratified it and
  the sweep caught it; never assert "replay → same id" on the route.
- **The false baseline**: finalize claimed baseline_state=established
  with no snapshot — a provider-agnostic inherited lie that made the
  first unattended tick a false discovery. Now finalize baselines
  for real; a failed fetch leaves `pending`.
- **Composition seams hide `if None` skips**: the Delta service was
  composed without project_service so item creation silently
  skipped — characterization-test the WEB context's composition, not
  a unit fixture's.
- **dw's row flip**: `dw story status … done` flips the phase table
  row too; python cadence edits must not assert the row's old state
  (two repair commits on 166-06).
- **acli truths**: `workitem search --fields` refuses duedate/
  resolution/updated (view accepts all → N+1 enrichment, calls
  reported); Jira Cloud search is eventually consistent (~3-6 s);
  team-managed Done issues carry no resolution (status_category is
  the completion signal); `acli` cannot set due dates.
- **Sweep collection**: a module-level pytest.skip breaks collection
  by node id ("found no collectors") and aborts the whole candidates
  run — use a skipif marker.
- **The main baseline** must be refreshed from the branch BASE
  commit's CI run (`gh run view <id> --log-failed | grep FAILED`);
  a dead scratchpad list is not a baseline.

## 3. The toolbox (session-scoped; recreate freely)

story166-NN-verify.sh wrappers (pipefail; scoped suites in isolated
HOME + a LIVE proof script with real HOME); live166-NN.py; the
close: close-suite-166.sh in two halves (unit / the rest, each
`-n auto`, ~13 + 8 min) + story166-07-verify.sh (totals from the
saved halves, `comm` vs main-failed-names.txt, the candidates re-run
with ids read into a bash ARRAY — unquoted `[1440]` is a glob —, the
live walk, web, the flake x2); the galleries are python-built HTML
with base64 PNGs published as NEW artifacts per phase (the old
stable-URL rule needs a full read of the prior page first).

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim,
fix the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Jira Parity sitting)

---

# HANDOVER: MUAD'DIB II — the orchestrator's mind, serialized again

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-02/03 at the close of the
session that merged THREE phases (163 The Steward's Hand #529, 164
The Unattended Desk #530, 165 The MCP Family #531) — the eighth,
ninth, and tenth Project Rooms phases — each chartered, built,
owner-verdicted, counsel-ratified, and merged inside one sitting.

---

## 0. The one-paragraph soul (unchanged, re-proven)

OWNER TRUST is the only currency. Every claim is backed by output
you personally read; every face passes your eyes before his; every
worker report is re-verified with your own hands before anything
flips. Speed and paranoia are not in tension: paranoia is WHY you
move fast. This session's proof: eleven orchestrator catches on
worker output, every one real (see §5).

## 1. The cast (unchanged)

- **The owner**: karolswdev. Verdicts close every face story; his
  words recorded VERBATIM, bounces and passes alike. This session:
  163 PASS (one round); 164 round-1 Bounce (scroll affordance + his
  model-wiring question — a question IS a finding) then PASS; 165
  PASS (Gate B ready, one round). He asked the arc's remaining
  length and ordered the WIND-DOWN: finish 165, hand over, zero
  context. NO NEW CHARTERS without his word.
- **The Fedaykin (opus-worker)**: all delegated work,
  claude-opus-4-6[1m], never Fable subagents. Workers run SCOPED
  tests only; you own every full gate.
- **You**: commit, verify, judge pixels AND wire transcripts, talk
  to the owner, write the PMO records, carry the memory.

## 2. The state of the world (2026-09-03)

- **The arc**: §14's slices P0..P6 are MERGED (#521 #522 #523 #524
  #525 #527 #529 #530 #531 — ten phases; 165's merge = main
  ddd4b050). **P7 The Jira Parity is the LAST slice and the owner
  RATIFIED it, verbatim: "Yes, I will want Jira parity."** Charter
  it FIRST thing next session (phase-166, branch
  feat/project-rooms-p7-the-jira-parity): §14 P7 — a real Jira
  provider adapter for site/Project/type/status discovery and issue
  search; compile/test/baseline/poll semantic issue Watches; exit =
  Jira readiness backed by LIVE discovery/search and the same
  no-duplicate Delta/action behavior, never pushed fixtures alone.
  Natural riders from the 165 ledger: the sidecar fetcher-seam fix
  (a provider-injection shape serves both gh and Jira), the
  legacy-side watch guard, the scheduled-path trigger wire. After
  P7 the SRS arc's V0 is COMPLETE; post-arc: Gate B partner
  feedback, MCP-008 remote (deferred by design), the debt ledger,
  the parked backlog (155 The Crew, the model-era collapse).
- **main**: ddd4b050 (the 165 merge, PR #531). Branch hygiene: phase branches merge via PR + merge
  commit; local gates are the substance (the owner's standing
  posture — record the basis on the PR, never wait the serial CI
  Unit job).
- **The verdict gallery artifact**: ONE stable URL
  (2e2e5683-e617-4f73-8ca9-5fee04ba78b7), republished per phase
  from the scratchpad's update-room-shots.html (same file path =
  same URL within a session; from a NEW session pass url= and READ
  it first). 165's round proved a gallery can be a WIRE TRANSCRIPT
  (no pixels — the face is the wire) when the phase is driver-side.
- **The debt ledger** (re-list at every close; the 165
  final-summary carries the full set): 165's eight counsel N + the
  legacy-side watch guard + the sidecar fetcher seam + per-watch
  cadence write wire + the scheduled-path trigger route; 164's
  five N + others; 163 S-4/N-1/N-3; 160 N-5/N-1/N-2; 158
  S-1/N-1/N-3; 159 seeding walls; 161 N-1.

## 3. The turn discipline (unchanged, one addition)

Privately enumerate needs with dependencies; request EVERYTHING
independent in one response; end the turn when all remaining items
depend on pending results; never poll (background tasks notify);
never predict a pending agent's result. ADDITION: the wrapper's
`echo SUITE_EXIT=$?` after a piped tail LIES (pipe exit) — the
totals line is the only truth; and a `; echo ===X===` chain in zsh
dies on `=`-prefixed words (equals-expansion) — use plain markers.

## 4. The story loop + the close liturgy (unchanged from Muad'Dib I)

Brief hard (verbatim intent, READ-FIRST file:line anchors, laws,
scoped commands, STOP CONDITIONS, REPORT BACK ending in SURPRISES);
re-verify with your own hands; evidence wrappers through dw capture
with the tail READ; flip; cadence by anchored python (assert-in;
a failed assert means READ, never force); stamped contract read
before every flip; msg files always python-written. Close: owner's
PASS -> flip 05 -> full suite background + counsel parallel ->
sweep (isolation x2 + git-log = the protocol; mid-run artifacts
re-run on the settled tree) -> churn restored BEFORE staging ->
final-summary -> COMPLETE 7/7 -> PR (create and merge as SEPARATE
gh calls — the classifier blocks chained create+merge) -> merge.
GATE LAW learned twice: evidence-story-NN ships ONLY in the commit
that flips its story done — a functional commit carrying evidence
is refused.

## 5. The scars that became laws THIS session (append to §7 of the old canon)

- **Production seams prove themselves**: 163's door idem key was a
  phantom held up by a unit fixture that hand-seeded the very key it
  asserted (the 161 scar reborn). When a fixture writes what only
  production should write, the test lies.
- **Rigs BUILD FIRST**: the 163 rig had no npm build step — stale
  pixels with fresh timestamps, caught live. Every shot/walk wrapper
  builds before it runs.
- **Version pins hide under lying names**: two v-pin tests asserting
  ==70 were named _is_69. On every schema bump: grep EVERY
  `SCHEMA_VERSION ==` in tests/ and rename honestly.
- **Crippled-service construction**: 164's conductor blocks built
  bare services (no fetcher, None collaborators) — green in
  fake-injected tests, dead in production. The cure is the
  set_scheduler_services injection seam (mirror set_broadcast);
  unwired = honest skip. The MCP twin: the sidecar's
  _watch_service() still composes no fetcher (ledgered).
- **Theater tests**: 164's block-isolation tests simulated try/
  except inline and touched nothing real — rewritten against the
  REAL _tick. If a test can pass with the product deleted, it is
  theater.
- **SurfaceLedgerRow's 52px time column**: primary lands in the
  time slot when no time= is passed — always pass time= (or lead=).
  And a wrapped token inside a ledger row clips its siblings —
  tokens nowrap.
- **Attention outranks configuration**: a broken source renders
  FIRST (the 164 circuit section move). Scrollable wells announce
  themselves (the Door scroll-hint species, ported vertical — reuse
  it for any scrolling well).
- **Egress badges exactly where egress happens**: the MODEL chip on
  create_proposals over-claimed (the Delta is deterministic,
  DEL-007). The owner's questions expose these — answer them
  plainly AND treat them as findings.
- **Copies drift; delegate**: serializers, provider lists — import
  from the one source (the resources.py precedent). Copied route
  glue goes in a REGISTER for counsel.
- **Docs must not promote**: 165's docs upgraded 'conceptual
  ownership' to 'enforced both directions' without code. The doc
  drift guard + the roadmap-vocabulary guard are allies; run them.
- **The watermark contract is caller-carried**: same-watermark
  dedup keys live ON the act step (project:watermark scoped; empty
  watermark = run-scoped, no contract); manual presses are governed
  by the follow-through read-back (only ever the NEXT uncovered
  item).
- **Wake dormant machinery as designed, never bypass**: 165-03's
  STOP found the 161 effect tables with zero callers; the ruling
  wired them properly (rules match, effects record, run_due
  drains). Trace-first briefs with STOP CONDITIONS are where these
  are caught.

## 6. The toolbox (scratchpad is session-scoped — recreate freely)

orch-scoped.sh (cd repo; HOME=$(mktemp -d); PLAYWRIGHT_BROWSERS_PATH
=$REAL_HOME/Library/Caches/ms-playwright; pytest "$@") — THE way.
story<phase>-<n>-verify.sh wrappers; msg-*.txt; pr-*-body.md;
main-failed-names.txt (27 names @ run 33459107466 — STILL VALID
through the 165 close by reasoning: only branch-new fixes merged;
refresh from a fresh main run if candidates smell like drift);
close-suite-<phase>.txt; update-room-shots.html (the gallery).

## 7. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never hedge about what you verified; never claim
what you didn't; the owner's bounces are gifts — answer the exact
words, record them, fix the root; scars become laws in memory.

— Muad'Dib, session 015wvZJuEHkmosZR349Mv9J8 (the three-phase sitting)
