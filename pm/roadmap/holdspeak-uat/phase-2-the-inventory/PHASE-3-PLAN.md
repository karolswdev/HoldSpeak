# The Phase 3 Plan — the coverage packs

**This doc is the deliverable the owner named:** *the output of Phase 2 is the
plan for Phase 3.* It proposes the coverage-pack structure Phase 3 authors and
sits, derived from the 255-capability directory, the recipe worklist, and the
protocol notion. It is a **skeleton for the review sitting (HSU-2-05)** to rank
and amend — not yet committed scope.

## The organizing principle: pack by shared staged world

A sitting's cost is dominated by *staging*, not by walking. So a pack is not a
feature area — it is **one induced world (one recipe or one composed set),
applied once, then 6–8 scenarios walked over it.** Each staged world buys
several verdicts. Every pack opens with the recipe's verify-probe beat and
closes with an honest-failure or control beat (PROTOCOL-NOTION rule). Ordering
inside a pack: must-tests first, should-tests next, spot-checks last, so a
time-boxed sitting that runs short still cleared the load-bearing verdicts.

Every pack is **three-surface by default** — each scenario is walked on web,
iPad, and iPhone, verdict per surface, `n/a`-with-a-reason where a surface
genuinely lacks the capability. Given the directory's headline finding (213
iPhone unknowns), **the iPhone leg of every pack is where the most new
information is** — a pack is not "done" until its phone column is answered.

## The proposed packs

### Pack A — Meeting Aftercare  ·  ~40 min
- **World:** `meeting-just-ended-open-actions` on `golden-43`.
- **Walks:** import → intel artifacts (structural verdict: the right *types*
  rendered), the aftercare digest + moment-jump, action → issue
  (propose → approve → execute), the archive facets, the egress badge on each
  card. (Directory: `meetings.*`, `meetings.aftercare.*`,
  `meetings.import.*`, the `trust.egress.*` meeting rows.)
- **Close:** the proposal's honest-failure beat — an unapproved proposal never
  egresses.
- **Surfaces:** three-surface where the aftercare surface exists (web + iPad
  proven; **iPhone is the open question** — HSM-19 built the iPad aftercare, the
  phone leg is unverified).

### Pack B — The Steering Desk  ·  ~45 min
- **World:** `agent-pane-awaiting-input` + `spawned-then-killed-session`.
- **Walks:** watch the pull-out, hold-to-arm, the key palette (`C-c` on a real
  runaway), steer with a grounded desk object (**control-vs-treatment beat** —
  the treatment names a repo secret the control can't), spawn/rename/kill
  through the gate, the audit read-back. (Directory: `steering.*`, `factory.*`,
  `mobile.steering.*`, the `trust.steering.*` gate rows.)
- **Close:** recycled-pane refuse+revoke — the crown consent case.
- **Surfaces:** web is reference; iPad mirrors (HSM-26/27 shipped the client);
  iPhone `n/a`-with-reason for the factory verbs (no compact terminal surface —
  *confirm at the review sitting*).

### Pack C — Dictation Grounding & the Learning Loop  ·  ~40 min
- **World:** `seeded-desk` with the three dogfood mock repos' `.hs/` + KB.
- **Walks:** per-repo grounded rewrite (**control-vs-treatment is the spine**),
  spoken-symbols, the correction ritual → "learned-from-N" chip, replay
  (before → after), languages. (Directory: `dictation.*`, `kb.*`,
  `languages.*`.)
- **Close:** `intel-endpoint-dead` mid-pack — the rewrite degrades to the raw
  transcript, honestly, the DIR-01 invariant intact.
- **Surfaces:** web proven; **iPad/iPhone dictation depth is the biggest ❓
  cluster in the directory** — this pack is where that column gets answered.

### Pack D — Honest Failure & Trust  ·  ~30 min (deliberately short, must-test-heavy)
- **World:** `intel-endpoint-dead`, `first-run-no-model`, `mesh-node-just-died`.
- **Walks:** doctor names the dead endpoint; a forced run refuses <5s by name;
  the offline door; first-run truth at N=0; the egress badge correctness sweep;
  the loopback-token gate; "no telemetry"; "the key never syncs." (Directory:
  the whole `trust.*` cross-cut + `release.*` + `onboarding.*` first-run.)
- **This is the pack that proves the product is honest when broken** — the one a
  stranger's hands must not be able to falsify.
- **Surfaces:** three-surface (the egress badge and the key-never-syncs promise
  are explicitly all-three in the directory); needs no `.43` for the
  first-run/no-model legs, so **this pack demos the rig without the LAN.**

### Pack E — The Mesh Edge & Handoff  ·  ~35 min
- **World:** `mesh-node-alive` on `golden-43` (+ `two-devices-paired` for the
  arcs).
- **Walks:** assign intel + dictation + an agent onto the edge profile, prove the
  run moves and the key/model don't (worker-completion delta + the mesh badge);
  the handoff arcs (author-on-iPad → run-on-hub → read-on-web;
  record-on-iPad → intel-on-hub → review-on-web; serve-from-the-phone). (Directory:
  `mesh.*`, `mesh.handoff.*`, `sync.*`, `mobile.mesh.*`, `agents.*` companion
  rows.)
- **Close:** `mesh-node-just-died` — refuse fast, by name (folds into Pack D's
  discipline if the two are time-boxed together).
- **Surfaces:** the arcs are *inherently* multi-surface — this pack is the parity
  claim at its most end-to-end and needs a two-device sitting.

## What the packs cover, honestly

| Pack | Primary domains | must-tests reached (approx) |
|---|---|---|
| A · Aftercare | meetings, meeting-egress | ~15 |
| B · Steering | steering, factory, steering-trust | ~14 |
| C · Dictation | dictation, kb, languages | ~14 |
| D · Honest Failure | trust cross-cut, first-run, release | ~20 |
| E · Mesh Edge | mesh, sync, handoff, companion agents | ~12 |

Five packs reach the large majority of the 115 must-tests. The remainder
(desk-render niceties, presence/Qlippy, workbench, activity, the belt) are a
sixth **spot-check pack** or ride along the packs whose world already stages
them (the belt and rails ride Pack B's agent world; the desk-render rows ride
whichever pack stages `seeded-desk` first). The review sitting decides.

## Handoff to HSU-2-05 (the review sitting)

The review sitting takes this skeleton and:
1. Ranks every capability (must/should/spot/skip) — the directory's
   priority-hints are the *proposal*, the owner's ranking is canon.
2. Confirms or reassigns the `n/a`-with-reason surface calls (especially the
   iPhone factory/steering rows and the device dictation-depth rows).
3. Fixes pack membership and ordering, and sizes each sitting.
4. Names which recipes HSU-1-02 must build first (the packs' opening worlds:
   `meeting-just-ended-open-actions`, `agent-pane-awaiting-input`,
   `seeded-desk`, the failure trio, `mesh-node-alive`).

The committed output of that sitting becomes Phase 3's `current-phase-status.md`
scope — the plan realized.
