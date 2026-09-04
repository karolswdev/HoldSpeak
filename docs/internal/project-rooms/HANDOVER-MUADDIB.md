# HANDOVER: MUAD'DIB VI — the orchestrator's mind, serialized a sixth time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-04 at the END of the
Connections Door sitting — after the owner WALKED THE BRANCH ON HIS
DESK AND BOUNCED. Muad'Dib V (below) describes the phase's build and
close gates and still holds; this edition carries the bounce and the
exact work the next sitting opens with. NO NEW CHARTERS. Pay the
bounce, re-walk his desk, ask again.

## 0. His words, verbatim (2026-09-04, on http://127.0.0.1:53379)

"unacceptable UI work..., see how the TIMELINE, DECISIONS, SEARCH, ASK
are just completely off to the side of the window, as on this
screenshot... second to this..., I really don't understand why
everything's still so complicated. The tool suggestions are still not
obvious AT ALL, it's not obvious I have to click them to then scroll
within that same dialog to test them, validate them, and so on. I'm
telling you - this stuff is still not streamlined at all..." — "so
prepare another Muad'Dib."

## 1. The two roots (anchored this sitting; NOT paid)

1. **Wings escape the Room window on a long title.**
   web/src/desk/components/pullout.css:284 —
   `.desk-pullout-head.has-wings .desk-pullout-title { flex: none }`
   (HS-100-07). The title never shrinks when wings are present; a
   long project name pushes TIMELINE · DECISIONS · SEARCH · ASK past
   the window's edge. Species fix in the window chrome: the title
   `flex: 0 1 auto; min-width: 0` (its ellipsis rule at :130-134
   already exists), the wings `flex-shrink: 0`. Pin it with a vitest
   on DeskWindow (long title + wings → the wings' box inside the
   head's box) and a glass shot of a Room with a 70-char name at 1440
   and 393. Check every OTHER head with wings (grep `has-wings`).
   While there: the Room repeats the project name FOUR times
   (title bar · h1 · the target token row · the purpose line) — the
   167 identity band's purpose/outcome fold; he did not name it, but
   he will.
2. **The Sources step is not legible.** SetupRoot.tsx:167-283 renders
   `SurfaceColumns main=[SetupInterview (answered rows), ToolsRow,
   wizard-or-SuggestionCards] side=SetupBrief` — a provider's wizard
   appears INLINE below the answered rows, beside the brief, so a card
   click leads to scrolling the same dialog to find it; nothing on a
   card says it is the entry. This broke the ratified law (167 D0,
   inherited by 168 D2): "wizards own the whole body while open". The
   amendment is recorded in assets/settled-design-connections.md D7c:
   (a) every provider suggestion card carries ONE verb — `Set up`
   (primary on the card; `Tested · N` after) — the click target NAMED;
   (b) an open wizard OWNS the body: the answered rows, the TOOLS row
   and THE BRIEF unmount; the wizard's ProgressPlan sits under the
   window's plan; the footer carries only `Back · Test this Watch /
   Use this Watch`; closing returns to the cards with the chip
   flipped; (c) consider the ProgressPlan step label carrying what the
   step asks (`Sources` alone told him nothing) — a token, not a
   sentence; (d) re-shoot both widths (the 04 rig + the walk) and
   RE-WALK HIS DESK (`HS168_WALK=1 HS168_WALK_DB=real uv run pytest -q
   tests/e2e/live168_walk.py`) before asking him again.
   Design first? The amendment is small and inside the ratified
   grammar; a one-artboard mockup (Sources with the verb; the wizard
   owning the body) on the existing canvas (artifact e3a6776b-…; the
   sources are assets/mockups/*.dc.html) is cheap insurance — do it,
   show him, then build. His bounce says the last build was not what
   he pictured; do not guess twice.

## 2. The state of the world

- Branch feat/connections-door, HEAD = this handover's commit. 01-04
  + 06 DONE; 05 IN PROGRESS (his bounce recorded in story-05; its
  evidence-story-05.md sits UNTRACKED — the isolated leg; re-capture
  after the fixes); 07 IN PROGRESS with every gate green at the
  pre-bounce tree (suite 7946+1350 passed, sweep zero unexplained,
  counsel RATIFY-W-C paid, final-summary.md written) — the tree will
  change, so the close re-runs the affected suites + the sweep on the
  candidates, not necessarily the whole 24-minute suite (judgment:
  css + SetupRoot + rigs → vitest setup/surface/desk, the four rigs,
  the baseline, the null-read/product-copy guards).
- The hub from this sitting may still be running in the background
  on 127.0.0.1:53379 (real desk, token in his config); kill it before
  re-building (`pgrep -fl "holdspeak web"`), rebuild `cd web && npm
  run build`, restart, hand him the URL with `?token=` again.
- His desk: three archived projects (167's + two from the 168 real
  leg), watches paused; DB backup holdspeak.db.bak-hs168-005512.
- Post-phase menu unchanged (Muad'Dib V §1).

## 3. Laws this bounce adds

- **"Owns the body" means UNMOUNT the rest** — an inline wizard under
  other content is a scroll hunt, not a step.
- **A card that is an entry carries its verb** — a chip row is not an
  affordance.
- **A window's wings never leave the window** — titles shrink first.
- **Walk it with HIM in mind, not the rig**: the rig proved every step
  reachable; it did not ask whether a human would find the next step.
  Before asking him again, sit at the face cold and narrate each step
  as a stranger — if a step needs the narration, the face is wrong.

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim, fix
the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Connections Door sitting, second close)

---

# HANDOVER: MUAD'DIB V — the orchestrator's mind, serialized a fifth time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-04 at the close of the
session that chartered, designed, built, walked and closed Phase 168
The Connections Door — the front door for connectors, born from the
owner's bounce on his own walk of the Room. Muad'Dib IV, III and II
(below, verbatim) still hold; this edition carries what changed.

## 0. The soul, re-proven again

Four worker rounds on one story (04) because "all green" was said
over shots that showed a washed-out column, a footer on the desk
below the window, a heading with no name, an emoji emblem, sixty-
seven vitest skips called "selector edits", and Jira shots skipped
and called "acceptable". Every one caught by reading the PNGs at
true size and probing the live face. Paranoia is WHY you move fast.

## 1. The state of the world (2026-09-04)

- **Phase 168 ACTIVE 5/7 on feat/connections-door** (HEAD after the
  close commits: the sweep paid, final-summary.md written). Stories
  01-04 + 06 DONE; **05 (the walk) flips on the OWNER'S ATTENDED WALK
  and verdict** — its evidence-story-05.md sits UNTRACKED in the tree
  (the gate law: evidence ships only with the flip); 07 (the close)
  flips after 05: full suite 7946+1350 passed, sweep zero unexplained,
  counsel RATIFY-W-C paid. Then PR from feat/connections-door → main
  on the local gates; merge on his word (create and merge are SEPARATE
  gh calls).
- **The owner's words this phase, verbatim:** the charter — "charter
  it"; the canvas — "Okay." (read as PASS, said so to him); the live
  face — "dude. Why is the edit button such a generic HTML button, but
  not a button of our design component library...? — and also, why is
  the checkmark on one line and then the content on another..." (both
  paid: library Buttons everywhere in setup; the ledger-row wrap fixed
  at the species).
- **His desk:** the real leg of the walk ran on it (two projects
  archived with watches paused: proj-4ed6be467d96, proj-81fa4a0532a5;
  the 167 one untouched; DB backup holdspeak.db.bak-hs168-005512
  beside the DB). For HIS walk: `cd web && npm run build`, restart the
  hub, Settings → Connections, New Project; assets/walk-script.md.
- **Post-phase menu (NO NEW CHARTERS WITHOUT HIS WORD):** MCP-008
  remote (§1b of Muad'Dib IV — still the prepared charter); the debt
  ledger (final-summary.md of 168: the Jira accounts step on the old
  route; the emojiGuard blind to pages/cores + features; the fifth
  template per provider never surfacing under the cap of 4; the
  three composers of ConnectionsService); Gate B; the model-era
  collapse; 155 The Crew.

## 2. The laws this session added (append to §7 of the old canon)

- **The connectors' front door**: a tool is connected ONCE in Settings
  → Connections (one row, one state, one verb; the command in a well
  with COPY; no token ever crosses the face); the interview asks
  scope only; the TOOLS row lists every connector provider FROM THE
  WIRE (`GET /api/connections`) — on a cold desk the suggest step
  yields zero provider proposals, so the row is the only place a user
  learns GitHub exists.
- **Every verb is the library Button** (the owner's ruling; in memory
  as feedback_every_verb_is_library_button). `grep '<button'` before a
  face flips.
- **Rigs settle animations before every shot** (glass_infra._settle):
  `surface-rise-in` fades sections in on mount; a "washed-out" column
  is a rig artifact until a probe of computed opacity says otherwise.
- **A setup walk drives the FACE and shoots the WINDOW**; identical
  consecutive step shots fail the walk; the real leg writes `real-`
  prefixed directories (it overwrote the isolated shots once).
- **Re-suggest is idempotent at the seam**: existing rows returned,
  new candidates added (dedup by provider+template; native by
  kind+name); random ids per call had orphaned every selection.
- **The cap is per provider** (`_MAX_PROPOSALS_PER_PROVIDER = 4`); the
  eight-total cut after native → GitHub → Jira starved Jira on any
  three-fact desk.
- **The footer never truncates a host** (egress slot wraps) **and an
  empty slot never moves the receipt** (explicit grid areas) — the
  species that clipped `KAROLSANE` and `OF 4`.
- **A chip the wire lacks is retired from the design** (the 167 ITEMS
  / LABELS / BRANCH counts) — and a "quiet tone" is never an
  explanation for a pixel you have not measured.
- **Skips are theater**: a worker's `describe.skip("interface
  changed")` is a bounce, never a selector edit.
- **Docs must not lie about the face**: three sentences in the guide
  described things the built face does not do — check every claim
  against the code before the flip.
- **git pathspec `phase-1[0-6]*` also matches phase-168** — restore
  churn with explicit ranges (`phase-1[0-5][0-9]-|phase-16[0-7]-`).

## 3. The toolbox (session-scoped; recreate freely)

shot_artboards.py (per-.dc.html shots at true width via Playwright);
build_canvas.py (canvas.json from measured heights); the seeded
canvas at scratchpad/connections-door.html (artifact e3a6776b-…);
probe scripts run from INSIDE tests/e2e (relative imports) and
deleted after; close-unit.txt / close-rest.txt; main-failed-names.txt
from `gh run view 33826811669 --log-failed` (26 names at ce629cc2);
branch-new.txt = comm -13; candidates re-run serially.

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim, fix
the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Connections Door sitting)

---

# HANDOVER: MUAD'DIB IV — the orchestrator's mind, serialized a fourth time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-04 at the close of the
session that chartered, built, owner-verdicted (three words), counsel-
ratified and PR'd Phase 167 The Room in Use — the phase that made the
eight Project Rooms faces ONE Room on the surface library and put the
FIRST real project on the owner's desk. Muad'Dib III and II (below,
verbatim) still hold; this edition carries what changed.

## 0. The soul, re-proven again

Eight faces from eight sittings had drifted from the library; the
owner's real desk had ZERO projects. This session's proof of the soul:
every worker report re-verified by hand, and the catches that only
hands find — a build helper that trusted a stale marker (the 163
theater reborn TWICE: first the marker, then a build RACE leaving two
chunks with a marker newer than stale chunks); a species-level `6ch`
grid column overprinting every date cell on every recomposed face; a
submit inside a React state updater; a trigger route lying about
project scope; a local import making a name unbound on nine MCP
tool paths; a walk that archived a real project and left its watches
evaluating the owner's real providers on the tick (mitigated on his
desk within minutes; paid at the root). Speed and paranoia: paranoia
is WHY you move fast.

## 1. The state of the world (2026-09-04)

- **Phase 167 COMPLETE 8/8**; PR opened from
  feat/project-rooms-the-room-in-use → main on the local gates (full
  suite 24f/9220p, sweep zero unexplained; web 789 + baseline zero
  branch-new; the eight glass rigs 46 green; counsel RATIFY-W-C, all
  M+S paid). MERGE ON THE OWNER'S WORD. If he says merge: `gh pr merge
  <n> --merge` (create and merge are SEPARATE gh calls), then memory
  (the TWELFTH Project Rooms phase merged).
- **The owner's words this phase, verbatim:** the design canvas —
  "PASS — build it."; the whole-Room gallery — "PASS"; the attended
  walk — "Walk it later — close on the dry run." His attended walk is
  LEDGERED PENDING: his desk is set up (restart the hub on the branch
  build; walk the eight steps of assets/walk-script.md; the Tuesday
  question). The runner: tests/e2e/live167_walk.py (HS167_WALK=1,
  HS167_WALK_DB=isolated|real; real HOME; skip-guarded on gh + acli).
- **His desk after the walk:** one project (archived) `proj-102233e71c47`
  "The first real project through the whole Room, attended"; its two
  watches PAUSED and unattended OFF (the mitigation + the root fix);
  the DB backup `holdspeak.db.bak-hs167-163032` beside the DB.
- **Post-phase menu (NO NEW CHARTERS WITHOUT HIS WORD):** the attended
  walk; Gate B partner feedback; MCP-008 remote; the model-era collapse
  (backend); 155 The Crew; the debt ledger (final-summary.md of 167).

## 1b. THE NEXT SITTING: MCP-008 remote — charter it FIRST thing

**The owner's word (2026-09-04), verbatim:** "I want you to prepare
Muad'Dib IV for working on MCP-008, via a handover." That is his word
lifting the SRS deferral — MCP-008 is LATER/V2 "until after product
validation" (SRS_DOMAIN_DRIVER.md:512; Gate B in
SRS_PRODUCT_VALIDATION.md:249-258). Record in the charter that the
owner lifted the gate consciously; do not re-litigate it.

**The row, verbatim:** "MCP-008 | LATER/V2 | Current remote
transport/protocol, scoped remote identity, Tasks integration, and
ecosystem publication are deferred until after product validation."
MCP-001..007 are DONE (Phase 165, PR #531). This is the last MCP row.

**What exists (recon 2026-09-04, anchors re-verified):**
- The sidecar is stdio ONLY (holdspeak/mcp/server.py:116-151, protocol
  `2024-11-05` at :14; MCP_SIDECAR.md:945 "no network listener"). Its
  `handle_message()` is transport-agnostic (dict in, dict out).
- The sidecar ALWAYS runs as OWNER (holdspeak/mcp/auth.py:32); the
  HOLDSPEAK_TOKEN there is an identity LABEL, not a credential
  (MCP_SIDECAR.md:674-676). It opens the DB directly and composes its
  own bare services (the 165 fetcher-seam debt).
- The hub ALREADY serves authenticated HTTP off loopback for
  companions (iPad, AIPI-Lite) on LAN/Tailscale, no hosted relay
  (USER_GUIDE.md:1178-1179): bearer token = `config.meeting.
  web_auth_token` (holdspeak/web_auth.py:27-114 — header
  `X-HoldSpeak-Token`, `Authorization: Bearer`, or `?token=`); the
  middleware derives the principal from the credential
  (holdspeak/web_server.py:560-590; owner → agent credentials → node
  tokens → UNAUTHENTICATED); a non-loopback bind is REFUSED without a
  token (web_auth.py:73-89). `HOLDSPEAK_WEB_PORT` pins the port.
- `AgentCredentialStore` (holdspeak/principals.py:89-172) already
  mints per-identity tokens with TTL + revocation — the substrate for
  scoped remote identity. PROJECT_PALETTE (45 tools) is the palette
  mechanism (MCP-007).
- No SSE plumbing exists in the MCP layer (the hub's real-time channel
  is the WebSocket at /api/ws). Streamable HTTP (the current remote
  transport) arrived in spec revision `2025-03-26` — a protocol bump.
- "Tasks": the recon could not confirm a ratified MCP Tasks feature;
  MCP-003's run_id + explicit polling is the contract that exists.
  Verify against the current spec before designing; never build to a
  draft.

**The charter-ready chain (six stories; the 165 liturgy):**
01 The transport — a Streamable HTTP route ON THE HUB (FastAPI), behind
the existing `_web_auth_gate`, calling `handle_message()`; the remote
handler composes on the WEB runtime's live services (the conductor's
`set_scheduler_services` seam, the wired fetcher) — never the sidecar's
bare instances (this pays the 165 fetcher-seam debt); the protocol
version bumped honestly with its census.
02 Scoped remote identity — a non-OWNER principal per remote client
minted from AgentCredentialStore (TTL, revocation, owner-issued from
the desk), palette-restricted (PROJECT_PALETTE or a configured subset);
the kernel derives authority from the credential (Article XI:3); a
typed capability error for anything outside the palette (MCP-005).
03 Egress + receipts — every remote call kernel-admitted with a
terminal receipt (Article XI:2) and an EGRESS badge at the point of
decision (Article III:2) — reads included, since they cross the
network; the pipeline observer shows them; local stdio stays badgeless.
04 The long-running contract — MCP-003's run_id + polling over HTTP;
SSE push for run state ONLY if the spec's mechanism is ratified and
the Streamable HTTP notification channel fits; documented, tested.
05 The live proof — a second machine on the tailnet (the .43 Linux box
is the natural one; sandboxed Bash cannot reach the LAN — run the
client from a real shell) drives the SS15 scenario the 165 walk proved
over stdio, measured, with a transcript; the OWNER VERDICT. His hub:
`HOLDSPEAK_WEB_PORT=<port> holdspeak web` bound off loopback with the
config token (never paste the token into the repo).
06 The docs + the close — MCP_SIDECAR.md (generated — extend the
generator, never hand-edit counts), the companions section of the
guide, "ecosystem publication" named honestly as self-hosted
discoverability (the no-hosted-relay law), the debt ledger.

**Laws that bind it:** Article III (nothing leaves by default — the
listener is opt-in, disclosed by badge; no hosted relay); Article XI
(admission, receipts, the caller supplies neither principal nor
authority; custody — remote agents get bounded delegation, never
OWNER); MCP-001 parity (one implementation: remote = web = stdio);
ledger-not-gate (a flight recorder, not ceremony); the yolo rigor bar.

**Counsel's hunts to name in the charter:** a remote path composing
bare services (the 164/165 scar); a palette that leaks a tool through
an alias; an egress badge missing on a remote READ; a protocol bump
that silently changes a wire shape the 165 walk pinned; a credential
that never expires.

## 2. The laws this session added (append to §7 of the old canon)

- **Design the whole Room, not a face**: one design doc with a shared
  spine (identity band · ledger grammar · chip vocabulary · a plan
  species for anything that runs · ScrollHint · the footer), counsel
  reads it BEFORE the owner (18 findings paid: never retire a wing;
  never fabricate a chip the wire lacks; name real props).
- **A test that pins dead DOM shape gets a SELECTOR edit** — element
  types, class names, moved testids included. "Kept for test compat" is
  never a reason to keep hand-rolled markup. Say it in the brief.
- **Overprints are species bugs first**: when every recomposed row
  overprints, look at the grid template, not the faces (the `room`
  ledger template was born from a fixed `6ch` column).
- **The build-first helper compares the OLDEST built chunk against the
  newest source and never touches the marker**; two hashed chunks under
  the bundle = a build race = stale pixels. Grep the chunk for a new
  string before believing a shot.
- **Pixel-identical round N+1 shots = the bundle did not change.** Read
  timestamps AND content, never the worker's word.
- **Archive stops the watches** (list_due_watches excludes archived
  projects; archive pauses + unattended off; restore never auto-
  resumes). Any real-desk walk's finally disables unattended BEFORE
  archiving.
- **A local `from x import y` inside one branch makes `y` local to the
  whole function** — nine tool paths died of one worker's import. Hoist.
- **Version pins hide under lying names** (again): `is_44` → `is_45`;
  the project family 34 → 35; classify every new MCP tool in
  thread_tools._TOOL_CLASSES; regenerate the schema snapshot in the
  same commit as a column.
- **Thread-local side channels must clear on entry AND on the except
  path** (a failed fetch's calls count leaked into the next watch).
- **Candidates lists are branch-NEW names only** (comm -13 main branch),
  never the whole branch failure list — the sweep count lied by 8 once.
- **zsh gotchas**: `echo ===X===` dies on `=`-prefixed words; unquoted
  `$VAR` is NOT word-split (use arrays); `uv run` must run from the
  repo cwd; the rigs REWRITE older phases' shot PNGs — restore before
  staging (`git checkout -- pm/.../phase-1[0-6]*/assets`).

## 3. The toolbox (session-scoped; recreate freely)

shot-artboards.py (per-artboard shots of a design canvas at true size
via a one-artboard seed launched focused); measure.py (true rendered
heights of .dc.html roots); build-canvas.py (canvas.json + notes);
build-gallery.py (the verdict gallery: sheets + key pairs, ≤4 MB);
regen_schema.py (the canonical schema snapshot); close-unit.txt /
close-rest.txt (the two suite halves); main-failed-names.txt from `gh
run view <id> --log-failed | grep -oE 'FAILED tests/[^ ]+'` at the
branch BASE; branch-new.txt = comm -13 of the names.

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim, fix
the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Room in Use sitting)

---

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
